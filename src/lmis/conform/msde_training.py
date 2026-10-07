"""Supply-side training data from the MSDE Annual Report 2023-24 annexures.

THE FIVE SUPPLY CONCEPTS ARE NEVER INTERCHANGEABLE, so they are stored in LONG
format - one row per measure, each carrying its own `measure` label and
`measure_definition`. A wide table invites `trained == certified` style mistakes;
long format makes every measure name explicit at the point of use.

  ENROLLED   registered for training
  TRAINED    completed the training input
  ASSESSED   underwent assessment
  CERTIFIED  passed assessment and was certified
  PLACED     reported as placed AT POINT OF REPORT - not sustained employment

Training INFRASTRUCTURE (PMKK centres) is a different concept again and goes to
its own table.

GRAIN: these annexures are STATE-level. District-level training data is not
published here and remains unavailable.

MISSINGNESS: the source writes '-' where it reports nothing. That is loaded as
NULL, never 0 - a zero would assert "nobody was placed", which the dash does not
say. The raw string is retained in `value_as_published` so the decision is
auditable and reversible.
"""
from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd
import pdfplumber

warnings.filterwarnings("ignore")

OUTCOME_MEASURES = ["ENROLLED", "TRAINED", "ASSESSED", "CERTIFIED", "PLACED"]
MEASURE_DEFINITION = {
    "ENROLLED": "candidates registered for training",
    "TRAINED": "candidates who completed the training input",
    "ASSESSED": "candidates who underwent assessment",
    "CERTIFIED": "candidates certified after assessment",
    "PLACED": "candidates reported placed at point of report; NOT sustained employment",
}
TOTAL_LABELS = {"grand total", "total", "all india", ""}

# Annexure page map, verified by reading the document.
ANNEXURES = {
    "ANNEXURE_11": {
        "page": 232,
        "scheme": "PMKVY_1.0",
        "scheme_period": "2015-16",
        "as_on": None,
        "title": "State wise training details of PMKVY 1.0 (2015-16)",
    },
    "ANNEXURE_14": {
        "page": 237,
        "scheme": "PMKVY_2.0_CSSM_STT",
        "scheme_period": "2016-20",
        "as_on": "2024-03-31",
        "title": (
            "State wise progress under Short Term Training (STT) component of "
            "CSSM - PMKVY 2.0 (as on 31.03.2024)"
        ),
    },
}
INFRA_ANNEXURE = {
    "page_range": (249, 250),
    "as_on": "2024-03-31",
    "title": "State wise details of PMKKs (as on 31.03.2024)",
}
TRADE_ANNEXURE = {"page_range": (251, 259), "title": "List of 155 NSQF Compliant Trades"}

INFRA_METRICS = [
    ("DISTRICTS_IN_STATE", "districts in the state as counted by MSDE"),
    ("DISTRICTS_WITH_PMKK", "districts having at least one PMKK"),
    ("PMKK_ALLOCATED", "PMKKs allocated"),
    ("PMKK_ESTABLISHED", "PMKKs established and operational"),
]


def _num(raw: str) -> float | None:
    """Indian-formatted integer, or None. '-' and blank are MISSING, not zero."""
    s = str(raw or "").strip()
    if s in ("", "-", "--", "NA", "N/A", "nan", "None"):
        return None
    s = re.sub(r"[^\d.]", "", s)
    if not re.search(r"\d", s):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _clean(v) -> str:
    """Normalise a PDF cell.

    The report hyphenates across line breaks, so "Andaman And Nicobar Is-\nlands"
    arrives as one cell. Rejoining a hyphen that is followed by whitespace is a
    TEXT-ARTIFACT fix, not a fuzzy geography match: it restores characters the
    typesetter split, and nothing else.
    """
    text = str(v or "").replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _state_resolver(location_master: pd.DataFrame, location_alias: pd.DataFrame):
    """Exact name then curated alias. Never fuzzy: a wrong geography join is
    invisible once made, so an unresolved name is returned as None and counted."""
    states = location_master[location_master["level"] == "STATE"]
    table = {
        _clean(n).lower().replace("&", "and"): str(c)
        for n, c in zip(states["name_en"], states["lgd_code"])
    }
    for a, c in zip(location_alias["normalised_alias"], location_alias["lgd_code"]):
        table.setdefault(_clean(a).lower().replace("&", "and"), str(c))

    def resolve(name: str) -> str | None:
        key = _clean(name).lower().replace("&", "and")
        key = re.sub(r"\s*\*+$", "", key)
        key = re.sub(r"\s+islands?$", " islands", key)
        return table.get(key)

    return resolve


def parse_training_outcomes(
    pdf_path: Path,
    location_master: pd.DataFrame,
    location_alias: pd.DataFrame,
    source_id: str,
    ingested_at: str,
) -> tuple[pd.DataFrame, list[dict]]:
    """Long-format state x scheme x measure outcomes, plus reconciliation records."""
    resolve = _state_resolver(location_master, location_alias)
    rows: list[dict] = []
    recon: list[dict] = []

    with pdfplumber.open(pdf_path) as pdf:
        for annexure, meta in ANNEXURES.items():
            table = pdf.pages[meta["page"] - 1].extract_tables()[0]
            header = [_clean(c) for c in table[0]]
            if len(header) != 7:
                raise ValueError(f"{annexure}: expected 7 columns, got {header}")
            published_total: dict[str, float | None] = {}

            for raw in table[1:]:
                cells = [_clean(c) for c in raw]
                label = cells[1] or cells[0]
                values = dict(zip(OUTCOME_MEASURES, cells[2:7]))
                if label.lower() in TOTAL_LABELS or cells[0].lower() in TOTAL_LABELS:
                    published_total = {m: _num(v) for m, v in values.items()}
                    continue
                lgd = resolve(label)
                for measure in OUTCOME_MEASURES:
                    rows.append(
                        {
                            "source_annexure": annexure,
                            "annexure_title": meta["title"],
                            "scheme": meta["scheme"],
                            "scheme_period": meta["scheme_period"],
                            "as_on_date": meta["as_on"],
                            "state_name_as_source": label,
                            "state_lgd_code": lgd,
                            "geo_level": "STATE",
                            "geography_status": "MATCHED" if lgd else "UNMATCHED",
                            "measure": measure,
                            "measure_definition": MEASURE_DEFINITION[measure],
                            "value_as_published": values[measure],
                            "value": _num(values[measure]),
                            "unit": "candidates",
                            "value_status": (
                                "AVAILABLE" if _num(values[measure]) is not None else "NO_DATA"
                            ),
                            "observed_or_estimated": "OBSERVED",
                            "source_id": source_id,
                            "snapshot_file": pdf_path.name,
                            "ingested_at": ingested_at,
                        }
                    )
            for measure in OUTCOME_MEASURES:
                extracted = sum(
                    r["value"] or 0
                    for r in rows
                    if r["source_annexure"] == annexure and r["measure"] == measure
                )
                recon.append(
                    {
                        "source_annexure": annexure,
                        "measure": measure,
                        "extracted_sum": extracted,
                        "published_total": published_total.get(measure),
                        "difference": (
                            None
                            if published_total.get(measure) is None
                            else extracted - published_total[measure]
                        ),
                        "source_id": source_id,
                        "ingested_at": ingested_at,
                    }
                )
    return pd.DataFrame(rows), recon


def parse_training_infrastructure(
    pdf_path: Path,
    location_master: pd.DataFrame,
    location_alias: pd.DataFrame,
    source_id: str,
    ingested_at: str,
) -> tuple[pd.DataFrame, list[dict]]:
    """PMKK centre counts per state - training INFRASTRUCTURE, not outcomes."""
    resolve = _state_resolver(location_master, location_alias)
    rows: list[dict] = []
    published_total: dict[str, float | None] = {}
    first, last = INFRA_ANNEXURE["page_range"]

    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(first, last + 1):
            for table in pdf.pages[pno - 1].extract_tables():
                if len(table[0]) != 6:
                    continue
                for raw in table:
                    cells = [_clean(c) for c in raw]
                    label = cells[1] or cells[0]
                    if not label or label.lower().startswith(("s no", "s� no", "state")):
                        continue
                    numbers = cells[2:6]
                    if label.lower() in TOTAL_LABELS or cells[0].lower() in TOTAL_LABELS:
                        published_total = {
                            m: _num(v) for (m, _d), v in zip(INFRA_METRICS, numbers)
                        }
                        continue
                    lgd = resolve(label)
                    for (metric, definition), value in zip(INFRA_METRICS, numbers):
                        rows.append(
                            {
                                "as_on_date": INFRA_ANNEXURE["as_on"],
                                "source_annexure": "ANNEXURE_21",
                                "annexure_title": INFRA_ANNEXURE["title"],
                                "state_name_as_source": label,
                                "state_lgd_code": lgd,
                                "geo_level": "STATE",
                                "geography_status": "MATCHED" if lgd else "UNMATCHED",
                                "metric": metric,
                                "metric_definition": definition,
                                "value_as_published": value,
                                "value": _num(value),
                                "unit": "count",
                                "value_status": (
                                    "AVAILABLE" if _num(value) is not None else "NO_DATA"
                                ),
                                "observed_or_estimated": "OBSERVED",
                                "source_id": source_id,
                                "snapshot_file": pdf_path.name,
                                "ingested_at": ingested_at,
                            }
                        )
    df = pd.DataFrame(rows).drop_duplicates(
        subset=["state_name_as_source", "metric"], keep="first"
    )
    recon = [
        {
            "source_annexure": "ANNEXURE_21",
            "measure": metric,
            "extracted_sum": float(df[df["metric"] == metric]["value"].sum()),
            "published_total": published_total.get(metric),
            "difference": (
                None
                if published_total.get(metric) is None
                else float(df[df["metric"] == metric]["value"].sum()) - published_total[metric]
            ),
            "source_id": source_id,
            "ingested_at": ingested_at,
        }
        for metric, _d in INFRA_METRICS
    ]
    return df.reset_index(drop=True), recon


def parse_training_trades(
    pdf_path: Path, source_id: str, ingested_at: str
) -> pd.DataFrame:
    """Official NSQF-compliant trade list (Annexure-22).

    NO NCO CODE IS PUBLISHED here, so `nco_2015_code` is NULL and
    `nco_mapping_status` is UNMAPPED_NO_OFFICIAL_MAPPING. A trade -> NCO mapping is
    NOT invented: see docs/step5_0_supply_data_foundation.md for the evidence that
    would be required.
    """
    first, last = TRADE_ANNEXURE["page_range"]
    rows: list[dict] = []
    # The annexure is "85 Engineering + 65 Non-Engineering + 05 trades", and the
    # serial numbering RESTARTS at each section. Keying on the serial alone
    # silently collapses the sections together (it dropped 70 trades on the first
    # attempt), so a section counter is incremented whenever the serial resets.
    section_index = 1
    previous_serial = 0
    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(first, last + 1):
            text = pdf.pages[pno - 1].extract_text() or ""
            if "Annexure-23" in text or "Flexi MoU" in text:
                break
            for table in pdf.pages[pno - 1].extract_tables():
                if len(table[0]) != 6:
                    continue
                for raw in table:
                    cells = [_clean(c) for c in raw]
                    if not re.fullmatch(r"\d+", cells[0] or ""):
                        continue
                    serial = int(cells[0])
                    if serial < previous_serial:
                        section_index += 1
                    previous_serial = serial
                    rows.append(
                        {
                            "trade_section_index": section_index,
                            "trade_serial": serial,
                            "trade_name": cells[1],
                            "entry_qualification": cells[2] or None,
                            "nsqf_level": cells[3] or None,
                            "duration": cells[4] or None,
                            "revision_year": cells[5] or None,
                            "scheme": "CRAFTSMEN_TRAINING_SCHEME",
                            "trade_scheme_source": "DGT_NSQF_COMPLIANT_TRADES",
                            "nco_2015_code": None,
                            "nco_mapping_status": "UNMAPPED_NO_OFFICIAL_MAPPING",
                            "nco_mapping_authority": None,
                            "nco_mapping_confidence": None,
                            "source_annexure": "ANNEXURE_22",
                            "annexure_title": TRADE_ANNEXURE["title"],
                            "observed_or_estimated": "OBSERVED",
                            "source_id": source_id,
                            "snapshot_file": pdf_path.name,
                            "ingested_at": ingested_at,
                        }
                    )
    df = pd.DataFrame(rows).drop_duplicates(
        subset=["trade_section_index", "trade_serial"], keep="first"
    )
    df["trade_id"] = (
        "DGT_S" + df["trade_section_index"].astype(str) + "_" + df["trade_serial"].astype(str)
    )
    return df.sort_values(["trade_section_index", "trade_serial"]).reset_index(drop=True)
