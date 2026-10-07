"""Contract tests for the Step 2.0 observed fact tables.

These assert the things that would be invisible if they broke: that estimation
cannot arrive unlabelled, that missing values stay missing, that units are
explicit, and that the two NCS marginal tables are not silently joinable.
"""
import pandas as pd
import pytest

from lmis.common.paths import standardized_path

OBSERVED = {"OBSERVED", "OBSERVED_SURVEY_ESTIMATE"}


@pytest.fixture(scope="module")
def by_state():
    return pd.read_parquet(standardized_path("fact_vacancy_official_by_state"))


@pytest.fixture(scope="module")
def by_sector():
    return pd.read_parquet(standardized_path("fact_vacancy_official_by_sector"))


@pytest.fixture(scope="module")
def est():
    return pd.read_parquet(standardized_path("fact_establishment_district"))


@pytest.fixture(scope="module")
def plfs():
    return pd.read_parquet(standardized_path("fact_labour_force_estimate"))


# ---------------------------------------------------------------- NCS vacancies

def test_state_rows_reconcile_to_the_published_grand_total(by_state):
    """The published answer states 35,275,833 vacancies as on 2024-11-15. Our
    rows must sum to exactly that - the arithmetic check that proves the
    extraction is faithful."""
    snap = by_state[by_state.snapshot_file == "RS_UQ2798_2024-12-19.pdf"]
    assert int(snap.vacancies_cumulative.sum()) == 35_275_833


def test_pan_india_residual_is_flagged_and_has_no_geography(by_state):
    pan = by_state[by_state.is_pan_india_residual]
    assert len(pan) > 0
    assert pan.lgd_code.isna().all(), "PAN-India rows must carry no district/state code"
    assert set(pan.geo_level) == {"NATIONAL"}


def test_state_attributable_share_is_reported_not_redistributed(by_state):
    """41.9% state-attributable. If someone 'fixes' coverage by spreading the
    residual across states, this test fails."""
    snap = by_state[by_state.snapshot_file == "RS_UQ2798_2024-12-19.pdf"]
    total = snap.vacancies_cumulative.sum()
    attributable = snap[~snap.is_pan_india_residual].vacancies_cumulative.sum()
    assert 0.41 < attributable / total < 0.43


def test_every_state_name_resolves_to_an_lgd_code(by_state):
    """Aliases cover the 2019 Dadra/Daman merger, so nothing should be unresolved."""
    unresolved = by_state[~by_state.is_pan_india_residual & by_state.lgd_code.isna()]
    assert len(unresolved) == 0, unresolved.state_name_as_source.unique().tolist()


def test_measure_basis_records_that_this_is_a_stock(by_state, by_sector):
    assert set(by_state.measure_basis) == {"CUMULATIVE_SINCE_INCEPTION"}
    assert set(by_sector.measure_basis) == {"CUMULATIVE_SINCE_INCEPTION"}


def test_sector_units_are_lakh_and_not_silently_converted(by_sector):
    assert set(by_sector.unit) == {"lakh"}


def test_state_and_sector_tables_share_no_joinable_key(by_state, by_sector):
    """They are independent MARGINAL tables. If a future change gives them a
    common dimension beyond the snapshot date, a joint cross-tab becomes
    temptingly derivable - and it would be fabricated."""
    shared = (set(by_state.columns) & set(by_sector.columns)) - {
        "snapshot_date", "unit", "measure_basis", "observed_or_estimated",
        "source_id", "snapshot_file", "ingested_at", "vacancies_cumulative",
    }
    assert shared == set(), f"unexpected shared dimension(s): {shared}"


def test_sector_not_specified_stays_unmapped(by_sector):
    row = by_sector[by_sector.ncs_sector_name == "Sector Not Specified"]
    assert len(row) > 0
    assert row.nic_section_code.isna().all()


# ------------------------------------------------------------ Udyam / districts

def test_establishment_rows_key_to_the_lgd_spine(est):
    lm = pd.read_parquet(standardized_path("location_master"))
    districts = set(lm[lm.level == "DISTRICT"].lgd_code)
    assert set(est.lgd_code) <= districts


def test_na_becomes_null_never_zero(est):
    """The source writes 'NA' in small/medium for some districts. Those rows must
    be NULL. A zero would silently assert 'no medium enterprises here'."""
    assert est.enterprise_count.isna().sum() == 352
    missing = est[est.enterprise_count.isna()]
    assert set(missing.size_class) <= {"SMALL", "MEDIUM"}


def test_establishments_are_not_labelled_as_demand(est):
    assert set(est.measure_basis) == {"CUMULATIVE_REGISTRATIONS"}
    assert "demand" not in " ".join(est.columns).lower()


def test_both_enterprise_categories_present(est):
    assert set(est.enterprise_category) == {"TOTAL", "SERVICES"}


# ----------------------------------------------------------------------- PLFS

def test_plfs_is_national_only(plfs):
    """District- or state-level PLFS rows would be a statistically invalid claim."""
    assert set(plfs.geo_level) == {"NATIONAL"}
    assert plfs.lgd_code.isna().all()


def test_plfs_grain_is_complete(plfs):
    """3 indicators x 3 areas x 3 age groups x 3 sexes = 81."""
    assert len(plfs) == 81
    assert set(plfs.indicator) == {"LFPR", "WPR", "UR"}
    assert set(plfs.area) == {"RURAL", "URBAN", "RURAL_URBAN"}
    assert plfs.groupby(["indicator", "area", "age_group", "sex"]).size().max() == 1


@pytest.mark.parametrize(
    "indicator,area,age,sex,expected",
    [
        ("LFPR", "RURAL", "15-29 years", "MALE", 63.5),
        ("LFPR", "RURAL_URBAN", "15 years and above", "PERSON", 55.6),
        ("WPR", "RURAL_URBAN", "15 years and above", "PERSON", 52.8),
        ("WPR", "URBAN", "15 years and above", "MALE", 71.0),
        ("UR", "URBAN", "15-29 years", "FEMALE", 23.7),
        ("UR", "RURAL", "all ages", "PERSON", 4.5),
    ],
)
def test_plfs_values_match_the_printed_bulletin(plfs, indicator, area, age, sex, expected):
    """Hard-coded against the April 2025 bulletin as printed. This is the
    manual spot-check gate, encoded so it keeps being checked."""
    row = plfs[
        (plfs.indicator == indicator) & (plfs.area == area)
        & (plfs.age_group == age) & (plfs.sex == sex)
    ]
    assert len(row) == 1
    assert row.value_percent.iloc[0] == pytest.approx(expected)


def test_plfs_std_error_is_null_not_guessed(plfs):
    """The monthly bulletin publishes no per-cell standard errors."""
    assert plfs.std_error.isna().all()


# ------------------------------------------------------------- cross-cutting

@pytest.mark.parametrize(
    "table",
    [
        "fact_vacancy_official_by_state",
        "fact_vacancy_official_by_sector",
        "fact_establishment_district",
        "fact_labour_force_estimate",
    ],
)
def test_every_fact_row_is_labelled_observed(table):
    """Step 2.0 loads OBSERVED rows only. The column exists so that estimated
    rows can never arrive unlabelled later."""
    df = pd.read_parquet(standardized_path(table))
    assert set(df.observed_or_estimated) <= OBSERVED


@pytest.mark.parametrize(
    "table",
    [
        "fact_vacancy_official_by_state",
        "fact_vacancy_official_by_sector",
        "fact_establishment_district",
        "fact_labour_force_estimate",
    ],
)
def test_every_fact_declares_its_unit_and_source(table):
    df = pd.read_parquet(standardized_path(table))
    assert df.unit.notna().all()
    assert df.source_id.notna().all()
    assert df.snapshot_file.notna().all()
