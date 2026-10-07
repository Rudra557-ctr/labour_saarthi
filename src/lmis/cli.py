"""LMIS Step 1 command line interface.

Every pipeline stage is one command, so a run is reproducible from the shell and
inspectable step by step. `make reproduce` chains them in order.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer

from lmis.common import paths
from lmis.common.registry import load_pilot_scope, load_registry
from lmis.conform.location import (
    build_census_district_candidates,
    build_location_alias,
    build_location_master,
    empty_location_change_event,
)
from lmis.conform.ncs import build_vacancy_by_sector, build_vacancy_by_state
from lmis.conform.nic import build_ncs_sector_to_nic_map, parse_nic_sections
from lmis.conform.plfs import build_labour_force_estimate
from lmis.conform.provenance import build_source_master, build_source_snapshot
from lmis.conform.census_b24 import parse_b24
from lmis.conform.ilostat import parse_ilostat_eco_occ
from lmis.conform.dgt_curriculum import (
    classify_trade_mapping_status,
    parse_dgt_curriculum,
)
from lmis.conform.msde_trade_supply import parse_trade_level_supply
from lmis.conform.nqr_qfile import build_supply_evidence_matrix, parse_qfile_nco_mapping
from lmis.conform.msde_training import (
    parse_training_infrastructure,
    parse_training_outcomes,
    parse_training_trades,
)
from lmis.conform.udyam import build_establishment_district
from lmis.analytics import build as ab
from lmis.demand import estimate as de
from lmis.validate.schemas import SCHEMAS, validate as validate_table
from lmis.warehouse import load as wh
from lmis.publish import (
    build_envelopes,
    build_unavailability_register,
    lint_contract,
    lint_derivation_labels,
    lint_envelopes,
    lint_label_catalogue,
    load_contract,
)
from lmis.publish.contract import assert_no_experimental_leak, production_envelopes
from lmis.conform.occupation import (
    build_nco2004_concordance,
    build_occupation_master,
    parse_nat_snapshot,
)
from lmis.conform.period import build_dim_period
from lmis.conform.sector import parse_nqr_sectors
from lmis.ingest.acquire import acquire
from lmis.ingest.manifest import utc_now_iso, verify_snapshot
from lmis.profile.profiler import profile_parquet_dir, summary_markdown

app = typer.Typer(add_completion=False, help="LMIS Step 1 pipeline")


def _latest_snapshot(source_id: str) -> Path:
    base = paths.RAW / source_id
    snaps = sorted(d for d in base.iterdir() if d.is_dir()) if base.exists() else []
    if not snaps:
        raise typer.BadParameter(f"no snapshot found for {source_id}; run `acquire` first")
    return snaps[-1]


@app.command()
def sources() -> None:
    """List the source registry."""
    reg = load_registry()
    for sid, s in reg.items():
        typer.echo(
            f"{sid:30} {s['role']:9} {s['access_method']:14} {s['verification_status']:16} "
            f"geo={s['geo_level_available']}"
        )
    typer.echo(f"\n{len(reg)} sources registered")


@app.command()
def acquire_all(source_id: str = typer.Option(None, help="one source, or all if omitted")) -> None:
    """Acquire immutable raw snapshots. Existing files are never overwritten."""
    reg = load_registry()
    targets = [source_id] if source_id else list(reg)
    for sid in targets:
        if not (reg[sid].get("files") or reg[sid].get("paged_files")):
            typer.echo(f"{sid:30} SKIP (no downloadable files declared)")
            continue
        _snap, outcomes = acquire(sid)
        ok = sum(1 for o in outcomes if o.ok)
        skipped = sum(1 for o in outcomes if o.skipped_existing)
        typer.echo(f"{sid:30} {ok}/{len(outcomes)} ok ({skipped} already present)")
        for o in outcomes:
            if not o.ok:
                typer.echo(f"  FAIL {o.name}: {o.reason}")


@app.command()
def verify() -> None:
    """Re-hash every snapshot against its manifest. Exits non-zero on mismatch."""
    bad = 0
    checked = 0
    for man in sorted(paths.RAW.rglob("manifest.json")):
        problems = verify_snapshot(man.parent)
        checked += 1
        if problems:
            bad += 1
            typer.echo(f"FAIL {man.parent.relative_to(paths.RAW)}")
            for name, why in problems:
                typer.echo(f"   {name}: {why}")
    typer.echo(f"checked {checked} snapshot(s); {bad} with problems")
    raise typer.Exit(code=1 if bad else 0)


@app.command()
def build_masters() -> None:
    """Build occupation_master, sector_master, dim_period and the location tables."""
    paths.STANDARDIZED.mkdir(parents=True, exist_ok=True)
    paths.STAGING.mkdir(parents=True, exist_ok=True)
    ts = utc_now_iso()

    raw = parse_nat_snapshot(_latest_snapshot("NCO_2015_NAT_TABLE"))
    raw.to_parquet(paths.STAGING / "nat_table_raw.parquet", index=False)
    om = build_occupation_master(raw, "NCO_2015_NAT_TABLE", ts)
    om.to_parquet(paths.standardized_path("occupation_master"), index=False)
    conc = build_nco2004_concordance(raw, "NCO_2015_NAT_TABLE", ts)
    conc.to_parquet(paths.standardized_path("map_nco2004_to_nco2015"), index=False)
    typer.echo(f"occupation_master            {len(om):>6} rows")
    typer.echo(f"map_nco2004_to_nco2015      {len(conc):>6} rows")

    sec = parse_nqr_sectors(_latest_snapshot("NQR_SECTORS") / "nqr_sectors.html")
    sec.to_parquet(paths.standardized_path("sector_master"), index=False)
    typer.echo(f"sector_master               {len(sec):>6} rows")

    per = build_dim_period()
    per.to_parquet(paths.standardized_path("dim_period"), index=False)
    typer.echo(f"dim_period                 {len(per):>6} rows")

    lgd = _latest_snapshot("LGD_DISTRICTS_DATAGOVIN")
    lm = build_location_master(
        lgd / "lgd_states.csv", lgd / "lgd_districts.csv", "LGD_DISTRICTS_DATAGOVIN", ts
    )
    lm.to_parquet(paths.standardized_path("location_master"), index=False)
    n_states = int((lm.level == "STATE").sum())
    n_dist = int((lm.level == "DISTRICT").sum())
    no_census = int(lm[lm.level == "DISTRICT"].census_2011_code.isna().sum())
    typer.echo(
        f"location_master             {len(lm):>6} rows  ({n_states} states, {n_dist} districts; "
        f"{no_census} districts have no Census-2011 code)"
    )
    alias = build_location_alias(
        paths.MAPPINGS / "aliases" / "state_name_aliases.csv", lm, "PROJECT_ALIAS", ts
    )
    alias.to_parquet(paths.standardized_path("location_alias"), index=False)
    typer.echo(f"location_alias              {len(alias):>6} rows  (curated, reviewed)")
    change = empty_location_change_event()
    change.to_parquet(paths.standardized_path("location_change_event"), index=False)
    typer.echo(f"location_change_event      {len(change):>6} rows  (source publishes no change events)")

    nic = parse_nic_sections(_latest_snapshot("NIC_2008") / "NIC_2008.pdf")
    nic["source_id"] = "NIC_2008"
    nic["ingested_at"] = ts
    nic.to_parquet(paths.standardized_path("nic_section_master"), index=False)
    typer.echo(f"nic_section_master         {len(nic):>6} rows")

    ncs_map = build_ncs_sector_to_nic_map(ts)
    ncs_map.to_parquet(paths.standardized_path("map_ncs_sector_to_nic_section"), index=False)
    unmapped = int(ncs_map.section_code.isna().sum())
    typer.echo(
        f"map_ncs_sector_to_nic_section {len(ncs_map):>4} rows  "
        f"(authority=PROJECT; {unmapped} deliberately unmapped)"
    )

    sm = build_source_master()
    sm.to_parquet(paths.standardized_path("source_master"), index=False)
    ss = build_source_snapshot()
    ss.to_parquet(paths.standardized_path("source_snapshot"), index=False)
    typer.echo(f"source_master              {len(sm):>6} rows")
    typer.echo(f"source_snapshot            {len(ss):>6} rows  (one row per acquired file)")

    dbf = _latest_snapshot("DATAMEET_DISTRICT_ATTRS") / "2011_Dist.dbf"
    cand = build_census_district_candidates(dbf, "DATAMEET_DISTRICT_ATTRS")
    cand.to_parquet(paths.STAGING / "census2011_district_candidates.parquet", index=False)
    typer.echo(f"staging/census2011_district_candidates {len(cand):>6} rows (NOT the geography spine)")


@app.command()
def profile() -> None:
    """Profile every standardized table and write reports to docs/profiling/."""
    profs = profile_parquet_dir(paths.STANDARDIZED, paths.PROFILING)
    profs += profile_parquet_dir(paths.STAGING, paths.PROFILING)
    md = summary_markdown(profs)
    (paths.PROFILING / "SUMMARY.md").write_text(
        "# Profiling summary\n\nGenerated by `lmis profile`.\n\n" + md + "\n"
    )
    typer.echo(md)


@app.command()
def pilot_coverage() -> None:
    """Check the provisional pilot scope against what was actually acquired."""
    scope = load_pilot_scope()
    sec = pd.read_parquet(paths.standardized_path("sector_master"))
    typer.echo(f"pilot scope status: {scope['status']}\n")
    typer.echo("sector match against sector_master:")
    for s in scope["candidate_sectors"]:
        official = s["official_sector_name"]
        hit = sec[sec.sector_name_en.str.lower() == official.lower()]
        status = f"FOUND {hit.iloc[0].sector_id}" if len(hit) else "NOT FOUND"
        label = s["provisional_label"]
        note = "" if label == official else f"  (requested as {label!r})"
        typer.echo(f"  {official:34} {status}{note}")
    typer.echo("\nstate coverage: CANNOT BE CHECKED - location_master is empty (LGD blocked)")


@app.command()
def report() -> None:
    """Print the Step 1 status table."""
    reg = load_registry()
    rows = []
    for sid in reg:
        base = paths.RAW / sid
        snaps = sorted(d.name for d in base.iterdir() if d.is_dir()) if base.exists() else []
        n_files = 0
        if snaps:
            man = base / snaps[-1] / "manifest.json"
            if man.exists():
                n_files = len(json.loads(man.read_text())["files"])
        rows.append((sid, snaps[-1] if snaps else "-", n_files))
    for sid, snap, n in rows:
        typer.echo(f"{sid:30} snapshot={snap:12} files={n}")




@app.command()
def drop(
    source_id: str = typer.Argument(..., help="registered source_id"),
    file_path: str = typer.Argument(..., help="file you downloaded by hand"),
    publication_vintage: str = typer.Option(None, help="as-on date the SOURCE states, e.g. 2026-10-01"),
) -> None:
    """Register a file a human downloaded, writing a provenance manifest for it.

    Needed because some official sources cannot be fetched programmatically -
    LGD's bulk download sits behind a CAPTCHA, which we will not circumvent. A
    human downloads the file, drops it here, and it gets the same checksummed
    manifest treatment as an automated acquisition.
    """
    from datetime import date
    import shutil

    from lmis.ingest.manifest import FileRecord, Manifest, sha256_file

    src = load_registry()[source_id]
    srcfile = Path(file_path)
    if not srcfile.exists():
        raise typer.BadParameter(f"{file_path} does not exist")

    snap = paths.raw_dir(source_id, date.today().isoformat())
    snap.mkdir(parents=True, exist_ok=True)
    dest = snap / srcfile.name
    if dest.exists():
        raise typer.BadParameter(f"{dest} already exists; raw snapshots are immutable")
    shutil.copy2(srcfile, dest)

    Manifest(
        source_id=source_id,
        retrieved_at=utc_now_iso(),
        access_method=src.get("access_method"),
        licence=src.get("licence"),
        publisher_org=src.get("publisher_org"),
        landing_url=src.get("landing_url"),
        verification_status=src.get("verification_status"),
        retrieved_by="manual download (lmis.cli drop)",
        files=[
            FileRecord(
                name=dest.name,
                url=None,
                sha256=sha256_file(dest),
                size_bytes=dest.stat().st_size,
                publication_vintage=publication_vintage,
                notes="acquired by human download; see docs/limitations.md",
            )
        ],
    ).write(snap)
    typer.echo(f"registered {dest.relative_to(paths.ROOT)} with manifest")


@app.command()
def build_facts() -> None:
    """Build the observed fact tables from acquired raw snapshots.

    Loads OBSERVED rows only. Nothing here estimates, allocates or indexes.
    """
    ts = utc_now_iso()
    paths.STANDARDIZED.mkdir(parents=True, exist_ok=True)
    lm = pd.read_parquet(paths.standardized_path("location_master"))
    alias = pd.read_parquet(paths.standardized_path("location_alias"))
    ncs_map = pd.read_parquet(paths.standardized_path("map_ncs_sector_to_nic_section"))

    # --- NCS vacancies: two separate marginal tables, never joined -----------
    ncs_dir = _latest_snapshot("NCS_PARLIAMENTARY_ANSWERS")
    state_frames, sector_frames = [], []
    for pdf in sorted(ncs_dir.glob("*.pdf")):
        state_frames.append(build_vacancy_by_state(pdf, "NCS_PARLIAMENTARY_ANSWERS", ts, lm, alias))
        sector_frames.append(build_vacancy_by_sector(pdf, "NCS_PARLIAMENTARY_ANSWERS", ts, ncs_map))
    # Drop empty frames before concat: an all-NA frame degrades the dtypes of
    # the frames it is concatenated with (bool -> object), which then breaks
    # boolean indexing downstream.
    by_state = pd.concat([f for f in state_frames if len(f)], ignore_index=True)
    by_sector = pd.concat([f for f in sector_frames if len(f)], ignore_index=True)
    by_state["vacancies_cumulative"] = by_state["vacancies_cumulative"].astype("Int64")
    by_state["is_pan_india_residual"] = by_state["is_pan_india_residual"].astype(bool)
    by_sector["vacancies_cumulative"] = by_sector["vacancies_cumulative"].astype(float)
    by_state.to_parquet(paths.standardized_path("fact_vacancy_official_by_state"), index=False)
    by_sector.to_parquet(paths.standardized_path("fact_vacancy_official_by_sector"), index=False)
    unresolved = int(by_state[~by_state.is_pan_india_residual].lgd_code.isna().sum())
    typer.echo(
        f"fact_vacancy_official_by_state   {len(by_state):>6} rows "
        f"({by_state.snapshot_file.nunique()} source files; {unresolved} unresolved state names)"
    )
    typer.echo(f"fact_vacancy_official_by_sector  {len(by_sector):>6} rows")

    # --- Udyam establishments -------------------------------------------------
    ud_dir = _latest_snapshot("UDYAM_DISTRICT_MSME")
    ud_frames = []
    for fname, category in (
        ("district_level_total_Registered_msme.csv", "TOTAL"),
        ("district_level_service_msme.csv", "SERVICES"),
    ):
        fp = ud_dir / fname
        if fp.exists():
            ud_frames.append(build_establishment_district(fp, category, "UDYAM_DISTRICT_MSME", ts))
    est = pd.concat([f for f in ud_frames if len(f)], ignore_index=True)
    est["enterprise_count"] = est["enterprise_count"].astype("Int64")
    est.to_parquet(paths.standardized_path("fact_establishment_district"), index=False)
    typer.echo(
        f"fact_establishment_district       {len(est):>6} rows "
        f"({int(est.enterprise_count.isna().sum())} NULL counts = source 'NA', not zero)"
    )

    # --- PLFS labour-force estimates -----------------------------------------
    plfs_dir = _latest_snapshot("PLFS")
    lf_frames = [
        build_labour_force_estimate(p, "PLFS", ts)
        for p in sorted(plfs_dir.glob("PLFS_Monthly_Bulletin*.pdf"))
    ]
    lf = pd.concat([f for f in lf_frames if len(f)], ignore_index=True)
    lf.to_parquet(paths.standardized_path("fact_labour_force_estimate"), index=False)
    typer.echo(
        f"fact_labour_force_estimate        {len(lf):>6} rows "
        f"(periods: {sorted(lf.period_id.unique())}; geo_level NATIONAL only)"
    )


@app.command()
def validate_tables() -> None:
    """Enforce the Pandera contracts and write results to fact_data_quality."""
    from datetime import datetime, timezone

    import pandera.errors

    run_id = datetime.now(timezone.utc).strftime("DQ%Y%m%dT%H%M%S")
    rows, failures = [], 0
    for table in SCHEMAS:
        pq = paths.standardized_path(table)
        if not pq.exists():
            rows.append((table, "table_exists", "FAIL", "missing", "present", "HIGH"))
            failures += 1
            continue
        df = pd.read_parquet(pq)
        try:
            validate_table(table, df)
            rows.append((table, "schema_contract", "PASS", str(len(df)), "schema", "HIGH"))
            typer.echo(f"PASS  {table:34} {len(df):>6} rows")
        except pandera.errors.SchemaError as exc:
            failures += 1
            rows.append((table, "schema_contract", "FAIL", str(exc)[:200], "schema", "HIGH"))
            typer.echo(f"FAIL  {table:34} {str(exc)[:110]}")

    dq = pd.DataFrame(
        rows, columns=["table_name", "check_name", "status", "observed", "expected", "severity"]
    )
    dq.insert(0, "run_id", run_id)
    dq["checked_at"] = utc_now_iso()
    dq.to_parquet(paths.STANDARDIZED / "fact_data_quality.parquet", index=False)
    typer.echo(f"\n{len(dq)} checks, {failures} failure(s) -> fact_data_quality.parquet")
    raise typer.Exit(code=1 if failures else 0)


@app.command()
def load_warehouse() -> None:
    """Apply the DDL and load every standardized table into db/lmis.duckdb."""
    con = wh.connect()
    wh.apply_schema(con)
    for r in wh.load_all(con):
        note = f"  [{r.detail}]" if r.detail else ""
        typer.echo(f"{r.status:8} {r.table:34} {r.rows:>7} rows{note}")
    con.close()
    typer.echo(f"\nwarehouse: {wh.DB_PATH.relative_to(paths.ROOT)}")


@app.command()
def build_analytical() -> None:
    """Build the derived analytical layer.

    Aggregations, de-duplication, shares and confidence-scored mappings only.
    No district demand is estimated, no index is computed, nothing is forecast.
    """
    ts = utc_now_iso()
    paths.STANDARDIZED.mkdir(parents=True, exist_ok=True)

    # --- Census B-24 source fact at its native grain -------------------------
    census_dir = _latest_snapshot("CENSUS_2011_B24")
    b24 = pd.concat(
        [parse_b24(p, "CENSUS_2011_B24", ts) for p in sorted(census_dir.glob("*.XLSX"))],
        ignore_index=True,
    )
    b24["main_workers"] = b24["main_workers"].astype("Int64")
    b24.to_parquet(paths.standardized_path("fact_census_occupation_workers"), index=False)
    typer.echo(
        f"fact_census_occupation_workers            {len(b24):>6} rows "
        f"({b24.census_state_code.nunique()} states, "
        f"{b24[b24.geo_level=='DISTRICT'].census_district_code.nunique()} districts)"
    )

    # --- ILOSTAT industry x occupation (source fact, NOT the bridge) ---------
    ilo_dir = _latest_snapshot("ILOSTAT_EMP_ECO_OCU")
    ilo, ilo_stats = parse_ilostat_eco_occ(
        ilo_dir / "ILOSTAT_EMP_TEMP_ECO_OCU_NB_A_IND.csv",
        ilo_dir / "ILOSTAT_dic_source_en.csv",
        "ILOSTAT_EMP_ECO_OCU",
        ts,
    )
    ilo.to_parquet(paths.standardized_path("fact_ilo_employment_eco_occ"), index=False)
    typer.echo(
        f"fact_ilo_employment_eco_occ               {len(ilo):>6} rows "
        f"(years {','.join(ilo_stats['years'])}; {ilo_stats['sections']} NIC sections; "
        f"{ilo_stats['rows_excluded']} aggregate rows excluded; "
        f"{ilo_stats['null_values']} suppressed cells kept NULL)"
    )

    # --- derived division crosswalk, purity measured -------------------------
    conc = pd.read_parquet(paths.standardized_path("map_nco2004_to_nco2015"))
    dmap = ab.build_division_crosswalk(conc)
    dmap.to_parquet(
        paths.standardized_path("map_nco2004_division_to_nco2015_division"), index=False
    )
    low = dmap[dmap.confidence.notna() & (dmap.confidence < 0.9)]
    typer.echo(
        f"map_nco2004_division_to_nco2015_division  {len(dmap):>6} rows "
        f"({len(low)} divisions below 0.9 purity: "
        f"{', '.join(low.nco_2004_division + '=' + low.confidence.round(2).astype(str))})"
    )

    # --- analytical tables ---------------------------------------------------
    lm = pd.read_parquet(paths.standardized_path("location_master"))
    by_state = pd.read_parquet(paths.standardized_path("fact_vacancy_official_by_state"))
    by_sector = pd.read_parquet(paths.standardized_path("fact_vacancy_official_by_sector"))
    ncs_map = pd.read_parquet(paths.standardized_path("map_ncs_sector_to_nic_section"))
    est = pd.read_parquet(paths.standardized_path("fact_establishment_district"))
    plfs = pd.read_parquet(paths.standardized_path("fact_labour_force_estimate"))

    built: dict[str, pd.DataFrame] = {}
    built["analytical_state_demand"] = ab.build_analytical_state_demand(by_state)
    built["analytical_demand_by_industry"] = ab.build_analytical_demand_by_industry(
        by_sector, ncs_map
    )
    built["analytical_district_structure"] = ab.build_analytical_district_structure(est, lm)
    built["analytical_district_occupation_structure"] = (
        ab.build_analytical_district_occupation_structure(b24, dmap)
    )
    built["analytical_labour_market_context"] = ab.build_analytical_labour_market_context(plfs)

    meta = {
        "analytical_state_demand": dict(
            grain="snapshot_date x state (or NATIONAL residual)",
            source_tables="fact_vacancy_official_by_state",
            source_ids="NCS_PARLIAMENTARY_ANSWERS",
            source_vintage="as on 2024-11-15",
            geo_level="STATE + NATIONAL residual",
            occupation_level="NONE",
            industry_level="NONE",
            observation_status="OBSERVED",
            transformations="deduplicate identical corroborating documents; share within snapshot",
            coverage_note="36/36 LGD states covered; 58.1% of vacancies sit in the PAN-India residual",
            limitations="cumulative stock, not a flow; single as-on date so no time series; no occupation",
        ),
        "analytical_demand_by_industry": dict(
            grain="snapshot_date x NCS sector (NIC-2008 section)",
            source_tables="fact_vacancy_official_by_sector + map_ncs_sector_to_nic_section",
            source_ids="NCS_PARLIAMENTARY_ANSWERS; NIC_2008",
            source_vintage="as on 2024-11-15",
            geo_level="NATIONAL",
            occupation_level="NONE",
            industry_level="NIC_SECTION",
            observation_status="OBSERVED",
            transformations="deduplicate identical documents; share within snapshot; NCS->NIC name alignment",
            coverage_note="20 of 22 rows map to a NIC section; Sector Not Specified deliberately unmapped",
            limitations="industry is not occupation; marginal table only - no joint state x sector exists",
        ),
        "analytical_district_structure": dict(
            grain="snapshot_date x district x enterprise_category",
            source_tables="fact_establishment_district + location_master",
            source_ids="UDYAM_DISTRICT_MSME; LGD_DISTRICTS_DATAGOVIN",
            source_vintage="2023-12-21 (Udyam); 2023-11-30 (LGD)",
            geo_level="DISTRICT",
            occupation_level="NONE",
            industry_level="NONE",
            observation_status="SUPPORTING",
            transformations="pivot size class; share within state; share of national; size-class composition",
            coverage_note="785/785 districts",
            limitations="registered ENTERPRISES, not vacancies/demand/employment; 2023 snapshot; 'NA' preserved as NULL",
        ),
        "analytical_district_occupation_structure": dict(
            grain="census_year x district x NCO-2004 division x area x sex",
            source_tables="fact_census_occupation_workers + map_nco2004_division_to_nco2015_division",
            source_ids="CENSUS_2011_B24",
            source_vintage="2011 (Census)",
            geo_level="DISTRICT",
            occupation_level="NCO_2004_DIVISION",
            industry_level="NONE",
            observation_status="SUPPORTING",
            transformations="division share within district; derived NCO-2004->NCO-2015 division map",
            coverage_note="3 pilot states only (MH 35, TN 32, UP 71 Census-2011 districts)",
            limitations="HISTORICAL 2011 structure, not demand; universe is main workers in non-household industry; 'X' unclassified not mappable to NCO-2015",
        ),
        "analytical_labour_market_context": dict(
            grain="period x NATIONAL x area x sex x age_group x indicator",
            source_tables="fact_labour_force_estimate",
            source_ids="PLFS",
            source_vintage="M202504",
            geo_level="NATIONAL",
            occupation_level="NONE",
            industry_level="NONE",
            observation_status="OBSERVED",
            transformations="none (pass-through: no valid transformation exists at this grain)",
            coverage_note="one month only (April 2025)",
            limitations="sample survey rates; district estimates NOT valid; context not demand",
        ),
    }

    rows = []
    for name, df in built.items():
        df.to_parquet(paths.standardized_path(name), index=False)
        typer.echo(f"{name:41} {len(df):>6} rows")
        m = meta[name]
        rows.append({"analytical_table": name, "row_count": len(df), "built_at": ts, **m})
    pd.DataFrame(rows).to_parquet(
        paths.standardized_path("analytical_dataset_catalog"), index=False
    )
    typer.echo(f"analytical_dataset_catalog                {len(rows):>6} rows")


@app.command()
def build_demand() -> None:
    """Build the three approved demand estimates (Step 4.0).

    The baseline period is read FROM THE DATABASE, never hard-coded, so adding a
    genuine second NCS snapshot later needs no code change here.
    """
    ts = utc_now_iso()
    paths.STANDARDIZED.mkdir(parents=True, exist_ok=True)

    state_demand = pd.read_parquet(paths.standardized_path("analytical_state_demand"))
    periods = sorted(state_demand["snapshot_date"].unique())
    if len(periods) != 1:
        # More than one genuine dated snapshot changes the design question (a flow
        # becomes derivable), so stop rather than silently pick one.
        raise typer.BadParameter(
            f"expected exactly one NCS as-on date, found {periods}. A flow may now be "
            "derivable - revisit the methodology before building a baseline."
        )
    baseline = periods[0]
    typer.echo(f"baseline_period (read from warehouse): {baseline}\n")

    by_industry = pd.read_parquet(paths.standardized_path("analytical_demand_by_industry"))
    ilo = pd.read_parquet(paths.standardized_path("fact_ilo_employment_eco_occ"))
    district_structure = pd.read_parquet(paths.standardized_path("analytical_district_structure"))
    district_occ = pd.read_parquet(
        paths.standardized_path("analytical_district_occupation_structure")
    )
    division_map = pd.read_parquet(
        paths.standardized_path("map_nco2004_division_to_nco2015_division")
    )
    lm = pd.read_parquet(paths.standardized_path("location_master"))

    a = de.build_national_occupation_composition(by_industry, ilo, baseline, ts)
    a.to_parquet(paths.standardized_path("demand_national_occupation_composition"), index=False)
    typer.echo(
        f"A demand_national_occupation_composition  {len(a):>6} rows  "
        f"({a.nic_section_code.nunique()} NIC sections x {a.nco_2015_division.nunique()} "
        f"NCO divisions; confidence {dict(a.overall_confidence.value_counts())})"
    )

    b = de.build_district_relative_signal(state_demand, district_structure, lm, baseline, ts)
    b.to_parquet(paths.standardized_path("demand_district_relative_signal"), index=False)
    typer.echo(
        f"B demand_district_relative_signal         {len(b):>6} rows  "
        f"({b.lgd_code.nunique()} districts, {b.state_lgd_code.nunique()} states; "
        f"confidence {dict(b.overall_confidence.value_counts())})"
    )

    c_ = de.build_district_occupation_signal(b, district_occ, division_map, lm, baseline, ts)
    c_.to_parquet(paths.standardized_path("demand_district_occupation_signal"), index=False)
    status = dict(c_.groupby("occupation_prior_status").lgd_code.nunique())
    typer.echo(
        f"C demand_district_occupation_signal       {len(c_):>6} rows  "
        f"(districts by prior status: {status}; "
        f"confidence {dict(c_.overall_confidence.value_counts())})"
    )

    cov = de.build_coverage_summary(state_demand, b, c_, baseline, ts)
    cov.to_parquet(paths.standardized_path("demand_coverage_summary"), index=False)
    share = float(cov.loc[cov.metric == "ncs_state_attributable_share", "value"].iloc[0])
    typer.echo(
        f"  demand_coverage_summary                 {len(cov):>6} rows  "
        f"(state-attributable share of NCS vacancies: {share:.1%})"
    )


@app.command()
def build_supply() -> None:
    """Build the OBSERVED supply-side tables (Step 5.0).

    No supply estimation, no gap, no forecast. The five training concepts are kept
    in long format so none can be mistaken for another.
    """
    ts = utc_now_iso()
    paths.STANDARDIZED.mkdir(parents=True, exist_ok=True)
    pdf = _latest_snapshot("MSDE_ANNUAL_REPORT_2023_24") / "MSDE_Annual_Report_2023-24.pdf"
    lm = pd.read_parquet(paths.standardized_path("location_master"))
    alias = pd.read_parquet(paths.standardized_path("location_alias"))

    outcomes, recon_o = parse_training_outcomes(
        pdf, lm, alias, "MSDE_ANNUAL_REPORT_2023_24", ts
    )
    outcomes.to_parquet(paths.standardized_path("fact_training_outcome"), index=False)
    typer.echo(
        f"fact_training_outcome          {len(outcomes):>5} rows  "
        f"({outcomes.scheme.nunique()} schemes x {outcomes.state_name_as_source.nunique()} states "
        f"x {outcomes.measure.nunique()} measures; "
        f"geography {dict(outcomes.geography_status.value_counts())}; "
        f"{int((outcomes.value_status=='NO_DATA').sum())} cells NO_DATA kept NULL)"
    )

    infra, recon_i = parse_training_infrastructure(
        pdf, lm, alias, "MSDE_ANNUAL_REPORT_2023_24", ts
    )
    infra.to_parquet(paths.standardized_path("fact_training_infrastructure"), index=False)
    typer.echo(
        f"fact_training_infrastructure   {len(infra):>5} rows  "
        f"({infra.state_name_as_source.nunique()} states x {infra.metric.nunique()} metrics; "
        f"geography {dict(infra.geography_status.value_counts())})"
    )

    trades = parse_training_trades(pdf, "MSDE_ANNUAL_REPORT_2023_24", ts)
    trades.to_parquet(paths.standardized_path("dim_training_trade"), index=False)
    typer.echo(
        f"dim_training_trade             {len(trades):>5} rows  "
        f"(sections {dict(trades.trade_section_index.value_counts().sort_index())}; "
        f"NCO mapping: {dict(trades.nco_mapping_status.value_counts())})"
    )

    recon = pd.DataFrame(recon_o + recon_i)
    recon.to_parquet(paths.standardized_path("fact_training_reconciliation"), index=False)
    exact = int((recon.difference == 0).sum())
    typer.echo(
        f"fact_training_reconciliation   {len(recon):>5} rows  "
        f"({exact}/{len(recon)} reconcile EXACTLY to the source's own published totals)"
    )

    # --- Step 5.1: OFFICIAL qualification -> NCO mapping from NQR Q-Files -----
    om = pd.read_parquet(paths.standardized_path("occupation_master"))
    qfiles = sorted(_latest_snapshot("NQR_QUALIFICATIONS").glob("*.pdf"))
    frames = [parse_qfile_nco_mapping(p, om, "NQR_QUALIFICATIONS", ts) for p in qfiles]
    qmap = pd.concat([f for f in frames if len(f)], ignore_index=True) if any(
        len(f) for f in frames
    ) else pd.DataFrame(columns=frames[0].columns)
    qmap.to_parquet(paths.standardized_path("map_qualification_to_nco"), index=False)
    typer.echo(
        f"map_qualification_to_nco       {len(qmap):>5} rows  "
        f"(authority OFFICIAL, from {len(qfiles)} Q-File(s); "
        f"level {sorted(set(qmap.nco_mapping_level)) if len(qmap) else 'n/a'})"
    )

    # --- Step 5.2: OFFICIAL DGT trade -> NCO from DGT's own CTS curricula ----
    trades = pd.read_parquet(paths.standardized_path("dim_training_trade"))
    curricula = sorted(_latest_snapshot("DGT_CTS_CURRICULUM").glob("*.pdf"))
    cframes = [
        parse_dgt_curriculum(p, trades, om, "DGT_CTS_CURRICULUM", ts) for p in curricula
    ]
    tmap = pd.concat([f for f in cframes if len(f)], ignore_index=True)
    tmap.to_parquet(paths.standardized_path("map_trade_to_nco"), index=False)
    typer.echo(
        f"map_trade_to_nco               {len(tmap):>5} rows  "
        f"({tmap.trade_id.nunique()} trades from {len(curricula)} curricula; "
        f"multi-NCO preserved: {int(tmap.is_multi_nco.sum())} rows; "
        f"level {sorted(set(tmap.nco_mapping_level))})"
    )

    status = classify_trade_mapping_status(trades, tmap)
    status.to_parquet(paths.standardized_path("dim_trade_mapping_status"), index=False)
    counts = dict(status.mapping_status.value_counts())
    typer.echo(
        f"dim_trade_mapping_status       {len(status):>5} rows  "
        f"({counts}; reconciles to {len(status)})"
    )

    # --- supply coverage summary (built LAST so it summarises what now exists) -
    #
    # Step 7.1 found `trades_mapped_to_nco` hard-coded to 0.0 here. It was written
    # during Step 5.0, before Step 5.2 read the official trade -> NCO linkage off
    # DGT's own CTS curricula, and it then contradicted dim_trade_mapping_status
    # for the rest of the project. The counts below are DERIVED from the
    # authoritative mapping tables, and the summary moved after them, so a summary
    # can no longer describe a state that predates it.
    #
    # This corrects metadata only. No supply quantity is created at any grain.
    mapped_trades = int(tmap.trade_id.nunique())
    unresolved_trades = int(
        (status.mapping_status == "MAPPING_UNKNOWN").sum()
    )
    officially_mapped = int(
        status.mapping_status.str.startswith("OFFICIAL").sum()
    )
    mapped_status = "UNMAPPED" if mapped_trades == 0 else "PARTIAL_OFFICIAL"
    cov = pd.DataFrame(
        [
            ("training_outcome_rows", float(len(outcomes)), "count", "AVAILABLE",
             "state x scheme x measure, OBSERVED"),
            ("states_with_training_outcomes", float(outcomes.state_lgd_code.nunique()),
             "count", "AVAILABLE", "resolved to LGD state codes"),
            ("geography_unmatched_rows",
             float((outcomes.geography_status == "UNMATCHED").sum()), "count",
             "AVAILABLE", "retained, never dropped"),
            ("measure_cells_no_data", float((outcomes.value_status == "NO_DATA").sum()),
             "count", "NO_DATA", "source prints '-'; kept NULL, never zero"),
            ("training_trades_catalogued", float(len(status)), "count", "AVAILABLE",
             "official NSQF-compliant trade list"),
            ("trades_mapped_to_nco", float(mapped_trades), "count", mapped_status,
             "derived from map_trade_to_nco; OFFICIAL DGT CTS curriculum linkage"),
            ("trades_officially_mapped_to_nco", float(officially_mapped), "count",
             "OFFICIAL",
             "derived from dim_trade_mapping_status; authority OFFICIAL only"),
            ("trades_mapping_unknown", float(unresolved_trades), "count",
             "MAPPING_UNKNOWN",
             "no official mapping ACQUIRED - distinct from MAPPING_DOES_NOT_EXIST"),
            ("district_level_training_data", 0.0, "count", "NOT_ACQUIRED",
             "PMKVY district CSV 404s on data.gov.in; NCVT MIS portal unreachable"),
            ("pmkvy_district_resource_api", 0.0, "count", "ACCESS_PENDING",
             "requires a registered data.gov.in API key the project does not hold"),
        ],
        columns=["metric", "value", "unit", "status", "note"],
    )
    cov["built_at"] = ts
    cov.to_parquet(paths.standardized_path("supply_coverage_summary"), index=False)
    typer.echo(
        f"supply_coverage_summary        {len(cov):>5} rows  "
        f"(trades_mapped_to_nco={mapped_trades} DERIVED, was hard-coded 0; "
        f"officially_mapped={officially_mapped}, "
        f"mapping_unknown={unresolved_trades}, total={len(status)})"
    )

    # --- Step 5.3: trade/job-role level supply QUANTITIES (national, top-N) --
    tso, tso_recon = parse_trade_level_supply(
        pdf, tmap, qmap, "MSDE_ANNUAL_REPORT_2023_24", ts
    )
    tso.to_parquet(paths.standardized_path("fact_training_trade_outcome"), index=False)
    linked = tso[tso.nco_link_status != "NO_EXISTING_OFFICIAL_MAP"]
    typer.echo(
        f"fact_training_trade_outcome    {len(tso):>5} rows  "
        f"({dict(tso.groupby('occupation_entity_type').entity_name_as_source.nunique())} entities; "
        f"geo_level NATIONAL; all rows is_top_n_subset=True; "
        f"{linked.entity_name_as_source.nunique()} entities link to an OFFICIAL NCO map)"
    )
    recon_df = pd.DataFrame(tso_recon)
    recon_df.to_parquet(
        paths.standardized_path("fact_trade_supply_reconciliation"), index=False
    )
    typer.echo(
        f"fact_trade_supply_reconciliation {len(recon_df):>3} rows  "
        f"(top-N shortfall is expected, not an error)"
    )

    ev = build_supply_evidence_matrix(ts)
    ev.to_parquet(paths.standardized_path("supply_evidence_matrix"), index=False)
    typer.echo(
        f"supply_evidence_matrix         {len(ev):>5} rows  "
        f"(decisions: {dict(ev.decision.value_counts())})"
    )


@app.command()
def publish_contract() -> None:
    """Emit the approved Step 7.1 publication contract (metadata only).

    Writes the mandatory metadata envelope for every contracted output and the
    explicit unavailability register. No analytical value is computed, altered or
    re-derived: coverage facts are read out of the warehouse, and evidence status
    is read out of each table's own status column.
    """
    contract = load_contract()
    paths.PUBLICATION.mkdir(parents=True, exist_ok=True)
    con = wh.connect()
    try:
        envelopes = build_envelopes(con, contract)
    finally:
        con.close()

    register = build_unavailability_register(contract)
    prod = production_envelopes(envelopes)
    assert_no_experimental_leak(prod)

    violations = lint_contract(contract) + lint_envelopes(envelopes, contract)
    if violations:
        for v in violations:
            typer.echo(f"TERMINOLOGY VIOLATION  {v}")
        raise typer.Exit(code=1)

    doc = {
        "contract_version": contract.contract_version,
        "mode": contract.mode,
        "coverage": {
            k: v for e in envelopes for k, v in e.get("coverage", {}).items()
        },
        "outputs": envelopes,
        "unavailable_capabilities": register,
        "barred_fields": contract.barred_fields,
    }
    paths.publication_path("publication_contract").write_text(
        json.dumps(doc, indent=2, sort_keys=False, default=str)
    )
    paths.publication_path("unavailability_register").write_text(
        json.dumps(register, indent=2, default=str)
    )

    exp = [e for e in envelopes if e["publication_status"] == "EXPERIMENTAL_ONLY"]
    typer.echo(
        f"publication_contract           {len(envelopes):>5} outputs  "
        f"({len(prod)} PRODUCTION, {len(exp)} EXPERIMENTAL_ONLY fenced, "
        f"{len(register)} capabilities UNAVAILABLE)"
    )
    for e in prod:
        typer.echo(
            f"  {e['output_id']:<42} {e['tier']:<11} "
            f"{','.join(e['evidence_status']):<22} "
            f"conf={','.join(str(c) for c in e['confidence']):<22} "
            f"rows={e['row_count']:>6}  shortage={e['is_measured_shortage']}"
        )
    cov = doc["coverage"]
    if cov:
        typer.echo("  mandatory coverage disclosures (DERIVED from the warehouse):")
        for k, v in cov.items():
            val = v["value"]
            shown = f"{val:.4%}" if v["unit"] == "ratio" else f"{val:,.0f}"
            typer.echo(f"    {k:<34} {shown:>12}   <- {v['derived_from']}")
    typer.echo("  terminology lint: PASS (0 violations)")


@app.command()
def lint_terminology() -> None:
    """Fail the build if a published label drifts into unsupported interpretation."""
    contract = load_contract()
    con = wh.connect()
    try:
        envelopes = build_envelopes(con, contract)
    finally:
        con.close()
    violations = (
        lint_contract(contract)
        + lint_envelopes(envelopes, contract)
        + lint_derivation_labels(contract)
    )
    # Step 7.4: the UI label catalogues are linted too - a translation file is where
    # terminology drifts most easily, because a label is written once and read by all.
    catalogues = 0
    i18n = paths.ROOT / "api" / "static" / "i18n"
    for f in sorted(i18n.glob("*.json")) if i18n.is_dir() else []:
        labels = {
            k: v for k, v in json.loads(f.read_text()).items() if isinstance(v, str)
        }
        violations += lint_label_catalogue(labels, contract, f"i18n/{f.stem}")
        catalogues += 1
    for v in violations:
        typer.echo(f"TERMINOLOGY VIOLATION  {v}")
    if violations:
        typer.echo(f"{len(violations)} violation(s)")
        raise typer.Exit(code=1)
    typer.echo(
        f"terminology lint PASS  ({len(envelopes)} outputs, {catalogues} UI label "
        f"catalogue(s), 0 violations; scope = published labels and interpretations, "
        f"not internal column names)"
    )


if __name__ == "__main__":
    app()
