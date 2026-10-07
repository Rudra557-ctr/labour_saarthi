"""Derived analytical tables.

Boundary for this layer, deliberately narrow:

  ALLOWED    aggregation, de-duplication of identical corroborating observations,
             shares, rates, normalisation, and mappings whose authority and
             confidence are recorded.
  NOT ALLOWED  estimating district demand, allocating state totals to districts,
             combining incompatible grains, or inventing any observation.

Every row carries `observation_status` (OBSERVED | SUPPORTING), the source vintage,
the geography/occupation level it is actually valid at, and its transformation
method - so a dashboard can always answer "where did this number come from?".
"""
from __future__ import annotations

import pandas as pd

OBSERVED = "OBSERVED"
SUPPORTING = "SUPPORTING"


# --------------------------------------------------------------------------- #
# 1. State-level demand (NCS)
# --------------------------------------------------------------------------- #
def build_analytical_state_demand(by_state: pd.DataFrame) -> pd.DataFrame:
    """One analytical observation per (observation_date, geography).

    The three acquired Parliament answers report the SAME as-on date and the same
    figures, so they are three documents describing ONE observation, not three
    observations. They are de-duplicated and `n_source_documents` records the
    corroboration. Identity is asserted first - if the documents ever disagree the
    build fails rather than silently picking one.

    `flow_available` is False with a stated reason: the measure is a cumulative
    stock and every acquired snapshot shares one as-on date, so differencing is
    impossible. No monthly demand is fabricated.
    """
    key = ["snapshot_date", "state_name_as_source"]
    disagree = (
        by_state.groupby(key)["vacancies_cumulative"].nunique().reset_index()
    )
    bad = disagree[disagree["vacancies_cumulative"] > 1]
    if len(bad):
        raise ValueError(
            f"NCS documents disagree for {len(bad)} geographies; cannot de-duplicate: "
            f"{bad.head().to_dict('records')}"
        )

    agg = (
        by_state.groupby(key, dropna=False)
        .agg(
            vacancies_cumulative=("vacancies_cumulative", "first"),
            n_source_documents=("snapshot_file", "nunique"),
            source_documents=("snapshot_file", lambda s: "; ".join(sorted(set(s)))),
            lgd_code=("lgd_code", "first"),
            geo_level=("geo_level", "first"),
            is_pan_india_residual=("is_pan_india_residual", "first"),
            source_id=("source_id", "first"),
        )
        .reset_index()
    )

    # Share of the national total, computed WITHIN the snapshot date. The
    # PAN-India residual is included in the denominator because it is part of the
    # published total - excluding it would silently inflate every state's share.
    totals = agg.groupby("snapshot_date")["vacancies_cumulative"].transform("sum")
    agg["share_of_published_total"] = agg["vacancies_cumulative"] / totals
    state_only = agg[~agg["is_pan_india_residual"]]
    attributable = (
        state_only.groupby("snapshot_date")["vacancies_cumulative"].transform("sum")
    )
    agg["share_of_state_attributable"] = pd.NA
    agg.loc[state_only.index, "share_of_state_attributable"] = (
        state_only["vacancies_cumulative"] / attributable
    )

    agg["measure_basis"] = "CUMULATIVE_SINCE_INCEPTION"
    agg["unit"] = "count"
    agg["observation_status"] = OBSERVED
    agg["occupation_level"] = "NONE"
    agg["industry_level"] = "NONE"
    agg["flow_available"] = False
    agg["flow_unavailable_reason"] = (
        "measure is a cumulative stock and all acquired snapshots share one "
        "as-on date; differencing requires two different dated snapshots"
    )
    agg["source_vintage"] = agg["snapshot_date"]
    agg["transformation"] = "DEDUPLICATE_IDENTICAL_DOCUMENTS + SHARE_WITHIN_SNAPSHOT"
    return agg.sort_values(["snapshot_date", "state_name_as_source"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 2. State-level demand by industry (NCS sector -> NIC section)
# --------------------------------------------------------------------------- #
def build_analytical_demand_by_industry(
    by_sector: pd.DataFrame, sector_nic_map: pd.DataFrame
) -> pd.DataFrame:
    """One observation per (observation_date, NCS sector), with the NIC section.

    The NCS sector vocabulary IS the NIC-2008 section list, so this table carries
    an INDUSTRY dimension. It deliberately carries no occupation dimension: an
    industry-to-occupation mapping is many-to-many and must come from empirical
    evidence (a PLFS cross-tab), which is not yet available.
    """
    key = ["snapshot_date", "ncs_sector_name"]
    disagree = by_sector.groupby(key)["vacancies_cumulative"].nunique().reset_index()
    bad = disagree[disagree["vacancies_cumulative"] > 1]
    if len(bad):
        raise ValueError(f"NCS sector documents disagree: {bad.head().to_dict('records')}")

    agg = (
        by_sector.groupby(key, dropna=False)
        .agg(
            vacancies_cumulative=("vacancies_cumulative", "first"),
            n_source_documents=("snapshot_file", "nunique"),
            source_documents=("snapshot_file", lambda s: "; ".join(sorted(set(s)))),
            nic_section_code=("nic_section_code", "first"),
            source_id=("source_id", "first"),
        )
        .reset_index()
    )
    m = sector_nic_map.set_index("ncs_sector_name")
    agg["mapping_authority"] = agg["ncs_sector_name"].map(m["authority"])
    agg["mapping_confidence"] = agg["ncs_sector_name"].map(m["confidence"])
    agg["mapping_method"] = agg["ncs_sector_name"].map(m["method"])
    # Heterogeneous or residual industry sections must not be treated as
    # occupationally specific later on.
    agg["is_heterogeneous_or_residual"] = (
        agg["nic_section_code"].isna() | (agg["mapping_confidence"].fillna(0) < 0.9)
    )
    total = agg.groupby("snapshot_date")["vacancies_cumulative"].transform("sum")
    agg["share_of_published_total"] = agg["vacancies_cumulative"] / total
    agg["unit"] = "lakh"
    agg["measure_basis"] = "CUMULATIVE_SINCE_INCEPTION"
    agg["observation_status"] = OBSERVED
    agg["geo_level"] = "NATIONAL"
    agg["industry_level"] = "NIC_SECTION"
    agg["occupation_level"] = "NONE"
    agg["source_vintage"] = agg["snapshot_date"]
    agg["transformation"] = "DEDUPLICATE_IDENTICAL_DOCUMENTS + SHARE_WITHIN_SNAPSHOT"
    return agg.sort_values(key).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 3. District establishment structure (Udyam)
# --------------------------------------------------------------------------- #
def build_analytical_district_structure(
    est: pd.DataFrame, location_master: pd.DataFrame
) -> pd.DataFrame:
    """District enterprise counts and shares within state and nationally.

    SUPPORTING, never demand. Udyam counts REGISTERED ENTERPRISES; it says nothing
    about vacancies, hiring or employment. The shares here are structural weights
    only - converting an enterprise share into a vacancy count is an ESTIMATE and
    belongs to the demand-estimation step, not here.
    """
    totals = est[est["size_class"] == "TOTAL"].copy()
    districts = location_master[location_master["level"] == "DISTRICT"][
        ["lgd_code", "name_en", "state_lgd_code", "census_2011_code", "valid_from"]
    ]
    df = totals.merge(districts, on="lgd_code", how="left", validate="many_to_one")

    wide = (
        est.pivot_table(
            index=["snapshot_date", "lgd_code", "enterprise_category"],
            columns="size_class",
            values="enterprise_count",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"MICRO": "micro", "SMALL": "small", "MEDIUM": "medium", "TOTAL": "total"})
    )
    out = df[
        ["snapshot_date", "lgd_code", "enterprise_category", "name_en",
         "state_lgd_code", "census_2011_code", "source_id", "snapshot_file"]
    ].merge(wide, on=["snapshot_date", "lgd_code", "enterprise_category"], how="left")

    # Shares computed within (snapshot, category) so TOTAL and SERVICES never mix.
    grp = ["snapshot_date", "enterprise_category"]
    out["enterprise_share_of_national"] = out["total"] / out.groupby(grp)["total"].transform("sum")
    out["enterprise_share_within_state"] = out["total"] / out.groupby(
        grp + ["state_lgd_code"]
    )["total"].transform("sum")
    # Size-class composition. NULL stays NULL: 'NA' in the source is missing, so a
    # share built on it must be missing too, not zero.
    for col in ("micro", "small", "medium"):
        out[f"{col}_share_of_district"] = out[col] / out["total"]

    out = out.rename(columns={"name_en": "district_name_lgd"})
    out["geo_level"] = "DISTRICT"
    out["occupation_level"] = "NONE"
    out["measure_basis"] = "CUMULATIVE_REGISTRATIONS"
    out["unit"] = "count"
    out["observation_status"] = SUPPORTING
    out["not_a_demand_measure"] = True
    out["source_vintage"] = out["snapshot_date"]
    out["transformation"] = "PIVOT_SIZE_CLASS + SHARE_WITHIN_STATE + SHARE_OF_NATIONAL"
    return out.sort_values(["enterprise_category", "lgd_code"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 4. District occupation structure (Census B-24)
# --------------------------------------------------------------------------- #
def build_analytical_district_occupation_structure(
    b24: pd.DataFrame, division_map: pd.DataFrame
) -> pd.DataFrame:
    """District x NCO-2004 division shares of main workers, Census 2011.

    SUPPORTING and explicitly historical. Only DIVISION_TOTAL and UNCLASSIFIED
    rows are used, because mixing them with SUB_DIVISION rows or with the
    all-occupations total would double-count.

    The NCO-2015 division is attached through a crosswalk DERIVED from the official
    NCO-2004 to NCO-2015 concordance, carrying its measured purity as confidence.
    The native NCO-2004 code is retained so nothing is lost in translation.
    """
    use = b24[
        (b24["geo_level"] == "DISTRICT")
        & (b24["row_type"].isin(["DIVISION_TOTAL", "UNCLASSIFIED"]))
    ].copy()

    denom_keys = ["census_state_code", "census_district_code", "area", "sex"]
    totals = (
        b24[(b24["geo_level"] == "DISTRICT") & (b24["row_type"] == "TOTAL_ALL_OCCUPATIONS")]
        .groupby(denom_keys)["main_workers"]
        .sum()
        .rename("district_total_main_workers")
        .reset_index()
    )
    out = use.merge(totals, on=denom_keys, how="left", validate="many_to_one")
    out["occupation_share_of_district"] = (
        out["main_workers"] / out["district_total_main_workers"]
    )

    m = division_map.set_index("nco_2004_division")
    out["nco_2015_division"] = out["nco_2004_division"].map(m["nco_2015_division"])
    out["division_map_confidence"] = out["nco_2004_division"].map(m["confidence"])
    out["division_map_authority"] = out["nco_2004_division"].map(m["authority"])

    out["observation_status"] = SUPPORTING
    out["source_vintage"] = "2011 (Census)"
    out["is_historical"] = True
    out["not_a_demand_measure"] = True
    out["transformation"] = "DIVISION_SHARE_WITHIN_DISTRICT + NCO2004_TO_NCO2015_DIVISION_MAP"
    return out.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 5. NCO-2004 division -> NCO-2015 division, derived from the official concordance
# --------------------------------------------------------------------------- #
def build_division_crosswalk(concordance: pd.DataFrame) -> pd.DataFrame:
    """Derive a division-level crosswalk and MEASURE how clean it is.

    Census B-24 publishes occupation only at NCO-2004 division/sub-division level,
    while the official concordance keys on 8-digit codes. Truncating both sides to
    their first digit yields a division-level relationship whose purity can be
    computed: for each NCO-2004 division, the share of concorded codes that land in
    the modal NCO-2015 division.

    That purity becomes the confidence. The authority is PROJECT_DERIVED_FROM_OFFICIAL
    - the inputs are official, the truncation is ours. Divisions whose purity is low
    are still recorded, so a consumer can filter rather than be misled.
    """
    c = concordance.dropna(subset=["nco_2004_code"]).copy()
    c["div_2004"] = c["nco_2004_code"].astype(str).str.strip().str[0]
    c["div_2015"] = c["nco_2015_code"].astype(str).str.strip().str[0]
    c = c[c["div_2004"].str.isdigit() & c["div_2015"].str.isdigit()]

    rows = []
    for div04, grp in c.groupby("div_2004"):
        counts = grp["div_2015"].value_counts()
        modal = counts.index[0]
        purity = float(counts.iloc[0] / counts.sum())
        rows.append(
            {
                "nco_2004_division": div04,
                "nco_2015_division": modal,
                "confidence": round(purity, 4),
                "n_concorded_codes": int(counts.sum()),
                "n_in_modal_division": int(counts.iloc[0]),
                "alternative_divisions": "; ".join(
                    f"{k}:{v}" for k, v in counts.iloc[1:].items()
                )
                or None,
                "authority": "PROJECT_DERIVED_FROM_OFFICIAL",
                "method": "FIRST_DIGIT_TRUNCATION_OF_OFFICIAL_CONCORDANCE",
            }
        )
    # 'X' (workers not classified by occupation) has no NCO-2015 equivalent and is
    # left unmapped rather than forced somewhere.
    rows.append(
        {
            "nco_2004_division": "X",
            "nco_2015_division": None,
            "confidence": None,
            "n_concorded_codes": 0,
            "n_in_modal_division": 0,
            "alternative_divisions": None,
            "authority": "PROJECT_DERIVED_FROM_OFFICIAL",
            "method": "NOT_MAPPABLE_workers_not_classified_by_occupation",
        }
    )
    return pd.DataFrame(rows).sort_values("nco_2004_division").reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 6. Labour-market context (PLFS)
# --------------------------------------------------------------------------- #
def build_analytical_labour_market_context(plfs: pd.DataFrame) -> pd.DataFrame:
    """PLFS indicators, passed through at their only valid grain.

    No transformation is applied beyond labelling, because there is nothing valid
    to do: these are national rates from one month. They are context, never demand,
    and `geo_level` stays NATIONAL.
    """
    out = plfs.copy()
    out["observation_status"] = OBSERVED
    out["statistical_basis"] = "SAMPLE_SURVEY_CWS"
    out["valid_geo_level"] = "NATIONAL"
    out["district_estimates_valid"] = False
    out["not_a_demand_measure"] = True
    out["source_vintage"] = out["period_id"]
    out["transformation"] = "NONE_PASSTHROUGH"
    return out.reset_index(drop=True)
