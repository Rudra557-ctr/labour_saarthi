"""Build dim_period.

Generated deterministically, not sourced: it exists so that no module ever does
inline date arithmetic. It reconciles the three calendars that collide in Indian
administrative data - calendar month, fiscal year (April-March) and
academic/training year (April-March, labelled YYYY-YY).
"""
from __future__ import annotations

import pandas as pd


def fiscal_year(year: int, month: int) -> str:
    """Indian fiscal year: April YYYY to March YYYY+1, labelled 'YYYY-YY'."""
    start = year if month >= 4 else year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def fiscal_quarter(month: int) -> int:
    """Q1 = Apr-Jun ... Q4 = Jan-Mar."""
    return ((month - 4) % 12) // 3 + 1


def build_dim_period(start_year: int = 2017, end_year: int = 2027) -> pd.DataFrame:
    rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            start = pd.Timestamp(year=year, month=month, day=1)
            end = start + pd.offsets.MonthEnd(1)
            fy = fiscal_year(year, month)
            rows.append(
                {
                    "period_id": f"M{year}{month:02d}",
                    "period_start": start.date().isoformat(),
                    "period_end": end.date().isoformat(),
                    "period_grain": "M",
                    "calendar_year": year,
                    "calendar_month": month,
                    "calendar_quarter": (month - 1) // 3 + 1,
                    "fiscal_year": fy,
                    "fiscal_quarter": fiscal_quarter(month),
                    # Training/academic year uses the same Apr-Mar boundary as
                    # the fiscal year in the schemes we have verified so far.
                    # Recorded separately so a source that differs can override
                    # it without changing fiscal logic.
                    "academic_year": fy,
                    "label_en": start.strftime("%b %Y"),
                }
            )
    return pd.DataFrame(rows)
