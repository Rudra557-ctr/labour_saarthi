"""NCS vacancy facts from Parliament answer PDFs.

TWO SEPARATE TABLES, deliberately:
  fact_vacancy_official_by_state   (39 rows per answer, absolute counts)
  fact_vacancy_official_by_sector  (22 rows per answer, in lakh)

They are NOT joined, because the source publishes them as independent MARGINAL
tables. There is no joint state x sector cross-tabulation, and producing one
would require assuming independence - i.e. fabricating it.

Two more things recorded rather than smoothed over:
  * the measure is CUMULATIVE SINCE INCEPTION, a stock and not a flow;
  * "Multiple States/PAN India" is a real category (the employer posted
    nationwide), so it is kept as a flagged NATIONAL row, never redistributed.
"""
from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd
import pdfplumber

warnings.filterwarnings("ignore")

PAN_INDIA_LABELS = {"multiple states/pan india", "multiple states / pan india", "pan india"}
GRAND_TOTAL_LABELS = {"grand total", "total"}

STATE_FACT_COLUMNS = [
    "snapshot_date", "lgd_code", "geo_level", "state_name_as_source",
    "vacancies_cumulative", "unit", "measure_basis", "is_pan_india_residual",
    "observed_or_estimated", "source_id", "snapshot_file", "ingested_at",
]
SECTOR_FACT_COLUMNS = [
    "snapshot_date", "ncs_sector_name", "nic_section_code", "vacancies_cumulative",
    "unit", "measure_basis", "observed_or_estimated", "source_id",
    "snapshot_file", "ingested_at",
]


def extract_as_on_date(pdf_path: Path) -> str | None:
    """Read the 'As on <date>' the answer itself states. Never defaulted to the
    download date - if the document does not say it, it stays None."""
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join((pg.extract_text() or "") for pg in pdf.pages[:3])
    text = re.sub(r"\s+", " ", text)
    m = re.search(
        r"As on\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Z][a-z]+),?\s+(\d{4})", text
    )
    if not m:
        return None
    day, month, year = m.groups()
    months = {
        "January": "01", "February": "02", "March": "03", "April": "04",
        "May": "05", "June": "06", "July": "07", "August": "08",
        "September": "09", "October": "10", "November": "11", "December": "12",
    }
    mm = months.get(month)
    return f"{year}-{mm}-{int(day):02d}" if mm else None


def _num(v: str) -> float | None:
    """Parse a published figure. Anything without a digit (blank, '-', a stray
    '.') is MISSING and returns None - it is never coerced to zero."""
    s = re.sub(r"[^\d.]", "", str(v or ""))
    if not re.search(r"\d", s):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _find_tables(pdf_path: Path, needle: str) -> list[list[list[str | None]]]:
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            text = pg.extract_text() or ""
            if needle.lower() in text.lower():
                out.extend(pg.extract_tables())
    return out


def build_vacancy_by_state(
    pdf_path: Path,
    source_id: str,
    ingested_at: str,
    location_master: pd.DataFrame,
    location_alias: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Resolve each published state name to an LGD code.

    Resolution is exact-name first, then the curated alias table. Nothing is
    fuzzy-matched: a wrong geography join is invisible afterwards. A name that
    resolves to neither is loaded with lgd_code NULL so the miss is visible and
    countable rather than silently dropped.
    """
    snapshot_date = extract_as_on_date(pdf_path)
    states = location_master[location_master["level"] == "STATE"]
    by_name = {str(n).strip().lower(): str(c) for n, c in zip(states["name_en"], states["lgd_code"])}
    if location_alias is not None and len(location_alias):
        for alias, code in zip(location_alias["normalised_alias"], location_alias["lgd_code"]):
            by_name.setdefault(str(alias).strip().lower(), str(code))

    rows = []
    for tbl in _find_tables(pdf_path, "State wise"):
        for raw in tbl:
            cells = [(c or "").strip() for c in raw]
            if len(cells) < 2 or not cells[0]:
                continue
            label, value = cells[0], cells[1]
            low = label.lower()
            if low in GRAND_TOTAL_LABELS or "state name" in low or "vacancy mobilized" in low:
                continue
            n = _num(value)
            if n is None:
                continue
            is_pan = low in PAN_INDIA_LABELS
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    # PAN-India has no geography by definition -> NULL, NATIONAL.
                    "lgd_code": None if is_pan else by_name.get(low),
                    "geo_level": "NATIONAL" if is_pan else "STATE",
                    "state_name_as_source": label,
                    "vacancies_cumulative": int(n),
                    "unit": "count",
                    "measure_basis": "CUMULATIVE_SINCE_INCEPTION",
                    "is_pan_india_residual": is_pan,
                    "observed_or_estimated": "OBSERVED",
                    "source_id": source_id,
                    "snapshot_file": pdf_path.name,
                    "ingested_at": ingested_at,
                }
            )
    return pd.DataFrame(rows, columns=STATE_FACT_COLUMNS).drop_duplicates(
        subset=["snapshot_date", "state_name_as_source", "snapshot_file"]
    )


def build_vacancy_by_sector(
    pdf_path: Path, source_id: str, ingested_at: str, sector_nic_map: pd.DataFrame
) -> pd.DataFrame:
    snapshot_date = extract_as_on_date(pdf_path)
    nic_by_sector = dict(zip(sector_nic_map["ncs_sector_name"], sector_nic_map["section_code"]))

    rows = []
    for tbl in _find_tables(pdf_path, "Sector wise"):
        for raw in tbl:
            cells = [(c or "").strip() for c in raw]
            if len(cells) < 2 or not cells[0]:
                continue
            label, value = cells[0], cells[1]
            low = label.lower()
            if low in GRAND_TOTAL_LABELS or "sector wise" in low or "no. of vacancies" in low:
                continue
            n = _num(value)
            if n is None:
                continue
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "ncs_sector_name": label,
                    "nic_section_code": nic_by_sector.get(label),
                    "vacancies_cumulative": n,
                    "unit": "lakh",  # as published; NOT silently converted
                    "measure_basis": "CUMULATIVE_SINCE_INCEPTION",
                    "observed_or_estimated": "OBSERVED",
                    "source_id": source_id,
                    "snapshot_file": pdf_path.name,
                    "ingested_at": ingested_at,
                }
            )
    return pd.DataFrame(rows, columns=SECTOR_FACT_COLUMNS).drop_duplicates(
        subset=["snapshot_date", "ncs_sector_name", "snapshot_file"]
    )
