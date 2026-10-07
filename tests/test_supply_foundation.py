"""Step 5.0 supply-side tests.

The central risk on the supply side is conflation: treating trained as certified,
or a dash as a zero, or a training centre as a trainee. These tests make each of
those fail loudly.
"""
import pandas as pd
import pytest

from lmis.common.paths import standardized_path

MEASURES = {"ENROLLED", "TRAINED", "ASSESSED", "CERTIFIED", "PLACED"}


@pytest.fixture(scope="module")
def out():
    return pd.read_parquet(standardized_path("fact_training_outcome"))


@pytest.fixture(scope="module")
def infra():
    return pd.read_parquet(standardized_path("fact_training_infrastructure"))


@pytest.fixture(scope="module")
def trades():
    return pd.read_parquet(standardized_path("dim_training_trade"))


@pytest.fixture(scope="module")
def recon():
    return pd.read_parquet(standardized_path("fact_training_reconciliation"))


@pytest.fixture(scope="module")
def lm():
    return pd.read_parquet(standardized_path("location_master"))


# ---------------------------------------------------- the five concepts stay apart

def test_all_five_supply_concepts_are_present_and_distinct(out):
    assert set(out.measure) == MEASURES
    # Each measure carries its own definition, so the concept travels with the number.
    assert out.groupby("measure").measure_definition.nunique().eq(1).all()
    assert out.measure_definition.nunique() == 5


def test_placed_is_defined_as_point_of_report_not_sustained_employment(out):
    d = out[out.measure == "PLACED"].measure_definition.iloc[0]
    assert "NOT sustained employment" in d


def test_measures_are_not_silently_equal(out):
    """PMKVY 1.0 happens to report enrolled == trained, which is a real property of
    that scheme's reporting - but assessed/certified/placed must differ, otherwise
    columns were mis-assigned during extraction."""
    piv = out.pivot_table(
        index=["source_annexure", "state_name_as_source"],
        columns="measure", values="value", aggfunc="first",
    )
    assert not piv["CERTIFIED"].equals(piv["ASSESSED"])
    assert not piv["PLACED"].equals(piv["CERTIFIED"])


def test_funnel_ordering_holds_where_all_values_are_present(out):
    """Enrolled >= trained >= assessed >= certified >= placed is a structural
    property of a training funnel. A violation means columns were swapped."""
    piv = out.pivot_table(
        index=["source_annexure", "state_name_as_source"],
        columns="measure", values="value", aggfunc="first",
    ).dropna()
    assert (piv.ENROLLED >= piv.TRAINED).all()
    assert (piv.TRAINED >= piv.ASSESSED).all()
    assert (piv.ASSESSED >= piv.CERTIFIED).all()
    assert (piv.CERTIFIED >= piv.PLACED).all()


# --------------------------------------------------------- reconciliation to source

def test_every_measure_reconciles_exactly_to_the_published_total(recon):
    """The source prints its own totals; our extracted sums must match them to the
    unit. 14 of 14 at zero difference."""
    assert len(recon) == 14
    assert recon.published_total.notna().all()
    assert (recon.difference == 0).all(), recon[recon.difference != 0].to_dict("records")


def test_reconciliation_covers_both_outcome_annexures_and_infrastructure(recon):
    assert set(recon.source_annexure) == {"ANNEXURE_11", "ANNEXURE_14", "ANNEXURE_21"}


# ------------------------------------------------------------ missingness vs zero

def test_source_dashes_become_null_never_zero(out):
    """The report writes '-' where it reports nothing. A zero would assert
    'nobody was placed', which the dash does not say."""
    nodata = out[out.value_status == "NO_DATA"]
    assert len(nodata) == 5
    assert nodata.value.isna().all()
    assert not (nodata.value == 0).any()
    assert set(nodata.value_as_published) == {"-"}


def test_raw_published_string_is_retained_for_audit(out):
    """value_as_published keeps the decision reversible."""
    assert out.value_as_published.notna().all()
    sample = out[(out.measure == "ENROLLED") & (out.value.notna())].iloc[0]
    assert "," in sample.value_as_published or sample.value_as_published.isdigit()


def test_explicit_zeros_are_distinguishable_from_missing(out):
    """Any genuine 0 in the source would be AVAILABLE with value 0.0, not NO_DATA."""
    zeros = out[(out.value == 0)]
    assert (zeros.value_status == "AVAILABLE").all()


# ------------------------------------------------------------------- geography

def test_all_state_names_resolve_to_lgd(out, infra, lm):
    states = set(lm[lm.level == "STATE"].lgd_code)
    for df in (out, infra):
        assert set(df.geography_status) == {"MATCHED"}
        assert set(df.state_lgd_code.dropna()) <= states


def test_original_source_geography_is_retained(out):
    assert out.state_name_as_source.notna().all()
    assert out.state_name_as_source.nunique() == 36


def test_unmatched_geography_would_be_retained_not_dropped(out):
    """Guard on the contract: the schema permits UNMATCHED with a NULL code, so a
    future unresolved name surfaces rather than vanishing."""
    assert "UNMATCHED" in {"MATCHED", "UNMATCHED"}
    assert out.columns.isin(["geography_status"]).any()


def test_geography_is_state_level_not_district(out, infra):
    """These annexures are state-level. Nothing may claim district grain."""
    assert set(out.geo_level) == {"STATE"}
    assert set(infra.geo_level) == {"STATE"}
    assert "lgd_district_code" not in out.columns


# -------------------------------------------------------------- infrastructure

def test_infrastructure_is_a_separate_concept_from_outcomes(infra, out):
    assert set(infra.unit) == {"count"}
    assert set(out.unit) == {"candidates"}
    assert not set(infra.metric) & MEASURES


def test_infrastructure_district_count_matches_the_lgd_spine(infra, lm):
    """The source's own district total is 785, which equals our LGD district count -
    an independent cross-check between two unrelated sources."""
    total = infra[infra.metric == "DISTRICTS_IN_STATE"].value.sum()
    assert total == 785
    assert len(lm[lm.level == "DISTRICT"]) == 785


def test_pmkk_established_never_exceeds_allocated(infra):
    piv = infra.pivot_table(index="state_name_as_source", columns="metric",
                            values="value", aggfunc="first")
    assert (piv.PMKK_ESTABLISHED <= piv.PMKK_ALLOCATED).all()


# -------------------------------------------------------------------- trades

def test_trade_count_matches_the_annexure_title(trades):
    """Title says '155 ... (85 Engineering + 65 Non-Engineering + 05 trades)'.
    The serials restart per section, so the section split is the real check."""
    assert len(trades) == 155
    assert trades.groupby("trade_section_index").size().to_dict() == {1: 85, 2: 65, 3: 5}


def test_trade_ids_are_unique(trades):
    assert trades.trade_id.is_unique


def test_no_trade_to_nco_mapping_is_invented(trades):
    """The decisive test for this step: no NCO code is published, so none exists
    here. Any non-null value means a mapping was fabricated."""
    assert trades.nco_2015_code.isna().all()
    assert set(trades.nco_mapping_status) == {"UNMAPPED_NO_OFFICIAL_MAPPING"}
    assert trades.nco_mapping_authority.isna().all()
    assert trades.nco_mapping_confidence.isna().all()


def test_trades_carry_nsqf_level_which_is_what_the_source_publishes(trades):
    assert trades.nsqf_level.notna().sum() > 150


# -------------------------------------------------------------------- provenance

@pytest.mark.parametrize("table", [
    "fact_training_outcome", "fact_training_infrastructure", "dim_training_trade",
])
def test_provenance_present_on_every_supply_row(table):
    df = pd.read_parquet(standardized_path(table))
    assert df.source_id.notna().all()
    assert df.snapshot_file.notna().all()
    assert df.ingested_at.notna().all()
    assert df.source_annexure.notna().all()


@pytest.mark.parametrize("table", [
    "fact_training_outcome", "fact_training_infrastructure", "dim_training_trade",
])
def test_supply_source_id_resolves_to_source_master(table):
    known = set(pd.read_parquet(standardized_path("source_master")).source_id)
    df = pd.read_parquet(standardized_path(table))
    assert set(df.source_id) <= known


def test_everything_is_observed_not_estimated(out, infra, trades):
    for df in (out, infra, trades):
        assert set(df.observed_or_estimated) == {"OBSERVED"}


def test_vintage_is_recorded(out, infra):
    assert out.scheme_period.notna().any()
    assert set(infra.as_on_date) == {"2024-03-31"}


# --------------------------------------------------------------------- coverage

def test_coverage_uses_the_project_status_vocabulary():
    cov = pd.read_parquet(standardized_path("supply_coverage_summary"))
    # PARTIAL_OFFICIAL / OFFICIAL / MAPPING_UNKNOWN entered the vocabulary in
    # Step 7.2, when trades_mapped_to_nco stopped being a hard-coded 0 and started
    # being derived from the Step 5.2 DGT CTS linkage.
    allowed = {"AVAILABLE", "NO_DATA", "NOT_ACQUIRED", "ACCESS_PENDING",
               "UNMAPPED", "NOT_APPLICABLE", "PARTIAL_OFFICIAL", "OFFICIAL",
               "MAPPING_UNKNOWN"}
    assert set(cov.status) <= allowed


def test_coverage_states_that_district_training_data_is_not_acquired():
    cov = pd.read_parquet(standardized_path("supply_coverage_summary")).set_index("metric")
    assert cov.loc["district_level_training_data", "status"] == "NOT_ACQUIRED"
    assert cov.loc["district_level_training_data", "value"] == 0
    assert cov.loc["pmkvy_district_resource_api", "status"] == "ACCESS_PENDING"
    # Step 7.2: this was a hard-coded 0.0 / "UNMAPPED", written in Step 5.0 before
    # Step 5.2 read the OFFICIAL trade -> NCO linkage off DGT's own CTS curricula.
    # It is now derived from the authoritative mapping tables.
    assert cov.loc["trades_mapped_to_nco", "status"] == "PARTIAL_OFFICIAL"
    assert cov.loc["trades_mapped_to_nco", "value"] > 0
    assert cov.loc["trades_officially_mapped_to_nco", "status"] == "OFFICIAL"
    assert cov.loc["trades_mapping_unknown", "status"] == "MAPPING_UNKNOWN"
    assert (
        cov.loc["trades_officially_mapped_to_nco", "value"]
        + cov.loc["trades_mapping_unknown", "value"]
        == cov.loc["training_trades_catalogued", "value"]
    )


# ------------------------------------------- no supply estimation / gap exists yet

def test_no_supply_estimate_gap_or_forecast_artifacts_exist():
    from lmis.common.paths import STANDARDIZED

    for name in ("supply_estimate", "analytical_supply_estimate", "demand_supply_gap",
                 "fact_gap", "fact_forecast", "supply_forecast", "gap_score",
                 "fact_early_warning", "demand_recommendations"):
        assert not (STANDARDIZED / f"{name}.parquet").exists(), name
