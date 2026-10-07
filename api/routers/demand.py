"""R5-R10: the demand surface.

Two protocol-level guarantees, not UI conventions:

* `state` is REQUIRED on the district and district x occupation resources, so
  within-state is the default comparison by construction. An unparameterised
  national district list would hand back a cross-state ranking as though it were
  neutral, and cross-state ordering carries NCS registration coverage as well as
  labour demand.
* `/demand/states` excludes the PAN-India residual by default. It is an
  observation, not a state, and it outranks every actual state - so including it
  silently would put it at the top of any ranking.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api import envelope, warehouse

router = APIRouter(prefix="/api/demand", tags=["demand"])

_RESIDUAL_FLAG = "is_pan_india_residual"


@router.get("/national/industry", summary="OBSERVED NCS vacancies by NCS sector")
def national_industry(ncs_sector: str | None = Query(None)):
    sql = (
        "SELECT snapshot_date, ncs_sector_name, nic_section_code, vacancies_cumulative, "
        "unit, measure_basis, share_of_published_total, mapping_authority, "
        "mapping_method, mapping_confidence, is_heterogeneous_or_residual, "
        "observation_status, source_vintage, source_id, n_source_documents, "
        "source_documents FROM analytical_demand_by_industry"
    )
    params: list = []
    if ncs_sector:
        sql += " WHERE ncs_sector_name = ?"
        params.append(ncs_sector)
    rows = warehouse.query(sql + " ORDER BY vacancies_cumulative DESC", params)
    return envelope.respond(
        "analytical_demand_by_industry", rows, {"ncs_sector": ncs_sector},
        extra_meta={
            "filter_key": "ncs_sector_name",
            "filter_key_note": (
                "The industry filter keys on ncs_sector_name (22 values). Two NCS "
                "sectors have a NULL nic_section_code, so a NIC-keyed filter would "
                "silently drop them."
            ),
            "null_nic_section_rows": sum(
                1 for r in rows if r["nic_section_code"] is None
            ),
            "heterogeneous_or_residual_rows": sum(
                1 for r in rows if r["is_heterogeneous_or_residual"]
            ),
        },
    )


@router.get(
    "/national/occupation-composition",
    summary="ESTIMATED national occupation composition (NIC section x NCO division)",
)
def national_occupation_composition(
    nco_division: str | None = Query(None),
    nic_section: str | None = Query(None),
    confidence: str | None = Query(None, pattern="^(HIGH|MEDIUM|LOW)$"),
):
    sql = (
        "SELECT baseline_period, nic_section_code, ncs_sector_name, nco_2015_division, "
        "vacancies_cumulative, occupation_conditional_share, estimated_occupation_demand, "
        "occupation_total_all_sections, occupation_share_of_total, bridge_year, unit, "
        "measure_basis, is_heterogeneous_or_residual, overall_confidence, "
        "observed_or_estimated, transformation_depth, methodology, source_ids "
        "FROM demand_national_occupation_composition WHERE 1=1"
    )
    params: list = []
    if nco_division:
        sql += " AND nco_2015_division = ?"
        params.append(nco_division)
    if nic_section:
        sql += " AND nic_section_code = ?"
        params.append(nic_section)
    if confidence:
        sql += " AND overall_confidence = ?"
        params.append(confidence)
    rows = warehouse.query(
        sql + " ORDER BY nco_2015_division, estimated_occupation_demand DESC", params
    )
    return envelope.respond(
        "demand_national_occupation_composition", rows,
        {"nco_division": nco_division, "nic_section": nic_section,
         "confidence": confidence},
        extra_meta={
            "confidence_is_per_row": True,
            "confidence_note": (
                "Confidence varies within this output; it is a per-row badge, never "
                "one badge for the view."
            ),
        },
    )


@router.get("/states", summary="OBSERVED state-attributable demand (residual excluded)")
def states(include_residual: bool = Query(False)):
    sql = (
        "SELECT snapshot_date, state_name_as_source, lgd_code, geo_level, "
        f"vacancies_cumulative, unit, measure_basis, {_RESIDUAL_FLAG}, "
        "share_of_published_total, share_of_state_attributable, observation_status, "
        "source_vintage, source_id, n_source_documents, source_documents, "
        "flow_available, flow_unavailable_reason FROM analytical_state_demand"
    )
    if not include_residual:
        sql += f" WHERE {_RESIDUAL_FLAG} = FALSE"
    rows = warehouse.query(sql + " ORDER BY vacancies_cumulative DESC")
    residual = warehouse.query(
        "SELECT state_name_as_source, vacancies_cumulative, share_of_published_total "
        f"FROM analytical_state_demand WHERE {_RESIDUAL_FLAG} = TRUE"
    )
    return envelope.respond(
        "analytical_state_demand", rows, {"include_residual": include_residual},
        extra_meta={
            "residual_excluded_by_default": not include_residual,
            "residual_disclosure": residual,
            "residual_note": (
                "'Multiple States/PAN India' is a residual observation, not a state. "
                "It is never allocated to states or districts, and it is excluded "
                "from the default comparison because it outranks every actual state."
            ),
        },
    )


def _state_exists(state: str) -> dict | None:
    rows = warehouse.query(
        "SELECT DISTINCT state_lgd_code, state_name_lgd FROM "
        "demand_district_relative_signal WHERE state_lgd_code = ? OR state_name_lgd = ?",
        [state, state],
    )
    return rows[0] if rows else None


@router.get(
    "/districts",
    summary="ESTIMATED District Relative Demand Allocation Signal (state required)",
)
def districts(
    state: str = Query(..., description="LGD state code or state name - REQUIRED"),
    comparison: str = Query("within_state", pattern="^(within_state|cross_state)$"),
):
    st = _state_exists(state)
    if st is None:
        raise HTTPException(404, f"unknown state {state!r}")
    order = "rank_within_state" if comparison == "within_state" else "rank_national"
    rows = warehouse.query(
        "SELECT baseline_period, lgd_code, district_name_lgd, state_lgd_code, "
        "state_name_lgd, census_2011_code, observed_state_vacancies, "
        "district_enterprise_count, enterprise_share_within_state, "
        "relative_demand_signal, signal_share_of_national, rank_within_state, "
        "rank_national, unit, geo_level, occupation_level, pan_india_residual_excluded, "
        "udyam_snapshot_date, overall_confidence, observed_or_estimated, "
        "transformation_depth, within_state_ranking_caveat, methodology, source_ids "
        "FROM demand_district_relative_signal WHERE state_lgd_code = ? "
        f"ORDER BY {order}",
        [st["state_lgd_code"]],
    )
    extra = {
        "default_comparison": "within_state",
        "comparison_applied": comparison,
        "districts_in_state": len(rows),
    }
    if comparison == "cross_state":
        extra["cross_state_caveat"] = (
            "Cross-state comparison reflects NCS source/registration coverage as well "
            "as labour demand and is not directly comparable absolute labour demand. "
            "Within-state ranking is the default."
        )
    return envelope.respond(
        "demand_district_relative_signal", rows,
        {"state": state, "comparison": comparison}, extra_meta=extra,
    )


@router.get(
    "/districts/{lgd_code}",
    summary="One district: allocation signal plus its occupation-panel status",
)
def district(lgd_code: str):
    rows = warehouse.query(
        "SELECT * FROM demand_district_relative_signal WHERE lgd_code = ?", [lgd_code]
    )
    if not rows:
        raise HTTPException(404, f"unknown district {lgd_code!r}")
    occ = warehouse.query(
        "SELECT nco_2015_division, nco_name, district_occupation_signal, "
        "occupation_share_of_district, rank_within_district, main_workers, "
        "district_total_main_workers, unclassified_share_not_allocated, "
        "occupation_prior_status, overall_confidence, within_district_ranking_caveat "
        "FROM demand_district_occupation_signal WHERE lgd_code = ? "
        "ORDER BY rank_within_district NULLS LAST",
        [lgd_code],
    )
    n_in_state = warehouse.query(
        "SELECT count(*) AS n FROM demand_district_relative_signal "
        "WHERE state_lgd_code = ?", [rows[0]["state_lgd_code"]]
    )[0]["n"]
    status = occ[0]["occupation_prior_status"] if occ else "CENSUS_NOT_ACQUIRED"
    available = status == "AVAILABLE"
    panel = {
        "status": status if available else "NOT_AVAILABLE",
        "reason_code": None if available else status,
        "reason": None if available else _OCC_REASONS[status],
        # No zero substitute: a district without a prior has no division rows at all.
        "rows": occ if available else None,
        "divisions": len(occ) if available else 0,
    }
    return envelope.respond(
        "demand_district_relative_signal", rows, {"lgd_code": lgd_code},
        extra_meta={"occupation_panel": panel, "districts_in_state": n_in_state},
    )


_OCC_REASONS = {
    "CENSUS_NOT_ACQUIRED": (
        "Census 2011 table B-24 has not been acquired for this district's state. "
        "This is an absence of acquired evidence, not an absence of demand."
    ),
    "NO_CENSUS_2011_CODE": (
        "This district was constituted after the 2011 Census, so a Census occupation "
        "prior can never exist for it. This is not an absence of demand."
    ),
    "AVAILABLE": None,
}


@router.get(
    "/district-occupation",
    summary="ESTIMATED District x Occupation Relative Demand Allocation Signal",
)
def district_occupation(
    state: str = Query(..., description="LGD state code or state name - REQUIRED"),
    nco_division: str | None = Query(None),
    occupation_prior_status: str | None = Query(
        None, pattern="^(AVAILABLE|CENSUS_NOT_ACQUIRED|NO_CENSUS_2011_CODE)$"
    ),
):
    st = _state_exists(state)
    if st is None:
        raise HTTPException(404, f"unknown state {state!r}")
    sql = (
        "SELECT baseline_period, lgd_code, district_name_lgd, state_lgd_code, "
        "state_name_lgd, nco_2015_division, nco_name, relative_demand_signal, "
        "occupation_share_of_district, district_occupation_signal, "
        "unclassified_share_not_allocated, main_workers, district_total_main_workers, "
        "rank_within_district, rank_within_occupation_across_districts, "
        "occupation_prior_status, unit, interpretation, overall_confidence, "
        "observed_or_estimated, transformation_depth, within_district_ranking_caveat, "
        "methodology, source_ids FROM demand_district_occupation_signal "
        "WHERE state_lgd_code = ?"
    )
    params: list = [st["state_lgd_code"]]
    if nco_division:
        sql += " AND nco_2015_division = ?"
        params.append(nco_division)
    if occupation_prior_status:
        sql += " AND occupation_prior_status = ?"
        params.append(occupation_prior_status)
    rows = warehouse.query(
        sql + " ORDER BY rank_within_occupation_across_districts NULLS LAST", params
    )
    breakdown: dict[str, int] = {}
    for r in rows:
        k = r["occupation_prior_status"]
        breakdown[k] = breakdown.get(k, 0) + 1
    return envelope.respond(
        "demand_district_occupation_signal", rows,
        {"state": state, "nco_division": nco_division,
         "occupation_prior_status": occupation_prior_status},
        extra_meta={
            "row_status_breakdown": breakdown,
            "unavailable_reasons": {
                k: v for k, v in _OCC_REASONS.items() if v and k in breakdown
            },
            "informative_comparison": (
                "Across districts within one state and one NCO division, this ordering "
                "combines the enterprise and occupation structures and so restates "
                "neither input. It remains an ESTIMATED allocation signal, never an "
                "observed demand ranking."
            ),
            "default_comparison": "within_state",
        },
    )
