"""The publication contract: what may be published, and with what metadata.

Implements the APPROVED Step 7.1 decision
(`docs/step7.1_indicator_publication_decision.md`, ADR-0011).

Two rules shape the whole module:

1. **The data decides the evidence status, not the contract.** Every envelope reads
   `observation_status` / `observed_or_estimated` out of the table itself. The
   contract declares which column to read, never what the answer is - so a derived
   output cannot be labelled OBSERVED by editing a config file, which is precisely
   the Step 7.1 discrepancy that made this layer necessary.

2. **Coverage numbers are derived, never written here.** The PAN-India residual share,
   the state-attributable share and the district counts are all resolved from
   `demand_coverage_summary` at build time. They appear in exactly one place in the
   repository - the warehouse - and nowhere in code or config, which
   `test_coverage_numbers_are_not_hard_coded_in_code_or_config` enforces.

No table is created, no migration is added, and no analytical value is read back
out in modified form.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import duckdb
import yaml

from lmis.common.paths import PUBLICATION_CONTRACT_YAML

# Enforced invariant of the whole system: no output anywhere is a measured shortage.
IS_MEASURED_SHORTAGE = False

PRODUCTION = "PRODUCTION"
EXPERIMENTAL = "EXPERIMENTAL_ONLY"
UNAVAILABLE = "UNAVAILABLE"

OBSERVED = "OBSERVED"
ESTIMATED = "ESTIMATED"
SUPPORTING = "SUPPORTING"

# Tiers are ROLES. Evidence status stays read from the data (see module docstring).
VALID_TIERS = (OBSERVED, ESTIMATED, SUPPORTING)

_STATUS_COLUMN_CANDIDATES = ("observation_status", "observed_or_estimated")
_PROVENANCE_COLUMNS = ("source_ids", "source_id", "source_documents", "snapshot_file")


class ContractError(RuntimeError):
    """Raised when an output would be published outside the approved contract."""


@dataclass(frozen=True)
class PublicationContract:
    contract_version: str
    mode: dict[str, Any]
    coverage_sources: dict[str, dict[str, Any]]
    outputs: list[dict[str, Any]]
    unavailable_capabilities: list[dict[str, Any]]
    barred_fields: list[dict[str, Any]]
    terminology: dict[str, Any]
    publication_tiers: dict[str, Any] = field(default_factory=dict)
    derivation_inputs: list[dict[str, Any]] = field(default_factory=list)
    vintage_policy: dict[str, Any] = field(default_factory=dict)

    def output(self, output_id: str) -> dict[str, Any]:
        for o in self.outputs:
            if o["output_id"] == output_id:
                return o
        raise ContractError(
            f"{output_id!r} is not in the publication contract. An output absent "
            f"from the contract may not be published."
        )

    @property
    def production_outputs(self) -> list[dict[str, Any]]:
        return [o for o in self.outputs if o["status"] == PRODUCTION]

    @property
    def experimental_outputs(self) -> list[dict[str, Any]]:
        return [o for o in self.outputs if o["status"] == EXPERIMENTAL]

    @property
    def supporting_outputs(self) -> list[dict[str, Any]]:
        return [o for o in self.outputs if o.get("tier") == SUPPORTING]

    @property
    def barred_field_names(self) -> set[str]:
        return {b["field"] for b in self.barred_fields}

    def derivation_rule(self, input_table: str) -> dict[str, Any]:
        for d in self.derivation_inputs:
            if d["input"] == input_table:
                return d
        raise ContractError(f"{input_table!r} is not a declared derivation input")

    def inputs_of(self, output_id: str) -> list[str]:
        """Tables that are FACTORS in this output - never its corroboration."""
        return [d["input"] for d in self.derivation_inputs
                if output_id in d["is_input_to"]]


def load_contract(path=None) -> PublicationContract:
    raw = yaml.safe_load((path or PUBLICATION_CONTRACT_YAML).read_text())
    contract = PublicationContract(
        contract_version=raw["contract_version"],
        mode=raw["mode"],
        coverage_sources=raw["coverage_sources"],
        outputs=raw["outputs"],
        unavailable_capabilities=raw["unavailable_capabilities"],
        barred_fields=raw.get("barred_fields", []),
        terminology=raw["terminology"],
        publication_tiers=raw.get("publication_tiers", {}),
        derivation_inputs=raw.get("derivation_inputs", []),
        vintage_policy=raw.get("vintage_policy", {}),
    )
    _validate_contract(contract)
    return contract


def _validate_contract(c: PublicationContract) -> None:
    if c.mode["MEASURED_SHORTAGE"] is not False:
        raise ContractError("MEASURED_SHORTAGE must be false.")
    if c.mode["NUMERIC_GAP"] != "NOT_IDENTIFIABLE":
        raise ContractError("NUMERIC_GAP must remain NOT_IDENTIFIABLE.")
    if c.mode["FORECASTING"] != "NOT_SUPPORTED_YET":
        raise ContractError("FORECASTING must remain NOT_SUPPORTED_YET.")
    if c.mode["HYBRID_PRESSURE_INDICATOR"] != EXPERIMENTAL:
        raise ContractError("HYBRID_PRESSURE_INDICATOR must remain EXPERIMENTAL_ONLY.")
    if c.mode["DEFAULT_DISTRICT_RANKING"] != "WITHIN_STATE":
        raise ContractError("Default district ranking must be WITHIN_STATE.")
    ids = [o["output_id"] for o in c.outputs]
    if len(ids) != len(set(ids)):
        raise ContractError("Duplicate output_id in the contract.")
    # Step 7.3.1: tiers are a closed set, and SUPPORTING may not be a primary measure.
    for name, spec in c.publication_tiers.items():
        if name not in (*VALID_TIERS, UNAVAILABLE):
            raise ContractError(f"unknown publication tier {name!r}")
    if c.publication_tiers:
        if c.publication_tiers[SUPPORTING]["may_be_primary_measure"] is not False:
            raise ContractError("SUPPORTING may never be a primary measure")
        if c.publication_tiers[UNAVAILABLE]["may_be_primary_measure"] is not False:
            raise ContractError("UNAVAILABLE may never be a primary measure")
    if c.vintage_policy:
        if c.vintage_policy.get("global_as_of_date") != "PROHIBITED":
            raise ContractError("a single global as-of date is prohibited")
        if c.vintage_policy.get("time_series_across_vintages") != "PROHIBITED":
            raise ContractError("a time series across heterogeneous vintages is prohibited")
    for d in c.derivation_inputs:
        if d.get("display_role") != "DERIVATION_DISCLOSURE_ONLY":
            raise ContractError(
                f"{d['input']}: a derivation input may only be displayed as "
                f"derivation disclosure"
            )
        if not d.get("prohibited_labels"):
            raise ContractError(f"{d['input']}: prohibited_labels must be declared")
    for o in c.outputs:
        if o["status"] not in (PRODUCTION, EXPERIMENTAL):
            raise ContractError(f"{o['output_id']}: bad status {o['status']!r}")
        if o.get("tier") not in VALID_TIERS:
            raise ContractError(f"{o['output_id']}: bad tier {o.get('tier')!r}")
        if o.get("tier") == SUPPORTING and o.get("requires_data_flag") != "not_a_demand_measure":
            raise ContractError(
                f"{o['output_id']}: a SUPPORTING output must declare "
                f"requires_data_flag: not_a_demand_measure"
            )
        if o.get("is_observed_vacancy_ranking") is True:
            raise ContractError(
                f"{o['output_id']}: no output may be declared an observed vacancy ranking"
            )
        if o["status"] == EXPERIMENTAL:
            for flag in ("excluded_from_production_responses",
                         "excluded_from_production_exports"):
                if o.get(flag) is not True:
                    raise ContractError(f"{o['output_id']}: {flag} must be true")
            if o.get("required_display_guard") != "NOT_MEASURED_SHORTAGE":
                raise ContractError(
                    f"{o['output_id']}: experimental output needs the "
                    f"NOT_MEASURED_SHORTAGE display guard"
                )


# --------------------------------------------------------------------------
# Coverage: resolved from the warehouse, never hard-coded.
# --------------------------------------------------------------------------
def resolve_coverage(
    con: duckdb.DuckDBPyConnection, contract: PublicationContract
) -> dict[str, dict[str, Any]]:
    """Resolve every declared coverage fact from the warehouse."""
    out: dict[str, dict[str, Any]] = {}
    for key, spec in contract.coverage_sources.items():
        row = con.execute(
            f"SELECT value, unit FROM {spec['table']} WHERE metric = ?",  # noqa: S608
            [spec["metric"]],
        ).fetchone()
        if row is None:
            raise ContractError(
                f"coverage fact {key!r} not resolvable: "
                f"{spec['table']}.{spec['metric']} is absent from the warehouse"
            )
        value, unit = float(row[0]), row[1]
        if spec["derive"] == "complement":
            value = 1.0 - value
        elif spec["derive"] != "value":
            raise ContractError(f"{key}: unknown derive {spec['derive']!r}")
        out[key] = {
            "value": value,
            "unit": unit,
            "label": spec["label"],
            "derived_from": f"{spec['table']}.{spec['metric']}",
            "derivation": spec["derive"],
        }
    return out


# --------------------------------------------------------------------------
# Envelopes
# --------------------------------------------------------------------------
def _columns(con: duckdb.DuckDBPyConnection, table: str) -> list[str]:
    return [r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()]


def _distinct(con: duckdb.DuckDBPyConnection, table: str, col: str) -> list[str]:
    rows = con.execute(
        f'SELECT DISTINCT "{col}" FROM {table} WHERE "{col}" IS NOT NULL ORDER BY 1'  # noqa: S608
    ).fetchall()
    return [r[0] for r in rows]


def _evidence_status(
    con: duckdb.DuckDBPyConnection, table: str, spec: dict[str, Any], cols: list[str]
) -> list[str]:
    """Read the evidence status OUT OF THE TABLE. The contract may not assert it."""
    declared = spec.get("evidence_status_column")
    col = declared if declared in cols else next(
        (c for c in _STATUS_COLUMN_CANDIDATES if c in cols), None
    )
    if col is None:
        # A pure metadata table (coverage, data quality) carries no status column.
        return [OBSERVED]
    return _distinct(con, table, col)


def build_envelopes(
    con: duckdb.DuckDBPyConnection, contract: PublicationContract
) -> list[dict[str, Any]]:
    """Build the mandatory metadata envelope for every contracted output."""
    coverage = resolve_coverage(con, contract)
    envelopes: list[dict[str, Any]] = []

    for spec in contract.outputs:
        oid = spec["output_id"]
        implemented = spec.get("implemented", True)
        env: dict[str, Any] = {
            "output_id": oid,
            "publication_status": spec["status"],
            "contract_version": contract.contract_version,
            "implemented": implemented,
            "tier": spec.get("tier"),
            "allowed_label": spec["allowed_label"],
            "grain": {
                "geo_level": spec.get("geo_level"),
                "occupation_level": spec.get("occupation_level"),
            },
            "unit": spec.get("unit"),
            "measure_basis": spec.get("measure_basis"),
            "interpretation": spec.get("interpretation"),
            "prohibited_interpretations": spec.get("prohibited_interpretations", []),
            # Invariant, every output, every response.
            "is_measured_shortage": IS_MEASURED_SHORTAGE,
            "forecast_available": False,
            "forecast_unavailable_reason":
                "NOT_SUPPORTED_YET: one dated demand observation; see gate G-4",
        }

        if not implemented:
            # Declared so the boundary exists before anything can cross it.
            env["evidence_status"] = [spec["tier"]]
            # always a list - a bare string would be iterated character by character
            declared = spec.get("confidence")
            env["confidence"] = [declared] if isinstance(declared, str) else (declared or [])
            env["coverage"] = {}
            env["provenance"] = {}
            env["row_count"] = 0
            env["excluded_from_production_responses"] = spec.get(
                "excluded_from_production_responses", False
            )
            env["excluded_from_production_exports"] = spec.get(
                "excluded_from_production_exports", False
            )
            env["required_display_guard"] = spec.get("required_display_guard")
            env["allowed_status_values"] = spec.get("allowed_status_values", [])
            env["promotion_gates"] = spec.get("promotion_gates", [])
            envelopes.append(env)
            continue

        cols = _columns(con, oid)
        env["row_count"] = con.execute(f"SELECT count(*) FROM {oid}").fetchone()[0]  # noqa: S608
        env["evidence_status"] = _evidence_status(con, oid, spec, cols)

        # --- Step 7.3.1: a SUPPORTING declaration must be backed by the data ---
        flag = spec.get("requires_data_flag")
        if flag:
            if flag not in cols:
                raise ContractError(
                    f"{oid}: declared tier {spec.get('tier')} requires column "
                    f"{flag!r}, which the table does not have"
                )
            bad = con.execute(
                f'SELECT count(*) FROM {oid} WHERE "{flag}" IS NOT TRUE'  # noqa: S608
            ).fetchone()[0]
            if bad:
                raise ContractError(
                    f"{oid}: {bad} row(s) do not carry {flag} = TRUE, so it may not "
                    f"be published as {spec.get('tier')}"
                )
            env["is_demand_measure"] = False
            env["data_flag"] = {flag: True}
        else:
            env["is_demand_measure"] = spec.get("tier") in (OBSERVED, ESTIMATED)

        # SUPPORTING context may not be served at a grain its own data invalidates.
        dv = spec.get("district_estimates_valid_column")
        if dv and dv in cols:
            ok = con.execute(
                f'SELECT count(*) FROM {oid} WHERE "{dv}" IS TRUE'  # noqa: S608
            ).fetchone()[0]
            env["district_estimates_valid"] = bool(ok)
            env["valid_geo_levels"] = _distinct(con, oid, spec["valid_geo_level_column"]) \
                if spec.get("valid_geo_level_column") in cols else []

        # --- Step 7.3.1: the locked allocation-signal terminology needs its caveat -
        cav = spec.get("required_caveat_column")
        if cav:
            if cav not in cols:
                raise ContractError(
                    f"{oid}: the approved label requires caveat column {cav!r}, "
                    f"which the table does not have"
                )
            missing = con.execute(
                f'SELECT count(*) FROM {oid} WHERE "{cav}" IS NULL'  # noqa: S608
            ).fetchone()[0]
            if missing:
                raise ContractError(
                    f"{oid}: {missing} row(s) have no {cav}; the allocation-signal "
                    f"label may not be used without its caveat"
                )
            env["required_caveat"] = {
                "column": cav,
                "text": _distinct(con, oid, cav),
            }
        env["is_observed_vacancy_ranking"] = False
        if spec.get("derivation_inputs"):
            env["derivation_inputs"] = spec["derivation_inputs"]
            env["derivation_display_role"] = "DERIVATION_DISCLOSURE_ONLY"

        # --- Step 7.3.1: residual excluded from the default comparison ---------
        rh = spec.get("residual_handling")
        if rh:
            if rh["flag_column"] not in cols:
                raise ContractError(f"{oid}: missing {rh['flag_column']!r}")
            n_res = con.execute(
                f'SELECT count(*) FROM {oid} WHERE "{rh["flag_column"]}" IS TRUE'  # noqa: S608
            ).fetchone()[0]
            env["residual_handling"] = {
                **rh,
                "residual_rows": n_res,
                "default_comparison_rows": env["row_count"] - n_res,
            }

        conf_col = spec.get("confidence_column")
        if conf_col and conf_col in cols:
            env["confidence"] = _distinct(con, oid, conf_col)
            env["confidence_source"] = f"{oid}.{conf_col}"
        else:
            env["confidence"] = env["evidence_status"]
            env["confidence_source"] = "evidence_status"

        vcol = spec.get("vintage_column")
        if vcol and vcol in cols:
            env["vintage"] = _distinct(con, oid, vcol)
            env["vintage_source"] = f"{oid}.{vcol}"
        else:
            env["vintage"] = []
            env["vintage_source"] = None

        prov_cols = [c for c in _PROVENANCE_COLUMNS if c in cols]
        prov: dict[str, Any] = {"columns": prov_cols}
        ids: set[str] = set()
        for c in prov_cols:
            for v in _distinct(con, oid, c):
                ids.update(p.strip() for p in str(v).split(";") if p.strip())
        prov["source_ids"] = sorted(ids)
        if "transformation_depth" in cols:
            prov["transformation_depth"] = _distinct(con, oid, "transformation_depth")
        mcol = spec.get("mapping_authority_column")
        if mcol and mcol in cols:
            prov["mapping_authority"] = _distinct(con, oid, mcol)
        env["provenance"] = prov

        env["coverage"] = {
            k: coverage[k] for k in spec.get("coverage_disclosures", [])
        }
        if spec.get("default_ranking_column"):
            env["default_ranking"] = {
                "mode": "WITHIN_STATE",
                "column": spec["default_ranking_column"],
                "cross_state_column": spec.get("cross_state_ranking_column"),
                "cross_state_caveat":
                    "Cross-state comparison reflects NCS source/registration coverage "
                    "as well as labour demand and is not directly comparable absolute "
                    "labour demand. Within-state ranking is the default.",
            }
        if "flow_available" in cols:
            flows = _distinct(con, oid, "flow_available")
            env["flow_available"] = bool(flows and all(bool(f) for f in flows))
            if "flow_unavailable_reason" in cols:
                reasons = _distinct(con, oid, "flow_unavailable_reason")
                env["flow_unavailable_reason"] = reasons[0] if reasons else None
        if spec.get("notes"):
            env["notes"] = spec["notes"]
        if spec.get("mandatory"):
            env["publication_mandatory"] = True

        envelopes.append(env)

    _validate_envelopes(envelopes)
    return envelopes


def _validate_envelopes(envelopes: list[dict[str, Any]]) -> None:
    for e in envelopes:
        if e["is_measured_shortage"] is not False:
            raise ContractError(f"{e['output_id']}: is_measured_shortage must be False")
        if e["forecast_available"] is not False:
            raise ContractError(f"{e['output_id']}: forecast_available must be False")
        # The discrepancy this layer exists to prevent: a derived output published
        # as OBSERVED. The tier is declared; the status is read from the data.
        if e["publication_status"] == PRODUCTION and e["implemented"]:
            if OBSERVED in e["evidence_status"] and ESTIMATED in e["evidence_status"]:
                raise ContractError(
                    f"{e['output_id']}: mixes OBSERVED and ESTIMATED in one envelope"
                )
        if e["publication_status"] == EXPERIMENTAL:
            if not e.get("excluded_from_production_responses"):
                raise ContractError(f"{e['output_id']}: must be excluded from production")


def production_envelopes(envelopes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The only envelopes a production response or export may contain."""
    return [e for e in envelopes if e["publication_status"] == PRODUCTION]


def assert_no_experimental_leak(payload: list[dict[str, Any]]) -> None:
    """Guard a production response/export against an experimental output."""
    leaked = [
        e["output_id"] for e in payload if e.get("publication_status") == EXPERIMENTAL
    ]
    if leaked:
        raise ContractError(
            f"experimental output(s) {leaked} may not appear in a production "
            f"response or export"
        )


# --------------------------------------------------------------------------
# Unavailability register
# --------------------------------------------------------------------------
def build_unavailability_register(
    contract: PublicationContract,
) -> list[dict[str, Any]]:
    """Blocked capabilities, as explicit unavailability - never empty data.

    Returned with `data: None` so a consumer cannot read a blocked capability as
    "none found". Reasons and gates only; no values.
    """
    register = []
    for cap in contract.unavailable_capabilities:
        register.append(
            {
                "capability_id": cap["capability_id"],
                "data": None,
                "publication_status": UNAVAILABLE,
                "evidence_status": "UNAVAILABLE",
                "reason_code": cap["reason_code"],
                "reason": cap["reason"],
                "blocking_gate": cap["blocking_gate"],
                "unblocking_conditions_url":
                    f"/docs/step7.1#{str(cap['blocking_gate']).lower()}",
                "is_measured_shortage": IS_MEASURED_SHORTAGE,
                "forecast_available": False,
            }
        )
    return register
