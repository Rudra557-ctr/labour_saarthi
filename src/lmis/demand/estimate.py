"""Step 4.0 demand estimation — the three outputs approved in Step 3.1.

Nothing here invents a term. Each output is a product of quantities that exist in
the warehouse, and the formula for each is the one documented in
docs/step3_1_estimation_methodology.md §9.

Outputs A and C are kept SEPARATE and are never multiplied together: doing so
would apply two different occupational structures to one quantity and double-count
the occupational signal.
"""
from __future__ import annotations

import pandas as pd

from lmis.demand.confidence import Confidence

# The ILO cross-tab year used as the industry -> occupation bridge. Explicit, so
# the choice is reviewable rather than "whatever was latest at build time".
BRIDGE_YEAR = "2025"
# Udyam category used as the district allocation basis: all registered MSMEs.
ALLOCATION_CATEGORY = "TOTAL"

ESTIMATED = "ESTIMATED"
UNAVAILABLE = "UNAVAILABLE"


# ===========================================================================
# A. National occupation demand composition
# ===========================================================================
def build_national_occupation_composition(
    demand_by_industry: pd.DataFrame,
    ilo: pd.DataFrame,
    baseline_period: str,
    built_at: str,
) -> pd.DataFrame:
    """A = sum over industry sections of  V_national[section] x P(occupation | section).

    Joined ONLY at NIC-2008 section, the one validated common classification.
    Rows whose NCS sector has no NIC section (``Sector Not Specified``) are
    excluded from the product and reported in coverage metadata instead - they
    carry no industry information at all, so no occupation can be inferred.

    No geographic allocation happens here. This is a national result.
    """
    # Observed national vacancies by industry section (lakh, as published).
    obs = demand_by_industry[
        (demand_by_industry["snapshot_date"] == baseline_period)
        & demand_by_industry["nic_section_code"].notna()
    ][
        ["nic_section_code", "ncs_sector_name", "vacancies_cumulative", "unit",
         "mapping_confidence", "is_heterogeneous_or_residual"]
    ].rename(
        # Renamed so it cannot collide with the Confidence dataclass's own
        # `mapping_confidence` column on concat.
        columns={"mapping_confidence": "industry_mapping_confidence"}
    ).copy()

    # Conditional occupation distribution P(occupation | section) from the ILO
    # cross-tab. Suppressed cells are dropped from the numerator AND denominator,
    # so each section's distribution normalises over what the source publishes.
    bridge = ilo[(ilo["year"] == BRIDGE_YEAR) & ilo["employment_thousands"].notna()][
        ["nic_2008_section", "nco_2015_division", "employment_thousands"]
    ].copy()
    bridge["section_total"] = bridge.groupby("nic_2008_section")[
        "employment_thousands"
    ].transform("sum")
    bridge["occupation_conditional_share"] = (
        bridge["employment_thousands"] / bridge["section_total"]
    )
    bridge["bridge_cells_in_section"] = bridge.groupby("nic_2008_section")[
        "nco_2015_division"
    ].transform("count")

    df = obs.merge(
        bridge, left_on="nic_section_code", right_on="nic_2008_section", how="inner"
    )
    df["estimated_occupation_demand"] = (
        df["vacancies_cumulative"] * df["occupation_conditional_share"]
    )

    # Occupation totals across all sections -> the composition itself.
    occ_total = df.groupby("nco_2015_division")["estimated_occupation_demand"].transform("sum")
    grand_total = df["estimated_occupation_demand"].sum()
    df["occupation_total_all_sections"] = occ_total
    df["occupation_share_of_total"] = occ_total / grand_total

    # Confidence: mapping confidence is the NCS->NIC alignment for this section;
    # occupation evidence is DIRECT because the bridge is national and so is the
    # output. Depth 1 (one multiplication).
    rows = []
    for _, r in df.iterrows():
        conf = Confidence(
            source_confidence="OBSERVED",
            mapping_confidence=float(r["industry_mapping_confidence"]),
            temporal_confidence="CURRENT",
            geography_coverage="DIRECT",
            occupation_coverage="DIRECT",
            statistical_support="SURVEY_WITHOUT_N",
            transformation_depth=1,
        )
        rows.append(conf.as_columns())
    conf_df = pd.DataFrame(rows, index=df.index)
    out = pd.concat([df, conf_df], axis=1)

    out["baseline_period"] = baseline_period
    out["geo_level"] = "NATIONAL"
    out["industry_level"] = "NIC_SECTION"
    out["occupation_level"] = "NCO_2015_DIVISION"
    out["unit"] = "lakh_vacancy_equivalent"
    out["observed_or_estimated"] = ESTIMATED
    out["measure_basis"] = "CUMULATIVE_SINCE_INCEPTION_COMPOSITION"
    out["methodology"] = (
        "A: observed NCS vacancies by NIC-2008 section x P(NCO-2015 division | section) "
        f"from ILOSTAT EMP_TEMP_ECO_OCU_NB_A (India, PLFS, {BRIDGE_YEAR}); "
        "joined at NIC section only; no geographic allocation"
    )
    out["source_ids"] = "NCS_PARLIAMENTARY_ANSWERS; ILOSTAT_EMP_ECO_OCU"
    out["bridge_year"] = BRIDGE_YEAR
    out["flow_available"] = False
    out["flow_unavailable_reason"] = (
        "single NCS as-on date; a flow requires two differently dated snapshots"
    )
    out["built_at"] = built_at
    return out.drop(columns=["nic_2008_section"]).reset_index(drop=True)


# ===========================================================================
# B. District relative demand signal
# ===========================================================================
def build_district_relative_signal(
    state_demand: pd.DataFrame,
    district_structure: pd.DataFrame,
    location_master: pd.DataFrame,
    baseline_period: str,
    built_at: str,
) -> pd.DataFrame:
    """B = V_state_attributable[state] x enterprise_share_within_state[district].

    The PAN-India residual is excluded here by construction: only rows with
    ``is_pan_india_residual == False`` and a resolved lgd_code enter the join, so
    the residual can never reach a district.

    NOTE recorded on every row (`within_state_ranking_caveat`): because the state
    multiplier is constant inside a state, the WITHIN-STATE ordering of this
    signal is identical to the ordering of the Udyam enterprise share. B therefore
    adds information only when comparing districts ACROSS states.
    """
    attributable = state_demand[
        (state_demand["snapshot_date"] == baseline_period)
        & (~state_demand["is_pan_india_residual"])
        & state_demand["lgd_code"].notna()
    ]
    # Two NCS rows (the pre-2020 UTs) resolve to one LGD state, so sum per LGD
    # state rather than assuming one row each.
    per_state = (
        attributable.groupby("lgd_code", as_index=False)
        .agg(
            observed_state_vacancies=("vacancies_cumulative", "sum"),
            ncs_source_rows=("state_name_as_source", "count"),
            ncs_state_names=("state_name_as_source", lambda s: "; ".join(sorted(s))),
        )
        .rename(columns={"lgd_code": "state_lgd_code"})
    )

    dist = district_structure[
        (district_structure["enterprise_category"] == ALLOCATION_CATEGORY)
    ][
        ["lgd_code", "district_name_lgd", "state_lgd_code", "census_2011_code",
         "enterprise_share_within_state", "total", "snapshot_date", "source_vintage"]
    ].rename(
        columns={
            "total": "district_enterprise_count",
            "snapshot_date": "udyam_snapshot_date",
            "source_vintage": "udyam_source_vintage",
        }
    )

    df = dist.merge(per_state, on="state_lgd_code", how="inner", validate="many_to_one")
    df["relative_demand_signal"] = (
        df["observed_state_vacancies"] * df["enterprise_share_within_state"]
    )
    df["signal_share_of_national"] = (
        df["relative_demand_signal"] / df["relative_demand_signal"].sum()
    )
    df["rank_within_state"] = df.groupby("state_lgd_code")["relative_demand_signal"].rank(
        ascending=False, method="min"
    ).astype("Int64")
    df["rank_national"] = df["relative_demand_signal"].rank(
        ascending=False, method="min"
    ).astype("Int64")

    conf = Confidence(
        source_confidence="OBSERVED",
        mapping_confidence=None,
        temporal_confidence="RECENT",      # Udyam 2023 vs NCS as-on 2024
        geography_coverage="ALLOCATED",
        occupation_coverage="NOT_APPLICABLE",  # B has no occupation dimension by design
        statistical_support="ADMINISTRATIVE_FULL_COVERAGE",
        transformation_depth=1,
    ).as_columns()
    for k, v in conf.items():
        df[k] = v

    states = location_master[location_master["level"] == "STATE"][["lgd_code", "name_en"]]
    df = df.merge(
        states.rename(columns={"lgd_code": "state_lgd_code", "name_en": "state_name_lgd"}),
        on="state_lgd_code",
        how="left",
    )

    df["baseline_period"] = baseline_period
    df["geo_level"] = "DISTRICT"
    df["occupation_level"] = "NONE"
    df["unit"] = "relative_signal_unitless"
    df["observed_or_estimated"] = ESTIMATED
    df["methodology"] = (
        "B: observed NCS state-attributable vacancies x Udyam district enterprise "
        f"share within state (category {ALLOCATION_CATEGORY}); PAN-India residual excluded"
    )
    df["within_state_ranking_caveat"] = (
        "within a state this ordering equals the Udyam enterprise-share ordering; "
        "B adds information only across states"
    )
    df["source_ids"] = "NCS_PARLIAMENTARY_ANSWERS; UDYAM_DISTRICT_MSME; LGD_DISTRICTS_DATAGOVIN"
    df["pan_india_residual_excluded"] = True
    df["flow_available"] = False
    df["flow_unavailable_reason"] = (
        "single NCS as-on date; a flow requires two differently dated snapshots"
    )
    df["built_at"] = built_at
    return df.reset_index(drop=True)


# ===========================================================================
# C. District x occupation relative demand signal
# ===========================================================================
def build_district_occupation_signal(
    district_signal: pd.DataFrame,
    district_occupation_structure: pd.DataFrame,
    division_map: pd.DataFrame,
    location_master: pd.DataFrame,
    baseline_period: str,
    built_at: str,
) -> pd.DataFrame:
    """C = B[district] x census_occupation_share[district, division].

    Uses the CENSUS district occupation structure, never the ILO national bridge -
    multiplying B by the national bridge AND the census shares would double-count
    the occupational signal, so output A is not a factor here.

    Census cells used: area TOTAL, sex PERSON, row_type DIVISION_TOTAL. The
    UNCLASSIFIED bucket is excluded from the occupation product (it has no NCO
    equivalent) and its share is retained per district as
    `unclassified_share_not_allocated`, so the shortfall is visible rather than
    silently redistributed.

    EVERY district in B appears in C, with an explicit status - none is silently
    omitted. Three statuses are distinguished because they are genuinely different
    situations and must not be merged:

      AVAILABLE              Census prior exists and is used.
      NO_CENSUS_2011_CODE    The district post-dates Census 2011, so a prior can
                             NEVER exist for it. Permanent.
      CENSUS_NOT_ACQUIRED    The district has a Census-2011 code, but B-24 has not
                             been acquired for its state yet. Resolvable by
                             acquiring more states.

    Nothing is zero-filled, inherited from a parent district, or back-filled with a
    national distribution.
    """
    census = district_occupation_structure[
        (district_occupation_structure["area"] == "TOTAL")
        & (district_occupation_structure["sex"] == "PERSON")
    ].copy()

    dmap = division_map.set_index("nco_2004_division")
    allocatable = census[census["row_type"] == "DIVISION_TOTAL"].copy()
    allocatable["nco_2015_division"] = allocatable["nco_2004_division"].map(
        dmap["nco_2015_division"]
    )
    allocatable["division_map_confidence"] = allocatable["nco_2004_division"].map(
        dmap["confidence"]
    )
    allocatable = allocatable[allocatable["nco_2015_division"].notna()]

    unclassified = (
        census[census["row_type"] == "UNCLASSIFIED"]
        .groupby("census_district_code")["occupation_share_of_district"]
        .sum()
        .rename("unclassified_share_not_allocated")
        .reset_index()
    )

    # District signal keyed by Census code, available only where a prior exists.
    base = district_signal[
        ["lgd_code", "district_name_lgd", "state_lgd_code", "state_name_lgd",
         "census_2011_code", "relative_demand_signal", "observed_state_vacancies",
         "enterprise_share_within_state"]
    ].copy()
    with_prior = base[base["census_2011_code"].notna()]

    df = with_prior.merge(
        allocatable[
            ["census_district_code", "nco_2004_division", "nco_2015_division",
             "nco_name", "occupation_share_of_district", "division_map_confidence",
             "main_workers", "district_total_main_workers"]
        ],
        left_on="census_2011_code",
        right_on="census_district_code",
        how="inner",
    ).merge(unclassified, on="census_district_code", how="left")

    df["district_occupation_signal"] = (
        df["relative_demand_signal"] * df["occupation_share_of_district"]
    )
    df["rank_within_district"] = df.groupby("lgd_code")["district_occupation_signal"].rank(
        ascending=False, method="min"
    ).astype("Int64")
    df["rank_within_occupation_across_districts"] = df.groupby("nco_2015_division")[
        "district_occupation_signal"
    ].rank(ascending=False, method="min").astype("Int64")
    df["occupation_prior_status"] = "AVAILABLE"
    df["observed_or_estimated"] = ESTIMATED

    # Confidence is per-row because division purity differs by division.
    conf_rows = [
        Confidence(
            source_confidence="OBSERVED",
            mapping_confidence=float(c) if pd.notna(c) else None,
            temporal_confidence="HISTORICAL",   # Census 2011 occupation prior
            geography_coverage="ALLOCATED",
            occupation_coverage="DIVISION_MAPPED",
            statistical_support="CENSUS",
            transformation_depth=2,
        ).as_columns()
        for c in df["division_map_confidence"]
    ]
    df = pd.concat([df, pd.DataFrame(conf_rows, index=df.index)], axis=1)

    # Every district not covered above gets ONE explicit row stating WHY.
    covered = set(df["lgd_code"])
    acquired_census_codes = set(allocatable["census_district_code"])
    missing = base[~base["lgd_code"].isin(covered)].copy()
    if len(missing):
        for col in (
            "census_district_code", "nco_2004_division", "nco_2015_division", "nco_name",
            "occupation_share_of_district", "division_map_confidence", "main_workers",
            "district_total_main_workers", "district_occupation_signal",
            "rank_within_district", "rank_within_occupation_across_districts",
            "unclassified_share_not_allocated",
        ):
            missing[col] = pd.NA
        # Distinguish "can never have a prior" from "not acquired yet".
        missing["occupation_prior_status"] = missing["census_2011_code"].apply(
            lambda c: "NO_CENSUS_2011_CODE" if pd.isna(c) else "CENSUS_NOT_ACQUIRED"
        )
        missing["observed_or_estimated"] = UNAVAILABLE
        unavail_conf = Confidence(
            source_confidence="OBSERVED",
            mapping_confidence=None,
            temporal_confidence="HISTORICAL",
            geography_coverage="ALLOCATED",
            occupation_coverage="NOT_AVAILABLE",
            statistical_support="NONE",
            transformation_depth=2,
        ).as_columns()
        for k, v in unavail_conf.items():
            missing[k] = v
        df = pd.concat([df, missing], ignore_index=True)

    df["baseline_period"] = baseline_period
    df["geo_level"] = "DISTRICT"
    df["occupation_level"] = "NCO_2015_DIVISION"
    df["unit"] = "relative_signal_unitless"
    df["methodology"] = (
        "C: district relative demand signal (B) x Census-2011 district occupation "
        "share (NCO-2004 division mapped to NCO-2015 division). Output A is NOT a "
        "factor - using it as well would double-count the occupational signal."
    )
    df["within_district_ranking_caveat"] = (
        "within a district this ordering equals the Census-2011 occupation-share "
        "ordering; C adds information only across districts"
    )
    df["interpretation"] = "RELATIVE_RANKING_SIGNAL_NOT_A_VACANCY_COUNT"
    df["source_ids"] = (
        "NCS_PARLIAMENTARY_ANSWERS; UDYAM_DISTRICT_MSME; CENSUS_2011_B24; "
        "LGD_DISTRICTS_DATAGOVIN"
    )
    df["flow_available"] = False
    df["flow_unavailable_reason"] = (
        "single NCS as-on date; a flow requires two differently dated snapshots"
    )
    df["built_at"] = built_at
    return df.reset_index(drop=True)


def build_coverage_summary(
    state_demand: pd.DataFrame,
    district_signal: pd.DataFrame,
    occupation_signal: pd.DataFrame,
    baseline_period: str,
    built_at: str,
) -> pd.DataFrame:
    """Coverage accounting, including the PAN-India residual.

    The residual is reported here rather than dropped, so the share of the measure
    that is geographically attributable is always visible next to the outputs.
    """
    snap = state_demand[state_demand["snapshot_date"] == baseline_period]
    total = float(snap["vacancies_cumulative"].sum())
    residual = float(snap[snap["is_pan_india_residual"]]["vacancies_cumulative"].sum())
    attributable = total - residual
    avail = occupation_signal[occupation_signal["occupation_prior_status"] == "AVAILABLE"]
    no_code = occupation_signal[
        occupation_signal["occupation_prior_status"] == "NO_CENSUS_2011_CODE"
    ]
    not_acq = occupation_signal[
        occupation_signal["occupation_prior_status"] == "CENSUS_NOT_ACQUIRED"
    ]
    rows = [
        ("ncs_vacancies_published_total", total, "count", "observed published grand total"),
        ("ncs_vacancies_pan_india_residual", residual, "count",
         "kept NATIONAL; never allocated to districts"),
        ("ncs_vacancies_state_attributable", attributable, "count",
         "the only part entering district allocation"),
        ("ncs_state_attributable_share", attributable / total, "ratio",
         "dashboard must state this as coverage"),
        ("districts_with_relative_signal", float(district_signal["lgd_code"].nunique()),
         "count", "output B coverage"),
        ("districts_with_occupation_signal", float(avail["lgd_code"].nunique()), "count",
         "output C coverage: Census prior available"),
        ("districts_no_census_2011_code", float(no_code["lgd_code"].nunique()), "count",
         "output C: post-2011 districts - a prior can never exist; never zero-filled"),
        ("districts_census_not_acquired", float(not_acq["lgd_code"].nunique()), "count",
         "output C: has a Census code but B-24 not yet acquired for its state"),
    ]
    out = pd.DataFrame(rows, columns=["metric", "value", "unit", "note"])
    out["baseline_period"] = baseline_period
    out["built_at"] = built_at
    return out
