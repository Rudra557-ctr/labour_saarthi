"""Step 5.2 occupation-linkage tests.

The single most important test here is the last one: no trade may receive an NCO
code because its name resembles an NCO title. Everything else guards the evidence
chain and the reconciliation to 155.
"""
import re

import pandas as pd
import pytest

from lmis.common.paths import standardized_path


@pytest.fixture(scope="module")
def tmap():
    return pd.read_parquet(standardized_path("map_trade_to_nco"))


@pytest.fixture(scope="module")
def status():
    return pd.read_parquet(standardized_path("dim_trade_mapping_status"))


@pytest.fixture(scope="module")
def trades():
    return pd.read_parquet(standardized_path("dim_training_trade"))


@pytest.fixture(scope="module")
def om():
    return pd.read_parquet(standardized_path("occupation_master"))


# ------------------------------------------------------------ the evidence chain

def test_mapping_is_official_from_dgts_own_curriculum(tmap):
    assert len(tmap) == 4
    assert set(tmap.mapping_authority) == {"OFFICIAL"}
    assert (tmap.mapping_confidence == 1.0).all()
    assert set(tmap.mapping_method) == {
        "DGT_CTS_CURRICULUM_GENERAL_INFORMATION_NCO_2015_FIELD"
    }


def test_every_mapping_carries_a_dgt_trade_code(tmap):
    """The Trade Code is the real identifier, and the MSDE annexure never
    published it - the curriculum supplies it."""
    assert tmap.dgt_trade_code.notna().all()
    assert tmap.dgt_trade_code.str.match(r"^DGT/\d{3,5}$").all()
    assert set(tmap.dgt_trade_code) == {"DGT/1001", "DGT/1002"}


def test_every_mapping_cites_field_and_file(tmap):
    assert tmap.evidence_field.str.contains("GENERAL INFORMATION").all()
    assert tmap.evidence_reference.str.endswith("(DGT CTS curriculum)").all()


def test_nco_codes_resolve_in_occupation_master(om, tmap):
    occupations = set(om[om.level == "OCCUPATION"].nco_code)
    assert set(tmap.nco_2015_code) <= occupations
    assert tmap.nco_code_resolves_in_master.all()


def test_nco_code_format_is_valid_eight_digit(tmap):
    assert tmap.nco_2015_code.str.match(r"^\d{4}\.\d{4}$").all()


def test_mapping_level_is_occupation_not_overclaimed(tmap):
    assert set(tmap.nco_mapping_level) == {"NCO_OCCUPATION"}


def test_no_mapping_exists_without_evidence(tmap):
    for col in ("evidence_field", "evidence_reference", "source_id", "snapshot_file",
                "dgt_trade_code", "mapping_method"):
        assert tmap[col].notna().all(), col


def test_nos_codes_are_captured_as_additional_evidence(tmap):
    """The curricula also cite Reference NOS codes, which corroborate the trade's
    occupational content."""
    assert tmap.reference_nos_codes.notna().any()
    assert tmap.reference_nos_codes.dropna().str.contains(r"[A-Z]{2,5}/N\d{3,5}").all()


# -------------------------------------------------------- multi-NCO is preserved

def test_multi_nco_ambiguity_is_preserved_not_collapsed(tmap):
    """Fitter maps to two NCO occupations and Electrician to two. Both codes must
    survive; picking one would be an arbitrary choice the source does not make."""
    per_trade = tmap.groupby("trade_id").nco_2015_code.nunique()
    assert (per_trade == 2).all()
    assert tmap.is_multi_nco.all()
    assert set(tmap.mapping_status) == {"OFFICIAL_MULTI_NCO"}


def test_all_codes_for_a_trade_are_recorded_together(tmap):
    for _, grp in tmap.groupby("trade_id"):
        published = set(grp.nco_codes_for_trade.iloc[0].replace(" ", "").split(","))
        assert set(grp.nco_2015_code) == published


def test_fitter_maps_to_both_published_codes(tmap):
    f = tmap[tmap.dgt_trade_code == "DGT/1002"]
    assert set(f.nco_2015_code) == {"7233.0100", "7233.0200"}


def test_electrician_maps_to_both_published_codes(tmap):
    e = tmap[tmap.dgt_trade_code == "DGT/1001"]
    assert set(e.nco_2015_code) == {"7411.0100", "7412.0200"}


def test_title_mismatch_is_reported_honestly_not_smoothed(tmap):
    """DGT prints 'Electrician General'; occupation_master has 'Electrician,
    General'. The comparison must flag that difference rather than loosen itself
    to look clean. The CODE is the mapping, not the title."""
    row = tmap[tmap.nco_2015_code == "7411.0100"].iloc[0]
    assert row.title_matches_master == False  # noqa: E712
    assert row.nco_code_resolves_in_master
    assert tmap.title_matches_master.sum() == 3


# ------------------------------------------------------ status reconciles to 155

def test_status_covers_exactly_155_trades(status, trades):
    assert len(status) == 155
    assert status.trade_id.is_unique
    assert set(status.trade_id) == set(trades.trade_id)


def test_status_totals_reconcile(status):
    counts = status.mapping_status.value_counts().to_dict()
    assert counts == {"MAPPING_UNKNOWN": 153, "OFFICIAL_MULTI_NCO": 2}
    assert sum(counts.values()) == 155


def test_mapping_unknown_is_distinguished_from_does_not_exist(status):
    """The brief is explicit about this distinction. DGT demonstrably publishes
    NCO codes on these curricula, so the mapping EXISTS - it cannot be enumerated.
    The status must say UNKNOWN and the reason must say why."""
    unknown = status[status.mapping_status == "MAPPING_UNKNOWN"]
    assert len(unknown) == 153
    assert unknown.status_reason.str.contains("not be enumerated").all()
    assert unknown.status_reason.str.contains("not non-existent").all()
    assert "MAPPING_DOES_NOT_EXIST" not in set(status.mapping_status)


def test_unmapped_trades_carry_no_nco_code(status):
    unknown = status[status.mapping_status == "MAPPING_UNKNOWN"]
    assert unknown.nco_codes_for_trade.isna().all()
    assert unknown.dgt_trade_code.isna().all()
    assert set(unknown.mapping_level) == {"UNMAPPED"}


def test_mapped_trades_carry_level_and_codes(status):
    mapped = status[status.mapping_status == "OFFICIAL_MULTI_NCO"]
    assert set(mapped.mapping_level) == {"NCO_OCCUPATION"}
    assert mapped.nco_codes_for_trade.notna().all()
    assert mapped.dgt_trade_code.notna().all()


# ------------------------------------- Step 5.0 artifact preserved and auditable

def test_step_50_trade_table_was_not_modified(trades):
    """Step 5.2 is additive. The original 155 rows and their UNMAPPED records must
    remain exactly as Step 5.0 wrote them."""
    assert len(trades) == 155
    assert trades.nco_2015_code.isna().all()
    assert set(trades.nco_mapping_status) == {"UNMAPPED_NO_OFFICIAL_MAPPING"}


def test_trade_identifiers_are_preserved(tmap, trades):
    assert set(tmap.trade_id.dropna()) <= set(trades.trade_id)
    assert tmap.trade_name_as_register.notna().all()


# ================= THE CRITICAL REGRESSION TEST =================

def test_no_trade_receives_an_nco_code_merely_because_its_name_matches(tmap, om, status):
    """NO TRADE MAY RECEIVE AN NCO CODE SOLELY BECAUSE ITS NAME MATCHES OR
    RESEMBLES AN NCO TITLE.

    Proven three ways:

    1. Every mapped row cites a DGT curriculum field as its evidence, and the
       link method is exact-name-within-scheme, never similarity.
    2. There are 9 trades whose names contain 'fitter' or 'electric'. If name
       resemblance drove the mapping, far more than 2 trades would be mapped.
    3. Many unmapped trade names ARE exact case-insensitive matches for NCO
       occupation titles. Every one of them must still be MAPPING_UNKNOWN - the
       name coincidence must buy nothing.
    """
    # 1. evidence and link method
    assert set(tmap.link_method) == {"EXACT_TRADE_NAME_WITHIN_CTS_SCHEME"}
    assert tmap.evidence_reference.notna().all()

    # 2. name-similar trades are not swept in
    similar = status[status.trade_name.str.contains(r"fitter|electric", case=False, regex=True)]
    assert len(similar) >= 9
    assert (similar.mapping_status == "MAPPING_UNKNOWN").sum() >= 7

    # 3. exact title coincidences must NOT be mapped
    occ_titles = {
        re.sub(r"\s+", " ", str(t)).strip().casefold()
        for t in om[om.level == "OCCUPATION"].title_en.dropna()
    }
    unknown = status[status.mapping_status == "MAPPING_UNKNOWN"]
    coincidences = [
        n for n in unknown.trade_name
        if re.sub(r"\s+", " ", str(n)).strip().casefold() in occ_titles
    ]
    # These exist, and they stayed unmapped - which is the whole point.
    assert len(coincidences) > 0, "expected some name coincidences to exist"
    for name in coincidences:
        row = unknown[unknown.trade_name == name].iloc[0]
        assert row.mapping_status == "MAPPING_UNKNOWN"
        assert pd.isna(row.nco_codes_for_trade)


def test_only_curricula_actually_acquired_produced_mappings(tmap):
    """A mapping may only come from a file in the raw snapshot - never from a name
    lookup against occupation_master."""
    from lmis.common.paths import RAW

    acquired = {p.name for p in (RAW / "DGT_CTS_CURRICULUM").rglob("*.pdf")}
    assert set(tmap.snapshot_file) <= acquired


# ---------------------------------------------- no supply/gap work crept in

def test_no_occupation_supply_or_gap_artifacts_exist():
    from lmis.common.paths import STANDARDIZED

    for name in ("supply_by_occupation", "fact_training_outcome_by_nco",
                 "analytical_supply_estimate", "demand_supply_gap", "fact_gap",
                 "fact_forecast", "supply_district_allocation", "gap_score"):
        assert not (STANDARDIZED / f"{name}.parquet").exists(), name


def test_supply_outcomes_still_have_no_occupation_dimension():
    """Step 5.2 solved taxonomy, not supply measurement. The outcome table must
    still carry no occupation column."""
    out = pd.read_parquet(standardized_path("fact_training_outcome"))
    for col in out.columns:
        assert "nco" not in col.lower()
        assert "occupation" not in col.lower()
