"""The LMIS API and dashboard application.

Read-only by construction: the warehouse connection is opened read-only, so no
route can write. The app computes no analytical value - it serves what the
warehouse holds, wrapped in the Step 7.2 publication envelope.

Run: `make serve`  (uvicorn api.main:app)
"""
from __future__ import annotations

import json
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api import envelope, warehouse
from api.routers import capabilities, context, coverage, demand, exports, meta, training
from lmis.publish import lint_contract, lint_envelopes, lint_label_catalogue
from lmis.publish.contract import ContractError

STATIC = Path(__file__).parent / "static"

def verify_contract() -> None:
    """Refuse to serve if the published surface breaches the contract.

    Checked at startup rather than per request, so a terminology regression or a
    stray `is_measured_shortage` fails the deploy instead of reaching a reader.
    """
    c = warehouse.contract()
    envs = warehouse.envelopes()
    violations = lint_contract(c) + lint_envelopes(envs, c)
    for lang in ("en", "hi"):
        f = STATIC / "i18n" / f"{lang}.json"
        if f.is_file():
            labels = {k: v for k, v in json.loads(f.read_text()).items()
                      if isinstance(v, str)}
            violations += lint_label_catalogue(labels, c, f"i18n/{lang}")
    if violations:
        raise ContractError(
            "terminology violations: " + "; ".join(str(v) for v in violations)
        )
    for e in envs:
        if e["is_measured_shortage"] is not False:
            raise ContractError(f"{e['output_id']}: is_measured_shortage must be False")
        if e["forecast_available"] is not False:
            raise ContractError(f"{e['output_id']}: forecast_available must be False")
    # No experimental output may be reachable from a production export.
    leaked = set(envelope.experimental_output_ids()) & set(exports.EXPORTABLE)
    if leaked:
        raise ContractError(f"experimental output(s) exportable: {sorted(leaked)}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    verify_contract()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="LMIS - Labour Market Intelligence System",
    version=warehouse.contract().contract_version,
    description=(
        "Evidence-qualified labour-market demand intelligence (production mode "
        "OPTION_A). No demand-supply gap, no forecast and no occupation-level "
        "supply is published: those capabilities are reported as explicitly "
        "unavailable, with a reason and a gate, at /api/capabilities."
    ),
)

# `capabilities` is registered FIRST so its literal blocked paths win over the
# parameterised demand routes. `/api/demand/districts/vacancy-count` must return
# the unavailability document, not be read as a district whose code is
# "vacancy-count" - FastAPI resolves in registration order.
for r in (capabilities.router, meta.router, coverage.router, demand.router,
          context.router, training.router, exports.router):
    app.include_router(r)


@app.exception_handler(ContractError)
def _contract_error(_request, exc: ContractError):
    """A contract breach is a server fault, never a silently degraded response."""
    return JSONResponse(
        {"error": "PUBLICATION_CONTRACT_VIOLATION", "detail": str(exc)}, status_code=500
    )


@app.get("/api/health", tags=["metadata"])
def health():
    c = warehouse.contract()
    return {
        "status": "ok",
        "contract_version": c.contract_version,
        "mode": c.mode,
        "production_outputs": len(envelope.production_output_ids()),
        "unavailable_capabilities": len(warehouse.register()),
        "is_measured_shortage": False,
        "forecast_available": False,
    }


if STATIC.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")
