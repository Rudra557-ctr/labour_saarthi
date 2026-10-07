"""R12-R13: OBSERVED training-system facts.

These are candidate counts within a named scheme and period. They are never
labelled supply: no occupation-level or geographic supply quantity exists, so a
`supply` reading would assert a quantity the project does not hold. The trade
resource is national Top-N only and says so.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from api import envelope, warehouse

router = APIRouter(prefix="/api/training", tags=["training system"])


@router.get("/states", summary="OBSERVED state training-system outcomes (not supply)")
def states(
    state: str | None = Query(None),
    scheme: str | None = Query(None),
    measure: str | None = Query(
        None, pattern="^(ENROLLED|TRAINED|ASSESSED|CERTIFIED|PLACED)$"
    ),
):
    sql = (
        "SELECT scheme, scheme_period, as_on_date, state_name_as_source, "
        "state_lgd_code, geo_level, geography_status, measure, measure_definition, "
        "value_as_published, value, unit, value_status, observed_or_estimated, "
        "source_annexure, source_id FROM fact_training_outcome WHERE 1=1"
    )
    params: list = []
    if state:
        sql += " AND (state_lgd_code = ? OR state_name_as_source = ?)"
        params += [state, state]
    if scheme:
        sql += " AND scheme = ?"
        params.append(scheme)
    if measure:
        sql += " AND measure = ?"
        params.append(measure)
    rows = warehouse.query(sql + " ORDER BY scheme, state_name_as_source, measure", params)
    infra = warehouse.query(
        "SELECT as_on_date, state_name_as_source, state_lgd_code, metric, "
        "metric_definition, value, unit, value_status, observed_or_estimated "
        "FROM fact_training_infrastructure"
        + (" WHERE state_lgd_code = ? OR state_name_as_source = ?" if state else "")
        + " ORDER BY state_name_as_source, metric",
        [state, state] if state else [],
    )
    return envelope.respond(
        "fact_training_outcome", rows,
        {"state": state, "scheme": scheme, "measure": measure},
        extra_meta={
            "infrastructure": infra,
            "infrastructure_output_id": "fact_training_infrastructure",
            "infrastructure_vintage": sorted({str(r["as_on_date"]) for r in infra}),
            "no_data_cells": sum(1 for r in rows if r["value_status"] == "NO_DATA"),
            "no_data_note": (
                "A cell published as '-' is NO_DATA with a NULL value - never zero. "
                "A state that did not report a measure is not a state with none."
            ),
            "never_pooled_across_schemes": True,
            "not_supply_note": (
                "Candidate counts within a named scheme and period. No occupation or "
                "trade dimension exists, so these are not a supply quantity."
            ),
        },
    )


@router.get("/trades/top-n", summary="OBSERVED national Top-N trades (not a distribution)")
def trades_top_n(scheme: str | None = Query(None)):
    sql = (
        "SELECT source_table, scheme, period_label, geo_level, occupation_entity_type, "
        "entity_name_as_source, published_rank, measure, measure_definition, "
        "value_as_published, value, unit, value_status, is_top_n_subset, "
        "published_grand_total, nco_link_status, nco_codes_via_existing_map, "
        "nco_link_method, observed_or_estimated, source_id "
        "FROM fact_training_trade_outcome"
    )
    params: list = []
    if scheme:
        sql += " WHERE scheme = ?"
        params.append(scheme)
    rows = warehouse.query(sql + " ORDER BY scheme, measure, published_rank", params)
    return envelope.respond(
        "fact_training_trade_outcome", rows, {"scheme": scheme},
        extra_meta={
            "is_top_n_subset": True,
            "top_n_note": (
                "A published Top-N subset, not a complete trade distribution. It may "
                "not be converted into trade shares, or into state or district trade "
                "quantities."
            ),
            "geo_level": "NATIONAL",
        },
    )
