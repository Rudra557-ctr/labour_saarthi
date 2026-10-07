"""Build occupation_master (the NCO-2015 spine) from the official DGE NAT table.

Source: data/raw/NCO_2015_NAT_TABLE/<date>/nat_page_*.html

Code structure is NOT inferred - it is as documented in NCVET's "Report on
Mapping of Qualifications with NCO Codes" (22 Aug 2023), Annexure IX s.3:

    8-digit structure, decimal after the first four digits: DDDD.OOQQ
      digit 1      -> Division        (ISCO-08 Major Group)
      digits 1-2   -> Sub-Division    (Sub-Major Group)
      digits 1-3   -> Group           (Minor Group)
      digits 1-4   -> Family          (Unit Group)
      digits 5-6   -> occupation within the Family
      digits 7-8   -> QP/NOS availability: 00 = no QP/NOS, 01-99 = QP/NOS exists

The last rule means the NCO code itself carries a QP/NOS-existence signal. It is
surfaced as a column (`qp_nos_indicated`) rather than acted upon here.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from lmis.common.htmltable import extract_tables

EXPECTED_HEADER = [
    "S.No.",
    "Occupational Title",
    "NCO 2015",
    "NCO 2004",
    "Division",
    "Sub Division",
    "Group",
    "Family",
]
CODE_RE = re.compile(r"^\d{4}\.\d{4}$")

LEVELS = (
    ("DIVISION", 1),
    ("SUB_DIVISION", 2),
    ("GROUP", 3),
    ("FAMILY", 4),
)


def parse_nat_snapshot(snapshot_dir: Path) -> pd.DataFrame:
    """Parse every nat_page_*.html in a snapshot into one raw row set."""
    frames = []
    for page_file in sorted(snapshot_dir.glob("nat_page_*.html")):
        html = page_file.read_text(errors="replace")
        for tbl in extract_tables(html):
            if not tbl or tbl[0][: len(EXPECTED_HEADER)] != EXPECTED_HEADER:
                continue
            for row in tbl[1:]:
                if len(row) < len(EXPECTED_HEADER):
                    continue
                frames.append(
                    {
                        "source_file": page_file.name,
                        "occupational_title": row[1],
                        "nco_2015": row[2].strip(),
                        "nco_2004": row[3].strip() or None,
                        "division_title": row[4],
                        "sub_division_title": row[5],
                        "group_title": row[6],
                        "family_title": row[7],
                    }
                )
    df = pd.DataFrame(frames)
    if df.empty:
        raise RuntimeError(f"no NAT table rows parsed from {snapshot_dir}")
    return df


def build_occupation_master(raw: pd.DataFrame, source_id: str, ingested_at: str) -> pd.DataFrame:
    """Explode the flat table into one row per hierarchy node.

    Titles for Division/Sub-Division/Group/Family come from the source's own
    columns; their CODES are derived from the documented digit positions of the
    occupation code. Nothing is invented: a node exists only because at least
    one official row implies it.
    """
    valid = raw[raw["nco_2015"].str.match(CODE_RE, na=False)].copy()
    rows: list[dict] = []

    # Hierarchy nodes
    for level_name, width in LEVELS:
        title_col = {
            "DIVISION": "division_title",
            "SUB_DIVISION": "sub_division_title",
            "GROUP": "group_title",
            "FAMILY": "family_title",
        }[level_name]
        tmp = valid.assign(code=valid["nco_2015"].str[:width])
        for code, grp in tmp.groupby("code", sort=True):
            titles = sorted({t for t in grp[title_col] if t})
            rows.append(
                {
                    "nco_version": "2015",
                    "nco_code": code,
                    "level": level_name,
                    "parent_nco_code": code[: width - 1] if width > 1 else None,
                    "title_en": titles[0] if titles else None,
                    "title_variant_count": len(titles),
                    "qp_nos_indicated": None,
                    "nco_2004_code": None,
                    "source_id": source_id,
                    "ingested_at": ingested_at,
                }
            )

    # Occupation nodes (8-digit)
    for _, r in valid.iterrows():
        code = r["nco_2015"]
        last_two = code[-2:]
        rows.append(
            {
                "nco_version": "2015",
                "nco_code": code,
                "level": "OCCUPATION",
                "parent_nco_code": code[:4],
                "title_en": r["occupational_title"],
                "title_variant_count": 1,
                # Per Annexure IX s.3: 00 means no QP/NOS, 01-99 means one exists.
                "qp_nos_indicated": None if last_two == "" else (last_two != "00"),
                "nco_2004_code": r["nco_2004"],
                "source_id": source_id,
                "ingested_at": ingested_at,
            }
        )

    out = pd.DataFrame(rows)
    # Occupation codes can legitimately repeat across pages only if the portal
    # duplicates them; collapse exact duplicates, keep genuine conflicts visible.
    out = out.drop_duplicates(subset=["nco_version", "nco_code", "level", "title_en"])
    return out.sort_values(["level", "nco_code"]).reset_index(drop=True)


def build_nco2004_concordance(raw: pd.DataFrame, source_id: str, ingested_at: str) -> pd.DataFrame:
    """OFFICIAL NCO-2004 <-> NCO-2015 concordance, as published in the same table.

    authority=OFFICIAL because the mapping is printed by the publisher of both
    classifications. Rows where the source leaves NCO 2004 blank are retained
    with nco_2004_code NULL - missing stays missing.
    """
    valid = raw[raw["nco_2015"].str.match(CODE_RE, na=False)]
    out = valid[["nco_2015", "nco_2004", "occupational_title"]].copy()
    out.columns = ["nco_2015_code", "nco_2004_code", "occupational_title"]
    out["authority"] = "OFFICIAL"
    out["method"] = "PUBLISHED_TABLE"
    out["confidence"] = 1.0
    out["source_id"] = source_id
    out["ingested_at"] = ingested_at
    return out.reset_index(drop=True)
