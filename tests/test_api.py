"""Step 7.4 - API and dashboard tests.

Every guardrail the publication contract asserts is checked at the HTTP boundary,
because that is where a consumer meets it. The numbered tests map onto the twenty
rules required by the Step 7.4 brief.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import duckdb
import pytest

warnings.filterwarnings("ignore")

from lmis.publish import load_contract, lint_label_catalogue  # noqa: E402
from lmis.warehouse.load import DB_PATH  # noqa: E402

pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="warehouse not built")

I18N = Path(__file__).resolve().parents[1] / "api" / "static" / "i18n"
STATIC = I18N.parent


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect(str(DB_PATH), read_only=True)
    yield c
    c.close()


def _meta(r):
    assert r.status_code == 200, r.text
    return r.json()["meta"]


# --- 1. national endpoints work -------------------------------------------
def test_health_reports_the_contract_mode(client):
    j = client.get("/api/health").json()
    assert j["status"] == "ok"
    assert j["mode"]["NUMERIC_GAP"] == "NOT_IDENTIFIABLE"
    assert j["mode"]["FORECASTING"] == "NOT_SUPPORTED_YET"
    assert j["mode"]["OFFICIAL_ANALYTICAL_MODE"] == "OPTION_A"
    assert j["is_measured_shortage"] is False


def test_national_industry_is_observed(client):
    r = client.get("/api/demand/national/industry")
    m = _meta(r)
    assert m["tier"] == "OBSERVED"
    assert m["evidence_status"] == ["OBSERVED"]
    assert len(r.json()["data"]) == 22
    # the NIC-NULL sectors must survive, which is why the filter keys on sector
    assert m["filter_key"] == "ncs_sector_name"
    assert m["null_nic_section_rows"] == 2


def test_national_occupation_composition_is_estimated(client):
    r = client.get("/api/demand/national/occupation-composition")
    m = _meta(r)
    assert m["tier"] == "ESTIMATED"
    assert "OBSERVED" not in m["evidence_status"]
    assert len(r.json()["data"]) == 175
    assert m["confidence_is_per_row"] is True
    assert set(m["confidence"]) == {"LOW", "MEDIUM"}


def test_no_national_total_demand_field_anywhere(client):
    for p in ("/api/demand/national/industry", "/api/demand/states", "/api/health"):
        body = json.dumps(client.get(p).json()).lower()
        for banned in ("total_labour_demand", "national_demand_total",
                       "total_demand", "labour_demand_total"):
            assert banned not in body, (p, banned)


# --- 2. state endpoint excludes the residual by default -------------------
def test_states_excludes_pan_india_residual_by_default(client):
    r = client.get("/api/demand/states")
    data, m = r.json()["data"], _meta(r)
    names = [x["state_name_as_source"] for x in data]
    assert "Multiple States/PAN India" not in names
    assert len(data) == 37
    assert m["residual_excluded_by_default"] is True
    assert m["residual_disclosure"][0]["vacancies_cumulative"] == 20507320
    assert "never allocated" in m["residual_note"]


def test_residual_is_opt_in_only(client):
    assert len(client.get(
        "/api/demand/states", params={"include_residual": True}
    ).json()["data"]) == 38


def test_residual_still_outranks_every_state(con):
    """Why the default filter matters, asserted against the data."""
    top = con.execute(
        "select state_name_as_source from analytical_state_demand "
        "order by vacancies_cumulative desc limit 1"
    ).fetchone()[0]
    assert top == "Multiple States/PAN India"


def test_residual_allocation_is_a_blocked_route(client):
    m = _meta(client.get("/api/residual-allocation"))
    assert m["reason_code"] == "PROHIBITED"
    assert client.get("/api/residual-allocation").json()["data"] is None


# --- 3/4. district + district x occupation envelopes ----------------------
def test_district_list_requires_a_state(client):
    assert client.get("/api/demand/districts").status_code == 422
    assert client.get("/api/demand/districts", params={"state": "ZZ"}).status_code == 404


def test_district_occupation_requires_a_state(client):
    assert client.get("/api/demand/district-occupation").status_code == 422


def test_district_list_returns_the_publication_envelope(client):
    r = client.get("/api/demand/districts", params={"state": "27"})
    m = _meta(r)
    for key in ("output_id", "publication_status", "tier", "evidence_status",
                "confidence", "coverage", "grain", "unit", "measure_basis",
                "vintage", "provenance", "interpretation",
                "prohibited_interpretations", "is_measured_shortage",
                "forecast_available", "limitations", "contract_version"):
        assert key in m, key
    assert m["publication_status"] == "PRODUCTION"
    assert m["unit"] == "relative_signal_unitless"
    assert m["contract_version"] == load_contract().contract_version


def test_output_b_uses_the_approved_allocation_label(client):
    m = _meta(client.get("/api/demand/districts", params={"state": "27"}))
    assert m["allowed_label"] == "District Relative Demand Allocation Signal"
    assert m["is_observed_vacancy_ranking"] is False
    assert any("Udyam enterprise-share ordering" in x for x in m["limitations"])


def test_output_c_uses_the_approved_allocation_label(client):
    m = _meta(client.get("/api/demand/district-occupation", params={"state": "27"}))
    assert m["allowed_label"] == (
        "District x Occupation Relative Demand Allocation Signal"
    )
    assert m["is_observed_vacancy_ranking"] is False
    assert any("Census-2011 occupation-share ordering" in x for x in m["limitations"])
    assert "VACANCY_COUNT" in m["prohibited_interpretations"]


def test_b_and_c_are_never_labelled_observed_rankings(client):
    banned = ("district demand ranking", "district vacancy ranking",
              "highest-demand districts", "vacancy count by district",
              "top occupations by vacancies", "highest-demand occupations",
              "occupation vacancy ranking", "shortage ranking")
    for p, q in (("/api/demand/districts", {"state": "27"}),
                 ("/api/demand/district-occupation", {"state": "27"})):
        body = json.dumps(client.get(p, params=q).json()).lower()
        for b in banned:
            assert b not in body, (p, b)


# --- 5. missing Census coverage -> NOT_AVAILABLE, never zero --------------
@pytest.mark.parametrize("status", ["CENSUS_NOT_ACQUIRED", "NO_CENSUS_2011_CODE"])
def test_missing_census_returns_not_available_with_a_reason(client, con, status):
    lgd = con.execute(
        "select lgd_code from demand_district_occupation_signal "
        "where occupation_prior_status = ? limit 1", [status]
    ).fetchone()[0]
    panel = _meta(client.get(f"/api/demand/districts/{lgd}"))["occupation_panel"]
    assert panel["status"] == "NOT_AVAILABLE"
    assert panel["reason_code"] == status
    assert panel["reason"]
    assert panel["rows"] is None       # not [] and not a zero-filled skeleton
    assert panel["divisions"] == 0
    assert "not an absence of demand" in panel["reason"].lower() or \
           "not an absence of demand" in panel["reason"]


def test_available_district_returns_nine_divisions(client, con):
    lgd = con.execute(
        "select lgd_code from demand_district_occupation_signal "
        "where occupation_prior_status = 'AVAILABLE' limit 1"
    ).fetchone()[0]
    panel = _meta(client.get(f"/api/demand/districts/{lgd}"))["occupation_panel"]
    assert panel["status"] == "AVAILABLE"
    assert panel["divisions"] == 9


def test_no_zero_is_ever_substituted_for_a_missing_signal(client, con):
    assert con.execute(
        "select count(*) from demand_district_occupation_signal "
        "where district_occupation_signal = 0"
    ).fetchone()[0] == 0
    r = client.get("/api/demand/district-occupation",
                   params={"state": "9", "occupation_prior_status": "CENSUS_NOT_ACQUIRED"})
    for row in r.json()["data"]:
        assert row["district_occupation_signal"] is None


# --- 6. PLFS is SUPPORTING and not a demand measure ----------------------
def test_plfs_is_supporting_context(client):
    r = client.get("/api/context/labour-force")
    m = _meta(r)
    assert m["tier"] == "SUPPORTING"
    assert m["evidence_status"] == ["OBSERVED"]      # evidence read from the data
    assert m["is_demand_measure"] is False
    assert m["data_flag"] == {"not_a_demand_measure": True}
    assert m["display_banner"] == "SUPPORTING CONTEXT - NOT A DEMAND MEASURE"
    assert all(row["not_a_demand_measure"] for row in r.json()["data"])


def test_plfs_is_national_only_with_no_geo_filter(client):
    m = _meta(client.get("/api/context/labour-force"))
    assert m["national_only"] is True
    assert m["district_estimates_valid"] is False
    assert m["valid_geo_levels"] == ["NATIONAL"]
    # there is deliberately no state/district parameter to filter by
    assert client.get("/api/context/labour-force",
                      params={"state": "27"}).status_code == 200
    assert len(client.get("/api/context/labour-force",
                          params={"state": "27"}).json()["data"]) == 81


def test_plfs_cannot_be_read_as_demand_supply_or_gap(client):
    m = _meta(client.get("/api/context/labour-force"))
    for term in ("DEMAND", "VACANCY_DATA", "SUPPLY", "DEMAND_SUPPLY_GAP", "SHORTAGE",
                 "STATE_DEMAND", "DISTRICT_DEMAND", "OCCUPATION_LEVEL_SUPPLY"):
        assert term in m["prohibited_interpretations"], term


def test_no_plfs_derived_metric_is_computed(client):
    """No new field may be computed from PLFS - only published columns are served.

    `prohibited_interpretations` legitimately NAMES shortage and supply, so the
    check is on the row fields, not on the whole document.
    """
    rows = client.get("/api/context/labour-force").json()["data"]
    served = set(rows[0])
    expected = {
        "period_id", "geo_level", "area", "sex", "age_group", "indicator",
        "approach", "value_percent", "std_error", "unit", "statistical_basis",
        "valid_geo_level", "district_estimates_valid", "not_a_demand_measure",
        "observation_status", "source_vintage", "source_id", "snapshot_file",
    }
    assert served == expected, served ^ expected
    for f in served:
        for banned in ("vacancy", "shortage", "supply", "gap", "ratio", "forecast"):
            assert banned not in f.lower(), f


# --- 7/8. evidence status and vintage are preserved ----------------------
def test_evidence_status_matches_the_warehouse(client, con):
    pairs = [
        ("/api/demand/states", "analytical_state_demand", "observation_status"),
        ("/api/demand/national/industry", "analytical_demand_by_industry",
         "observation_status"),
        ("/api/demand/districts?state=27", "demand_district_relative_signal",
         "observed_or_estimated"),
        ("/api/context/labour-force", "analytical_labour_market_context",
         "observation_status"),
    ]
    for path, table, col in pairs:
        in_db = sorted({
            r[0] for r in con.execute(
                f"select distinct {col} from {table} where {col} is not null"
            ).fetchall()
        })
        assert _meta(client.get(path))["evidence_status"] == in_db, path


def test_each_output_keeps_its_own_vintage(client):
    seen = {}
    for path, oid in (("/api/demand/states", "analytical_state_demand"),
                      ("/api/demand/districts?state=27", "demand_district_relative_signal"),
                      ("/api/context/labour-force", "analytical_labour_market_context"),
                      ("/api/training/states", "fact_training_outcome")):
        m = _meta(client.get(path))
        assert m["vintage"], path
        seen[oid] = tuple(m["vintage"])
    assert len(set(seen.values())) > 1, "vintages must stay heterogeneous"
    assert seen["analytical_state_demand"] == ("2024-11-15",)
    assert seen["analytical_labour_market_context"] == ("M202504",)


def test_no_global_as_of_date_is_published(client):
    c = client.get("/api/meta/contract").json()["data"]
    assert c["vintage_policy"]["global_as_of_date"] == "PROHIBITED"
    assert c["vintage_policy"]["time_series_across_vintages"] == "PROHIBITED"


def test_provenance_travels_with_every_analytical_response(client):
    for p in ("/api/demand/states", "/api/demand/districts?state=27",
              "/api/demand/district-occupation?state=27", "/api/training/states"):
        assert _meta(client.get(p))["provenance"]["source_ids"], p


# --- 9/10. within-state default and the cross-state caveat ---------------
def test_within_state_is_the_default_comparison(client):
    m = _meta(client.get("/api/demand/districts", params={"state": "27"}))
    assert m["comparison_applied"] == "within_state"
    assert m["default_ranking"]["mode"] == "WITHIN_STATE"
    rows = client.get("/api/demand/districts", params={"state": "27"}).json()["data"]
    assert [r["rank_within_state"] for r in rows] == sorted(
        r["rank_within_state"] for r in rows
    )


def test_cross_state_is_opt_in_and_carries_the_caveat(client):
    m = _meta(client.get("/api/demand/districts",
                         params={"state": "27", "comparison": "cross_state"}))
    assert m["comparison_applied"] == "cross_state"
    assert "not directly comparable" in m["cross_state_caveat"]
    assert "registration coverage" in m["cross_state_caveat"]


def test_district_occupation_defaults_to_within_state(client):
    m = _meta(client.get("/api/demand/district-occupation", params={"state": "27"}))
    assert m["default_comparison"] == "within_state"
    assert "restates neither input" in m["informative_comparison"]


# --- 11. derivation inputs are never framed as corroboration ------------
def test_derivation_inputs_are_declared_not_corroborating(client):
    m = _meta(client.get("/api/demand/districts", params={"state": "27"}))
    assert m["derivation_display_role"] == "DERIVATION_DISCLOSURE_ONLY"
    assert "analytical_district_structure" in m["derivation_inputs"]
    body = json.dumps(client.get("/api/demand/districts",
                                 params={"state": "27"}).json()).lower()
    for banned in ("supporting evidence for the demand signal", "independent validation",
                   "corroborating demand data", "corroborating evidence"):
        assert banned not in body, banned


def test_contract_exposes_the_derivation_rules(client):
    rules = client.get("/api/meta/contract").json()["data"]["derivation_inputs"]
    assert {r["input"] for r in rules} == {
        "analytical_district_structure", "analytical_district_occupation_structure"
    }
    for r in rules:
        assert r["display_role"] == "DERIVATION_DISCLOSURE_ONLY"
        assert "How this signal is derived" in r["permitted_section_labels"]
        assert "independent validation" in r["prohibited_labels"]


def test_ui_shows_derivation_only_under_a_derivation_heading():
    """The UI's own label for the derivation panel must be a permitted one."""
    en = json.loads((I18N / "en.json").read_text())
    rules = load_contract().derivation_inputs
    permitted = {p.lower() for r in rules for p in r["permitted_section_labels"]}
    assert en["derivation.heading"].lower() in permitted
    assert "not independent evidence" in en["derivation.note"]


# --- 12. unavailable capabilities use the unavailability contract --------
BLOCKED = [
    ("/api/demand-supply-gap", "demand_supply_gap_numeric", "NOT_IDENTIFIABLE"),
    ("/api/forecast", "forecast", "NOT_SUPPORTED_YET"),
    ("/api/supply/district-occupation", "district_occupation_supply", "NOT_IDENTIFIABLE"),
    ("/api/supply/state-occupation", "state_occupation_supply", "NOT_IDENTIFIABLE"),
    ("/api/supply/district-trade", "district_trade_supply", "NOT_ACQUIRED"),
    ("/api/supply/state-trade", "state_trade_supply", "NOT_IDENTIFIABLE"),
    ("/api/shortage", "shortage_or_surplus_count", "NOT_IDENTIFIABLE"),
    ("/api/demand/districts/vacancy-count", "district_vacancy_count", "NOT_AVAILABLE"),
    ("/api/demand/district-occupation/vacancy-count",
     "district_occupation_vacancy_count", "NOT_AVAILABLE"),
    ("/api/residual-allocation", "pan_india_residual_allocation", "PROHIBITED"),
]


@pytest.mark.parametrize("path,cap,code", BLOCKED)
def test_blocked_route_returns_200_with_an_explicit_reason(client, path, cap, code):
    r = client.get(path)
    assert r.status_code == 200, "a 404 would read as 'none found', not 'not computable'"
    body = r.json()
    assert body["data"] is None, "never an empty array and never zero"
    m = body["meta"]
    assert m["capability_id"] == cap
    assert m["publication_status"] == "UNAVAILABLE"
    assert m["evidence_status"] == "UNAVAILABLE"
    assert m["reason_code"] == code
    assert m["reason"] and m["blocking_gate"]
    assert m["is_measured_shortage"] is False


def test_capabilities_index_groups_by_reason_code(client):
    j = client.get("/api/capabilities").json()
    assert len(j["data"]) == 16
    g = j["meta"]["grouped_by_reason_code"]
    assert "NOT_IDENTIFIABLE" in g and "NOT_ACQUIRED" in g
    assert "structural" in j["meta"]["reason_code_meaning"]["NOT_IDENTIFIABLE"].lower()
    assert all(r["data"] is None for r in j["data"])


def test_blocked_route_does_not_shadow_a_real_district(client):
    assert client.get("/api/demand/districts/532").status_code == 200


# --- 13. the experimental hybrid is absent from production --------------
def test_hybrid_is_not_served_by_any_production_route(client):
    spec = client.get("/openapi.json").json()
    paths = " ".join(spec["paths"]).lower()
    for banned in ("hybrid", "potential-pressure", "potential_pressure",
                   "quadrant", "pressure-score"):
        assert banned not in paths, banned


def test_hybrid_is_declared_experimental_and_unimplemented(client):
    outs = client.get("/api/meta/contract").json()["data"]["outputs"]
    hy = next(o for o in outs if o["output_id"] == "hybrid_potential_pressure")
    assert hy["publication_status"] == "EXPERIMENTAL_ONLY"
    assert hy["implemented"] is False


def test_hybrid_cannot_be_exported(client):
    assert client.get("/api/export/hybrid_potential_pressure.json").status_code == 403
    assert client.get("/api/export/hybrid_potential_pressure.csv").status_code == 403
    assert "hybrid_potential_pressure" not in client.get(
        "/api/export/outputs").json()["data"]


# --- 14/15/16/17. shortage, gap, forecast, supply are never produced ----
def test_is_measured_shortage_false_on_every_response(client):
    paths = ["/api/health", "/api/demand/national/industry",
             "/api/demand/national/occupation-composition", "/api/demand/states",
             "/api/demand/districts?state=27", "/api/demand/districts/532",
             "/api/demand/district-occupation?state=27", "/api/context/labour-force",
             "/api/training/states", "/api/training/trades/top-n", "/api/coverage",
             "/api/capabilities", "/api/quality", "/api/meta/contract",
             "/api/meta/methodology", "/api/meta/filters", "/api/meta/sources",
             "/api/export/outputs"] + [p for p, _, _ in BLOCKED]
    for p in paths:
        body = client.get(p).json()
        m = body.get("meta", body)
        if "is_measured_shortage" in m:
            assert m["is_measured_shortage"] is False, p
        assert '"is_measured_shortage": true' not in json.dumps(body).lower()


def test_forecast_is_unavailable_on_every_analytical_response(client):
    for p in ("/api/demand/states", "/api/demand/districts?state=27",
              "/api/demand/district-occupation?state=27", "/api/context/labour-force"):
        m = _meta(client.get(p))
        assert m["forecast_available"] is False
        assert "G-4" in m["forecast_unavailable_reason"]


def test_no_route_produces_a_gap_shortage_or_forecast_value(client):
    spec = client.get("/openapi.json").json()
    for path in spec["paths"]:
        if path in dict((p, 1) for p, _, _ in BLOCKED):
            continue
        assert "gap" not in path.lower() or "demand-supply-gap" in path
        assert "shortage" not in path.lower()
        assert "forecast" not in path.lower()


def test_no_unsupported_supply_route_returns_data(client):
    for p in ("/api/supply/district-occupation", "/api/supply/state-occupation",
              "/api/supply/district-trade", "/api/supply/state-trade"):
        assert client.get(p).json()["data"] is None


def test_training_is_never_labelled_supply(client):
    r = client.get("/api/training/states", params={"state": "27"})
    m = _meta(r)
    assert "SUPPLY" in m["prohibited_interpretations"]
    assert "not a supply quantity" in m["not_supply_note"]
    for row in r.json()["data"]:
        assert "supply" not in " ".join(str(k) for k in row).lower()
    assert m["grain"]["occupation_level"] == "NONE"


def test_trade_outcome_stays_national_top_n(client):
    r = client.get("/api/training/trades/top-n")
    m = _meta(r)
    assert m["is_top_n_subset"] is True
    assert m["geo_level"] == "NATIONAL"
    assert all(row["geo_level"] == "NATIONAL" for row in r.json()["data"])
    assert all(row["is_top_n_subset"] for row in r.json()["data"])


# --- 18. production exports exclude experimental/unavailable -------------
def test_export_index_lists_only_production_outputs(client):
    listed = client.get("/api/export/outputs").json()["data"]
    outs = {o["output_id"]: o for o in
            client.get("/api/meta/contract").json()["data"]["outputs"]}
    for oid in listed:
        assert outs[oid]["publication_status"] == "PRODUCTION"


def test_csv_export_carries_the_mandatory_metadata_block(client):
    r = client.get("/api/export/demand_district_relative_signal.csv")
    assert r.status_code == 200
    head = [l for l in r.text.splitlines() if l.startswith("#")]
    joined = "\n".join(head)
    for key in ("output_id", "publication_status", "tier", "evidence_status",
                "confidence", "unit", "vintage", "interpretation",
                "is_measured_shortage", "forecast_available", "contract_version"):
        assert f"# {key}:" in joined, key
    assert "# limitation:" in joined
    assert "Udyam enterprise-share ordering" in joined
    assert "# coverage." in joined


def test_json_export_carries_the_mandatory_metadata_block(client):
    j = client.get("/api/export/demand_district_occupation_signal.json").json()
    m = j["meta"]
    assert m["tier"] == "ESTIMATED"
    assert m["unit"] == "relative_signal_unitless"
    assert m["is_measured_shortage"] is False
    assert m["forecast_available"] is False
    assert m["limitations"]
    assert len(j["data"]) == 1889


def test_export_never_renames_a_relative_signal_to_vacancies(client):
    j = client.get("/api/export/demand_district_occupation_signal.json").json()
    cols = set(j["data"][0])
    assert not any("vacanc" in c.lower() for c in cols)
    assert "district_occupation_signal" in cols
    assert j["meta"]["unit"] == "relative_signal_unitless"


def test_unknown_or_blocked_export_is_refused(client):
    assert client.get("/api/export/fact_gap.json").status_code == 404
    assert client.get("/api/export/analytical_district_structure.json").status_code == 404


def test_csv_export_can_omit_meta_only_on_explicit_request(client):
    r = client.get("/api/export/demand_coverage_summary.csv",
                   params={"include_meta": False})
    assert not r.text.startswith("#")
    assert client.get("/api/export/demand_coverage_summary.csv").text.startswith("#")


# --- 19. terminology lint passes, including the UI catalogue ------------
def _flat_labels(lang):
    """Every translated STRING in a catalogue, including the elements of a list.

    The explanation copy added in the readability pass is authored as lists, and
    `lint_label_catalogue` skips a non-string value. Flattening is what keeps a
    list element under the same guardrail as a plain label - otherwise a panel's
    reading notes would be the one place terminology could drift unchecked.
    """
    flat = {}
    for k, v in json.loads((I18N / f"{lang}.json").read_text()).items():
        if isinstance(v, str):
            flat[k] = v
        elif isinstance(v, list):
            for i, x in enumerate(v):
                if isinstance(x, str):
                    flat[f"{k}[{i}]"] = x
    return flat


@pytest.mark.parametrize("lang", ["en", "hi"])
def test_ui_label_catalogue_passes_the_terminology_lint(lang):
    labels = _flat_labels(lang)
    v = lint_label_catalogue(labels, load_contract(), f"i18n/{lang}")
    assert v == [], [str(x) for x in v]


def test_list_valued_explanation_copy_is_actually_linted():
    """Guard on the guard: a forbidden assertion inside a LIST must be caught."""
    flat = _flat_labels("en")
    assert any(k.endswith("]") for k in flat), "no list elements were flattened"
    assert len(flat) > len(
        {k: v for k, v in json.loads((I18N / "en.json").read_text()).items()
         if isinstance(v, str)})


def test_the_catalogue_lint_still_catches_real_assertions():
    c = load_contract()
    for bad in ("Demand-supply gap by district", "Demand–supply gap by district",
                "District demand ranking", "Occupation supply by district",
                "Shortage heatmap", "Corroborating demand data",
                "Highest-demand occupations", "Skill gap index"):
        assert lint_label_catalogue({"k": bad}, c), bad


def test_the_catalogue_lint_permits_the_required_negations():
    c = load_contract()
    for good in ("It does not publish a demand-supply gap.",
                 "Why no demand-supply gap is published",
                 "not a measured shortage", "Relative signal - not a vacancy count"):
        assert lint_label_catalogue({"k": good}, c) == [], good


def test_app_startup_enforces_the_contract(client):
    """The app refuses to start on a terminology or shortage breach."""
    assert client.get("/api/health").json()["status"] == "ok"


# --- frontend foundation (i18n + accessibility) -------------------------
def test_frontend_assets_are_served(client):
    for p in ("/", "/static/app.js", "/static/styles.css",
              "/static/i18n/en.json", "/static/i18n/hi.json"):
        assert client.get(p).status_code == 200, p


def test_official_codes_are_never_translated():
    """Taxonomy identifiers must stay machine-comparable and officially citable."""
    for lang in ("en", "hi"):
        d = json.loads((I18N / f"{lang}.json").read_text())
        for k, v in d.items():
            if not isinstance(v, str):
                continue
            # no translation file may redefine a scheme or status identifier
            assert not k.startswith(("nco.", "nic.", "lgd.", "census.")), k
        assert "NCO" not in d.get("_meta", {}).get("translated_codes", [])
    hi = json.loads((I18N / "hi.json").read_text())
    assert hi["_meta"]["complete"] is False
    assert "never translated" in hi["_meta"]["note"]


def test_incomplete_translation_falls_back_rather_than_fabricating():
    en = json.loads((I18N / "en.json").read_text())
    hi = json.loads((I18N / "hi.json").read_text())
    missing = set(en) - set(hi)
    assert missing, "hi is deliberately partial"
    # every hi key must exist in en, so nothing is invented that en does not define
    assert not (set(hi) - set(en))


def test_evidence_status_has_a_plain_language_explanation():
    en = json.loads((I18N / "en.json").read_text())
    for s in ("OBSERVED", "ESTIMATED", "SUPPORTING", "UNAVAILABLE"):
        assert en[f"evidence.{s}"] and en[f"evidence.{s}.plain"]
    for c in ("MEDIUM", "LOW"):
        assert en[f"confidence.{c}"] and en[f"confidence.{c}.plain"]
    assert "does not exist" in en["evidence.vsUnavailable"]
    assert "never a percentage" in en["confidence.notNumeric"]


def test_status_is_not_carried_by_colour_alone():
    """Each evidence state gets a glyph and a text label, not just a hue."""
    js = (STATIC / "app.js").read_text()
    assert "GLYPH" in js
    for g in ("■", "◪", "□", "⬚"):
        assert g in js, g
    # the badge renders glyph + translated word together
    assert "class=\"glyph\" aria-hidden=\"true\"" in js


def test_accessibility_foundations_present_in_the_frontend():
    html = (STATIC / "index.html").read_text()
    js = (STATIC / "app.js").read_text()
    css = (STATIC / "styles.css").read_text()
    assert 'class="skip"' in html and "Skip to main content" in html
    assert 'aria-label="Main navigation"' in html
    assert 'aria-live="polite"' in html
    assert 'lang="en"' in html
    assert "scope=\"col\"" in js and "<caption" in js
    assert "aria-describedby" in js        # caveat linked to its table
    assert "aria-current" in js            # current page announced
    assert ":focus-visible" in css
    assert "prefers-color-scheme" in css


def test_map_has_a_table_fallback_string():
    en = json.loads((I18N / "en.json").read_text())
    assert "table" in en["table.mapFallback"].lower()
    assert "without the map" in en["table.mapFallback"]


def test_frontend_hard_codes_no_analytical_value():
    """Every number on screen must come from an API response."""
    js = (STATIC / "app.js").read_text()
    for banned in ("58.13", "41.87", "0.5813", "0.4187", "20507320", "14768513",
                   "35275830", "3710699"):
        assert banned not in js, banned


def test_frontend_offers_no_unsupported_filter():
    js = (STATIC / "app.js").read_text().lower()
    for banned in ("nsqf", "qualification", "trade_filter", "period_range"):
        assert banned not in js, banned


# ===========================================================================
# Step 7.5 - QA regressions. Each pins a defect found in the end-to-end audit,
# so none of them can return silently.
# ===========================================================================

# --- QA-1: reflected XSS through a route argument (FIXED) ----------------
def test_esc_escapes_attribute_delimiters():
    """esc() must cover ' and ` - a value in a single-quoted attribute, or in a JS
    string inside an inline handler, escapes its delimiter without them."""
    js = (STATIC / "app.js").read_text()
    body = js[js.index("const esc ="):js.index("const get =")]
    for pair in ("&amp;", "&lt;", "&gt;", "&quot;", "&#39;", "&#96;"):
        assert pair in body, pair
    assert "/'/g" in body and "/`/g" in body


def test_route_arguments_are_validated_before_use():
    js = (STATIC / "app.js").read_text()
    assert "const ROUTE_ARG" in js
    assert "const safeArg" in js
    assert "arg = safeArg(arg);" in js


def test_no_inline_handler_interpolates_untrusted_data():
    """The occupation state selector used to inject a hash argument into an
    onchange handler; it now reads the value from a data attribute."""
    js = (STATIC / "app.js").read_text()
    import re
    for m in re.finditer(r'on(?:click|change)="([^"]*)"', js):
        handler = m.group(1)
        if "${" not in handler:
            continue
        # the only permitted interpolation is a page name from the PAGES constant
        assert re.fullmatch(r"go\('\$\{p\}'\)", handler), handler
    assert "this.dataset.division" in js


def test_translation_substitution_is_escaped():
    js = (STATIC / "app.js").read_text()
    assert ".join(esc(v))" in js, "t() vars land in innerHTML and must be escaped"


def test_xss_payload_in_a_query_value_is_not_reflected_as_html(client):
    r = client.get("/api/demand/national/industry",
                   params={"ncs_sector": "<script>alert(1)</script>"})
    assert r.status_code == 200
    assert r.json()["data"] == []            # genuinely no match
    assert r.headers["content-type"].startswith("application/json")


# --- QA-2: the district rank chip rendered "rank / 0" (FIXED) ------------
def test_district_detail_exposes_its_state_district_count(client, con):
    m = _meta(client.get("/api/demand/districts/532"))
    assert "districts_in_state" in m
    state = client.get("/api/demand/districts/532").json()["data"][0]["state_lgd_code"]
    expected = con.execute(
        "select count(*) from demand_district_relative_signal where state_lgd_code = ?",
        [state],
    ).fetchone()[0]
    assert m["districts_in_state"] == expected > 0


def test_rank_chip_no_longer_divides_by_an_empty_string():
    js = (STATIC / "app.js").read_text()
    assert "count(r.meta.districts_in_state)}" in js
    assert "S.states.find(s => s.state_lgd_code === row.state_lgd_code) ? '' : ''" not in js


# --- QA-3: an available output with no matching rows (FIXED) -------------
def test_empty_but_available_result_is_distinguished_from_unavailable(client):
    """Three states must stay distinct: available-but-no-match, not-available,
    and unsupported-capability."""
    no_match = client.get("/api/demand/district-occupation",
                          params={"state": "27", "nco_division": "99"}).json()
    not_avail = client.get("/api/demand/district-occupation",
                           params={"state": "32"}).json()
    unsupported = client.get("/api/demand-supply-gap").json()
    assert no_match["data"] == [] and no_match["meta"]["publication_status"] == "PRODUCTION"
    assert not_avail["data"] and set(
        r["occupation_prior_status"] for r in not_avail["data"]
    ) == {"CENSUS_NOT_ACQUIRED"}
    assert all(r["district_occupation_signal"] is None for r in not_avail["data"])
    assert unsupported["data"] is None
    assert unsupported["meta"]["reason_code"] == "NOT_IDENTIFIABLE"


def test_frontend_explains_an_empty_table_rather_than_rendering_nothing():
    js = (STATIC / "app.js").read_text()
    assert "function noMatch" in js
    assert "if (!rows || !rows.length) return noMatch" in js
    en = json.loads((I18N / "en.json").read_text())
    assert en["table.noMatch"] == "No matching observation"
    assert "different from the data being unavailable" in en["table.noMatchVsUnavailable"]


def test_signal_bars_cannot_divide_by_negative_infinity():
    """Math.max() over an empty filtered set returns -Infinity."""
    js = (STATIC / "app.js").read_text()
    assert "Math.max(...)" not in js
    assert js.count("Math.max(0, ...") == 4


# --- QA-4: export mixed a relative signal with an observed count (FIXED) --
def test_export_declares_per_column_semantics(client):
    h = "\n".join(l for l in client.get(
        "/api/export/demand_district_relative_signal.csv").text.splitlines()
        if l.startswith("#"))
    assert "# column.relative_demand_signal: THE MEASURE" in h
    assert "NOT this district's vacancy count" in h
    assert "# column.district_enterprise_count:" in h
    j = client.get("/api/export/demand_district_relative_signal.json").json()
    notes = j["meta"]["column_notes"]
    assert notes["observed_state_vacancies"].startswith("OBSERVED input at STATE grain")
    assert "Not a count of anything" in notes["relative_demand_signal"]


def test_every_production_export_conforms(client):
    from api.routers.exports import EXPORTABLE

    required = ("output_id", "publication_status", "tier", "evidence_status",
                "confidence", "unit", "measure_basis", "vintage", "interpretation",
                "is_measured_shortage", "forecast_available", "contract_version")
    for oid in EXPORTABLE:
        rc = client.get(f"/api/export/{oid}.csv")
        rj = client.get(f"/api/export/{oid}.json")
        assert rc.status_code == 200 and rj.status_code == 200, oid
        head = "\n".join(l for l in rc.text.splitlines() if l.startswith("#"))
        for k in required:
            assert f"# {k}:" in head, (oid, k)
            assert k in rj.json()["meta"], (oid, k)
        m = rj.json()["meta"]
        assert m["is_measured_shortage"] is False
        assert m["forecast_available"] is False
        # the measure column keeps its own name
        if m["unit"] == "relative_signal_unitless":
            cols = set(rj.json()["data"][0])
            assert any("signal" in c for c in cols), oid


# --- QA-5: a training domain was displayed as "supply" (FIXED) -----------
def test_coverage_does_not_display_a_training_domain_as_supply(client):
    j = client.get("/api/coverage").json()
    assert j["meta"]["domain_labels"] == {
        "demand": "Demand evidence", "supply": "Training evidence"
    }
    for row in j["data"]:
        assert row["domain_label"] in ("Demand evidence", "Training evidence")
        if row["domain"] == "supply":
            assert row["domain_label"] == "Training evidence"
    # the query key is retained for compatibility
    assert len(client.get("/api/coverage", params={"domain": "supply"}).json()["data"]) == 10


def test_frontend_renders_the_domain_label_not_the_raw_key():
    js = (STATIC / "app.js").read_text()
    assert "r.domain_label || r.domain" in js


# --- QA-6: accessibility - touch target size (FIXED) --------------------
def test_interactive_targets_meet_the_44px_minimum():
    css = (STATIC / "styles.css").read_text()
    assert "min-height:38px" not in css
    assert css.count("min-height:44px") >= 3


# --- QA-7: structural guards that must not regress ----------------------
def test_no_route_collision_shadows_a_blocked_capability(client):
    """`/demand/districts/vacancy-count` must stay the unavailability document,
    not be read as a district whose code is "vacancy-count"."""
    r = client.get("/api/demand/districts/vacancy-count")
    assert r.status_code == 200
    assert r.json()["data"] is None
    assert r.json()["meta"]["reason_code"] == "NOT_AVAILABLE"
    assert client.get("/api/demand/districts/532").json()["data"]


def test_openapi_generates_and_declares_no_blocked_capability_as_data(client):
    spec = client.get("/openapi.json").json()
    assert len(spec["paths"]) == 30
    text = json.dumps(spec).lower()
    for banned in ("hybrid", "potential_pressure", "quadrant"):
        assert banned not in text, banned


def test_malformed_input_fails_safely_without_leaking(client):
    for path, params in (
        ("/api/demand/districts", {"state": "27' OR 1=1--"}),
        ("/api/demand/districts/27%27%20OR%201%3D1", None),
        ("/api/demand/national/occupation-composition", {"confidence": "VERY_HIGH"}),
        ("/api/context/labour-force", {"indicator": "BOGUS"}),
        ("/api/demand/districts", {"state": "2" * 5000}),
        ("/api/export/..%2F..%2Fetc%2Fpasswd.json", None),
    ):
        r = client.get(path, params=params or {})
        assert r.status_code in (404, 422), (path, r.status_code)
        low = r.text.lower()
        for leak in ("traceback", "duckdb", "select ", "binder error", "/users/"):
            assert leak not in low, (path, leak)


def test_no_global_as_of_date_in_any_rendered_surface():
    """The five vintages span fourteen years; no single date may describe them."""
    js = (STATIC / "app.js").read_text()
    html = (STATIC / "index.html").read_text()
    en = json.loads((I18N / "en.json").read_text())
    for surface in (js, html):
        for banned in ("data as of", "real-time", "updated just now"):
            assert banned.lower() not in surface.lower(), banned
    # the only permitted use is the methodology page NEGATING it
    assert "No single" in en["methodology.vintagesBody"]
    assert "data as of" in en["methodology.vintagesBody"]
    assert "no trend may be drawn" in en["methodology.vintagesBody"]


# ===========================================================================
# Readability pass - the panel contract. The complaint these pin was that a
# table arrived with no statement of what it was, so a reader met the numbers
# first and had to reverse-engineer the meaning. The contract is now: every
# table is introduced, in a fixed order, by the single helper that renders it.
# ===========================================================================

def test_navigation_is_a_single_vertical_rail_on_the_left():
    html = (STATIC / "index.html").read_text()
    css = (STATIC / "styles.css").read_text()
    assert 'class="side"' in html or 'class="side" ' in html
    assert 'aria-label="Main navigation"' in html
    # the rail is a column, and it is the first grid track
    assert "grid-template-columns:var(--rail)" in css
    assert "flex-direction:column" in css
    # it collapses rather than disappearing on a phone
    assert ".side-toggle" in css and 'id="side-toggle"' in html
    assert 'aria-expanded' in html


def test_panel_renders_explanation_before_the_table():
    """Order is the whole point: title, one-line description, reading notes,
    evidence strip, qualifiers, then the figures."""
    js = (STATIC / "app.js").read_text()
    body = js[js.index("function panel(o)"):js.index("function noMatch")]
    for frag in ("panel-title", "o.explain + '.what'", "points(o.explain + '.points')",
                 "strip(o.meta)", "o.qualifiers", "o.body"):
        assert frag in body, frag
    # the description and the notes must precede the figures in the template
    assert body.index(".what") < body.index("o.body")
    assert body.index(".points") < body.index("o.body")
    assert body.index("o.qualifiers") < body.index("o.body")


def test_every_panel_explanation_referenced_by_the_ui_exists_in_english():
    """A missing key would render the key name, or an empty header."""
    import re
    js = (STATIC / "app.js").read_text()
    en = json.loads((I18N / "en.json").read_text())
    keys = set(re.findall(r"explain:\s*'([a-zA-Z.]+)'", js))
    keys |= set(re.findall(r"t\('(explain\.[a-zA-Z.]+)\.what'\)", js))
    assert len(keys) >= 12, sorted(keys)
    for k in sorted(keys):
        assert isinstance(en.get(f"{k}.what"), str) and en[f"{k}.what"], k
        pts = en.get(f"{k}.points")
        assert isinstance(pts, list), k
        assert 2 <= len(pts) <= 3, (k, len(pts))
        assert all(isinstance(x, str) and x.strip() for x in pts), k


def test_reading_notes_are_marked_by_shape_not_only_wording():
    """A caution point is prefixed '!' in the catalogue and gets its own marker,
    so the distinction survives for a reader who cannot rely on colour."""
    js = (STATIC / "app.js").read_text()
    css = (STATIC / "styles.css").read_text()
    en = json.loads((I18N / "en.json").read_text())
    assert "raw.startsWith('!')" in js
    assert ".points li.warn::before" in css
    warned = [k for k, v in en.items()
              if isinstance(v, list) and any(x.startswith("!") for x in v)]
    assert len(warned) >= 8, warned


def test_a_relative_signal_bar_has_a_track_and_no_unit_axis():
    js = (STATIC / "app.js").read_text()
    css = (STATIC / "styles.css").read_text()
    assert 'class="track"' in js and ".track{" in css
    assert "legend.bar" in js
    en = json.loads((I18N / "en.json").read_text())
    assert "no unit" in en["legend.bar"]
    assert "not a quantity" in en["legend.rank"]


def test_every_page_states_what_it_is_before_any_figure():
    js = (STATIC / "app.js").read_text()
    en = json.loads((I18N / "en.json").read_text())
    assert "function pageHead" in js
    for page in ("national", "state", "district", "occupation",
                 "methodology", "coverage"):
        assert isinstance(en.get(f"{page}.lede"), str) and en[f"{page}.lede"], page
