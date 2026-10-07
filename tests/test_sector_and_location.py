import pandas as pd

from lmis.common.paths import standardized_path
from lmis.conform.location import (
    LOCATION_ALIAS_COLUMNS,
    LOCATION_CHANGE_EVENT_COLUMNS,
    LOCATION_MASTER_COLUMNS,
)


def test_sector_master_matches_ncvet_documented_count():
    """NCVET documents the NQR as covering 59 sectors. If this count drifts, the
    extraction or the source changed and must be re-verified rather than
    silently accepted."""
    sec = pd.read_parquet(standardized_path("sector_master"))
    assert len(sec) == 59
    assert sec["sector_id"].is_unique
    assert sec["portal_sector_id"].is_unique


def test_pilot_sectors_exist_in_sector_master():
    sec = pd.read_parquet(standardized_path("sector_master"))
    names = set(sec["sector_name_en"].str.lower())
    for pilot in ("capital goods & manufacturing", "it-ites", "healthcare"):
        assert pilot in names, pilot


def test_sector_master_leaves_unpublished_fields_null():
    """ssc_name/ssc_code are not on the listing page, so they must be NULL."""
    sec = pd.read_parquet(standardized_path("sector_master"))
    assert sec["ssc_name"].isna().all()
    assert sec["ssc_code"].isna().all()


def test_location_master_is_populated_from_validated_lgd():
    """Populated in Step 1.7 from validated official LGD extracts (ADR-0006):
    36 states/UTs and 785 districts."""
    lm = pd.read_parquet(standardized_path("location_master"))
    assert list(lm.columns) == LOCATION_MASTER_COLUMNS
    assert (lm.level == "STATE").sum() == 36
    assert (lm.level == "DISTRICT").sum() == 785
    assert lm[lm.level == "STATE"].lgd_code.is_unique
    assert lm[lm.level == "DISTRICT"].lgd_code.is_unique


def test_every_district_parent_is_a_known_state():
    lm = pd.read_parquet(standardized_path("location_master"))
    states = set(lm[lm.level == "STATE"].lgd_code)
    assert set(lm[lm.level == "DISTRICT"].parent_lgd_code) <= states


def test_no_national_row_is_synthesised():
    """LGD issues no code for the country; inventing one would put a fabricated
    key in the authoritative table."""
    lm = pd.read_parquet(standardized_path("location_master"))
    assert "NATIONAL" not in set(lm.level)


def test_missing_census_code_stays_missing_not_zero():
    """125 districts post-date Census 2011. LGD marks that with '000'; it must
    become NULL, never the integer zero or the string '000'."""
    lm = pd.read_parquet(standardized_path("location_master"))
    dist = lm[lm.level == "DISTRICT"]
    assert dist.census_2011_code.isna().sum() == 125
    assert not dist.census_2011_code.isin(["000", "0", 0]).any()


def test_snapshot_vintage_is_carried_on_every_row():
    """The source is a 2023 snapshot while LGD updates monthly. Its age must be
    visible on the data, not only in documentation."""
    lm = pd.read_parquet(standardized_path("location_master"))
    assert lm.valid_from.notna().all()
    assert set(lm.valid_from.unique()) <= {"2023-11-30", "2023-12-01"}


def test_change_events_stay_empty_because_source_publishes_none():
    """LGD's CSV exposes no split/merge/rename events, so this table must not be
    populated by inference."""
    change = pd.read_parquet(standardized_path("location_change_event"))
    assert list(change.columns) == LOCATION_CHANGE_EVENT_COLUMNS
    assert len(change) == 0


def test_location_alias_is_curated_and_resolves_to_real_lgd_codes():
    """Populated in Step 2.0 from mappings/aliases/state_name_aliases.csv. Each
    row is a reviewed rename, abbreviation or territorial reorganisation - never
    a fuzzy match, because a wrong geography alias is invisible once joined."""
    alias = pd.read_parquet(standardized_path("location_alias"))
    lm = pd.read_parquet(standardized_path("location_master"))
    assert list(alias.columns) == LOCATION_ALIAS_COLUMNS
    assert len(alias) >= 8
    assert alias.alias_id.is_unique
    assert set(alias.lgd_code) <= set(lm[lm.level == "STATE"].lgd_code)
    assert alias.confidence.between(0, 1).all()
    assert alias.match_method.notna().all()


def test_merged_union_territory_aliases_both_resolve_to_one_code():
    """NCS still reports the pre-2020 UTs separately; LGD carries the single
    merged UT. Many-to-one is correct here and must be preserved."""
    alias = pd.read_parquet(standardized_path("location_alias"))
    merged = alias[alias.alias_text.isin(["Dadra and Nagar Haveli", "Daman and Diu"])]
    assert len(merged) == 2
    assert merged.lgd_code.nunique() == 1


def test_udyam_joins_cleanly_to_location_master():
    """100% join is what makes Udyam usable as a district allocation basis."""
    import glob
    lm = pd.read_parquet(standardized_path("location_master"))
    districts = set(lm[lm.level == "DISTRICT"].lgd_code)
    path = sorted(glob.glob("data/raw/UDYAM_DISTRICT_MSME/*/district_level_total_Registered_msme.csv"))[-1]
    ud = pd.read_csv(path, dtype=str, keep_default_na=False)
    codes = set(ud["lg_dist_code"].str.strip())
    assert codes <= districts, sorted(codes - districts)[:10]


def test_census_candidates_are_not_treated_as_lgd():
    """The Census-2011 candidate district set must be flagged non-authoritative
    and must live in staging, never in location_master."""
    cand = pd.read_parquet("data/staging/census2011_district_candidates.parquet")
    assert len(cand) > 500
    assert (cand["is_authoritative_for_lgd"] == False).all()  # noqa: E712
