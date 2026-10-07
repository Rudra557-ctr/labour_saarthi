"""R4 + R15: coverage disclosures and pipeline data quality."""
from __future__ import annotations

from fastapi import APIRouter, Query

from api import envelope, warehouse
from lmis.publish import resolve_coverage

router = APIRouter(prefix="/api", tags=["coverage"])


@router.get("/coverage", summary="Coverage disclosures, derived from the warehouse")
def get_coverage(domain: str | None = Query(None, pattern="^(demand|supply)$")):
    con = warehouse.connect()
    try:
        derived = resolve_coverage(con, warehouse.contract())
    finally:
        con.close()
    rows: list[dict] = []
    if domain in (None, "demand"):
        rows += warehouse.query(
            "SELECT 'demand' AS domain, 'Demand evidence' AS domain_label, "
            "baseline_period, metric, value, unit, note "
            "FROM demand_coverage_summary ORDER BY metric"
        )
    if domain in (None, "supply"):
        # The query parameter stays `supply` for compatibility, but the DISPLAYED
        # label does not: these rows describe TRAINING-EVIDENCE coverage, and
        # "supply" is a reserved word that may not name a training measure.
        rows += warehouse.query(
            "SELECT 'supply' AS domain, 'Training evidence' AS domain_label, "
            "NULL AS baseline_period, metric, value, unit, note "
            "FROM supply_coverage_summary ORDER BY metric"
        )
    barred = {b["field"] for b in warehouse.contract().barred_fields}
    return envelope.meta_only(
        rows,
        derived_disclosures=derived,
        barred_fields=sorted(barred),
        domain_labels={"demand": "Demand evidence", "supply": "Training evidence"},
        domain_label_note=(
            "The `supply` domain key is retained for compatibility; its displayed "
            "label is 'Training evidence', because these rows describe training "
            "evidence coverage and not a supply quantity."
        ),
        note=(
            "The residual and state-attributable shares and the district counts are "
            "resolved from the warehouse, never hard-coded."
        ),
    )


@router.get("/quality", summary="Pipeline data-quality check results")
def get_quality(table: str | None = Query(None)):
    sql = (
        "SELECT run_id, table_name, check_name, status, observed, expected, severity, "
        "checked_at FROM fact_data_quality"
    )
    params: list = []
    if table:
        sql += " WHERE table_name = ?"
        params.append(table)
    return envelope.meta_only(
        warehouse.query(sql + " ORDER BY table_name, check_name", params),
        note="Pipeline contract checks, not a statement about data accuracy.",
    )
