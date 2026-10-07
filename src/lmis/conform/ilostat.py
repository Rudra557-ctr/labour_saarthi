"""ILOSTAT employment by economic activity and occupation (India).

This is a SOURCE fact table at the source's native grain. It is NOT the
industry->occupation bridge: computing P(occupation | industry) and using it to
estimate demand belongs to Step 4, under the methodology in
docs/step3_1_estimation_methodology.md.

Why it matters: for India the ILO source code is BA:14121 = "LFS - Periodic
Labour Force Survey", so this is India's own PLFS, harmonised and published by
the ILO as a cross-tabulation MoSPI does not publish directly.

Classification alignment, both documented rather than assumed:
  ISIC-Rev.4 section     -> NIC-2008 section   (NIC-2008 is the Indian adaptation
                                                of ISIC-Rev.4; section letters and
                                                titles verified against the
                                                official NIC-2008 PDF)
  ISCO-08 major group    -> NCO-2015 division  (NCVET report Annexure IX s.3:
                                                "one to one correspondence between
                                                ISCO-08 and the NCO-2015", first
                                                digit = Division / Major Group)

Only ISIC4-section x ISCO08-major-group rows are kept. Aggregates (TOTAL, the
ECO_AGGREGATE_* families, ISIC-Rev.3 rows, skill-level rows and the 'X' not-
classified bucket) are excluded so nothing double-counts; `excluded_reason`
statistics are reported by the caller rather than silently dropped.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

SECTION_RE = re.compile(r"^ECO_ISIC4_([A-U])$")
ISCO_RE = re.compile(r"^OCU_ISCO08_([1-9])$")

OUT_COLUMNS = [
    "ref_area", "year", "nic_2008_section", "isco_08_major_group",
    "nco_2015_division", "employment_thousands", "unit", "measure_basis",
    "geo_level", "industry_level", "occupation_level", "survey_source_code",
    "survey_source_label", "obs_status", "observed_or_estimated",
    "source_id", "snapshot_file", "ingested_at",
]


def parse_ilostat_eco_occ(
    csv_path: Path, source_dic_path: Path, source_id: str, ingested_at: str
) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    raw["obs_value_num"] = pd.to_numeric(raw["obs_value"], errors="coerce")

    sec = raw["classif1"].str.extract(SECTION_RE)[0]
    isco = raw["classif2"].str.extract(ISCO_RE)[0]
    keep = sec.notna() & isco.notna()

    dic = pd.read_csv(source_dic_path, dtype=str, keep_default_na=False)
    dic.columns = [c.replace("﻿", "").strip('"') for c in dic.columns]
    labels = dict(zip(dic["source"], dic["source.label"]))

    df = raw[keep].copy()
    df["nic_2008_section"] = sec[keep]
    df["isco_08_major_group"] = isco[keep]
    # ISCO-08 major group IS the NCO-2015 division (one-to-one, per NCVET).
    df["nco_2015_division"] = df["isco_08_major_group"]
    out = pd.DataFrame(
        {
            "ref_area": df["ref_area"],
            "year": df["time"],
            "nic_2008_section": df["nic_2008_section"],
            "isco_08_major_group": df["isco_08_major_group"],
            "nco_2015_division": df["nco_2015_division"],
            "employment_thousands": df["obs_value_num"],
            "unit": "thousands_of_persons",
            "measure_basis": "EMPLOYMENT_STOCK_SURVEY_ESTIMATE",
            "geo_level": "NATIONAL",
            "industry_level": "NIC_SECTION",
            "occupation_level": "NCO_2015_DIVISION",
            "survey_source_code": df["source"],
            "survey_source_label": df["source"].map(labels),
            "obs_status": df["obs_status"],
            "observed_or_estimated": "OBSERVED_SURVEY_ESTIMATE",
            "source_id": source_id,
            "snapshot_file": csv_path.name,
            "ingested_at": ingested_at,
        }
    )[OUT_COLUMNS]

    stats = {
        "rows_in_source": int(len(raw)),
        "rows_kept": int(len(out)),
        "rows_excluded": int(len(raw) - len(out)),
        "years": sorted(out["year"].unique().tolist()),
        "sections": int(out["nic_2008_section"].nunique()),
        "null_values": int(out["employment_thousands"].isna().sum()),
    }
    return out.reset_index(drop=True), stats
