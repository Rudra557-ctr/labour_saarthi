"""Step 3.1 evidence tests.

These encode the evidence the Step 4 methodology rests on, so that if a source
changes shape the methodology's premises fail loudly rather than quietly.
"""
import pandas as pd
import pytest

from lmis.common.paths import standardized_path


@pytest.fixture(scope="module")
def ilo():
    return pd.read_parquet(standardized_path("fact_ilo_employment_eco_occ"))


@pytest.fixture(scope="module")
def lm():
    return pd.read_parquet(standardized_path("location_master"))


# ----------------------------------------- industry x occupation bridge evidence

def test_ilo_crosstab_is_derived_from_indias_own_plfs(ilo):
    """The whole justification for using this source is its provenance: for India
    the ILO source code resolves to the Periodic Labour Force Survey."""
    assert set(ilo.survey_source_label) == {"LFS - Periodic Labour Force Survey"}
    assert set(ilo.ref_area) == {"IND"}


def test_ilo_crosstab_has_both_industry_and_occupation(ilo):
    assert set(ilo.industry_level) == {"NIC_SECTION"}
    assert set(ilo.occupation_level) == {"NCO_2015_DIVISION"}
    assert ilo.nic_2008_section.nunique() == 20
    assert set(ilo.nco_2015_division) == {str(i) for i in range(1, 10)}


def test_isco_major_group_equals_nco_division(ilo):
    """NCVET documents a one-to-one correspondence between ISCO-08 and NCO-2015
    with the first digit as the Division / Major Group."""
    assert (ilo.isco_08_major_group == ilo.nco_2015_division).all()


def test_ilo_crosstab_is_national_only(ilo):
    """P(occupation | industry, STATE) is NOT available from this source. If a
    state dimension ever appears, the methodology can be upgraded - until then
    the national-only constraint must stay visible."""
    assert set(ilo.geo_level) == {"NATIONAL"}


def test_ilo_has_four_years_enabling_a_stability_check(ilo):
    assert set(ilo.year) == {"2022", "2023", "2024", "2025"}


def test_suppressed_cells_stay_null(ilo):
    """45 cells are absent in the source. They must remain NULL - a zero would
    assert 'no such workers', which the ILO does not say."""
    assert ilo.employment_thousands.isna().sum() == 45


def test_conditional_distribution_is_computable_and_normalised(ilo):
    """The quantity Step 4 needs: P(occupation | industry) must sum to 1 within
    every industry section, in every year."""
    df = ilo.dropna(subset=["employment_thousands"])
    for year, grp in df.groupby("year"):
        totals = grp.groupby("nic_2008_section").employment_thousands.transform("sum")
        p = grp.employment_thousands / totals
        sums = p.groupby(grp.nic_2008_section).sum()
        assert sums.round(6).eq(1.0).all(), year


def test_conditional_distribution_is_face_valid(ilo):
    """Sanity, not circularity: manufacturing should be craft-dominated,
    construction elementary-dominated, IT professional-dominated. If these flip,
    the classification alignment is wrong."""
    y = ilo[(ilo.year == "2025") & ilo.employment_thousands.notna()].copy()
    y["p"] = y.employment_thousands / y.groupby("nic_2008_section").employment_thousands.transform("sum")
    def modal(section):
        s = y[y.nic_2008_section == section]
        return s.loc[s.p.idxmax(), "nco_2015_division"]
    assert modal("C") == "7"   # Manufacturing -> craft and related trades
    assert modal("F") == "9"   # Construction  -> elementary occupations
    assert modal("J") == "2"   # Info & comms  -> professionals
    assert modal("G") == "5"   # Wholesale/retail -> service and sales


def test_conditional_distribution_is_stable_enough_to_hold_constant(ilo):
    """Evidence for the Step 4 decision to treat the bridge as time-stable:
    median absolute change in P across 2022->2025 must stay small."""
    df = ilo.dropna(subset=["employment_thousands"]).copy()
    df["p"] = df.employment_thousands / df.groupby(
        ["year", "nic_2008_section"]
    ).employment_thousands.transform("sum")
    a = df[df.year == "2022"][["nic_2008_section", "nco_2015_division", "p"]]
    b = df[df.year == "2025"][["nic_2008_section", "nco_2015_division", "p"]]
    m = a.merge(b, on=["nic_2008_section", "nco_2015_division"], suffixes=("_a", "_b"))
    delta = (m.p_b - m.p_a).abs()
    assert delta.median() < 0.02, delta.median()


# ------------------------------------------------- Census -> LGD coverage facts

def test_every_census_district_maps_to_an_lgd_district(lm):
    dos = pd.read_parquet(standardized_path("analytical_district_occupation_structure"))
    census_codes = set(dos.census_district_code.dropna())
    lgd_census = set(lm[lm.level == "DISTRICT"].census_2011_code.dropna())
    assert census_codes <= lgd_census
    assert len(census_codes) == 138


def test_pilot_district_prior_coverage_is_exactly_quantified(lm):
    """149 LGD districts in the pilot states; 11 post-2011 districts can never
    receive a Census-2011 occupation prior. Step 4 must mark those NOT_AVAILABLE."""
    pilot = lm[(lm.level == "DISTRICT") & (lm.state_lgd_code.isin(["27", "33", "9"]))]
    assert len(pilot) == 149
    assert pilot.census_2011_code.isna().sum() == 11
    by_state = pilot[pilot.census_2011_code.isna()].groupby("state_lgd_code").size().to_dict()
    assert by_state == {"27": 1, "33": 6, "9": 4}


def test_districts_without_prior_are_named_and_known(lm):
    """Each is a documented post-2011 creation, so the gap is explainable rather
    than mysterious."""
    pilot = lm[(lm.level == "DISTRICT") & (lm.state_lgd_code.isin(["27", "33", "9"]))]
    missing = set(pilot[pilot.census_2011_code.isna()].name_en)
    assert "Palghar" in missing          # split from Thane, 2014
    assert "Chengalpattu" in missing     # Tamil Nadu reorganisation, 2019
    assert "Hapur" in missing            # split from Ghaziabad, 2011
    assert len(missing) == 11


# ------------------------------------- the estimator is NOT built in this step

def test_no_estimator_output_exists_yet():
    """Step 3.1 is design only. These artifacts must not exist."""
    from lmis.common.paths import STANDARDIZED

    forbidden = [
        "analytical_district_demand_estimate",
        "analytical_demand_index",
        "fact_demand_index",
        "fact_gap",
        "fact_forecast",
        "analytical_industry_occupation_bridge",
    ]
    for name in forbidden:
        assert not (STANDARDIZED / f"{name}.parquet").exists(), name
