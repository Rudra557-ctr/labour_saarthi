"""R1-R3: contract, sources, methodology."""
from __future__ import annotations

from fastapi import APIRouter, Query

from api import envelope, warehouse

router = APIRouter(prefix="/api/meta", tags=["metadata"])


@router.get("/contract", summary="The publication contract and its modes")
def get_contract():
    c = warehouse.contract()
    return envelope.meta_only(
        {
            "contract_version": c.contract_version,
            "mode": c.mode,
            "publication_tiers": c.publication_tiers,
            "vintage_policy": c.vintage_policy,
            "derivation_inputs": c.derivation_inputs,
            "barred_fields": c.barred_fields,
            "terminology": c.terminology,
            "outputs": [
                {
                    "output_id": e["output_id"],
                    "publication_status": e["publication_status"],
                    "tier": e["tier"],
                    "allowed_label": e["allowed_label"],
                    "evidence_status": e.get("evidence_status"),
                    "confidence": e.get("confidence"),
                    "implemented": e.get("implemented", True),
                    "prohibited_interpretations": e.get("prohibited_interpretations", []),
                }
                for e in warehouse.envelopes()
            ],
        }
    )


@router.get("/sources", summary="Source registry and snapshot provenance")
def get_sources(source_id: str | None = Query(None)):
    sql = (
        "SELECT source_id, source_name, publisher_org, landing_url, role, "
        "access_method, licence, licence_verified, geo_level_available, "
        "occ_coding_scheme, period_grain, update_cadence, is_authoritative, "
        "verification_status FROM source_master"
    )
    params: list = []
    if source_id:
        sql += " WHERE source_id = ?"
        params.append(source_id)
    rows = warehouse.query(sql + " ORDER BY source_id", params)
    snaps = warehouse.query(
        "SELECT source_id, retrieved_at, retrieved_date, file_name, file_url, "
        "sha256, size_bytes, http_status, publication_vintage "
        "FROM source_snapshot ORDER BY source_id, file_name"
    )
    by_src: dict[str, list] = {}
    for s in snaps:
        by_src.setdefault(s["source_id"], []).append(s)
    for r in rows:
        r["snapshots"] = by_src.get(r["source_id"], [])
    return envelope.meta_only(rows, note="Registry state; not a statement of availability.")


@router.get("/methodology", summary="Stored methodology strings and derivation chains")
def get_methodology(output_id: str | None = Query(None)):
    """Methodology text as STORED on each output - not re-derived here."""
    stored = {
        "demand_national_occupation_composition": "methodology",
        "demand_district_relative_signal": "methodology",
        "demand_district_occupation_signal": "methodology",
    }
    out = []
    for e in warehouse.envelopes():
        oid = e["output_id"]
        if output_id and oid != output_id:
            continue
        item = {
            "output_id": oid,
            "tier": e["tier"],
            "publication_status": e["publication_status"],
            "allowed_label": e["allowed_label"],
            "evidence_status": e.get("evidence_status"),
            "confidence": e.get("confidence"),
            "unit": e.get("unit"),
            "measure_basis": e.get("measure_basis"),
            "vintage": e.get("vintage", []),
            "provenance": e.get("provenance", {}),
            "interpretation": e.get("interpretation"),
            "prohibited_interpretations": e.get("prohibited_interpretations", []),
            "limitations": envelope._limitations(e),
            "derivation_inputs": e.get("derivation_inputs", []),
        }
        if oid in stored and e.get("implemented", True):
            rows = warehouse.query(f"SELECT DISTINCT {stored[oid]} AS m FROM {oid}")
            item["methodology"] = [r["m"] for r in rows]
        out.append(item)
    c = warehouse.contract()
    return envelope.meta_only(
        out,
        note=(
            "Evidence status is read from each output's own column; the contract "
            "declares only which column to read."
        ),
        derivation_rule=(
            "Derivation inputs are FACTORS in their outputs and may be shown only "
            "under 'How this signal is derived' - never as independent corroboration."
        ),
        gap_not_identifiable=c.mode["NUMERIC_GAP"],
        forecasting=c.mode["FORECASTING"],
    )


@router.get("/filters", summary="Valid filter domains, read from the data")
def get_filters():
    """Every selectable value comes from the warehouse, so the UI cannot offer a
    filter the data does not support - and cannot miss one it does."""
    states = warehouse.query(
        "SELECT DISTINCT state_lgd_code, state_name_lgd FROM "
        "demand_district_relative_signal ORDER BY state_name_lgd"
    )
    occ_states = warehouse.query(
        "SELECT DISTINCT state_lgd_code, state_name_lgd FROM "
        "demand_district_occupation_signal WHERE occupation_prior_status = 'AVAILABLE' "
        "ORDER BY state_name_lgd"
    )
    divisions = warehouse.query(
        "SELECT DISTINCT nco_2015_division, nco_name FROM "
        "demand_district_occupation_signal WHERE nco_name IS NOT NULL "
        "ORDER BY nco_2015_division"
    )
    sectors = warehouse.query(
        "SELECT DISTINCT ncs_sector_name, nic_section_code FROM "
        "analytical_demand_by_industry ORDER BY ncs_sector_name"
    )
    return envelope.meta_only(
        {
            "states": states,
            "states_with_occupation_detail": occ_states,
            "nco_2015_divisions": divisions,
            "ncs_sectors": sectors,
            "evidence_status": ["OBSERVED", "ESTIMATED", "SUPPORTING", "UNAVAILABLE"],
            "confidence": ["MEDIUM", "LOW"],
            "occupation_prior_status": [
                "AVAILABLE", "CENSUS_NOT_ACQUIRED", "NO_CENSUS_2011_CODE"
            ],
            "schemes": [
                r["scheme"] for r in warehouse.query(
                    "SELECT DISTINCT scheme FROM fact_training_outcome ORDER BY scheme"
                )
            ],
            "measures": ["ENROLLED", "TRAINED", "ASSESSED", "CERTIFIED", "PLACED"],
        },
        industry_filter_key="ncs_sector_name",
        industry_filter_note=(
            "The industry filter keys on ncs_sector_name. Two NCS sectors have a NULL "
            "nic_section_code, so a NIC-keyed filter would silently drop them."
        ),
        unsupported_filters=[
            "trade", "qualification", "nsqf_level", "district_plfs",
            "training_supply", "period_range", "sub_district",
        ],
        unsupported_filters_note=(
            "No column supports these, so they are not offered rather than "
            "returning empty results."
        ),
    )
