"""fact_establishment_district from the Udyam district MSME extracts.

Grain: snapshot_date x lgd_code x enterprise_category x size_class.

WHAT THIS IS NOT: labour demand, vacancies, hiring or employment. It is a
cumulative count of REGISTERED ENTERPRISES. A district with many registrations
may simply have formalised earlier. The `measure_basis` column says so on every
row, and nothing downstream may read it as demand.

The source writes 'NA' in `small` and `medium` for some districts. That is real
missingness and is loaded as NULL, never as zero.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SIZE_COLUMNS = {"micro": "MICRO", "small": "SMALL", "medium": "MEDIUM", "total": "TOTAL"}
FACT_COLUMNS = [
    "snapshot_date", "lgd_code", "geo_level", "district_name_as_source",
    "enterprise_category", "size_class", "enterprise_count", "unit",
    "measure_basis", "observed_or_estimated", "source_id", "snapshot_file",
    "ingested_at",
]


def _norm(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).replace("﻿", "").strip().strip('"').strip().lower() for c in df.columns]
    return df


def _to_count(v: str) -> int | None:
    """'NA', '' and '-' are MISSING. They must never become 0."""
    s = str(v).strip().replace(",", "")
    if s.upper() in ("NA", "N/A", "", "-", "NONE", "NULL"):
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def build_establishment_district(
    csv_path: Path, enterprise_category: str, source_id: str, ingested_at: str
) -> pd.DataFrame:
    df = _norm(pd.read_csv(csv_path, dtype=str, keep_default_na=False))
    # Column casing differs between the two Udyam files; normalisation above
    # makes them identical, which is why this builder handles both.
    snapshot_dates = sorted({v.strip() for v in df["last_updated"] if v.strip()})
    rows = []
    for _, r in df.iterrows():
        for col, size_class in SIZE_COLUMNS.items():
            rows.append(
                {
                    "snapshot_date": r["last_updated"].strip(),
                    "lgd_code": r["lg_dist_code"].strip(),
                    "geo_level": "DISTRICT",
                    "district_name_as_source": r["district_name"].strip(),
                    "enterprise_category": enterprise_category,
                    "size_class": size_class,
                    "enterprise_count": _to_count(r[col]),
                    "unit": "count",
                    "measure_basis": "CUMULATIVE_REGISTRATIONS",
                    "observed_or_estimated": "OBSERVED",
                    "source_id": source_id,
                    "snapshot_file": csv_path.name,
                    "ingested_at": ingested_at,
                }
            )
    out = pd.DataFrame(rows, columns=FACT_COLUMNS)
    out.attrs["snapshot_dates"] = snapshot_dates
    return out
