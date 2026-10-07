"""Tests for the NCO-2015 spine.

The code-structure rules asserted here are quoted from NCVET's "Report on
Mapping of Qualifications with NCO Codes" (22 Aug 2023), Annexure IX s.3 -
they are not our invention.
"""
import pandas as pd
import pytest

from lmis.common.paths import standardized_path
from lmis.conform.occupation import build_occupation_master, build_nco2004_concordance

RAW = pd.DataFrame(
    [
        {
            "source_file": "t.html",
            "occupational_title": "Accountant",
            "nco_2015": "2411.0100",
            "nco_2004": "2411.10",
            "division_title": "Professionals",
            "sub_division_title": "Business and Administrative Professionals",
            "group_title": "Finance Professionals",
            "family_title": "Accountants",
        },
        {
            "source_file": "t.html",
            "occupational_title": "Sewing Machine Operator",
            "nco_2015": "8153.0111",
            "nco_2004": None,
            "division_title": "Plant and Machine Operators",
            "sub_division_title": "Textile Operators",
            "group_title": "Textile Machine Operators",
            "family_title": "Sewing Machine Operators",
        },
    ]
)


@pytest.fixture(scope="module")
def om():
    return build_occupation_master(RAW, "TEST", "2026-01-01T00:00:00+00:00")


def test_all_five_hierarchy_levels_are_produced(om):
    assert set(om["level"]) == {
        "DIVISION",
        "SUB_DIVISION",
        "GROUP",
        "FAMILY",
        "OCCUPATION",
    }


def test_hierarchy_codes_follow_documented_digit_positions(om):
    """digit 1 = Division, 1-2 = Sub-Division, 1-3 = Group, 1-4 = Family."""
    codes = set(om["nco_code"])
    for expected in ("2", "24", "241", "2411", "2411.0100"):
        assert expected in codes, expected


def test_parent_chain_is_consistent(om):
    by_code = dict(zip(om["nco_code"], om["parent_nco_code"]))
    assert by_code["2411.0100"] == "2411"
    assert by_code["2411"] == "241"
    assert by_code["241"] == "24"
    assert by_code["24"] == "2"
    # A Division is the hierarchy root: pandas stores the absent parent as NaN.
    assert pd.isna(by_code["2"])


def test_qp_nos_indicator_follows_annexure_ix_rule(om):
    """Last two digits: 00 means no QP/NOS exists, 01-99 means one does."""
    occ = om[om["level"] == "OCCUPATION"].set_index("nco_code")
    assert occ.loc["2411.0100", "qp_nos_indicated"] is False  # ...00
    assert occ.loc["8153.0111", "qp_nos_indicated"] is True   # ...11


def test_qp_nos_indicator_is_null_for_hierarchy_nodes(om):
    """A Family or Group has no QP/NOS digit pair, so the flag must be NULL
    rather than a default False."""
    nodes = om[om["level"] != "OCCUPATION"]
    assert nodes["qp_nos_indicated"].isna().all()


def test_missing_nco2004_stays_missing():
    """Missing stays missing: a blank NCO-2004 cell must never become a value."""
    conc = build_nco2004_concordance(RAW, "TEST", "2026-01-01T00:00:00+00:00")
    row = conc[conc["nco_2015_code"] == "8153.0111"].iloc[0]
    assert row["nco_2004_code"] is None or pd.isna(row["nco_2004_code"])


def test_concordance_is_marked_official():
    conc = build_nco2004_concordance(RAW, "TEST", "2026-01-01T00:00:00+00:00")
    assert set(conc["authority"]) == {"OFFICIAL"}
    assert (conc["confidence"] == 1.0).all()


def test_built_occupation_master_on_disk_is_sane():
    """Guards the real artifact, not just the unit fixture."""
    df = pd.read_parquet(standardized_path("occupation_master"))
    assert len(df) > 3000
    occ = df[df["level"] == "OCCUPATION"]
    assert occ["nco_code"].str.match(r"^\d{4}\.\d{4}$").all()
    # Every occupation's parent family must exist in the table.
    families = set(df[df["level"] == "FAMILY"]["nco_code"])
    assert set(occ["parent_nco_code"]) <= families
