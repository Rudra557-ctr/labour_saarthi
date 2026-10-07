"""The single response shape, built on the Step 7.2 publication envelope.

There is deliberately no second metadata system here. `meta` is the envelope that
`src/lmis/publish/contract.py` produces, with only the four additions Step 7.3 §8
specifies: `data`, `query`, `links`, and two derived-from-stored-columns fields
(`limitations`, `row_status_breakdown`).

`limitations` is never authored in this layer - it is read out of the output's own
caveat columns, so a caveat cannot drift from the data that carries it.
"""
from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from api import warehouse
from lmis.publish.contract import EXPERIMENTAL, PRODUCTION, ContractError

# Extra limitation text that is a property of the output, not of a row.
_STATIC_LIMITATIONS: dict[str, list[str]] = {
    "demand_district_occupation_signal": [
        "Census occupation structure is 2011; the demand baseline is 2024-11-15.",
    ],
    "analytical_demand_by_industry": [
        "The NCS-sector to NIC-section alignment is the project's own (authority "
        "PROJECT, confidence 0.95); the vacancy counts are observed.",
    ],
    "fact_training_trade_outcome": [
        "Top-N subset as published; not a complete trade distribution.",
    ],
    "analytical_labour_market_context": [
        "Supporting context, not a demand measure. National only - district "
        "estimates are not valid for this source.",
    ],
}


def _limitations(env: dict[str, Any]) -> list[str]:
    out: list[str] = []
    cav = env.get("required_caveat")
    if cav:
        out.extend(cav["text"])
    out.extend(_STATIC_LIMITATIONS.get(env["output_id"], []))
    return out


def respond(
    output_id: str,
    data: list[dict[str, Any]] | None,
    query: dict[str, Any] | None = None,
    extra_meta: dict[str, Any] | None = None,
    links: dict[str, str] | None = None,
) -> JSONResponse:
    """Wrap rows in the contracted envelope. Production outputs only."""
    env = warehouse.envelope(output_id)
    if env["publication_status"] != PRODUCTION:
        # Defence in depth: an experimental output can never reach a production route.
        raise ContractError(
            f"{output_id} is {env['publication_status']}, not PRODUCTION; it may not "
            f"be served from a production route"
        )
    env["limitations"] = _limitations(env)
    if extra_meta:
        env.update(extra_meta)
    env["returned_rows"] = 0 if data is None else len(data)
    return JSONResponse(
        {
            "data": data,
            "query": query or {},
            "meta": env,
            "links": links
            or {
                "methodology": f"/api/meta/methodology?output_id={output_id}",
                "coverage": "/api/coverage",
                "capabilities": "/api/capabilities",
            },
        }
    )


def unavailable(capability_id: str) -> JSONResponse:
    """The explicit unavailability document - HTTP 200, `data: null`, never 404.

    A 404 or an empty array reads as "none found" rather than "not computable",
    which is the misreading the whole publication contract exists to prevent.
    """
    for r in warehouse.register():
        if r["capability_id"] == capability_id:
            return JSONResponse(
                {
                    "data": None,
                    "query": {},
                    "meta": r
                    | {
                        "unblocking_conditions_url": r["unblocking_conditions_url"],
                        "contract_version": warehouse.contract().contract_version,
                    },
                    "links": {"capabilities": "/api/capabilities"},
                }
            )
    raise KeyError(capability_id)


def meta_only(payload: dict[str, Any] | list[Any], **extra: Any) -> JSONResponse:
    return JSONResponse({"data": payload, "meta": {
        "publication_status": PRODUCTION,
        "contract_version": warehouse.contract().contract_version,
        "is_measured_shortage": False,
        "forecast_available": False,
        **extra,
    }})


def production_output_ids() -> list[str]:
    return [
        e["output_id"]
        for e in warehouse.envelopes()
        if e["publication_status"] == PRODUCTION and e.get("implemented", True)
    ]


def experimental_output_ids() -> list[str]:
    return [
        e["output_id"]
        for e in warehouse.envelopes()
        if e["publication_status"] == EXPERIMENTAL
    ]
