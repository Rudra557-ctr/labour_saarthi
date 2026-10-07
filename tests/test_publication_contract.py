"""Step 7.2 — tests for the APPROVED Step 7.1 publication contract.

Every rule the contract asserts is pinned here, so a later refactor cannot quietly
relax it. The numbered tests map one-to-one onto the twelve rules required by the
Step 7.2 brief.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd
import pytest
import yaml

from lmis.common import paths
from lmis.publish import (
    build_envelopes,
    build_unavailability_register,
    lint_contract,
    lint_envelopes,
    load_contract,
    resolve_coverage,
)
from lmis.publish.contract import (
    ContractError,
    EXPERIMENTAL,
    OBSERVED,
    PRODUCTION,
    assert_no_experimental_leak,
    production_envelopes,
)
from lmis.warehouse.load import DB_PATH, TABLES

pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(), reason="warehouse not built"
)


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect(str(DB_PATH), read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def contract():
    return load_contract()


@pytest.fixture(scope="module")
def envelopes(con, contract):
    return build_envelopes(con, contract)


def _env(envelopes, oid):
    return next(e for e in envelopes if e["output_id"] == oid)


# --- 1. OBSERVED outputs retain OBSERVED status -----------------------------
def test_observed_outputs_retain_observed_status(envelopes):
    for oid in (
        "analytical_state_demand",
        "analytical_demand_by_industry",
        "fact_training_outcome",
        "fact_training_infrastructure",
        "fact_training_trade_outcome",
    ):
        e = _env(envelopes, oid)
        assert e["evidence_status"] == [OBSERVED], (oid, e["evidence_status"])


# --- 2. Derived signals are NOT published as OBSERVED ----------------------
def test_derived_outputs_are_never_observed(envelopes):
    """The Step 7.1 discrepancy: output A is ESTIMATED, not OBSERVED."""
    for oid in (
        "demand_national_occupation_composition",
        "demand_district_relative_signal",
        "demand_district_occupation_signal",
    ):
        e = _env(envelopes, oid)
        assert OBSERVED not in e["evidence_status"], (oid, e["evidence_status"])
        assert "ESTIMATED" in e["evidence_status"], (oid, e["evidence_status"])


def test_evidence_status_is_read_from_the_data_not_the_contract(con, contract):
    """Flipping the contract cannot make a derived output OBSERVED."""
    tampered = [dict(o) for o in contract.outputs]
    for o in tampered:
        if o["output_id"] == "demand_district_relative_signal":
            o["tier"] = OBSERVED  # a lie in the config
    forged = type(contract)(
        contract_version=contract.contract_version,
        mode=contract.mode,
        coverage_sources=contract.coverage_sources,
        outputs=tampered,
        unavailable_capabilities=contract.unavailable_capabilities,
        barred_fields=contract.barred_fields,
        terminology=contract.terminology,
    )
    e = _env(build_envelopes(con, forged), "demand_district_relative_signal")
    assert e["evidence_status"] == ["ESTIMATED"]


# --- 3. is_measured_shortage is False everywhere ---------------------------
def test_is_measured_shortage_false_on_every_envelope(envelopes):
    assert envelopes
    for e in envelopes:
        assert e["is_measured_shortage"] is False, e["output_id"]


def test_is_measured_shortage_false_on_unavailability_register(contract):
    reg = build_unavailability_register(contract)
    assert reg
    for r in reg:
        assert r["is_measured_shortage"] is False


def test_contract_rejects_measured_shortage_true(tmp_path, contract):
    raw = yaml.safe_load(paths.PUBLICATION_CONTRACT_YAML.read_text())
    raw["mode"]["MEASURED_SHORTAGE"] = True
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(raw))
    with pytest.raises(ContractError, match="MEASURED_SHORTAGE"):
        load_contract(bad)


def test_contract_rejects_identifiable_gap_or_forecast(tmp_path):
    for key, value, msg in (
        ("NUMERIC_GAP", "IDENTIFIABLE", "NUMERIC_GAP"),
        ("FORECASTING", "SUPPORTED", "FORECASTING"),
        ("HYBRID_PRESSURE_INDICATOR", "PRODUCTION", "HYBRID"),
        ("DEFAULT_DISTRICT_RANKING", "NATIONAL", "WITHIN_STATE"),
    ):
        raw = yaml.safe_load(paths.PUBLICATION_CONTRACT_YAML.read_text())
        raw["mode"][key] = value
        bad = tmp_path / f"bad_{key}.yaml"
        bad.write_text(yaml.safe_dump(raw))
        with pytest.raises(ContractError, match=msg):
            load_contract(bad)


# --- 4. A relative signal cannot be published as a vacancy count ----------
def test_relative_signals_keep_a_unitless_unit(envelopes):
    for oid in ("demand_district_relative_signal", "demand_district_occupation_signal"):
        assert _env(envelopes, oid)["unit"] == "relative_signal_unitless"


def test_relative_signal_prohibits_vacancy_count_interpretation(envelopes):
    for oid in ("demand_district_relative_signal", "demand_district_occupation_signal"):
        assert "VACANCY_COUNT" in _env(envelopes, oid)["prohibited_interpretations"]


def test_terminology_lint_passes_on_the_live_contract(contract, envelopes):
    violations = lint_contract(contract) + lint_envelopes(envelopes, contract)
    assert violations == [], [str(v) for v in violations]


def test_terminology_lint_catches_a_count_label_on_a_relative_signal(contract, envelopes):
    tampered = [dict(e) for e in envelopes]
    for e in tampered:
        if e["output_id"] == "demand_district_relative_signal":
            e["allowed_label"] = "Number of vacancies by district"
    v = lint_envelopes(tampered, contract)
    assert any(x.rule == "relative_signal_not_a_count" for x in v), [str(x) for x in v]


def test_terminology_lint_catches_shortage_and_supply_words(contract, envelopes):
    for bad_label, rule in (
        ("District shortage ranking", "reserved_everywhere"),
        ("Occupation supply by district", "reserved_for_quantities"),
        ("Skill gap index", "reserved_everywhere"),
    ):
        tampered = [dict(e) for e in envelopes]
        for e in tampered:
            if e["output_id"] == "demand_district_occupation_signal":
                e["allowed_label"] = bad_label
        v = lint_envelopes(tampered, contract)
        assert any(x.rule == rule for x in v), (bad_label, [str(x) for x in v])


def test_terminology_lint_permits_a_negated_term(contract, envelopes):
    """"NOT a vacancy count" is the guardrail, not a breach of it."""
    e = _env(envelopes, "demand_district_relative_signal")
    assert "VACANCY" in e["interpretation"]
    assert lint_envelopes([e], contract) == []


def test_confidence_stays_categorical(contract, envelopes):
    allowed = set(contract.terminology["allowed_confidence_values"])
    for e in envelopes:
        for c in e["confidence"]:
            assert c in allowed, (e["output_id"], c)
            assert not any(ch.isdigit() for ch in str(c))


def test_numeric_confidence_is_rejected(contract, envelopes):
    tampered = [dict(e) for e in envelopes]
    tampered[0]["confidence"] = ["0.83"]
    v = lint_envelopes(tampered, contract)
    assert any(x.rule == "confidence_must_be_categorical" for x in v)


# --- 5. Required coverage metadata is present and DERIVED -----------------
def test_coverage_is_derived_from_the_warehouse(con, contract):
    cov = resolve_coverage(con, contract)
    for key in (
        "state_attributable_share",
        "pan_india_residual_share",
        "districts_with_relative_signal",
        "districts_with_occupation_signal",
    ):
        assert key in cov
        assert cov[key]["derived_from"].startswith("demand_coverage_summary.")


def test_coverage_values_match_the_approved_disclosures(con, contract):
    cov = resolve_coverage(con, contract)
    assert cov["state_attributable_share"]["value"] == pytest.approx(0.4187, abs=5e-4)
    assert cov["pan_india_residual_share"]["value"] == pytest.approx(0.5813, abs=5e-4)
    assert cov["districts_with_relative_signal"]["value"] == 785
    assert cov["districts_with_occupation_signal"]["value"] == 138
    assert cov["districts_census_not_acquired"]["value"] == 522
    assert cov["districts_no_census_2011_code"]["value"] == 125
    # the two shares must complement exactly
    assert cov["state_attributable_share"]["value"] + cov[
        "pan_india_residual_share"
    ]["value"] == pytest.approx(1.0)


def test_coverage_numbers_are_not_hard_coded_in_code_or_config():
    """58.13 / 41.87 / 138 of 785 live in the warehouse, nowhere else."""
    forbidden = ("58.13", "41.87", "0.5813", "0.4187")
    searched = list((paths.ROOT / "src").rglob("*.py")) + [
        paths.PUBLICATION_CONTRACT_YAML
    ]
    offenders = [
        f"{p}:{n}"
        for p in searched
        for n, line in enumerate(p.read_text().splitlines(), 1)
        for term in forbidden
        if term in line
    ]
    assert offenders == [], offenders


def test_demand_outputs_carry_their_mandatory_disclosures(envelopes):
    occ = _env(envelopes, "demand_district_occupation_signal")["coverage"]
    assert "districts_with_occupation_signal" in occ
    assert "pan_india_residual_share" in occ
    dist = _env(envelopes, "demand_district_relative_signal")["coverage"]
    assert "pan_india_residual_share" in dist
    assert "state_attributable_share" in dist


def test_every_envelope_declares_forecast_unavailable(envelopes):
    for e in envelopes:
        assert e["forecast_available"] is False
        assert "G-4" in e["forecast_unavailable_reason"]


def test_envelopes_carry_provenance(envelopes):
    for oid in (
        "demand_district_occupation_signal",
        "analytical_state_demand",
        "fact_training_outcome",
    ):
        assert _env(envelopes, oid)["provenance"]["source_ids"]


# --- 6. Within-state ranking is the default -------------------------------
def test_within_state_ranking_is_the_contract_default(contract):
    assert contract.mode["DEFAULT_DISTRICT_RANKING"] == "WITHIN_STATE"


def test_district_outputs_default_to_within_state_with_a_caveat(envelopes):
    for oid in ("demand_district_relative_signal", "demand_district_occupation_signal"):
        r = _env(envelopes, oid)["default_ranking"]
        assert r["mode"] == "WITHIN_STATE"
        assert r["column"] in ("rank_within_state", "rank_within_district")
        assert r["cross_state_column"]  # retained, not deleted
        assert "not directly comparable" in r["cross_state_caveat"]


# --- 7. The experimental hybrid cannot enter production -------------------
def test_hybrid_is_experimental_only_and_unimplemented(envelopes):
    e = _env(envelopes, "hybrid_potential_pressure")
    assert e["publication_status"] == EXPERIMENTAL
    assert e["implemented"] is False
    assert e["required_display_guard"] == "NOT_MEASURED_SHORTAGE"
    assert e["is_measured_shortage"] is False
    assert e["confidence"] == ["LOW"]
    for term in ("SHORTAGE", "DEFICIT", "SKILL_GAP", "VACANCY_ESTIMATE",
                 "DEMAND_SUPPLY_GAP", "FORECAST"):
        assert term in e["prohibited_interpretations"]


def test_hybrid_absent_from_production_envelopes(envelopes):
    prod = production_envelopes(envelopes)
    assert all(e["output_id"] != "hybrid_potential_pressure" for e in prod)
    assert_no_experimental_leak(prod)  # must not raise


def test_experimental_leak_into_production_raises(envelopes):
    leaky = production_envelopes(envelopes) + [
        _env(envelopes, "hybrid_potential_pressure")
    ]
    with pytest.raises(ContractError, match="experimental"):
        assert_no_experimental_leak(leaky)


def test_contract_rejects_an_unfenced_experimental_output(tmp_path):
    for flag in ("excluded_from_production_responses",
                 "excluded_from_production_exports"):
        raw = yaml.safe_load(paths.PUBLICATION_CONTRACT_YAML.read_text())
        for o in raw["outputs"]:
            if o["output_id"] == "hybrid_potential_pressure":
                o[flag] = False
        bad = tmp_path / f"bad_{flag}.yaml"
        bad.write_text(yaml.safe_dump(raw))
        with pytest.raises(ContractError, match=flag):
            load_contract(bad)


def test_hybrid_is_not_a_warehouse_table(con):
    """Step 7.2 implements the boundary, not the indicator."""
    tables = {r[0] for r in con.execute(
        "select table_name from information_schema.tables where table_schema='main'"
    ).fetchall()}
    for forbidden in ("analytical_potential_pressure", "hybrid_potential_pressure",
                      "fact_gap", "fact_forecast", "fact_alert"):
        assert forbidden not in tables


# --- 8. Unsupported capabilities are explicitly unavailable ---------------
def test_required_capabilities_are_explicitly_unavailable(contract):
    reg = {r["capability_id"]: r for r in build_unavailability_register(contract)}
    for cap in (
        "demand_supply_gap_numeric",
        "forecast",
        "district_occupation_supply",
        "state_occupation_supply",
        "district_trade_supply",
        "state_trade_supply",
    ):
        assert cap in reg, cap
        r = reg[cap]
        assert r["publication_status"] == "UNAVAILABLE"
        assert r["evidence_status"] == "UNAVAILABLE"
        assert r["data"] is None, "must be explicit unavailability, never empty data"
        assert r["reason"]
        assert r["blocking_gate"]


def test_unavailable_reason_codes_stay_distinct(contract):
    reg = {r["capability_id"]: r for r in build_unavailability_register(contract)}
    assert reg["demand_supply_gap_numeric"]["reason_code"] == "NOT_IDENTIFIABLE"
    assert reg["district_trade_supply"]["reason_code"] == "NOT_ACQUIRED"
    assert reg["forecast"]["reason_code"] == "NOT_SUPPORTED_YET"
    assert reg["pan_india_residual_allocation"]["reason_code"] == "PROHIBITED"


def test_an_output_absent_from_the_contract_cannot_be_published(contract):
    with pytest.raises(ContractError, match="not in the publication contract"):
        contract.output("fact_gap")


# --- 9/10. The stale trades_mapped_to_nco zero cannot return --------------
def test_trades_mapped_to_nco_is_no_longer_zero(con):
    v = con.execute(
        "select value from supply_coverage_summary where metric='trades_mapped_to_nco'"
    ).fetchone()[0]
    assert v > 0, "the stale hard-coded 0.0 has returned"


def test_trades_mapped_to_nco_is_derived_from_the_mapping_tables(con):
    published = con.execute(
        "select value, status from supply_coverage_summary "
        "where metric='trades_mapped_to_nco'"
    ).fetchone()
    authoritative = con.execute(
        "select count(distinct trade_id) from map_trade_to_nco"
    ).fetchone()[0]
    assert published[0] == authoritative
    assert published[1] == "PARTIAL_OFFICIAL"


def test_derived_mapping_state_matches_current_evidence(con):
    cov = dict(
        con.execute("select metric, value from supply_coverage_summary").fetchall()
    )
    status = dict(
        con.execute(
            "select mapping_status, count(*) from dim_trade_mapping_status group by 1"
        ).fetchall()
    )
    assert cov["trades_officially_mapped_to_nco"] == status["OFFICIAL_MULTI_NCO"] == 2
    assert cov["trades_mapping_unknown"] == status["MAPPING_UNKNOWN"] == 153
    assert cov["training_trades_catalogued"] == 155
    assert (
        cov["trades_officially_mapped_to_nco"] + cov["trades_mapping_unknown"]
        == cov["training_trades_catalogued"]
    )


def test_no_hard_coded_zero_remains_for_trades_mapped(con):
    src = (paths.ROOT / "src" / "lmis" / "cli.py").read_text()
    assert '("trades_mapped_to_nco", 0.0' not in src


def test_mapping_unknown_is_distinct_from_does_not_exist(con):
    """Step 5.1 constraint preserved: unresolved is not the same as non-existent."""
    note = con.execute(
        "select note from supply_coverage_summary where metric='trades_mapping_unknown'"
    ).fetchone()[0]
    assert "MAPPING_DOES_NOT_EXIST" in note
    statuses = {
        r[0] for r in con.execute(
            "select distinct mapping_status from dim_trade_mapping_status"
        ).fetchall()
    }
    assert "MAPPING_DOES_NOT_EXIST" not in statuses


def test_barred_field_is_registered_not_rewritten(con, contract):
    """dim_training_trade.nco_mapping_status is barred from publication, not edited."""
    assert "dim_training_trade.nco_mapping_status" in contract.barred_field_names
    barred = next(
        b for b in contract.barred_fields
        if b["field"] == "dim_training_trade.nco_mapping_status"
    )
    assert barred["publish_instead"] == "dim_trade_mapping_status.mapping_status"
    # the stored value is untouched - it describes its own source correctly
    vals = {
        r[0] for r in con.execute(
            "select distinct nco_mapping_status from dim_training_trade"
        ).fetchall()
    }
    assert vals == {"UNMAPPED_NO_OFFICIAL_MAPPING"}


# --- 11. No state x trade or district x trade supply was created ----------
def test_no_state_or_district_trade_supply_cells_exist(con):
    """The metadata fix must not have created a supply quantity at any grain."""
    rows = con.execute(
        "select distinct geo_level from fact_training_trade_outcome"
    ).fetchall()
    assert {r[0] for r in rows} == {"NATIONAL"}
    assert con.execute(
        "select count(*) from fact_training_trade_outcome where is_top_n_subset = false"
    ).fetchone()[0] == 0
    # training outcomes stay state x scheme x measure, with no trade/occupation axis
    cols = {r[0] for r in con.execute("DESCRIBE fact_training_outcome").fetchall()}
    for forbidden in ("trade_id", "nco_2015_code", "nco_2015_division", "occupation"):
        assert forbidden not in cols


def test_no_supply_table_gained_an_occupation_or_district_grain(con):
    for t in ("fact_training_outcome", "fact_training_infrastructure"):
        levels = {
            r[0] for r in con.execute(f"select distinct geo_level from {t}").fetchall()
        }
        assert levels == {"STATE"}


def test_no_gap_shortage_or_forecast_column_exists_anywhere(con):
    hits = con.execute(
        """select table_name, column_name from information_schema.columns
           where table_schema='main' and (
             lower(column_name) like '%gap%' or lower(column_name) like '%shortage%'
             or lower(column_name) like '%surplus%' or lower(column_name) like '%deficit%'
             or lower(column_name) like '%forecast%' or lower(column_name) like '%supply_q%')"""
    ).fetchall()
    assert hits == [], hits


# --- 12. No migration was introduced -------------------------------------
def test_no_new_migration_was_added():
    migrations = sorted(p.name for p in (paths.ROOT / "db" / "migrations").glob("*.sql"))
    assert migrations == [
        "001_schema.sql",
        "002_analytical.sql",
        "003_demand.sql",
        "004_supply.sql",
        "005_supply_evidence.sql",
        "006_trade_nco.sql",
        "007_trade_supply.sql",
    ], migrations


def test_table_count_unchanged(con):
    n = con.execute(
        "select count(*) from information_schema.tables where table_schema='main'"
    ).fetchone()[0]
    assert n == 40, n
    assert len(TABLES) == 40


def test_publication_artifacts_are_not_warehouse_tables(con):
    """The contract is emitted as JSON, so no table or migration was needed."""
    tables = {r[0] for r in con.execute(
        "select table_name from information_schema.tables where table_schema='main'"
    ).fetchall()}
    assert "publication_contract" not in tables
    assert "unavailability_register" not in tables


# --- emitted artifact ----------------------------------------------------
@pytest.mark.skipif(
    not paths.publication_path("publication_contract").exists(),
    reason="run `make publish` first",
)
def test_emitted_contract_is_wellformed_and_fenced():
    doc = json.loads(paths.publication_path("publication_contract").read_text())
    assert doc["mode"]["MEASURED_SHORTAGE"] is False
    assert doc["mode"]["NUMERIC_GAP"] == "NOT_IDENTIFIABLE"
    assert doc["mode"]["FORECASTING"] == "NOT_SUPPORTED_YET"
    assert doc["mode"]["HYBRID_PRESSURE_INDICATOR"] == EXPERIMENTAL
    prod = [o for o in doc["outputs"] if o["publication_status"] == PRODUCTION]
    # Step 7.3.1 added analytical_labour_market_context as the SUPPORTING tier's
    # first member, taking production outputs from 11 to 12.
    assert len(prod) == 12
    assert sum(1 for o in prod if o["tier"] == "SUPPORTING") == 1
    assert all(o["is_measured_shortage"] is False for o in doc["outputs"])
    exp = [o for o in doc["outputs"] if o["publication_status"] == EXPERIMENTAL]
    assert len(exp) == 1 and exp[0]["implemented"] is False
    assert len(doc["unavailable_capabilities"]) >= 6
    assert all(c["data"] is None for c in doc["unavailable_capabilities"])


# ===========================================================================
# Step 7.3.1 - SUPPORTING tier and locked allocation-signal terminology
# ===========================================================================

from lmis.publish import lint_derivation_labels  # noqa: E402
from lmis.publish.contract import SUPPORTING, VALID_TIERS  # noqa: E402


# --- 1. SUPPORTING is a valid publication tier ----------------------------
def test_supporting_is_a_recognised_tier(contract):
    assert SUPPORTING in VALID_TIERS
    assert SUPPORTING in contract.publication_tiers
    spec = contract.publication_tiers[SUPPORTING]
    assert spec["may_be_primary_measure"] is False
    assert spec["requires_data_flag"] == "not_a_demand_measure"
    assert spec["definition"]


def test_all_four_tiers_are_defined(contract):
    assert set(contract.publication_tiers) == {
        "OBSERVED", "ESTIMATED", "SUPPORTING", "UNAVAILABLE"
    }


def test_every_output_declares_a_valid_tier(contract, envelopes):
    for o in contract.outputs:
        assert o["tier"] in VALID_TIERS, (o["output_id"], o.get("tier"))
    for e in envelopes:
        assert e["tier"] in VALID_TIERS


def test_unknown_tier_is_rejected(tmp_path):
    raw = yaml.safe_load(paths.PUBLICATION_CONTRACT_YAML.read_text())
    for o in raw["outputs"]:
        if o["output_id"] == "analytical_state_demand":
            o["tier"] = "AUTHORITATIVE"
    bad = tmp_path / "bad_tier.yaml"
    bad.write_text(yaml.safe_dump(raw))
    with pytest.raises(ContractError, match="bad tier"):
        load_contract(bad)


def test_supporting_cannot_be_declared_a_primary_measure(tmp_path):
    raw = yaml.safe_load(paths.PUBLICATION_CONTRACT_YAML.read_text())
    raw["publication_tiers"]["SUPPORTING"]["may_be_primary_measure"] = True
    bad = tmp_path / "bad_primary.yaml"
    bad.write_text(yaml.safe_dump(raw))
    with pytest.raises(ContractError, match="SUPPORTING may never be a primary measure"):
        load_contract(bad)


# --- 2/3. Existing tiers are preserved exactly ----------------------------
def test_existing_observed_outputs_still_observed(envelopes):
    for oid in ("analytical_state_demand", "analytical_demand_by_industry"):
        e = _env(envelopes, oid)
        assert e["tier"] == OBSERVED
        assert e["evidence_status"] == [OBSERVED]


def test_existing_estimated_outputs_still_estimated(envelopes):
    for oid in (
        "demand_national_occupation_composition",
        "demand_district_relative_signal",
        "demand_district_occupation_signal",
    ):
        e = _env(envelopes, oid)
        assert e["tier"] == "ESTIMATED"
        assert "ESTIMATED" in e["evidence_status"]
        assert OBSERVED not in e["evidence_status"]


# --- 4. UNAVAILABLE stays distinct from SUPPORTING ------------------------
def test_unavailable_is_distinct_from_supporting(contract):
    sup = contract.publication_tiers[SUPPORTING]
    una = contract.publication_tiers["UNAVAILABLE"]
    assert sup["definition"] != una["definition"]
    assert "does not exist" in una["definition"]
    # UNAVAILABLE is never a tier on a published output; it is a capability state
    assert all(o["tier"] != "UNAVAILABLE" for o in contract.outputs)
    reg = build_unavailability_register(contract)
    assert all(r["evidence_status"] == "UNAVAILABLE" for r in reg)
    assert all(r["data"] is None for r in reg)


def test_supporting_output_has_data_whereas_unavailable_does_not(envelopes, contract):
    sup = _env(envelopes, "analytical_labour_market_context")
    assert sup["row_count"] > 0
    assert sup["publication_status"] == PRODUCTION
    for r in build_unavailability_register(contract):
        assert r["data"] is None


# --- 5/6/7. PLFS as SUPPORTING, data-backed, and not demand/supply/gap ----
def test_plfs_is_published_as_supporting(envelopes):
    e = _env(envelopes, "analytical_labour_market_context")
    assert e["tier"] == SUPPORTING
    assert e["publication_status"] == PRODUCTION
    assert e["is_demand_measure"] is False
    assert "CONTEXT, NOT A DEMAND MEASURE" in e["allowed_label"]


def test_plfs_evidence_status_still_read_from_data(con, envelopes):
    """Tier is a declared role; evidence status stays the data's own value."""
    e = _env(envelopes, "analytical_labour_market_context")
    in_db = {
        r[0] for r in con.execute(
            "select distinct observation_status from analytical_labour_market_context"
        ).fetchall()
    }
    assert e["evidence_status"] == sorted(in_db) == [OBSERVED]
    assert e["tier"] == SUPPORTING  # role differs from evidence status, by design


def test_plfs_remains_not_a_demand_measure(con, envelopes):
    bad = con.execute(
        "select count(*) from analytical_labour_market_context "
        "where not_a_demand_measure is not true"
    ).fetchone()[0]
    assert bad == 0
    assert _env(envelopes, "analytical_labour_market_context")["data_flag"] == {
        "not_a_demand_measure": True
    }


def test_supporting_declaration_fails_without_the_data_flag(con, contract):
    """A SUPPORTING tier cannot be asserted for a table lacking the flag."""
    tampered = [dict(o) for o in contract.outputs]
    for o in tampered:
        if o["output_id"] == "analytical_state_demand":
            o["tier"] = SUPPORTING
            o["requires_data_flag"] = "not_a_demand_measure"
    forged = type(contract)(
        contract_version=contract.contract_version, mode=contract.mode,
        coverage_sources=contract.coverage_sources, outputs=tampered,
        unavailable_capabilities=contract.unavailable_capabilities,
        barred_fields=contract.barred_fields, terminology=contract.terminology,
        publication_tiers=contract.publication_tiers,
        derivation_inputs=contract.derivation_inputs,
        vintage_policy=contract.vintage_policy,
    )
    with pytest.raises(ContractError, match="which the table does not have"):
        build_envelopes(con, forged)


def test_plfs_cannot_be_represented_as_vacancy_supply_or_gap(envelopes):
    e = _env(envelopes, "analytical_labour_market_context")
    for term in ("DEMAND", "LABOUR_DEMAND", "VACANCY_DATA", "SUPPLY",
                 "OCCUPATION_LEVEL_SUPPLY", "DEMAND_SUPPLY_GAP", "SHORTAGE",
                 "STATE_DEMAND", "DISTRICT_DEMAND"):
        assert term in e["prohibited_interpretations"], term


def test_plfs_stays_national_only(con, envelopes):
    e = _env(envelopes, "analytical_labour_market_context")
    assert e["district_estimates_valid"] is False
    assert e["valid_geo_levels"] == ["NATIONAL"]
    levels = {
        r[0] for r in con.execute(
            "select distinct geo_level from analytical_labour_market_context"
        ).fetchall()
    }
    assert levels == {"NATIONAL"}


def test_supporting_tier_declares_its_prohibited_uses(contract):
    uses = contract.publication_tiers[SUPPORTING]["prohibited_uses"]
    for u in ("MANUFACTURE_STATE_OR_DISTRICT_DEMAND", "CREATE_A_DEMAND_SUPPLY_GAP",
              "SERVE_AS_OCCUPATION_LEVEL_SUPPLY", "REPRESENT_AS_VACANCY_DATA",
              "INDEPENDENT_CORROBORATION_OF_A_DERIVED_OUTPUT"):
        assert u in uses, u


# --- 8/9. Outputs B and C cannot be labelled observed rankings ------------
def test_output_b_uses_the_approved_allocation_label(envelopes):
    e = _env(envelopes, "demand_district_relative_signal")
    assert e["allowed_label"] == "District Relative Demand Allocation Signal"
    assert e["is_observed_vacancy_ranking"] is False


def test_output_c_uses_the_approved_allocation_label(envelopes):
    e = _env(envelopes, "demand_district_occupation_signal")
    assert e["allowed_label"] == "District x Occupation Relative Demand Allocation Signal"
    assert e["is_observed_vacancy_ranking"] is False


def test_allocation_labels_require_their_stored_caveat(envelopes):
    b = _env(envelopes, "demand_district_relative_signal")["required_caveat"]
    assert b["column"] == "within_state_ranking_caveat"
    assert "Udyam enterprise-share ordering" in b["text"][0]
    c = _env(envelopes, "demand_district_occupation_signal")["required_caveat"]
    assert c["column"] == "within_district_ranking_caveat"
    assert "Census-2011 occupation-share ordering" in c["text"][0]


def test_missing_caveat_column_blocks_the_allocation_label(con, contract):
    tampered = [dict(o) for o in contract.outputs]
    for o in tampered:
        if o["output_id"] == "demand_district_relative_signal":
            o["required_caveat_column"] = "no_such_caveat"
    forged = type(contract)(
        contract_version=contract.contract_version, mode=contract.mode,
        coverage_sources=contract.coverage_sources, outputs=tampered,
        unavailable_capabilities=contract.unavailable_capabilities,
        barred_fields=contract.barred_fields, terminology=contract.terminology,
        publication_tiers=contract.publication_tiers,
        derivation_inputs=contract.derivation_inputs,
        vintage_policy=contract.vintage_policy,
    )
    with pytest.raises(ContractError, match="requires caveat column"):
        build_envelopes(con, forged)


@pytest.mark.parametrize("bad_label", [
    "District demand ranking",
    "District vacancy ranking",
    "Highest-demand districts",
    "Number of vacancies by district",
    "Top occupations by vacancies",
    "Highest-demand occupations",
    "Occupation vacancy ranking",
    "Occupation shortage ranking",
    "Occupation demand count",
    "Observed demand ranking",
    "Vacancy ranking",
    "Shortage ranking",
])
def test_forbidden_ranking_labels_are_caught(contract, envelopes, bad_label):
    tampered = [dict(e) for e in envelopes]
    for e in tampered:
        if e["output_id"] == "demand_district_relative_signal":
            e["allowed_label"] = bad_label
    v = lint_envelopes(tampered, contract)
    assert any(x.rule in ("forbidden_ranking_label", "reserved_everywhere",
                          "relative_signal_not_a_count") for x in v), (
        bad_label, [str(x) for x in v])


def test_no_output_may_declare_itself_an_observed_vacancy_ranking(tmp_path):
    raw = yaml.safe_load(paths.PUBLICATION_CONTRACT_YAML.read_text())
    for o in raw["outputs"]:
        if o["output_id"] == "demand_district_relative_signal":
            o["is_observed_vacancy_ranking"] = True
    bad = tmp_path / "bad_ranking.yaml"
    bad.write_text(yaml.safe_dump(raw))
    with pytest.raises(ContractError, match="observed vacancy ranking"):
        load_contract(bad)


def test_preferred_signal_labels_are_declared(contract):
    pref = contract.terminology["preferred_signal_labels"]
    assert pref["demand_district_relative_signal"] == \
        "District Relative Demand Allocation Signal"
    assert pref["demand_district_occupation_signal"] == \
        "District x Occupation Relative Demand Allocation Signal"
    assert pref["occupation_view_comparison"] == "Relative Demand Allocation Signal"


# --- 10. Derivation inputs cannot be framed as corroboration -------------
def test_derivation_inputs_are_declared_for_b_and_c(contract):
    assert contract.inputs_of("demand_district_relative_signal") == [
        "analytical_district_structure"
    ]
    assert set(contract.inputs_of("demand_district_occupation_signal")) == {
        "analytical_district_structure", "analytical_district_occupation_structure"
    }


def test_derivation_inputs_are_disclosure_only(contract):
    for d in contract.derivation_inputs:
        assert d["display_role"] == "DERIVATION_DISCLOSURE_ONLY"
        assert d["permitted_section_labels"]
        assert d["prohibited_labels"]


def test_declared_derivation_rules_are_internally_consistent(contract):
    assert lint_derivation_labels(contract) == []


@pytest.mark.parametrize("bad_label", [
    "Supporting evidence for the demand signal",
    "Independent validation",
    "Corroborating demand data",
    "Corroborating evidence",
    "Independent evidence",
])
def test_corroboration_framing_of_an_input_is_caught(contract, bad_label):
    v = lint_derivation_labels(
        contract, {"analytical_district_structure": bad_label}
    )
    assert any(x.rule == "corroboration_label" for x in v), (
        bad_label, [str(x) for x in v])


def test_a_derivation_input_shown_outside_a_derivation_section_is_caught(contract):
    v = lint_derivation_labels(
        contract, {"analytical_district_occupation_structure": "Related datasets"}
    )
    assert any(x.rule == "derivation_disclosure_only" for x in v)


def test_permitted_derivation_section_label_passes(contract):
    assert lint_derivation_labels(
        contract, {"analytical_district_structure": "How this signal is derived"}
    ) == []


def test_corroboration_words_also_blocked_in_output_labels(contract, envelopes):
    tampered = [dict(e) for e in envelopes]
    for e in tampered:
        if e["output_id"] == "demand_district_relative_signal":
            e["interpretation"] = "CORROBORATING DEMAND DATA"
    v = lint_envelopes(tampered, contract)
    assert any(x.rule == "corroboration_label" for x in v)


def test_derivation_inputs_are_not_published_as_outputs(contract):
    """A factor is not a product; it has no output entry of its own."""
    ids = {o["output_id"] for o in contract.outputs}
    for d in contract.derivation_inputs:
        assert d["input"] not in ids, d["input"]


# --- 11. PAN-India residual excluded from the default comparison ---------
def test_residual_excluded_from_default_state_comparison(con, envelopes):
    e = _env(envelopes, "analytical_state_demand")["residual_handling"]
    assert e["excluded_from_default_comparison"] is True
    assert e["must_remain_disclosed"] is True
    assert e["allocation"] == "PROHIBITED"
    assert e["default_filter"] == "is_pan_india_residual = FALSE"
    assert e["residual_rows"] == 1
    assert e["default_comparison_rows"] == 37
    top = con.execute(
        "select state_name_as_source from analytical_state_demand "
        "order by vacancies_cumulative desc limit 1"
    ).fetchone()[0]
    assert top == "Multiple States/PAN India", (
        "the residual still outranks every state, so the default filter matters"
    )


def test_residual_value_unchanged(con):
    v = con.execute(
        "select vacancies_cumulative from analytical_state_demand "
        "where is_pan_india_residual"
    ).fetchone()[0]
    assert v == 20507320


def test_residual_allocation_remains_a_blocked_capability(contract):
    reg = {r["capability_id"]: r for r in build_unavailability_register(contract)}
    assert reg["pan_india_residual_allocation"]["reason_code"] == "PROHIBITED"


# --- 12. Source-specific vintage is preserved ---------------------------
def test_no_global_as_of_date_is_permitted(contract):
    vp = contract.vintage_policy
    assert vp["global_as_of_date"] == "PROHIBITED"
    assert vp["per_output_vintage_required"] is True
    assert vp["time_series_across_vintages"] == "PROHIBITED"


def test_global_as_of_date_is_rejected(tmp_path):
    for key in ("global_as_of_date", "time_series_across_vintages"):
        raw = yaml.safe_load(paths.PUBLICATION_CONTRACT_YAML.read_text())
        raw["vintage_policy"][key] = "ALLOWED"
        bad = tmp_path / f"bad_{key}.yaml"
        bad.write_text(yaml.safe_dump(raw))
        with pytest.raises(ContractError, match="prohibited"):
            load_contract(bad)


def test_each_output_keeps_its_own_vintage(envelopes):
    seen = {}
    for oid in ("analytical_state_demand", "demand_district_relative_signal",
                "fact_training_infrastructure", "analytical_labour_market_context"):
        e = _env(envelopes, oid)
        assert e["vintage"], oid
        assert e["vintage_source"].startswith(oid)
        seen[oid] = tuple(e["vintage"])
    # heterogeneous by construction - no single date could describe them
    assert len(set(seen.values())) > 1
    assert seen["analytical_state_demand"] == ("2024-11-15",)
    assert seen["fact_training_infrastructure"] == ("2024-03-31",)
    assert seen["analytical_labour_market_context"] == ("M202504",)


def test_vintage_policy_bans_live_language(contract):
    for term in ("live", "real-time", "current", "latest", "data as of"):
        assert term in contract.vintage_policy["prohibited_labels"]


# --- 13/14/15. Nothing analytical changed -------------------------------
def test_no_new_analytical_rows_or_values(con):
    """The amendment is metadata only."""
    expected = {
        "analytical_state_demand": 38, "analytical_demand_by_industry": 22,
        "demand_national_occupation_composition": 175,
        "demand_district_relative_signal": 785,
        "demand_district_occupation_signal": 1889,
        "fact_training_outcome": 350, "fact_training_infrastructure": 144,
        "fact_training_trade_outcome": 35, "analytical_labour_market_context": 81,
        "analytical_district_structure": 1570,
        "analytical_district_occupation_structure": 12420,
        "supply_coverage_summary": 10, "demand_coverage_summary": 8,
    }
    for t, n in expected.items():
        assert con.execute(f"select count(*) from {t}").fetchone()[0] == n, t


def test_demand_and_supply_measure_sums_unchanged(con):
    sums = {
        ("demand_district_occupation_signal", "district_occupation_signal"): 3710699.0538,
        ("demand_district_relative_signal", "relative_demand_signal"): 14768513.0,
        ("fact_training_outcome", "value"): 10965811.0,
        ("fact_training_trade_outcome", "value"): 2958767.0,
    }
    for (t, c), expected in sums.items():
        got = con.execute(f"select coalesce(sum({c}),0) from {t}").fetchone()[0]
        assert got == pytest.approx(expected, abs=1e-3), (t, got)


def test_no_state_or_district_trade_supply_created_by_the_amendment(con):
    assert {r[0] for r in con.execute(
        "select distinct geo_level from fact_training_trade_outcome").fetchall()
    } == {"NATIONAL"}
    assert {r[0] for r in con.execute(
        "select distinct geo_level from fact_training_outcome").fetchall()
    } == {"STATE"}
    tables = {r[0] for r in con.execute(
        "select table_name from information_schema.tables where table_schema='main'"
    ).fetchall()}
    assert len(tables) == 40


def test_is_measured_shortage_still_false_after_the_amendment(envelopes, contract):
    assert len(envelopes) == 13  # 12 production + 1 experimental
    for e in envelopes:
        assert e["is_measured_shortage"] is False
        assert e["forecast_available"] is False
    for r in build_unavailability_register(contract):
        assert r["is_measured_shortage"] is False


def test_supporting_output_is_not_experimental_and_does_not_leak(envelopes):
    prod = production_envelopes(envelopes)
    assert "analytical_labour_market_context" in {e["output_id"] for e in prod}
    assert_no_experimental_leak(prod)
    assert all(e["output_id"] != "hybrid_potential_pressure" for e in prod)
