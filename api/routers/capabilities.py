"""R14 plus the explicit blocked routes.

Each blocked capability has a real route that returns HTTP 200 with the
unavailability document. A 404 or an empty array would read as "none found"
rather than "not computable", and that misreading is the one the publication
contract exists to prevent.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api import envelope, warehouse

router = APIRouter(prefix="/api", tags=["capabilities"])


@router.get("/capabilities", summary="Every capability that is not available, with its gate")
def capabilities(capability_id: str | None = Query(None)):
    reg = warehouse.register()
    if capability_id:
        match = [r for r in reg if r["capability_id"] == capability_id]
        if not match:
            raise HTTPException(404, f"unknown capability {capability_id!r}")
        reg = match
    grouped: dict[str, list[str]] = {}
    for r in reg:
        grouped.setdefault(r["reason_code"], []).append(r["capability_id"])
    return envelope.meta_only(
        reg,
        grouped_by_reason_code=grouped,
        reason_code_meaning={
            "NOT_IDENTIFIABLE": (
                "Structural: the evidence cannot determine this quantity, and more of "
                "the same data would not change that."
            ),
            "NOT_ACQUIRED": "The source exists but no snapshot has been taken.",
            "ACCESS_PENDING": "Identified, but access is unresolved.",
            "NOT_AVAILABLE": "Not published at the grain required.",
            "NOT_SUPPORTED_YET": "Blocked by a temporal condition, not a structural one.",
            "PROHIBITED": "Permitted by no configuration; doing it would invent data.",
        },
    )


# --- Blocked capability routes. Each returns 200 + an explicit reason. --------
_BLOCKED = {
    "/demand-supply-gap": "demand_supply_gap_numeric",
    "/forecast": "forecast",
    "/supply/district-occupation": "district_occupation_supply",
    "/supply/state-occupation": "state_occupation_supply",
    "/supply/district-trade": "district_trade_supply",
    "/supply/state-trade": "state_trade_supply",
    "/shortage": "shortage_or_surplus_count",
    "/demand/districts/vacancy-count": "district_vacancy_count",
    "/demand/district-occupation/vacancy-count": "district_occupation_vacancy_count",
    "/residual-allocation": "pan_india_residual_allocation",
}


def _make(capability_id: str):
    def handler():
        return envelope.unavailable(capability_id)

    handler.__name__ = f"unavailable_{capability_id}"
    return handler


for _path, _cap in _BLOCKED.items():
    router.add_api_route(
        _path,
        _make(_cap),
        methods=["GET"],
        tags=["unavailable"],
        summary=f"UNAVAILABLE - {_cap}",
    )
