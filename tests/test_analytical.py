"""Contract tests for the Step 3.0 analytical layer.

The theme is the same as Step 2.0: assert the things whose failure would be
silent. Nothing here may be ESTIMATED, no missing value may become zero, no
historical structure may be relabelled as demand, and every analytical row must
still be traceable to a registered source and a stated vintage.
"""
import pandas as pd
import pytest

from lmis.common.paths import standardized_path

ANALYTICAL = [
    "analytical_state_demand",
    "analytical_demand_by_industry",
    "analytical_district_structure",
    "analytical_district_occupation_structure",
    "analytical_labour_market_context",
]


def load(name):
    return pd.read_parquet(standardized_path(name))


@pytest.fixture(scope="module")
def sd():
    return load("analytical_state_demand")


@pytest.fixture(scope="module")
def di():
    return load("analytical_demand_by_industry")


@pytest.fixture(scope="module")
def ds():
    return load("analytical_district_structure")


@pytest.fixture(scope="module")
def dos():
    return load("analytical_district_occupation_structure")


@pytest.fixture(scope="module")
def lmc():
    return load("analytical_labour_market_context")


# ------------------------------------------------------- nothing is ESTIMATED

@pytest.mark.parametrize("table", ANALYTICAL)
def test_no_estimated_rows_exist_yet(table):
    """Step 3.0 must not produce estimates. If 'ESTIMATED' appears here, the
    demand-estimation step has leaked into the analytical layer."""
    df = load(table)
    assert set(df.observation_status) <= {"OBSERVED", "SUPPORTING"}


@pytest.mark.parametrize("table", ANALYTICAL)
def test_every_analytical_row_carries_source_and_vintage(table):
    df = load(table)
    assert df.source_vintage.notna().all()
    assert df.transformation.notna().all()
    assert df.source_id.notna().all()


@pytest.mark.parametrize("table", ANALYTICAL)
def test_source_ids_resolve_to_source_master(table):
    known = set(load("source_master").source_id)
    df = load(table)
    assert set(df.source_id) <= known


# ----------------------------------------------------------------- state demand

def test_state_demand_keys_are_unique(sd):
    assert not sd.duplicated(["snapshot_date", "state_name_as_source"]).any()


def test_state_demand_deduplicates_three_identical_documents(sd):
    """114 fact rows -> 38 analytical rows, each corroborated by 3 documents."""
    assert len(sd) == 38
    assert set(sd.n_source_documents) == {3}


def test_state_demand_reconciles_to_published_total(sd):
    assert int(sd.vacancies_cumulative.sum()) == 35_275_833


def test_flow_is_explicitly_unavailable_with_a_reason(sd):
    """A single as-on date cannot yield a flow. The table must say so rather than
    leave a consumer to assume monthly demand."""
    assert (~sd.flow_available).all()
    assert sd.flow_unavailable_reason.notna().all()
    assert sd.snapshot_date.nunique() == 1


def test_pan_india_residual_stays_national_and_unallocated(sd):
    pan = sd[sd.is_pan_india_residual]
    assert len(pan) == 1
    assert set(pan.geo_level) == {"NATIONAL"}
    assert pan.lgd_code.isna().all()
    # The residual has no state-attributable share by definition.
    assert pan.share_of_state_attributable.isna().all()


def test_state_shares_sum_to_one_within_each_denominator(sd):
    assert sd.share_of_published_total.sum() == pytest.approx(1.0)
    assert sd[~sd.is_pan_india_residual].share_of_state_attributable.sum() == pytest.approx(1.0)


def test_state_demand_lgd_codes_are_real(sd):
    lm = load("location_master")
    states = set(lm[lm.level == "STATE"].lgd_code)
    present = sd[sd.lgd_code.notna()].lgd_code
    assert set(present) <= states


def test_state_demand_carries_no_occupation_dimension(sd):
    assert set(sd.occupation_level) == {"NONE"}


# -------------------------------------------------------------- industry demand

def test_industry_demand_keys_are_unique(di):
    assert not di.duplicated(["snapshot_date", "ncs_sector_name"]).any()


def test_industry_table_has_no_occupation_dimension(di):
    """NCS sectors are INDUSTRY (NIC-2008 sections). Attaching an occupation here
    would assert a many-to-many relationship as if it were a function."""
    assert set(di.occupation_level) == {"NONE"}


def test_nic_sections_are_real(di):
    nic = set(load("nic_section_master").section_code)
    assert set(di[di.nic_section_code.notna()].nic_section_code) <= nic


def test_heterogeneous_and_residual_sectors_are_flagged(di):
    flagged = set(di[di.is_heterogeneous_or_residual].ncs_sector_name)
    for name in (
        "Sector Not Specified",
        "Operations and Support",
        "Other Service Activities",
        "Specialized Professional Services",
    ):
        assert name in flagged, name


def test_unmapped_sector_has_null_section_and_is_flagged(di):
    row = di[di.ncs_sector_name == "Sector Not Specified"]
    assert len(row) == 1
    assert row.nic_section_code.isna().all()
    assert bool(row.is_heterogeneous_or_residual.iloc[0])


def test_industry_units_remain_lakh(di):
    assert set(di.unit) == {"lakh"}


# ------------------------------------------------------------ district structure

def test_district_structure_keys_are_unique(ds):
    assert not ds.duplicated(["snapshot_date", "lgd_code", "enterprise_category"]).any()


def test_district_structure_lgd_codes_are_real(ds):
    lm = load("location_master")
    assert set(ds.lgd_code) <= set(lm[lm.level == "DISTRICT"].lgd_code)


def test_udyam_is_never_labelled_demand(ds):
    assert ds.not_a_demand_measure.all()
    assert set(ds.observation_status) == {"SUPPORTING"}
    assert set(ds.measure_basis) == {"CUMULATIVE_REGISTRATIONS"}


def test_district_shares_sum_to_one_within_state(ds):
    for cat, grp in ds.groupby("enterprise_category"):
        s = grp.groupby("state_lgd_code").enterprise_share_within_state.sum()
        assert s.round(6).eq(1.0).all(), cat


def test_missing_counts_do_not_become_zero_shares(ds):
    """A NULL 'medium' count must give a NULL share, never 0.0 - a zero would
    assert 'no medium enterprises here', which the source never says."""
    assert ds.medium.isna().sum() > 0
    assert (ds[ds.medium.isna()].medium_share_of_district.isna()).all()
    assert not (ds[ds.medium.isna()].medium_share_of_district == 0).any()


def test_district_structure_preserves_2023_vintage(ds):
    assert set(ds.source_vintage) == {"2023-12-21"}


# -------------------------------------------------- district occupation structure

def test_occupation_structure_excludes_totals_to_avoid_double_counting(dos):
    """Only division totals and the unclassified bucket are kept. Including the
    all-occupations TOTAL row or sub-divisions would double-count."""
    assert set(dos.row_type) == {"DIVISION_TOTAL", "UNCLASSIFIED"}


def test_occupation_shares_sum_to_one_per_district_cell(dos):
    """Shares must sum to 1 within every district x area x sex cell, EXCEPT where
    the cell's own total is zero - fully urban districts (e.g. Mumbai City and
    Mumbai Suburban) have no rural workers at all. There 0/0 must stay NaN, which
    is 'unknown share', not 0.0."""
    keys = ["census_state_code", "census_district_code", "area", "sex"]
    totals = dos.groupby(keys).district_total_main_workers.max()
    shares = dos.groupby(keys).occupation_share_of_district.sum()
    nonzero = totals[totals > 0].index
    assert shares.loc[nonzero].round(6).eq(1.0).all()
    # Zero-total cells must be entirely NaN, never zero-filled.
    zero = totals[totals == 0].index
    if len(zero):
        rows = dos.set_index(keys).loc[zero]
        assert rows.occupation_share_of_district.isna().all()


def test_zero_total_cells_are_fully_urban_districts(dos):
    """Sanity-check the exception above against reality rather than assuming it."""
    keys = ["census_state_code", "census_district_code", "area", "sex"]
    totals = dos.groupby(keys).district_total_main_workers.max()
    zero = totals[totals == 0]
    assert len(zero) > 0
    # every zero-total cell is a RURAL cell
    assert {idx[2] for idx in zero.index} == {"RURAL"}


def test_occupation_structure_is_marked_historical_and_not_demand(dos):
    assert dos.is_historical.all()
    assert dos.not_a_demand_measure.all()
    assert set(dos.observation_status) == {"SUPPORTING"}
    assert set(dos.source_vintage) == {"2011 (Census)"}


def test_occupation_scheme_is_nco_2004_not_2015(dos):
    assert set(dos.occupation_scheme) == {"NCO_2004"}


def test_unclassified_division_is_not_forced_into_an_nco2015_division(dos):
    x = dos[dos.nco_2004_division == "X"]
    assert len(x) > 0
    assert x.nco_2015_division.isna().all()


def test_division_crosswalk_confidence_is_measured_not_assumed():
    """Purity is computed from the official concordance. If every confidence were
    1.0 it would mean the measurement was skipped."""
    dm = load("map_nco2004_division_to_nco2015_division")
    mapped = dm[dm.nco_2015_division.notna()]
    assert len(mapped) == 9
    assert mapped.confidence.between(0, 1).all()
    assert (mapped.confidence < 1.0).any(), "purity should not be uniformly perfect"
    assert (mapped.n_concorded_codes > 0).all()
    assert set(dm.authority) == {"PROJECT_DERIVED_FROM_OFFICIAL"}


def test_census_universe_is_recorded(dos):
    """B-24 covers main workers in non-household industry only - shares describe
    that universe, not all workers."""
    assert set(dos.universe) == {"MAIN_WORKERS_NON_HOUSEHOLD_INDUSTRY"}


# ---------------------------------------------------------------- PLFS context

def test_plfs_context_remains_national(lmc):
    assert set(lmc.geo_level) == {"NATIONAL"}
    assert set(lmc.valid_geo_level) == {"NATIONAL"}
    assert not lmc.district_estimates_valid.any()


def test_plfs_context_is_not_demand(lmc):
    assert lmc.not_a_demand_measure.all()
    assert set(lmc.statistical_basis) == {"SAMPLE_SURVEY_CWS"}


def test_plfs_context_applies_no_transformation(lmc):
    assert set(lmc.transformation) == {"NONE_PASSTHROUGH"}


# ------------------------------------------------------------------- catalog

def test_catalog_describes_every_analytical_table():
    cat = load("analytical_dataset_catalog")
    assert set(cat.analytical_table) == set(ANALYTICAL)
    for col in ("grain", "source_tables", "source_vintage", "observation_status",
                "transformations", "limitations"):
        assert cat[col].notna().all(), col


def test_catalog_row_counts_match_the_actual_tables():
    cat = load("analytical_dataset_catalog").set_index("analytical_table")
    for name in ANALYTICAL:
        assert int(cat.loc[name, "row_count"]) == len(load(name)), name


# ------------------------------------- the two NCS marginals stay unjoinable

def test_state_and_industry_analytics_share_no_joinable_dimension(sd, di):
    shared = (set(sd.columns) & set(di.columns)) - {
        "snapshot_date", "unit", "measure_basis", "observation_status",
        "source_id", "source_vintage", "transformation", "vacancies_cumulative",
        "n_source_documents", "source_documents", "share_of_published_total",
        "geo_level", "occupation_level", "industry_level",
    }
    assert shared == set(), f"unexpected shared dimension(s): {shared}"
