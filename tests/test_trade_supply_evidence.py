"""Step 5.3 trade-level supply evidence tests.

Two regression tests are mandated by the brief and are the most important here:
no state total may be expanded into trade-level values, and no district trade
supply value may exist without source evidence.
"""
import pandas as pd
import pytest

from lmis.common.paths import standardized_path


@pytest.fixture(scope="module")
def tso():
    return pd.read_parquet(standardized_path("fact_training_trade_outcome"))


@pytest.fixture(scope="module")
def recon():
    return pd.read_parquet(standardized_path("fact_trade_supply_reconciliation"))


@pytest.fixture(scope="module")
def evidence():
    return pd.read_parquet(standardized_path("supply_evidence_matrix"))


# --------------------------------------------------- quantitative measure present

def test_rows_carry_an_actual_quantitative_measure(tso):
    """A dataset only qualifies as supply evidence if it contains a quantity."""
    assert len(tso) == 35
    available = tso[tso.value_status == "AVAILABLE"]
    assert len(available) == len(tso)
    assert (available.value > 0).all()
    assert set(tso.unit) == {"candidates"}


def test_all_three_entity_types_present_with_their_measures(tso):
    got = tso.groupby("occupation_entity_type").measure.unique().apply(set).to_dict()
    assert got["TRADE"] == {"APPRENTICES_ENGAGED"}
    assert got["JOB_ROLE"] == {"ENROLLED", "TRAINED_ORIENTED"}
    assert got["SECTOR"] == {"ENROLLED"}


def test_measure_definitions_keep_the_concepts_distinct(tso):
    """apprentices engaged, enrolled and trained/oriented are different concepts
    from different schemes and must not be interchangeable."""
    assert tso.groupby("measure").measure_definition.nunique().eq(1).all()
    assert tso.measure_definition.nunique() == 3
    appr = tso[tso.measure == "APPRENTICES_ENGAGED"].measure_definition.iloc[0]
    assert "not training completion" in appr


def test_schemes_are_not_mixed_within_a_source_table(tso):
    assert tso.groupby("source_table").scheme.nunique().eq(1).all()
    assert set(tso.scheme) == {"NAPS_APPRENTICESHIP", "PMKVY_4.0"}


# ------------------------------------------------------------- grain integrity

def test_grain_is_national_only(tso):
    """These tables have no state or district dimension, and none is manufactured."""
    assert set(tso.geo_level) == {"NATIONAL"}
    for col in tso.columns:
        assert "district" not in col.lower()
        assert "lgd" not in col.lower()
        assert "state" not in col.lower()


def test_keys_are_unique(tso):
    assert not tso.duplicated(["source_table", "entity_name_as_source", "measure"]).any()


def test_top_n_subset_is_flagged_on_every_row(tso):
    """Rows do NOT sum to the population, so no share or denominator may be
    derived. The flag must be present and true everywhere."""
    assert tso.is_top_n_subset.all()


def test_published_rank_is_preserved(tso):
    for (table, measure), grp in tso.groupby(["source_table", "measure"]):
        ranks = sorted(grp.published_rank)
        assert ranks == list(range(1, len(ranks) + 1)), (table, measure)


# ------------------------------------------------------------ reconciliation

def test_apprenticeship_top_ten_matches_its_printed_subtotal(recon):
    """Table-5.54 prints a Grand Total that equals the sum of its ten displayed
    rows - a subtotal of the top ten, not a population total. It must match
    exactly, proving the extraction is faithful."""
    row = recon[(recon.source_table == "TABLE_5_54")].iloc[0]
    assert row.published_grand_total == 1_047_299
    assert row.top_n_extracted_sum == 1_047_299
    assert row.top_n_shortfall == 0


def test_tables_without_a_printed_total_report_null_not_zero(recon):
    """Tables 5.9 and 5.10 print no total. That is NULL, not 0."""
    no_total = recon[recon.source_table.isin(["TABLE_5_9", "TABLE_5_10"])]
    assert len(no_total) == 3
    assert no_total.published_grand_total.isna().all()
    assert no_total.top_n_shortfall.isna().all()


def test_reconciliation_explains_that_shortfall_is_expected(recon):
    assert recon.note.str.contains("Top-N subset").all()


# ------------------------------------------- NCO connected, never newly mapped

def test_nco_is_connected_only_through_existing_official_maps(tso):
    linked = tso[tso.nco_link_status != "NO_EXISTING_OFFICIAL_MAP"]
    assert set(linked.nco_link_status) <= {
        "OFFICIAL_VIA_MAP_TRADE_TO_NCO",
        "OFFICIAL_VIA_MAP_QUALIFICATION_TO_NCO",
    }
    assert set(linked.nco_link_method) == {"EXACT_NAME_AGAINST_EXISTING_OFFICIAL_MAP"}


def test_linked_entities_are_exactly_the_three_expected(tso):
    linked = set(
        tso[tso.nco_link_status != "NO_EXISTING_OFFICIAL_MAP"].entity_name_as_source
    )
    assert linked == {"Electrician", "Fitter", "Domestic Data Entry Operator"}


def test_linked_codes_match_the_existing_official_mapping_tables(tso):
    tmap = pd.read_parquet(standardized_path("map_trade_to_nco"))
    qmap = pd.read_parquet(standardized_path("map_qualification_to_nco"))
    official_trade = set(tmap.nco_codes_for_trade)
    official_qual = set(qmap.nco_2015_code)
    for _, r in tso[tso.nco_link_status == "OFFICIAL_VIA_MAP_TRADE_TO_NCO"].iterrows():
        assert r.nco_codes_via_existing_map in official_trade
    for _, r in tso[
        tso.nco_link_status == "OFFICIAL_VIA_MAP_QUALIFICATION_TO_NCO"
    ].iterrows():
        assert r.nco_codes_via_existing_map in official_qual


def test_unlinked_entities_carry_no_nco_code(tso):
    unlinked = tso[tso.nco_link_status == "NO_EXISTING_OFFICIAL_MAP"]
    assert unlinked.nco_codes_via_existing_map.isna().all()
    assert unlinked.nco_link_method.isna().all()


def test_no_new_mapping_system_was_created(tso):
    """Step 5.3 connects to the existing maps; it must not invent mapping columns
    of its own such as a confidence or authority field."""
    assert "mapping_confidence" not in tso.columns
    assert "mapping_authority" not in tso.columns


# ================= THE TWO MANDATED REGRESSION TESTS =================

def test_no_state_total_is_expanded_into_trade_level_values(tso):
    """NO STATE-LEVEL TOTAL MAY BE EXPANDED INTO TRADE-LEVEL VALUES WITHOUT AN
    EXPLICIT SOURCE TRADE DIMENSION.

    Proven two ways:
      1. Every trade-level row is NATIONAL. There is no state dimension at all,
         so no state total could have been distributed.
      2. The state-level supply table (fact_training_outcome, 350 rows) and this
         trade-level table share no joinable dimension, so a cross-product is not
         constructible.
    """
    assert set(tso.geo_level) == {"NATIONAL"}
    state_level = pd.read_parquet(standardized_path("fact_training_outcome"))
    assert set(state_level.geo_level) == {"STATE"}
    shared = (set(state_level.columns) & set(tso.columns)) - {
        "scheme", "measure", "measure_definition", "value_as_published", "value",
        "unit", "value_status", "observed_or_estimated", "source_id",
        "snapshot_file", "ingested_at", "geo_level",
    }
    assert shared == set(), f"unexpected shared dimension(s): {shared}"
    # And the state table still has no trade dimension to receive an expansion.
    for col in state_level.columns:
        assert "trade" not in col.lower()
        assert "job_role" not in col.lower()


def test_no_district_trade_supply_value_exists_without_source_evidence():
    """NO DISTRICT TRADE SUPPLY VALUE MAY EXIST WITHOUT SOURCE EVIDENCE.

    No official source provides district x trade supply, so no such table or
    column may exist anywhere in the standardized layer.
    """
    from lmis.common.paths import STANDARDIZED

    for name in ("fact_training_trade_district", "supply_district_trade",
                 "fact_district_trade_outcome", "supply_district_allocation",
                 "fact_training_outcome_by_district"):
        assert not (STANDARDIZED / f"{name}.parquet").exists(), name

    # And no existing supply table may carry district AND trade together.
    for table in ("fact_training_outcome", "fact_training_infrastructure",
                  "fact_training_trade_outcome"):
        cols = {c.lower() for c in pd.read_parquet(standardized_path(table)).columns}
        has_district = any("district" in c or "lgd" in c for c in cols)
        has_trade = any(("trade" in c or "job_role" in c or "nco" in c) for c in cols)
        assert not (has_district and has_trade), table


# -------------------------------------------------------- evidence matrix

def test_evidence_matrix_has_a_trade_supply_blocker_section(evidence):
    assert "C_TRADE_LEVEL_SUPPLY" in set(evidence.blocker)
    c = evidence[evidence.blocker == "C_TRADE_LEVEL_SUPPLY"]
    assert len(c) == 7
    assert c.reason.notna().all()
    assert (c.reason.str.len() > 40).all()


def test_institute_count_is_rejected_as_supply(evidence):
    """Counting institutes offering a course is not trainee supply, and the matrix
    must say so."""
    row = evidence[evidence.resource.str.contains("Drone")]
    assert len(row) == 1
    assert row.iloc[0].decision == "REJECTED"
    assert "not trainee supply" in row.iloc[0].reason


def test_state_marginal_table_is_rejected_for_state_times_trade(evidence):
    row = evidence[evidence.resource.str.contains("Top Ten States")]
    assert len(row) == 1
    assert row.iloc[0].decision == "REJECTED"
    assert "MARGINAL" in row.iloc[0].reason


def test_nqr_metadata_is_rejected_as_supply_evidence(evidence):
    row = evidence[(evidence.blocker == "C_TRADE_LEVEL_SUPPLY") & (evidence.source == "NQR")]
    assert len(row) == 1
    assert row.iloc[0].decision == "REJECTED"
    assert "taxonomy evidence, not" in row.iloc[0].reason


# -------------------------------------------------------------- provenance

def test_provenance_on_every_row(tso):
    for col in ("source_id", "snapshot_file", "source_table", "source_table_title",
                "period_label", "ingested_at"):
        assert tso[col].notna().all(), col


def test_source_resolves_to_source_master(tso):
    known = set(pd.read_parquet(standardized_path("source_master")).source_id)
    assert set(tso.source_id) <= known


def test_everything_is_observed(tso):
    assert set(tso.observed_or_estimated) == {"OBSERVED"}


# ------------------------------------------- no step 6 artifacts

def test_no_gap_or_forecast_artifacts_exist():
    from lmis.common.paths import STANDARDIZED

    for name in ("demand_supply_gap", "fact_gap", "gap_score", "fact_forecast",
                 "supply_forecast", "fact_early_warning", "demand_recommendations",
                 "analytical_supply_estimate"):
        assert not (STANDARDIZED / f"{name}.parquet").exists(), name
