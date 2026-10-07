"""Build sector_master from the NQR sector listing.

Sector is a DIMENSION, not a parent of occupation: an SSC sector spans
occupations across NCO divisions and one occupation may be served by
qualifications from more than one sector. The occupation<->sector relationship
therefore belongs in a weighted bridge table, which is NOT built in Step 1
because no official weighting basis has been verified.

Extraction targets the listing's own sector links:
    <a href="https://nqr.gov.in/qualifications-search/<ID>">Sector Name</a>
The numeric ID is the portal's own sector identifier, so sector_id is taken from
the source rather than invented.
"""
from __future__ import annotations

import html as H
import re
from pathlib import Path

import pandas as pd

SECTOR_LINK_RE = re.compile(
    r'href="https?://nqr\.gov\.in/qualifications-search/(\d+)"[^>]*>\s*([^<]{2,90}?)\s*<',
    re.I,
)
# Ligatures the source page uses in some sector names.
LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}


def _clean(name: str) -> str:
    name = H.unescape(name)
    for lig, repl in LIGATURES.items():
        name = name.replace(lig, repl)
    return re.sub(r"\s+", " ", name).strip()


def parse_nqr_sectors(html_path: Path) -> pd.DataFrame:
    """Recover (portal_sector_id, sector_name) pairs from the listing page.

    The count recovered is reported by the caller and compared against NCVET's
    documented 59 sectors. A shortfall is reported, never padded.
    """
    html = html_path.read_text(errors="replace")
    found: dict[str, str] = {}
    for sid, name in SECTOR_LINK_RE.findall(html):
        cleaned = _clean(name)
        if not cleaned or cleaned.lower() in {"all sectors", "view all", "search"}:
            continue
        found.setdefault(sid, cleaned)

    rows = [
        {
            "sector_id": f"SEC_{int(sid):03d}",
            "portal_sector_id": int(sid),
            "sector_name_en": name,
            # Not published on this page. Left NULL rather than guessed; the SSC
            # name is a separate verification task.
            "ssc_name": None,
            "ssc_code": None,
            "source_id": "NQR_SECTORS",
            "valid_from": None,
            "valid_to": None,
        }
        for sid, name in sorted(found.items(), key=lambda kv: int(kv[0]))
    ]
    return pd.DataFrame(rows)
