"""Step 4.0 invariant tests.

These are the guardrails that stop an estimate from being mistaken for an
observation, stop the PAN-India residual from leaking into a district, and stop
the occupational signal from being counted twice.
"""
import pandas as pd
import pytest

from lmis.common.paths import standardized_path
from lmis.demand.confidence import Confidence

BASELINE = "2024-11-15"


@pytest.fixture(scope="module")
def a():
    return pd.read_parquet(standardized_path("demand_national_occupation_composition"))


@pytest.fixture(scope="module")
def b():
    return pd.read_parquet(standardized_path("demand_district_relative_signal"))


@pytest.fixture(scope="module")
def c():
    return pd.read_parquet(standardized_path("demand_district_occupation_signal"))


@pytest.fixture(scope="module")
def cov():
    return pd.read_parquet(standardized_path("demand_coverage_summary"))


@pytest.fixture(scope="module")
def lm():
    return pd.read_parquet(standardized_path("location_master"))


# ------------------------------------------------------------- baseline / temporal

@pytest.mark.parametrize("table", [
    "demand_national_occupation_composition",
    "demand_district_relative_signal",
    "demand_district_occupation_signal",
])
def test_baseline_period_matches_the_observed_ncs_date(table):
    df = pd.read_parquet(standardized_path(table))
    assert set(df.baseline_period) == {BASELINE}


@pytest.mark.parametrize("table", [
    "demand_national_occupation_composition",
    "demand_district_relative_signal",
    "demand_district_occupation_signal",
])
def test_no_time_series_is_fabricated(table):
    """One observed as-on date means one period. More than one would mean
    interpolation or extrapolation happened."""
    df = pd.read_parquet(standardized_path(table))
    assert df.baseline_period.nunique() == 1
    assert (~df.flow_available).all()
    assert df.flow_unavailable_reason.notna().all()


# -------------------------------------------------------------- observed/estimated

def test_all_three_outputs_are_labelled_estimated(a, b, c):
    assert set(a.observed_or_estimated) == {"ESTIMATED"}
    assert set(b.observed_or_estimated) == {"ESTIMATED"}
    # C additionally carries UNAVAILABLE rows for districts with no prior.
    assert set(c.observed_or_estimated) == {"ESTIMATED", "UNAVAILABLE"}


def test_no_output_claims_to_be_an_observed_vacancy_count(b, c):
    assert set(b.unit) == {"relative_signal_unitless"}
    assert set(c.unit) == {"relative_signal_unitless"}
    assert set(c.interpretation) == {"RELATIVE_RANKING_SIGNAL_NOT_A_VACANCY_COUNT"}


def test_provenance_and_vintage_exist_for_every_estimated_row(a, b, c):
    for df in (a, b, c):
        assert df.source_ids.notna().all()
        assert df.methodology.notna().all()
        assert df.built_at.notna().all()


def test_source_ids_resolve_to_registered_sources(a, b, c):
    known = set(pd.read_parquet(standardized_path("source_master")).source_id)
    for df in (a, b, c):
        for ids in df.source_ids.unique():
            for sid in [s.strip() for s in ids.split(";")]:
                assert sid in known, sid


# ------------------------------------------------------------------- output A

def test_a_is_national_only(a):
    assert set(a.geo_level) == {"NATIONAL"}
    assert "lgd_code" not in a.columns
    assert set(a.industry_level) == {"NIC_SECTION"}
    assert set(a.occupation_level) == {"NCO_2015_DIVISION"}


def test_a_key_is_unique(a):
    assert not a.duplicated(["baseline_period", "nic_section_code", "nco_2015_division"]).any()


def test_a_joins_only_at_validated_nic_section(a):
    """20 NCS sections map to a NIC section and all 20 exist in the ILO cross-tab."""
    nic = set(pd.read_parquet(standardized_path("nic_section_master")).section_code)
    assert set(a.nic_section_code) <= nic
    assert a.nic_section_code.nunique() == 20


def test_a_conditional_shares_sum_to_one_within_each_section(a):
    s = a.groupby("nic_section_code").occupation_conditional_share.sum()
    assert s.round(6).eq(1.0).all()


def test_a_composition_shares_sum_to_one_across_occupations(a):
    comp = a.groupby("nco_2015_division").occupation_share_of_total.first()
    assert comp.sum() == pytest.approx(1.0)


def test_a_excludes_the_unmapped_ncs_sector(a):
    """'Sector Not Specified' carries no industry information, so no occupation
    can be inferred from it. It must not appear."""
    assert "Sector Not Specified" not in set(a.ncs_sector_name)


def test_a_product_equals_its_inputs(a):
    """Arithmetic check: the estimate really is input x share, nothing else."""
    expected = a.vacancies_cumulative * a.occupation_conditional_share
    assert (a.estimated_occupation_demand - expected).abs().max() < 1e-9


# ------------------------------------------------------------------- output B

def test_b_has_no_occupation_dimension(b):
    assert set(b.occupation_level) == {"NONE"}
    assert "nco_2015_division" not in b.columns


def test_b_key_is_unique(b):
    assert not b.duplicated(["baseline_period", "lgd_code"]).any()


def test_b_pan_india_residual_never_reaches_a_district(b):
    """The decisive test: the residual is 20,507,320 vacancies and must not appear
    in any district's input."""
    assert b.pan_india_residual_excluded.all()
    assert (b.observed_state_vacancies != 20_507_320).all()
    sd = pd.read_parquet(standardized_path("analytical_state_demand"))
    attributable = sd[~sd.is_pan_india_residual].vacancies_cumulative.sum()
    # Each state's observed input must come from the attributable pool only.
    per_state = b.groupby("state_lgd_code").observed_state_vacancies.first().sum()
    assert per_state == pytest.approx(attributable)


def test_b_only_contains_real_lgd_districts(b, lm):
    assert set(b.lgd_code) <= set(lm[lm.level == "DISTRICT"].lgd_code)
    assert b.lgd_code.nunique() == 785


def test_b_uses_the_within_state_denominator(b):
    """Udyam shares must be normalised within state, not nationally."""
    s = b.groupby("state_lgd_code").enterprise_share_within_state.sum()
    assert s.round(6).eq(1.0).all()


def test_b_product_equals_its_inputs(b):
    expected = b.observed_state_vacancies * b.enterprise_share_within_state
    assert (b.relative_demand_signal - expected).abs().max() < 1e-6


def test_b_discloses_that_within_state_ranking_is_just_the_udyam_ranking(b):
    """Honesty requirement: inside a state the state multiplier is constant, so
    B's ordering IS the enterprise-share ordering. The caveat must be stored."""
    assert b.within_state_ranking_caveat.notna().all()
    for _, grp in b.groupby("state_lgd_code"):
        if len(grp) > 2:
            by_signal = grp.sort_values("relative_demand_signal", ascending=False).lgd_code.tolist()
            by_share = grp.sort_values("enterprise_share_within_state", ascending=False).lgd_code.tolist()
            assert by_signal == by_share


def test_b_does_not_use_ncs_sector_marginals(b):
    """State demand and sector demand are independent marginals; B must use only
    the state one."""
    assert "nic_section_code" not in b.columns
    assert "ncs_sector_name" not in b.columns


# ------------------------------------------------------------------- output C

def test_c_has_district_and_occupation_dimensions(c):
    assert set(c.geo_level) == {"DISTRICT"}
    assert set(c.occupation_level) == {"NCO_2015_DIVISION"}


def test_c_covers_every_district_in_b(b, c):
    """No district may be silently absent; each gets a status instead."""
    assert set(c.lgd_code) == set(b.lgd_code)


def test_c_prior_status_partitions_all_districts(c):
    counts = c.groupby("occupation_prior_status").lgd_code.nunique().to_dict()
    assert counts == {"AVAILABLE": 138, "CENSUS_NOT_ACQUIRED": 522, "NO_CENSUS_2011_CODE": 125}
    assert sum(counts.values()) == 785


def test_c_signal_exists_only_where_a_census_prior_exists(c):
    avail = c[c.occupation_prior_status == "AVAILABLE"]
    rest = c[c.occupation_prior_status != "AVAILABLE"]
    assert avail.district_occupation_signal.notna().all()
    assert rest.district_occupation_signal.isna().all()


def test_c_never_zero_fills_an_unavailable_district(c):
    """A zero would assert 'no demand for this occupation here'. It must be NULL."""
    rest = c[c.occupation_prior_status != "AVAILABLE"]
    assert not (rest.district_occupation_signal == 0).any()
    assert rest.nco_2015_division.isna().all()
    assert rest.occupation_share_of_district.isna().all()


def test_c_does_not_invent_a_distribution_for_missing_districts(c):
    """Each unavailable district has exactly ONE row stating why - not nine
    fabricated occupation rows."""
    rest = c[c.occupation_prior_status != "AVAILABLE"]
    assert (rest.groupby("lgd_code").size() == 1).all()


def test_c_occupation_shares_sum_to_one_per_available_district(c):
    """Census division shares, excluding the unclassified bucket, plus the
    retained unallocated share, must account for the whole district."""
    avail = c[c.occupation_prior_status == "AVAILABLE"]
    s = avail.groupby("lgd_code").occupation_share_of_district.sum()
    unalloc = avail.groupby("lgd_code").unclassified_share_not_allocated.first()
    assert (s + unalloc).round(6).eq(1.0).all()


def test_c_product_equals_its_inputs(c):
    avail = c[c.occupation_prior_status == "AVAILABLE"]
    expected = avail.relative_demand_signal * avail.occupation_share_of_district
    assert (avail.district_occupation_signal - expected).abs().max() < 1e-6


def test_c_does_not_multiply_by_output_a(a, c):
    """The double-counting guard. C must contain no trace of A's national
    occupation composition as a factor."""
    for col in ("occupation_conditional_share", "occupation_share_of_total",
                "estimated_occupation_demand", "occupation_total_all_sections"):
        assert col not in c.columns
    # And the arithmetic must be exactly B x census share (asserted above), which
    # leaves no room for a third factor.
    avail = c[c.occupation_prior_status == "AVAILABLE"].iloc[0]
    assert avail.district_occupation_signal == pytest.approx(
        avail.relative_demand_signal * avail.occupation_share_of_district
    )


def test_c_retains_the_unclassified_share_instead_of_redistributing_it(c):
    avail = c[c.occupation_prior_status == "AVAILABLE"]
    assert avail.unclassified_share_not_allocated.notna().all()
    assert (avail.unclassified_share_not_allocated > 0).any()


# ------------------------------------------------------------------ confidence

def test_confidence_is_weakest_link_not_an_average(a, b, c):
    """C is LOW on every row because its occupation prior is HISTORICAL. If any C
    row were MEDIUM or HIGH, averaging has crept in."""
    assert set(c.overall_confidence) == {"LOW"}
    assert set(b.overall_confidence) == {"MEDIUM"}
    assert set(a.overall_confidence) <= {"MEDIUM", "LOW"}


def test_low_confidence_in_a_is_driven_by_weak_industry_mapping(a):
    low = a[a.overall_confidence == "LOW"]
    assert (low.mapping_confidence < 0.85).all()
    assert set(low.ncs_sector_name) == {"Operations and Support", "Other Service Activities"}


def test_all_seven_confidence_dimensions_are_stored(a, b, c):
    dims = ["source_confidence", "mapping_confidence", "temporal_confidence",
            "geography_coverage", "occupation_coverage", "statistical_support",
            "transformation_depth", "overall_confidence"]
    for df in (a, b, c):
        for d in dims:
            assert d in df.columns, d


def test_confidence_rejects_an_unknown_vocabulary_value():
    with pytest.raises(ValueError):
        Confidence("OBSERVED", None, "SOMETIME", "DIRECT", "DIRECT", "CENSUS", 0)


def test_no_numeric_probability_is_manufactured(a, b, c):
    """overall_confidence must be ordinal. A float would imply a statistical basis
    we do not have."""
    from pandas.api.types import is_numeric_dtype

    for df in (a, b, c):
        # The point is that it is NOT numeric; the exact string dtype varies by
        # pandas version.
        assert not is_numeric_dtype(df.overall_confidence)
        assert set(df.overall_confidence) <= {"HIGH", "MEDIUM", "LOW"}


# -------------------------------------------------------------------- coverage

def test_coverage_reports_the_pan_india_residual(cov):
    m = dict(zip(cov.metric, cov.value))
    assert m["ncs_vacancies_published_total"] == 35_275_833
    assert m["ncs_vacancies_pan_india_residual"] == 20_507_320
    assert m["ncs_vacancies_state_attributable"] == 14_768_513
    assert m["ncs_state_attributable_share"] == pytest.approx(0.4187, abs=1e-4)


def test_coverage_accounts_for_every_district(cov):
    m = dict(zip(cov.metric, cov.value))
    assert m["districts_with_relative_signal"] == 785
    assert (
        m["districts_with_occupation_signal"]
        + m["districts_census_not_acquired"]
        + m["districts_no_census_2011_code"]
    ) == 785


def test_residual_is_not_silently_discarded(cov):
    m = dict(zip(cov.metric, cov.value))
    assert (
        m["ncs_vacancies_state_attributable"] + m["ncs_vacancies_pan_india_residual"]
        == m["ncs_vacancies_published_total"]
    )


# --------------------------------------------------- nothing beyond demand exists

def test_no_supply_gap_or_forecast_artifacts_exist():
    from lmis.common.paths import STANDARDIZED

    for name in ("demand_supply_gap", "fact_gap", "fact_forecast", "demand_index",
                 "analytical_supply_estimate", "fact_early_warning",
                 "demand_recommendations"):
        assert not (STANDARDIZED / f"{name}.parquet").exists(), name
