from lmis.conform.period import build_dim_period, fiscal_quarter, fiscal_year


def test_fiscal_year_boundary_is_april():
    assert fiscal_year(2025, 3) == "2024-25"   # March belongs to the previous FY
    assert fiscal_year(2025, 4) == "2025-26"   # April starts the new FY


def test_fiscal_quarters_run_april_to_march():
    assert fiscal_quarter(4) == 1   # Apr
    assert fiscal_quarter(6) == 1   # Jun
    assert fiscal_quarter(7) == 2   # Jul
    assert fiscal_quarter(1) == 4   # Jan
    assert fiscal_quarter(3) == 4   # Mar


def test_dim_period_is_complete_and_unique():
    df = build_dim_period(2020, 2021)
    assert len(df) == 24
    assert df["period_id"].is_unique
    assert set(df["period_grain"]) == {"M"}


def test_period_end_is_month_end():
    df = build_dim_period(2024, 2024)
    feb = df[df["period_id"] == "M202402"].iloc[0]
    assert feb["period_end"] == "2024-02-29"  # leap year
