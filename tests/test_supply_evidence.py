"""Step 5.1 evidence-resolution tests.

The headline risk in this step is a fabricated mapping. These tests make any
invented trade -> NCO link, or any silent fuzzy match, fail loudly.
"""
import pandas as pd
import pytest

from lmis.common.paths import standardized_path


@pytest.fixture(scope="module")
def qmap():
    return pd.read_parquet(standardized_path("map_qualification_to_nco"))


@pytest.fixture(scope="module")
def trades():
    return pd.read_parquet(standardized_path("dim_training_trade"))


@pytest.fixture(scope="module")
def evidence():
    return pd.read_parquet(standardized_path("supply_evidence_matrix"))


@pytest.fixture(scope="module")
def om():
    return pd.read_parquet(standardized_path("occupation_master"))


# ----------------------------------------- the official qualification -> NCO link

def test_mapping_is_official_not_inferred(qmap):
    assert len(qmap) >= 1
    assert set(qmap.mapping_authority) == {"OFFICIAL"}
    assert (qmap.mapping_confidence == 1.0).all()
    assert set(qmap.mapping_method) == {"QFILE_FIELD_14_ALIGNED_TO_NCO_ISCO_CODE"}


def test_every_mapping_cites_the_exact_evidence(qmap):
    """A mapping must be auditable back to the field and file it came from."""
    assert qmap.evidence_field.notna().all()
    assert qmap.evidence_reference.notna().all()
    assert qmap.evidence_field.str.contains("field 14").all()
    assert qmap.evidence_reference.str.endswith(".pdf (NQR qualification file)").all()


def test_nco_code_resolves_in_the_official_spine(qmap, om):
    """Independent corroboration 1: the code the Q-File states must exist in
    occupation_master at OCCUPATION level."""
    occupations = set(om[om.level == "OCCUPATION"].nco_code)
    assert set(qmap.nco_2015_code) <= occupations
    assert qmap.nco_code_resolves_in_master.all()


def test_qualification_title_matches_the_nco_title(qmap):
    """Independent corroboration 2: the qualification name and the NCO occupation
    title agree, which is why this mapping needs no judgement."""
    assert qmap.title_matches_nco_title.all()


def test_qp_nos_indicator_corroborates_the_mapping(qmap):
    """Independent corroboration 3: NCO digits 7-8 != '00' signals that a QP/NOS
    exists for the job role, per the NCVET handbook. A qualification mapping to a
    code whose indicator is False would be internally contradictory."""
    assert qmap.qp_nos_indicated_by_nco_code.all()


def test_mapping_level_is_not_overclaimed(qmap):
    """8 digits with a decimal is the full OCCUPATION level. The level recorded
    must match what the code actually carries."""
    assert set(qmap.nco_mapping_level) == {"OCCUPATION"}
    assert qmap.nco_2015_code.str.match(r"^\d{4}\.\d{4}$").all()


def test_mapping_ids_are_unique(qmap):
    assert qmap.mapping_id.is_unique


# ------------------------------------------ the 155 trades remain UNMAPPED

def test_dgt_trades_are_still_unmapped(trades):
    """The decisive test. NQR qualifications are not DGT CTS trades, and no
    trade -> qualification link is published in anything held. Any NCO code
    appearing on a trade would be fabricated."""
    assert len(trades) == 155
    assert trades.nco_2015_code.isna().all()
    assert set(trades.nco_mapping_status) == {"UNMAPPED_NO_OFFICIAL_MAPPING"}


def test_qualification_mapping_does_not_claim_to_cover_trades(qmap):
    assert not qmap.applies_to_dgt_cts_trade.any()


def test_no_trade_name_was_matched_to_a_qualification_by_similarity(qmap, trades):
    """Guard against the specific temptation: mapping 'Fitter' the CTS trade to a
    similarly-named NQR qualification. No trade name may appear in the mapping."""
    trade_names = {n.strip().lower() for n in trades.trade_name}
    mapped_names = {str(n).strip().lower() for n in qmap.qualification_name}
    assert not (trade_names & mapped_names)


# ----------------------------------------------------------- evidence matrix

def test_evidence_matrix_covers_the_investigated_blockers(evidence):
    """Step 5.1 opened blockers A and B; Step 5.3 added C (trade-level supply).
    The matrix is cumulative, so all three must be present."""
    assert {"A_DISTRICT_SUPPLY", "B_TRADE_NCO"} <= set(evidence.blocker)
    assert set(evidence.blocker) <= {
        "A_DISTRICT_SUPPLY", "B_TRADE_NCO", "C_TRADE_LEVEL_SUPPLY"
    }


def test_every_decision_uses_the_allowed_vocabulary(evidence):
    allowed = {"ACQUIRED", "PARTIALLY_ACQUIRED", "ACCESS_PENDING", "UNAVAILABLE",
               "REJECTED", "ACQUIRED_METADATA_ONLY"}
    assert set(evidence.decision) <= allowed
    assert set(evidence.access_status) <= allowed


def test_every_negative_decision_has_a_concrete_reason(evidence):
    """A rejection without a reason is an unexamined assumption."""
    negative = evidence[evidence.decision.isin(
        ["REJECTED", "UNAVAILABLE", "ACCESS_PENDING", "PARTIALLY_ACQUIRED"]
    )]
    assert len(negative) >= 5
    assert negative.reason.notna().all()
    assert (negative.reason.str.len() > 40).all()


def test_access_pending_is_distinguished_from_unavailable(evidence):
    """The brief is explicit: do not call a dataset unavailable when the real
    issue is access."""
    pending = evidence[evidence.decision == "ACCESS_PENDING"]
    assert len(pending) == 1
    assert "API key" in pending.iloc[0].reason
    unavailable = evidence[evidence.decision == "UNAVAILABLE"]
    assert len(unavailable) >= 1
    assert not unavailable.reason.str.contains("API key").any()


def test_district_count_is_not_recorded_as_district_supply(evidence):
    """Annexure-21 gives a district COUNT per state. The matrix must say so and
    must not mark it district_available."""
    pmkk = evidence[evidence.resource.str.contains("PMKK")]
    assert len(pmkk) == 1
    assert not bool(pmkk.iloc[0].district_available)
    assert "NOT district-level" in pmkk.iloc[0].reason


def test_evidence_matrix_records_the_proven_nqr_chain(evidence):
    row = evidence[evidence.resource.str.contains("field 14")]
    assert len(row) == 1
    assert row.iloc[0].decision == "ACQUIRED"
    assert bool(row.iloc[0].nco_mapping_available)
    assert "4132.0402" in row.iloc[0].reason


def test_no_district_source_was_acquired_with_a_district_dimension(evidence):
    """Blocker A verdict, asserted from the data: nothing acquired carries a
    usable district training dimension."""
    district_rows = evidence[
        (evidence.blocker == "A_DISTRICT_SUPPLY")
        & (evidence.decision == "ACQUIRED")
        & (evidence.district_available == True)  # noqa: E712
    ]
    assert len(district_rows) == 0


# --------------------------------------------------- provenance and boundaries

def test_mapping_source_resolves_to_source_master(qmap):
    known = set(pd.read_parquet(standardized_path("source_master")).source_id)
    assert set(qmap.source_id) <= known


def test_step_50_dataset_was_not_replaced():
    """Step 5.1 is additive. The Step 5.0 tables must be untouched."""
    assert len(pd.read_parquet(standardized_path("fact_training_outcome"))) == 350
    assert len(pd.read_parquet(standardized_path("fact_training_infrastructure"))) == 144
    assert len(pd.read_parquet(standardized_path("fact_training_reconciliation"))) == 14


def test_no_supply_estimate_or_gap_artifacts_exist():
    from lmis.common.paths import STANDARDIZED

    for name in ("supply_estimate", "analytical_supply_estimate", "demand_supply_gap",
                 "fact_gap", "fact_forecast", "supply_district_allocation",
                 "gap_score", "fact_early_warning"):
        assert not (STANDARDIZED / f"{name}.parquet").exists(), name
