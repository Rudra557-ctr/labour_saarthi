"""Extract the OFFICIAL qualification -> NCO-2015 mapping from an NQR Q-File.

THE EVIDENCE CHAIN, verified end to end in Step 5.1:

  NQR Q-File field 14 "Aligned to NCO/ISCO Code/s"
      -> "NCO- 2015/4132.0402"
      -> occupation_master row 4132.0402, title "Domestic Data Entry Operator"
      -> identical to the qualification's own name
      -> qp_nos_indicated = True (NCO digits 7-8 = '02', not '00', which per the
         NCVET handbook signals that a QP/NOS exists for that job role)

Three independent sources agree, so this mapping is `authority='OFFICIAL'` with
confidence 1.0 - it is read out of a government document, not inferred.

WHAT THIS IS NOT: a trade -> NCO mapping. These are NQR QUALIFICATIONS. The 155
DGT Craftsmen Training Scheme trades in `dim_training_trade` are different
objects, and the trade -> qualification link is not published in anything we
hold. `dim_training_trade` therefore stays UNMAPPED.

NO fuzzy matching, no embeddings, no name similarity, no model-generated codes are
used anywhere in this module. A Q-File that does not state a code yields no row.
"""
from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd
import pdfplumber

warnings.filterwarnings("ignore")

# Field 14 of the Qualification File template.
NCO_FIELD_RE = re.compile(
    r"Aligned to NCO\s*/\s*ISCO Code/s.{0,120}?NCO[-\s]*2015\s*/\s*(\d{4}\.\d{4})",
    re.I | re.S,
)
NAME_RE = re.compile(r"Qualification Name[:\s]*(.{3,80}?)\s+\d{1,2}\.", re.I | re.S)
NSQF_RE = re.compile(r"NSQF Level[:\s]*(\d\.?\d?)", re.I)
# The published filename carries the awarding-body qualification code.
FILENAME_CODE_RE = re.compile(r"^QF_([A-Z0-9]+)_(.+?)_V(\d+)\.pdf$", re.I)

COLUMNS = [
    "mapping_id", "qualification_name", "qualification_code", "qfile_version",
    "nsqf_level", "nco_2015_code", "nco_2015_title", "nco_mapping_level",
    "mapping_authority", "mapping_method", "mapping_confidence",
    "evidence_field", "evidence_reference", "title_matches_nco_title",
    "nco_code_resolves_in_master", "qp_nos_indicated_by_nco_code",
    "applies_to_dgt_cts_trade", "source_id", "snapshot_file", "ingested_at",
]


def parse_qfile_nco_mapping(
    pdf_path: Path, occupation_master: pd.DataFrame, source_id: str, ingested_at: str
) -> pd.DataFrame:
    """Return zero or one mapping row. Zero if the Q-File states no NCO code."""
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join((pg.extract_text() or "") for pg in pdf.pages)
    flat = re.sub(r"\s+", " ", text)

    nco_match = NCO_FIELD_RE.search(flat)
    if not nco_match:
        # No code stated -> no row. Nothing is guessed.
        return pd.DataFrame(columns=COLUMNS)
    nco_code = nco_match.group(1)

    name_match = NAME_RE.search(flat)
    qualification_name = name_match.group(1).strip() if name_match else None
    nsqf_match = NSQF_RE.search(flat)

    fn = FILENAME_CODE_RE.match(pdf_path.name)
    qualification_code = fn.group(1) if fn else None
    qfile_version = fn.group(3) if fn else None

    occ = occupation_master[
        (occupation_master["nco_code"] == nco_code)
        & (occupation_master["level"] == "OCCUPATION")
    ]
    resolves = bool(len(occ))
    nco_title = str(occ.iloc[0]["title_en"]) if resolves else None
    qp_flag = bool(occ.iloc[0]["qp_nos_indicated"]) if resolves else None
    title_match = (
        None
        if not (resolves and qualification_name)
        else qualification_name.strip().lower() == str(nco_title).strip().lower()
    )

    return pd.DataFrame(
        [
            {
                "mapping_id": f"QFILE_{qualification_code or 'UNKNOWN'}_{nco_code}",
                "qualification_name": qualification_name,
                "qualification_code": qualification_code,
                "qfile_version": qfile_version,
                "nsqf_level": nsqf_match.group(1) if nsqf_match else None,
                "nco_2015_code": nco_code,
                "nco_2015_title": nco_title,
                # 8 digits with a decimal = the full OCCUPATION level, the finest
                # the taxonomy has. Not downgraded.
                "nco_mapping_level": "OCCUPATION",
                "mapping_authority": "OFFICIAL",
                "mapping_method": "QFILE_FIELD_14_ALIGNED_TO_NCO_ISCO_CODE",
                "mapping_confidence": 1.0,
                "evidence_field": "Q-File field 14: Aligned to NCO/ISCO Code/s",
                "evidence_reference": f"{pdf_path.name} (NQR qualification file)",
                "title_matches_nco_title": title_match,
                "nco_code_resolves_in_master": resolves,
                "qp_nos_indicated_by_nco_code": qp_flag,
                # These are NQR qualifications, NOT the 155 DGT CTS trades.
                "applies_to_dgt_cts_trade": False,
                "source_id": source_id,
                "snapshot_file": pdf_path.name,
                "ingested_at": ingested_at,
            }
        ],
        columns=COLUMNS,
    )


def build_supply_evidence_matrix(built_at: str) -> pd.DataFrame:
    """The Step 5.1 evidence matrix, stored as data so the decisions are queryable.

    Every REJECTED / UNAVAILABLE / ACCESS_PENDING row carries a concrete reason.
    """
    rows = [
        # blocker, source, resource, publisher, url, access_status, vintage, grain,
        # district, trade, occupation, measure, nco_mapping, decision, reason
        ("A_DISTRICT_SUPPLY", "data.gov.in", "PMKVY district enrolled/trained/assessed/certified/placed",
         "MSDE", "https://www.data.gov.in/resource/district-wise-enrolled-trained-assessed-certified-placed-under-pmkvy-21-april-2022",
         "ACCESS_PENDING", "as on 2022-04-21", "district x scheme training type", True, False, False, True, False,
         "ACCESS_PENDING",
         "Resource page names PMKVY-210422.csv but publishes no datafile_url; the constructed path "
         "returns HTTP 404 even on the apex host that served LGD and Udyam. A registered data.gov.in "
         "API key is required and the project holds none."),
        ("A_DISTRICT_SUPPLY", "data.gov.in", "ITI seating capacity resources",
         "MSDE / DGT", "https://www.data.gov.in/", "UNAVAILABLE", "2016 and earlier",
         "state/UT x ITI type", False, False, False, True, False, "REJECTED",
         "Published at state/UT level only; no district dimension exists to acquire."),
        ("A_DISTRICT_SUPPLY", "AIKosh (IndiaAI)", "catalogue of 346 datasets",
         "IndiaAI / MeitY", "https://aikosh.indiaai.gov.in/home/datasets.html", "ACQUIRED_METADATA_ONLY",
         "2026", "n/a", False, False, False, False, False, "REJECTED",
         "Probed its SSR state: it is an AI model/dataset hub. Its one education-and-skill category "
         "contains no training statistics."),
        ("A_DISTRICT_SUPPLY", "DGT", "dgt.gov.in site",
         "DGT, MSDE", "https://www.dgt.gov.in/", "UNAVAILABLE", "2026", "n/a",
         False, False, False, False, False, "REJECTED",
         "Site publishes notices and circulars only; no ITI directory, capacity or admissions dataset. "
         "robots.txt itself returns HTTP 403."),
        ("A_DISTRICT_SUPPLY", "NCVT MIS", "ncvtmis.gov.in",
         "DGT, MSDE", "https://www.ncvtmis.gov.in/", "UNAVAILABLE", "unknown", "unknown",
         None, None, None, None, False, "UNAVAILABLE",
         "Host unreachable (connection timeout) in Steps 1.5-1.7 and not reachable in 5.1."),
        ("A_DISTRICT_SUPPLY", "MSDE Annual Report 2023-24", "Annexure-21 PMKKs",
         "MSDE", "https://www.msde.gov.in/", "ACQUIRED", "as on 2024-03-31",
         "state x PMKK metric", False, False, False, True, False, "ACQUIRED",
         "Already loaded in Step 5.0. Reports a district COUNT per state, which is NOT district-level "
         "training supply - the distinction is preserved."),
        ("B_TRADE_NCO", "NQR", "Q-File field 14 'Aligned to NCO/ISCO Code/s'",
         "NCVET", "https://nqr.gov.in/qualification/file/QF_SSC2212_Domestic%20Data%20Entry%20Operator_V3.pdf",
         "ACQUIRED", "V3", "qualification", False, False, True, False, True, "ACQUIRED",
         "PROVEN: the Q-File states NCO-2015/4132.0402 at full 8-digit occupation level. It resolves in "
         "occupation_master to the identical title, and qp_nos_indicated=True independently corroborates "
         "it. This is the official qualification -> NCO evidence chain."),
        ("B_TRADE_NCO", "NQR", "filter-search bulk qualification listing",
         "NCVET", "https://nqr.gov.in/filter-search", "UNAVAILABLE", "2026", "qualification",
         False, False, True, False, True, "UNAVAILABLE",
         "POST returns HTTP 500 Server Error for every parameter combination tried, including with the "
         "page's own CSRF token. No sitemap.xml exists, so Q-File URLs cannot be enumerated by any "
         "sanctioned route. URL brute-forcing was not attempted."),
        ("B_TRADE_NCO", "NCVET", "Report on Mapping of Qualifications with NCO Codes",
         "NCVET", "https://ncvet.gov.in/wp-content/uploads/2025/05/Report-on-Mapping-of-Qualifications-with-NCO-Codes.pdf",
         "ACQUIRED", "2023-08-22", "awarding body", False, False, False, False, False, "ACQUIRED",
         "Already held from Step 1. Establishes that every NSQF qualification must carry an NCO code and "
         "audits mapping quality per awarding body, but publishes no per-qualification crosswalk table."),
        # ---- Step 5.3: trade-level supply quantities ----
        ("C_TRADE_LEVEL_SUPPLY", "MSDE Annual Report 2023-24",
         "Table-5.54 Top Ten Trades in Apprenticeship Training (NAPS)",
         "MSDE", "https://www.msde.gov.in/", "ACQUIRED", "FY2018-19 to FY2023-24",
         "national x trade x apprentices engaged", False, True, False, True, False, "PARTIALLY_ACQUIRED",
         "Real trade-level supply QUANTITIES, but NATIONAL and a TOP-10 SUBSET only. Rows do not sum to "
         "the population. Electrician (214,271) and Fitter (206,676) connect to official NCO codes via "
         "map_trade_to_nco."),
        ("C_TRADE_LEVEL_SUPPLY", "MSDE Annual Report 2023-24",
         "Table-5.10 Top 10 job roles under PMKVY 4.0",
         "MSDE", "https://www.msde.gov.in/", "ACQUIRED", "as on 2024-03-31",
         "national x job role x {enrolled, trained/oriented}", False, True, False, True, False,
         "PARTIALLY_ACQUIRED",
         "Real job-role-level supply QUANTITIES, NATIONAL and TOP-10 only, with no printed total. "
         "Domestic Data Entry Operator connects to NCO 4132.0402 via map_qualification_to_nco."),
        ("C_TRADE_LEVEL_SUPPLY", "MSDE Annual Report 2023-24",
         "Table-5.55 Top Ten States engaging Apprentices",
         "MSDE", "https://www.msde.gov.in/", "ACQUIRED", "FY2016-17 to FY2023-24",
         "national x state x apprentices engaged", False, False, False, True, False, "REJECTED",
         "State-level apprentices with NO trade dimension. It is a separate MARGINAL table alongside "
         "Table-5.54, so state x trade cannot be derived from the pair without assuming independence - "
         "the same situation as the NCS state/sector marginals."),
        ("C_TRADE_LEVEL_SUPPLY", "apprenticeshipindia.gov.in (NAPS portal)",
         "portal cited as the source of Tables 5.54/5.55",
         "MSDE / NSDC", "https://www.apprenticeshipindia.gov.in/", "UNAVAILABLE", "live",
         "unknown", None, None, None, None, False, "UNAVAILABLE",
         "Client-rendered SPA: every path including /robots.txt and /reports returns the same 75KB shell "
         "with 0 table rows, 0 mentions of 'trade' and no downloadable files. No server-rendered data and "
         "no sanctioned export; protected endpoints were not reverse-engineered."),
        ("C_TRADE_LEVEL_SUPPLY", "bharatskills.gov.in", "CTS trade statistics",
         "DGT, MSDE", "https://bharatskills.gov.in/Home/CTS", "UNAVAILABLE", "2026",
         "n/a", False, True, False, False, False, "REJECTED",
         "Client-rendered; exposes curriculum documents only, no quantitative trade participation, "
         "enrolment or examination data in its HTML."),
        ("C_TRADE_LEVEL_SUPPLY", "NQR", "qualification records",
         "NCVET", "https://nqr.gov.in/", "ACQUIRED_METADATA_ONLY", "2026", "qualification",
         False, False, True, False, True, "REJECTED",
         "NQR publishes qualification METADATA (NSQF level, NOS, NCO code), not supply statistics. A "
         "Q-File NCO code is taxonomy evidence, not enrolment or certification counts."),
        ("C_TRADE_LEVEL_SUPPLY", "MSDE Annual Report 2023-24",
         "Tables 5.20/5.22 State-wise ITIs affiliated for Drone courses",
         "MSDE", "https://www.msde.gov.in/", "ACQUIRED", "sessions 2022 and 2023",
         "state x course x ITI count", False, True, False, True, False, "REJECTED",
         "This is a count of INSTITUTES offering a course, not trainee supply. Counting institutes and "
         "calling it supply is exactly the conflation the methodology forbids."),
        ("B_TRADE_NCO", "MSDE Annual Report 2023-24", "Annexure-22 155 NSQF-compliant trades",
         "MSDE", "https://www.msde.gov.in/", "ACQUIRED", "2022 revisions", "trade",
         False, True, False, False, False, "PARTIALLY_ACQUIRED",
         "Trades carry NSQF level, entry qualification and duration but NO NCO code, and no trade -> "
         "qualification link is published. Mapping therefore remains UNMAPPED for all 155."),
    ]
    cols = ["blocker", "source", "resource", "official_publisher", "url", "access_status",
            "vintage", "grain", "district_available", "trade_available",
            "occupation_available", "measure_available", "nco_mapping_available",
            "decision", "reason"]
    df = pd.DataFrame(rows, columns=cols)
    df["access_date"] = "2026-10-04"
    df["built_at"] = built_at
    return df
