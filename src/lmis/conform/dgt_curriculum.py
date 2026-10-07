"""Official DGT CTS trade -> NCO-2015 mapping, read from DGT's own curricula.

THE EVIDENCE CHAIN (shorter and stronger than the one hypothesised in Step 5.1):

  DGT CTS curriculum "GENERAL INFORMATION" table
      -> `Trade Code`  e.g. DGT/1002
      -> `NCO - 2015`   e.g. 7233.0100, 7233.0200
      -> occupation_master (titles verified to match)

DGT publishes the NCO codes on the trade document itself, so no Qualification/QP
intermediate is needed. The Trade -> QP -> NCO chain is not required.

MULTI-NCO IS PRESERVED. Fitter maps to two NCO occupations and Electrician to two.
Both are kept as separate rows; neither is arbitrarily collapsed to one.

HOW A CURRICULUM IS LINKED TO A TRADE ROW, stated precisely because it matters:
the curriculum declares its own `Name of the Trade`, and that is matched to
`dim_training_trade.trade_name` by EXACT equality after case-folding and
whitespace normalisation, within the same scheme (CTS). Both documents are
official publications of the same CTS trade list, so this is an exact match on a
canonical name, NOT similarity matching. The Trade Code recovered from the
curriculum is stored as corroboration and as the identifier the MSDE annexure
never published.

NOTHING HERE USES fuzzy matching, embeddings, token overlap, nearest-name
matching or model-generated codes. A curriculum that states no NCO code yields no
mapping row. Note that 9 of the 155 trades contain "fitter" or "electric" in
their names (e.g. "Marine Fitter", "Electrician Power Distribution") - precisely
why similarity matching is refused.
"""
from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd
import pdfplumber

warnings.filterwarnings("ignore")

TRADE_CODE_RE = re.compile(r"Trade Code\s*[:\-]?\s*(DGT\s*/\s*\d{3,5})", re.I)
GENERAL_NCO_RE = re.compile(
    r"NCO\s*[-–]\s*2015\s*[:\-]?\s*((?:\d{4}\.\d{4}\s*,?\s*)+)", re.I
)
REFERENCE_NCO_RE = re.compile(
    r"Reference NCO\s*[-–]?\s*2015\s*:?\s*((?:\(?[ivx]+\)?\s*\)?\s*\d{4}\.\d{4}\s*[–\-]\s*[^\n]{0,60}\n?)+)",
    re.I,
)
NAME_RE = re.compile(r"Name of the Trade\s+([A-Z][A-Z0-9 \(\)&,\.\-/]{2,60}?)\s+Trade Code", re.I)
NOS_RE = re.compile(r"Reference NOS\s*:?\s*((?:\(?[ivx]+\)?\s*\)?\s*[A-Z]{2,5}/N\d{3,5}\s*,?\s*)+)", re.I)

COLUMNS = [
    "mapping_id", "dgt_trade_code", "dgt_trade_name_as_curriculum", "trade_id",
    "trade_name_as_register", "nco_2015_code", "nco_2015_title_as_curriculum",
    "nco_2015_title_in_master", "nco_mapping_level", "is_multi_nco",
    "nco_codes_for_trade", "reference_nos_codes", "mapping_status",
    "mapping_authority", "mapping_method", "mapping_confidence",
    "link_method", "evidence_field", "evidence_reference",
    "nco_code_resolves_in_master", "title_matches_master",
    "source_id", "snapshot_file", "ingested_at",
]


def _flat(pdf_path: Path) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join((pg.extract_text() or "") for pg in pdf.pages)
    return re.sub(r"[ \t]+", " ", text)


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", str(name or "")).strip().casefold()


def parse_dgt_curriculum(
    pdf_path: Path,
    trades: pd.DataFrame,
    occupation_master: pd.DataFrame,
    source_id: str,
    ingested_at: str,
) -> pd.DataFrame:
    """One row per (trade, NCO code). Empty frame if no NCO code is stated."""
    flat = _flat(pdf_path)

    code_m = TRADE_CODE_RE.search(flat)
    gen_m = GENERAL_NCO_RE.search(flat)
    if not (code_m and gen_m):
        return pd.DataFrame(columns=COLUMNS)

    trade_code = re.sub(r"\s+", "", code_m.group(1))
    nco_codes = re.findall(r"\d{4}\.\d{4}", gen_m.group(1))
    name_m = NAME_RE.search(flat)
    curriculum_trade_name = name_m.group(1).strip() if name_m else None

    # Titles as printed in the narrative "Reference NCO-2015" block, if present.
    titles: dict[str, str] = {}
    ref_m = REFERENCE_NCO_RE.search(flat)
    if ref_m:
        for code, title in re.findall(
            r"(\d{4}\.\d{4})\s*[–\-]\s*([^\n\(]{2,60})", ref_m.group(1)
        ):
            titles[code] = re.sub(r"\s+", " ", title).strip()

    nos_m = NOS_RE.search(flat)
    nos_codes = (
        "; ".join(re.findall(r"[A-Z]{2,5}/N\d{3,5}", nos_m.group(1))) if nos_m else None
    )

    # EXACT name equality within the CTS scheme. No similarity matching.
    register = trades[
        trades["trade_name"].map(_norm) == _norm(curriculum_trade_name)
    ]
    if len(register) == 1:
        trade_id = str(register.iloc[0]["trade_id"])
        register_name = str(register.iloc[0]["trade_name"])
        link_method = "EXACT_TRADE_NAME_WITHIN_CTS_SCHEME"
    else:
        # Ambiguous or absent -> no trade_id is asserted.
        trade_id = None
        register_name = None
        link_method = (
            "NO_UNIQUE_EXACT_NAME_MATCH" if len(register) != 1 else "UNKNOWN"
        )

    occ = occupation_master[occupation_master["level"] == "OCCUPATION"].set_index("nco_code")
    rows = []
    for code in nco_codes:
        resolves = code in occ.index
        master_title = str(occ.loc[code, "title_en"]) if resolves else None
        curriculum_title = titles.get(code)
        rows.append(
            {
                "mapping_id": f"DGTCTS_{trade_code.replace('/', '')}_{code}",
                "dgt_trade_code": trade_code,
                "dgt_trade_name_as_curriculum": curriculum_trade_name,
                "trade_id": trade_id,
                "trade_name_as_register": register_name,
                "nco_2015_code": code,
                "nco_2015_title_as_curriculum": curriculum_title,
                "nco_2015_title_in_master": master_title,
                # 8 digits with a decimal is the full occupation level.
                "nco_mapping_level": "NCO_OCCUPATION",
                "is_multi_nco": len(nco_codes) > 1,
                "nco_codes_for_trade": ", ".join(nco_codes),
                "reference_nos_codes": nos_codes,
                "mapping_status": "OFFICIAL_MULTI_NCO" if len(nco_codes) > 1 else "OFFICIAL_EXACT",
                "mapping_authority": "OFFICIAL",
                "mapping_method": "DGT_CTS_CURRICULUM_GENERAL_INFORMATION_NCO_2015_FIELD",
                "mapping_confidence": 1.0,
                "link_method": link_method,
                "evidence_field": "GENERAL INFORMATION table: 'Trade Code' and 'NCO - 2015'",
                "evidence_reference": f"{pdf_path.name} (DGT CTS curriculum)",
                "nco_code_resolves_in_master": resolves,
                "title_matches_master": (
                    None
                    if not (resolves and curriculum_title)
                    else _norm(curriculum_title) == _norm(master_title)
                ),
                "source_id": source_id,
                "snapshot_file": pdf_path.name,
                "ingested_at": ingested_at,
            }
        )
    return pd.DataFrame(rows, columns=COLUMNS)


def classify_trade_mapping_status(
    trades: pd.DataFrame, trade_nco_map: pd.DataFrame
) -> pd.DataFrame:
    """Assign every one of the 155 trades an explicit status. Totals must reconcile.

    MAPPING_UNKNOWN is used deliberately for the trades whose curriculum was not
    acquired: DGT demonstrably publishes NCO codes on these documents, so the
    mapping EXISTS - it simply cannot be enumerated. That is not the same as
    MAPPING_DOES_NOT_EXIST, and the distinction is preserved here.
    """
    mapped = trade_nco_map[trade_nco_map["trade_id"].notna()]
    status_by_trade = (
        mapped.groupby("trade_id")["mapping_status"].first().to_dict()
    )
    nco_by_trade = mapped.groupby("trade_id")["nco_codes_for_trade"].first().to_dict()
    code_by_trade = mapped.groupby("trade_id")["dgt_trade_code"].first().to_dict()

    rows = []
    for _, t in trades.iterrows():
        tid = str(t["trade_id"])
        if tid in status_by_trade:
            status = status_by_trade[tid]
            reason = "DGT CTS curriculum acquired; NCO-2015 field read directly"
        else:
            status = "MAPPING_UNKNOWN"
            reason = (
                "DGT publishes NCO-2015 on the CTS curriculum for this scheme, but no "
                "official index of curricula exists, so this trade's curriculum could "
                "not be enumerated. Mapping is UNKNOWN, not non-existent."
            )
        rows.append(
            {
                "trade_id": tid,
                "trade_name": t["trade_name"],
                "nsqf_level": t["nsqf_level"],
                "dgt_trade_code": code_by_trade.get(tid),
                "nco_codes_for_trade": nco_by_trade.get(tid),
                "mapping_status": status,
                "mapping_level": "NCO_OCCUPATION" if tid in status_by_trade else "UNMAPPED",
                "status_reason": reason,
            }
        )
    return pd.DataFrame(rows)
