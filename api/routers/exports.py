"""Production CSV/JSON export.

Two rules carry the weight here:

* **The metadata block is mandatory.** An export is the likeliest route by which a
  relative signal becomes "vacancies" in someone's slide, so every file carries its
  evidence status, tier, confidence, coverage, provenance, vintage, limitations and
  `is_measured_shortage` - as CSV comment lines or a JSON `meta` object.
* **A relative-signal column keeps its name and its unit.** Nothing is renamed to
  anything count-like, and no vacancies column is derived from one.

Experimental and unavailable outputs cannot be exported; the guard is the same
`assert_no_experimental_leak` the contract already ships.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from api import envelope, warehouse
from lmis.publish.contract import assert_no_experimental_leak

router = APIRouter(prefix="/api/export", tags=["export"])

# Only these outputs are exportable, and only at their own grain.
EXPORTABLE = {
    "analytical_state_demand":
        "SELECT * FROM analytical_state_demand ORDER BY vacancies_cumulative DESC",
    "analytical_demand_by_industry":
        "SELECT * FROM analytical_demand_by_industry ORDER BY vacancies_cumulative DESC",
    "demand_national_occupation_composition":
        "SELECT * FROM demand_national_occupation_composition "
        "ORDER BY nco_2015_division, nic_section_code",
    "demand_district_relative_signal":
        "SELECT * FROM demand_district_relative_signal "
        "ORDER BY state_name_lgd, rank_within_state",
    "demand_district_occupation_signal":
        "SELECT * FROM demand_district_occupation_signal "
        "ORDER BY state_name_lgd, lgd_code, rank_within_district NULLS LAST",
    "fact_training_outcome":
        "SELECT * FROM fact_training_outcome ORDER BY scheme, state_name_as_source, measure",
    "fact_training_infrastructure":
        "SELECT * FROM fact_training_infrastructure ORDER BY state_name_as_source, metric",
    "fact_training_trade_outcome":
        "SELECT * FROM fact_training_trade_outcome ORDER BY scheme, measure, published_rank",
    "analytical_labour_market_context":
        "SELECT * FROM analytical_labour_market_context "
        "ORDER BY indicator, area, sex, age_group",
    "demand_coverage_summary":
        "SELECT * FROM demand_coverage_summary ORDER BY metric",
    "supply_coverage_summary":
        "SELECT * FROM supply_coverage_summary ORDER BY metric",
}


# An export can mix the output's own measure with an observed input carried at a
# COARSER grain - e.g. `observed_state_vacancies` repeated on every district row of
# output B. The header declares one unit for the output, so each such column is
# called out by name; otherwise a reader could take a state total for a district one.
COLUMN_NOTES: dict[str, dict[str, str]] = {
    "demand_district_relative_signal": {
        "relative_demand_signal":
            "THE MEASURE - relative_signal_unitless. Not a count of anything.",
        "signal_share_of_national": "share of the national signal total; unitless",
        "observed_state_vacancies":
            "OBSERVED input at STATE grain, repeated on every district row of that "
            "state. It is NOT this district's vacancy count.",
        "district_enterprise_count":
            "OBSERVED Udyam registered-enterprise count (vintage 2023-12-21); a "
            "derivation input, not a demand measure.",
        "enterprise_share_within_state":
            "derivation input: the factor that sets this ordering within a state",
    },
    "demand_district_occupation_signal": {
        "district_occupation_signal":
            "THE MEASURE - relative_signal_unitless. Not a count of anything.",
        "relative_demand_signal": "the parent district signal (output B); unitless",
        "occupation_share_of_district":
            "derivation input: Census-2011 occupation share, the factor that sets "
            "this ordering within a district",
        "main_workers":
            "OBSERVED Census 2011 count of main workers - a 2011 stock, not demand",
        "district_total_main_workers": "OBSERVED Census 2011 district total",
    },
    "fact_training_trade_outcome": {
        "value": "candidates within a published Top-N subset; NOT a distribution",
        "published_grand_total": "the scheme total the Top-N is drawn from",
    },
}


def _export_meta(output_id: str) -> dict:
    env = warehouse.envelope(output_id)
    assert_no_experimental_leak([env])
    return {
        "output_id": env["output_id"],
        "publication_status": env["publication_status"],
        "tier": env["tier"],
        "evidence_status": env.get("evidence_status"),
        "confidence": env.get("confidence"),
        "coverage": env.get("coverage", {}),
        "unit": env.get("unit"),
        "measure_basis": env.get("measure_basis"),
        "vintage": env.get("vintage", []),
        "provenance": env.get("provenance", {}),
        "interpretation": env.get("interpretation"),
        "prohibited_interpretations": env.get("prohibited_interpretations", []),
        "limitations": envelope._limitations(env),
        "allowed_label": env["allowed_label"],
        "is_measured_shortage": env["is_measured_shortage"],
        "forecast_available": env["forecast_available"],
        "contract_version": env["contract_version"],
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "column_notes": COLUMN_NOTES.get(output_id, {}),
    }


def _resolve(output_id: str) -> str:
    if output_id not in EXPORTABLE:
        exp = envelope.experimental_output_ids()
        if output_id in exp:
            raise HTTPException(
                403,
                f"{output_id} is EXPERIMENTAL_ONLY and may not appear in a production "
                f"export",
            )
        raise HTTPException(404, f"{output_id!r} is not an exportable production output")
    return EXPORTABLE[output_id]


@router.get("/outputs", summary="What may be exported")
def exportable():
    return envelope.meta_only(
        sorted(EXPORTABLE),
        note=(
            "Production outputs only. Experimental outputs and unavailable "
            "capabilities are not exportable."
        ),
    )


@router.get("/{output_id}.json", summary="JSON export with its mandatory metadata")
def export_json(output_id: str):
    rows = warehouse.query(_resolve(output_id))
    return JSONResponse({"meta": _export_meta(output_id), "data": rows})


@router.get("/{output_id}.csv", summary="CSV export with its mandatory metadata header")
def export_csv(output_id: str, include_meta: bool = Query(True)):
    rows = warehouse.query(_resolve(output_id))
    meta = _export_meta(output_id)
    buf = io.StringIO()
    if include_meta:
        buf.write(f"# LMIS export - {meta['allowed_label']}\n")
        for key in ("output_id", "publication_status", "tier", "evidence_status",
                    "confidence", "unit", "measure_basis", "vintage",
                    "interpretation", "is_measured_shortage", "forecast_available",
                    "contract_version", "exported_at"):
            buf.write(f"# {key}: {json.dumps(meta[key], default=str)}\n")
        for k, v in meta["coverage"].items():
            buf.write(f"# coverage.{k}: {v['value']} ({v['label']})\n")
        for col, note in meta["column_notes"].items():
            buf.write(f"# column.{col}: {note}\n")
        for lim in meta["limitations"]:
            buf.write(f"# limitation: {lim}\n")
        for p in meta["prohibited_interpretations"]:
            buf.write(f"# prohibited_interpretation: {p}\n")
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return PlainTextResponse(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{output_id}.csv"'},
    )
