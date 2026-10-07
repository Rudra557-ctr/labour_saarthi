"""Census 2011 Table B-24: occupational classification of main workers.

Grain of the source: state x district x NCO-2004 division x sub-division x area x sex.

CLASSIFICATION, non-negotiable: this is HISTORICAL WORKFORCE STRUCTURE as at 2011.
It is not employer demand, not vacancies, and not current. It enters the analytical
layer with status SUPPORTING.

SCOPE CAVEAT carried on every row: B-24 counts main workers in NON-HOUSEHOLD
industry, trade, business, profession or service. It is not all workers, so shares
derived from it describe that universe only.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

HEADER_ROW_COUNT = 8  # data starts at the 9th spreadsheet row (0-indexed 8)
COLUMNS = [
    "table_name", "state_code", "district_code", "area_name", "division",
    "sub_division", "nco_name", "area", "persons", "males", "females",
]
AREA_MAP = {"total": "TOTAL", "rural": "RURAL", "urban": "URBAN"}

OUT_COLUMNS = [
    "census_year", "census_state_code", "census_district_code", "area_name",
    "nco_2004_division", "nco_2004_sub_division", "nco_name", "row_type", "area",
    "sex", "main_workers", "geo_level", "occupation_scheme", "occupation_level",
    "universe", "observed_or_estimated", "source_id", "snapshot_file", "ingested_at",
]


def _row_type(division: str, sub_division: str, nco_name: str) -> str:
    """Classify the row so totals are never summed together with their parts.

    The table mixes four kinds of row in one column pair:
      division '0' / sub '00' / name 'TOTAL' -> the grand total over ALL occupations
      divisions 1-9 / sub '00'               -> NCO-2004 division (major group) totals
      division 'X'                           -> workers not classified by occupation
      sub != '00'                            -> sub-division detail within a division
    Aggregating without this distinction double-counts, which is why it is a
    stored column rather than a query-time convention.
    """
    if division == "0" and nco_name.strip().upper() == "TOTAL":
        return "TOTAL_ALL_OCCUPATIONS"
    # Division X carries BOTH a '00' total and a detail row. Treating every X row
    # as a total double-counts it (verified: 2,538 rows = 1,269 cells x 2).
    if division == "X":
        return "UNCLASSIFIED" if sub_division in ("00", "0", "") else "SUB_DIVISION"
    if sub_division in ("00", "0", ""):
        return "DIVISION_TOTAL"
    return "SUB_DIVISION"


def _int_or_none(v) -> int | None:
    """Blank / '-' / non-numeric is MISSING, never zero."""
    s = str(v).strip().replace(",", "")
    if s in ("", "-", "nan", "None", "NA"):
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def parse_b24(xlsx_path: Path, source_id: str, ingested_at: str) -> pd.DataFrame:
    raw = pd.read_excel(xlsx_path, sheet_name=0, header=None, dtype=str)
    body = raw.iloc[HEADER_ROW_COUNT:, : len(COLUMNS)].copy()
    body.columns = COLUMNS
    body = body[body["state_code"].notna() & body["division"].notna()]

    rows = []
    for _, r in body.iterrows():
        area = AREA_MAP.get(str(r["area"]).strip().lower())
        if area is None:
            continue
        district_code = str(r["district_code"]).strip()
        # '000' is the Census convention for the state total, not a district.
        is_state_total = district_code in ("000", "0", "")
        for sex, col in (("PERSON", "persons"), ("MALE", "males"), ("FEMALE", "females")):
            rows.append(
                {
                    "census_year": 2011,
                    "census_state_code": str(r["state_code"]).strip().zfill(2),
                    "census_district_code": None if is_state_total else district_code.zfill(3),
                    "area_name": str(r["area_name"]).strip(),
                    "nco_2004_division": str(r["division"]).strip(),
                    "nco_2004_sub_division": str(r["sub_division"]).strip(),
                    "nco_name": str(r["nco_name"]).strip(),
                    "row_type": _row_type(
                        str(r["division"]).strip(),
                        str(r["sub_division"]).strip(),
                        str(r["nco_name"]),
                    ),
                    "area": area,
                    "sex": sex,
                    "main_workers": _int_or_none(r[col]),
                    "geo_level": "STATE" if is_state_total else "DISTRICT",
                    "occupation_scheme": "NCO_2004",
                    "occupation_level": (
                        "SUB_DIVISION"
                        if str(r["sub_division"]).strip() not in ("00", "0", "")
                        else "DIVISION"
                    ),
                    "universe": "MAIN_WORKERS_NON_HOUSEHOLD_INDUSTRY",
                    "observed_or_estimated": "OBSERVED",
                    "source_id": source_id,
                    "snapshot_file": xlsx_path.name,
                    "ingested_at": ingested_at,
                }
            )
    return pd.DataFrame(rows, columns=OUT_COLUMNS)
