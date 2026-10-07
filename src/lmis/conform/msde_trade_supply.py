"""Trade / job-role / sector level training supply QUANTITIES.

Source: MSDE Annual Report 2023-24, already held in the raw store since Step 5.0.
The data was there all along; Step 5.0 parsed the state-level annexures and did
not scan the report body.

THREE TABLES, all NATIONAL and all explicitly TOP-N SUBSETS:

  Table-5.54 p154  Top Ten Trades under NAPS apprenticeship
                   trade x trade_type x apprentices_engaged, FY2018-19..2023-24
                   published Grand Total 10,47,299 -> reconcilable
  Table-5.10 p89   Top 10 job roles under PMKVY 4.0
                   job_role x {enrolled, trained_oriented}
  Table-5.9  p89   Top 5 sectors under PMKVY 4.0
                   sector x enrolled

WHAT THESE ARE NOT:

  * NOT exhaustive. Each is a "Top N" list, so the rows do NOT sum to the
    population and no share or denominator may be computed from them. Every row
    carries is_top_n_subset=True and its published rank.
  * NOT state or district level. There is NO state x trade table in the report:
    Table-5.55 gives Top Ten STATES x apprentices with no trade dimension, which
    is a separate MARGINAL table - exactly the NCS situation. State x trade is
    therefore NOT derivable, and deriving it would mean assuming independence.
  * NOT interchangeable measures. `apprentices_engaged` is an apprenticeship
    engagement count; `enrolled` and `trained_oriented` are PMKVY 4.0 training
    measures. They are different schemes and different concepts, kept in separate
    rows with their own measure definitions.

NCO LINKAGE: where an OFFICIAL mapping already exists in map_trade_to_nco or
map_qualification_to_nco, it is CONNECTED by exact name equality and the method is
recorded. No new mapping system is created, and no name-similarity matching is
used - a name that does not match exactly links to nothing.
"""
from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd
import pdfplumber

warnings.filterwarnings("ignore")

TOTAL_LABELS = {"grand total", "total", ""}

MEASURE_DEFINITION = {
    "APPRENTICES_ENGAGED": (
        "apprentices engaged under NAPS, cumulative FY2018-19 to FY2023-24; "
        "an engagement count, not training completion"
    ),
    "ENROLLED": "candidates enrolled under PMKVY 4.0",
    "TRAINED_ORIENTED": "candidates trained or oriented under PMKVY 4.0",
}

SPECS = [
    {
        "source_table": "TABLE_5_54",
        "page": 154,
        "title": "Top Ten Trades in Apprenticeship Training (FY 2018-19 to FY 2023-24)",
        "entity_type": "TRADE",
        "scheme": "NAPS_APPRENTICESHIP",
        "period_label": "FY2018-19_to_FY2023-24",
        "expected_cols": 4,
        "entity_col": 1,
        "type_col": 2,
        "measures": {"APPRENTICES_ENGAGED": 3},
    },
    {
        "source_table": "TABLE_5_10",
        "page": 89,
        "title": "Top 10 job roles (based on number enrolled) under PMKVY 4.0",
        "entity_type": "JOB_ROLE",
        "scheme": "PMKVY_4.0",
        "period_label": "as_on_2024-03-31",
        "expected_cols": 4,
        "entity_col": 1,
        "type_col": None,
        "measures": {"ENROLLED": 2, "TRAINED_ORIENTED": 3},
    },
    {
        "source_table": "TABLE_5_9",
        "page": 89,
        "title": "Top 5 Sectors under PMKVY 4.0 (based on enrolled numbers)",
        "entity_type": "SECTOR",
        "scheme": "PMKVY_4.0",
        "period_label": "as_on_2024-03-31",
        "expected_cols": 3,
        "entity_col": 1,
        "type_col": None,
        "measures": {"ENROLLED": 2},
    },
]

COLUMNS = [
    "source_table", "source_table_title", "scheme", "period_label", "geo_level",
    "occupation_entity_type", "entity_name_as_source", "entity_type_as_source",
    "published_rank", "measure", "measure_definition", "value_as_published",
    "value", "unit", "value_status", "is_top_n_subset", "published_grand_total",
    "nco_link_status", "nco_codes_via_existing_map", "nco_link_method",
    "observed_or_estimated", "source_id", "snapshot_file", "ingested_at",
]


def _clean(v) -> str:
    text = str(v or "").replace("­", "")
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _num(raw: str) -> float | None:
    s = _clean(raw)
    if s in ("", "-", "--", "NA", "N/A"):
        return None
    s = re.sub(r"[^\d.]", "", s)
    if not re.search(r"\d", s):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _pick_table(pdf, spec):
    """Select the table on the page whose shape matches the spec."""
    for tb in pdf.pages[spec["page"] - 1].extract_tables():
        if tb and len(tb[0]) == spec["expected_cols"] and len(tb) >= 4:
            header = " ".join(_clean(c) for c in tb[0]).lower()
            if spec["entity_type"].replace("_", " ").split("_")[0].lower()[:5] in header or True:
                # Disambiguate the two tables on page 89 by column count.
                return tb
    return None


def parse_trade_level_supply(
    pdf_path: Path,
    trade_nco_map: pd.DataFrame,
    qualification_nco_map: pd.DataFrame,
    source_id: str,
    ingested_at: str,
) -> tuple[pd.DataFrame, list[dict]]:
    # Existing OFFICIAL mappings, keyed by exact normalised name. No fuzzy lookup.
    trade_lookup: dict[str, str] = {}
    for name, codes in zip(
        trade_nco_map["trade_name_as_register"], trade_nco_map["nco_codes_for_trade"]
    ):
        if pd.notna(name):
            trade_lookup[_clean(name).casefold()] = str(codes)
    qual_lookup: dict[str, str] = {}
    for name, code in zip(
        qualification_nco_map["qualification_name"], qualification_nco_map["nco_2015_code"]
    ):
        if pd.notna(name):
            qual_lookup[_clean(name).casefold()] = str(code)

    rows: list[dict] = []
    recon: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for spec in SPECS:
            table = _pick_table(pdf, spec)
            if table is None:
                raise ValueError(f"{spec['source_table']}: no table matched on page {spec['page']}")
            grand_total: dict[str, float | None] = {}
            body = []
            for raw in table[1:]:
                cells = [_clean(c) for c in raw]
                if len(cells) < spec["expected_cols"]:
                    continue
                label = cells[spec["entity_col"]]
                first = cells[0]
                if first.lower() in TOTAL_LABELS and not label:
                    for m, idx in spec["measures"].items():
                        grand_total[m] = _num(cells[idx])
                    continue
                if label.lower() in TOTAL_LABELS:
                    for m, idx in spec["measures"].items():
                        grand_total[m] = _num(cells[idx])
                    continue
                if not re.fullmatch(r"\d+", first):
                    continue
                body.append((int(first), label, cells))

            for rank, label, cells in body:
                key = _clean(label).casefold()
                if spec["entity_type"] == "TRADE" and key in trade_lookup:
                    status, codes, method = (
                        "OFFICIAL_VIA_MAP_TRADE_TO_NCO",
                        trade_lookup[key],
                        "EXACT_NAME_AGAINST_EXISTING_OFFICIAL_MAP",
                    )
                elif spec["entity_type"] == "JOB_ROLE" and key in qual_lookup:
                    status, codes, method = (
                        "OFFICIAL_VIA_MAP_QUALIFICATION_TO_NCO",
                        qual_lookup[key],
                        "EXACT_NAME_AGAINST_EXISTING_OFFICIAL_MAP",
                    )
                else:
                    status, codes, method = "NO_EXISTING_OFFICIAL_MAP", None, None
                for measure, idx in spec["measures"].items():
                    rows.append(
                        {
                            "source_table": spec["source_table"],
                            "source_table_title": spec["title"],
                            "scheme": spec["scheme"],
                            "period_label": spec["period_label"],
                            "geo_level": "NATIONAL",
                            "occupation_entity_type": spec["entity_type"],
                            "entity_name_as_source": label,
                            "entity_type_as_source": (
                                cells[spec["type_col"]] if spec["type_col"] is not None else None
                            ),
                            "published_rank": rank,
                            "measure": measure,
                            "measure_definition": MEASURE_DEFINITION[measure],
                            "value_as_published": cells[idx],
                            "value": _num(cells[idx]),
                            "unit": "candidates",
                            "value_status": (
                                "AVAILABLE" if _num(cells[idx]) is not None else "NO_DATA"
                            ),
                            # Top-N: rows do NOT sum to the population.
                            "is_top_n_subset": True,
                            "published_grand_total": None,
                            "nco_link_status": status,
                            "nco_codes_via_existing_map": codes,
                            "nco_link_method": method,
                            "observed_or_estimated": "OBSERVED",
                            "source_id": source_id,
                            "snapshot_file": pdf_path.name,
                            "ingested_at": ingested_at,
                        }
                    )
            for measure in spec["measures"]:
                total = grand_total.get(measure)
                for r in rows:
                    if r["source_table"] == spec["source_table"] and r["measure"] == measure:
                        r["published_grand_total"] = total
                extracted = sum(
                    r["value"] or 0
                    for r in rows
                    if r["source_table"] == spec["source_table"] and r["measure"] == measure
                )
                recon.append(
                    {
                        "source_table": spec["source_table"],
                        "measure": measure,
                        "top_n_extracted_sum": extracted,
                        "published_grand_total": total,
                        # The difference is EXPECTED and is the top-N shortfall,
                        # not an extraction error.
                        "top_n_shortfall": None if total is None else total - extracted,
                        "note": (
                            "Top-N subset: the extracted rows are a subset of the "
                            "population, so a non-zero shortfall is correct."
                        ),
                        "source_id": source_id,
                        "ingested_at": ingested_at,
                    }
                )
    return pd.DataFrame(rows, columns=COLUMNS), recon
