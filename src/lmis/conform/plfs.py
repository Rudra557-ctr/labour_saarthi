"""fact_labour_force_estimate from the PLFS monthly bulletin.

Grain: period x geo_level x area x sex x age_group x indicator.

TWO HARD CONSTRAINTS, both enforced here rather than documented and forgotten:

  1. geo_level is NATIONAL for every row. The post-Jan-2025 PLFS design yields
     monthly estimates at ALL-INDIA level only; district-level estimates are not
     statistically valid. `lgd_code` is therefore NULL by design, not by omission.
  2. These are SURVEY ESTIMATES with sampling error, flagged
     observed_or_estimated='OBSERVED_SURVEY_ESTIMATE'. The monthly bulletin does
     not publish standard errors per cell, so std_error stays NULL rather than
     being filled with a guess.

PLFS measures employment and unemployment RATES. It is labour-market context and
is never demand.
"""
from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd
import pdfplumber

warnings.filterwarnings("ignore")

INDICATORS = {
    "Statement 1": "LFPR",
    "Statement 2": "WPR",
    "Statement 3": "UR",
}
AREAS = ["RURAL", "URBAN", "RURAL_URBAN"]
AGE_GROUPS = ["15-29 years", "15 years and above", "all ages"]
# Longest key first: "rural + urban" must match before "rural".
AREA_LABELS = {"rural + urban": "RURAL_URBAN", "rural": "RURAL", "urban": "URBAN"}

ROW_RE = re.compile(
    r"^(?P<prefix>.*?)(?P<age>15-29 years|15 years and above|all ages)\s+"
    r"(?P<male>\d+\.\d+)\s+(?P<female>\d+\.\d+)\s+(?P<person>\d+\.\d+)\s*$"
)

FACT_COLUMNS = [
    "period_id", "geo_level", "lgd_code", "area", "sex", "age_group",
    "indicator", "approach", "value_percent", "std_error", "unit",
    "observed_or_estimated", "source_id", "snapshot_file", "ingested_at",
]


def extract_bulletin_period(pdf_path: Path) -> str | None:
    """Read the month the bulletin itself states, e.g. 'April 2025' -> M202504."""
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join((pg.extract_text() or "") for pg in pdf.pages[:4])
    m = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)[,\s]+(\d{4})",
        text,
    )
    if not m:
        return None
    months = {
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
        "December": 12,
    }
    return f"M{m.group(2)}{months[m.group(1)]:02d}"


def _parse_statement(text: str) -> list[tuple[str, str, float, float, float]]:
    """Return (area, age_group, male, female, person) rows for one statement.

    The bulletin's layout has two quirks that defeat simpler parsers:
      * the area label is printed on the SECOND row of each three-row block, not
        the first, so tracking "last label seen" drops each block's first row;
      * the area order is not consistent between statements (Statement 3 leads
        with urban), so fixed positional assignment mislabels rows.

    So rows are grouped into blocks of three by the age-group cycle, and each
    block takes its area from whichever of its rows carries the label. That is
    independent of both label position and block order.

    The age cycle is asserted, and a block with no recoverable label raises -
    a silent layout change must break the build, not produce mislabelled facts.
    """
    matched: list[tuple[str, str, float, float, float]] = []
    for raw_line in text.splitlines():
        m = ROW_RE.match(raw_line.strip())
        if m:
            matched.append(
                (m.group("prefix").strip().lower(), m.group("age"),
                 float(m.group("male")), float(m.group("female")), float(m.group("person")))
            )

    out: list[tuple[str, str, float, float, float]] = []
    for i in range(0, len(matched) - len(matched) % 3, 3):
        block = matched[i : i + 3]
        ages = [b[1] for b in block]
        if ages != AGE_GROUPS:
            raise ValueError(f"PLFS age cycle changed: expected {AGE_GROUPS}, got {ages}")
        area = None
        for prefix, *_ in block:
            for label, mapped in AREA_LABELS.items():
                if prefix.startswith(label):
                    area = mapped
                    break
            if area:
                break
        if area is None:
            raise ValueError(f"PLFS block at row {i} carries no recoverable area label: {block}")
        for _prefix, age, male, female, person in block:
            out.append((area, age, male, female, person))
    return out


def build_labour_force_estimate(pdf_path: Path, source_id: str, ingested_at: str) -> pd.DataFrame:
    period_id = extract_bulletin_period(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        pages = [(pg.extract_text() or "") for pg in pdf.pages]

    rows = []
    for marker, indicator in INDICATORS.items():
        idx = next((i for i, t in enumerate(pages) if marker + ":" in t), None)
        if idx is None:
            continue
        # A statement's table can continue onto the following page, so join the
        # marker page with the next one, then cut at the NEXT "Statement N:"
        # marker so the following statement's rows are not absorbed.
        block = "\n".join(pages[idx : idx + 2])
        start = block.index(marker + ":")
        tail = block[start + len(marker) + 1 :]
        own_number = marker.split()[-1]
        # The bulletin REPEATS a statement's header on its continuation page, so
        # cut only at a marker bearing a DIFFERENT statement number.
        cut = None
        for m2 in re.finditer(r"Statement\s+(\d+):", tail):
            if m2.group(1) != own_number:
                cut = m2.start()
                break
        block = block[start : start + len(marker) + 1 + cut] if cut is not None else block[start:]
        parsed = _parse_statement(block)
        areas_found = {a for a, *_ in parsed}
        if len(parsed) != 9 or areas_found != set(AREAS):
            raise ValueError(
                f"PLFS {marker} ({indicator}): expected 9 rows across {sorted(AREAS)}, "
                f"got {len(parsed)} across {sorted(areas_found)} - layout changed"
            )
        for area, age, male, female, person in parsed:
            for sex, value in (("MALE", male), ("FEMALE", female), ("PERSON", person)):
                rows.append(
                    {
                        "period_id": period_id,
                        "geo_level": "NATIONAL",
                        "lgd_code": None,  # PLFS monthly is all-India; NOT an omission
                        "area": area,
                        "sex": sex,
                        "age_group": age,
                        "indicator": indicator,
                        "approach": "CWS",
                        "value_percent": value,
                        "std_error": None,  # not published per cell in the bulletin
                        "unit": "percent",
                        "observed_or_estimated": "OBSERVED_SURVEY_ESTIMATE",
                        "source_id": source_id,
                        "snapshot_file": pdf_path.name,
                        "ingested_at": ingested_at,
                    }
                )
    return pd.DataFrame(rows, columns=FACT_COLUMNS)
