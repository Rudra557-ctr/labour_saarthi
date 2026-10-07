"""R11: PLFS supporting context.

SUPPORTING tier, OBSERVED evidence, `not_a_demand_measure = TRUE`, national only.
No PLFS-derived metric is computed here: the rows are served as published. There is
deliberately no state or district parameter, because `district_estimates_valid` is
FALSE on every row - the grain does not exist to filter by.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from api import envelope, warehouse

router = APIRouter(prefix="/api/context", tags=["supporting context"])


@router.get("/labour-force", summary="PLFS labour-force context - NOT a demand measure")
def labour_force(
    indicator: str | None = Query(None, pattern="^(LFPR|WPR|UR)$"),
    area: str | None = Query(None, pattern="^(RURAL|URBAN|RURAL\\+URBAN)$"),
    sex: str | None = Query(None, pattern="^(MALE|FEMALE|PERSON)$"),
    age_group: str | None = Query(None),
):
    sql = (
        "SELECT period_id, geo_level, area, sex, age_group, indicator, approach, "
        "value_percent, std_error, unit, statistical_basis, valid_geo_level, "
        "district_estimates_valid, not_a_demand_measure, observation_status, "
        "source_vintage, source_id, snapshot_file "
        "FROM analytical_labour_market_context WHERE 1=1"
    )
    params: list = []
    for col, val in (("indicator", indicator), ("area", area), ("sex", sex),
                     ("age_group", age_group)):
        if val:
            sql += f" AND {col} = ?"
            params.append(val)
    rows = warehouse.query(sql + " ORDER BY indicator, area, sex, age_group", params)
    return envelope.respond(
        "analytical_labour_market_context", rows,
        {"indicator": indicator, "area": area, "sex": sex, "age_group": age_group},
        extra_meta={
            "display_banner": "SUPPORTING CONTEXT - NOT A DEMAND MEASURE",
            "national_only": True,
            "state_or_district_breakdown": (
                "UNAVAILABLE: district_estimates_valid is FALSE for this source, so "
                "no state or district PLFS value may be derived or displayed."
            ),
        },
    )
