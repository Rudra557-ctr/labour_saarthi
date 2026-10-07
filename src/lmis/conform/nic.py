"""NIC-2008 section master, and the NCS-sector -> NIC-section alignment.

Step 1.7 verified that the NCS vacancy "sector" vocabulary IS the NIC-2008
section list: all 20 substantive categories align one-to-one by name. That makes
the NCS sector dimension an INDUSTRY dimension.

The alignment below is therefore industry->industry, which is legitimate. It is
NOT an industry->occupation crosswalk: that relationship is many-to-many and no
such mapping is created anywhere in this project.

Every row carries authority='PROJECT' with a confidence, because the alignment is
ours (verified by name against the official NIC document), not a published GoI
crosswalk.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# The title cap must be generous: NIC section T's title is 122 characters
# ("Activities of households as employers; undifferentiated goods- and services
# producing activities of households for own use"). A 95-char cap silently
# dropped it, which only surfaced when a fact row referenced section T.
SECTION_RE = re.compile(
    r"\bSection\s+([A-U])\b[\s\-:]{0,4}([A-Za-z][A-Za-z,;&\-\s/]{8,170}?)(?:\s+Division|\s+\d|\s*$)"
)

# Verified 2026-10-02 against NIC_2008.pdf (section titles) and against the NCS
# sector names extracted from the Parliament answer tables.
# section_code None => deliberately unmapped.
NCS_SECTOR_TO_NIC = {
    "Agriculture and Related": ("A", 0.95, "NIC A: Agriculture, forestry and fishing"),
    "Mining And Quarrying": ("B", 0.99, "NIC B: Mining and quarrying - name identical"),
    "Manufacturing": ("C", 0.99, "NIC C: Manufacturing - name identical"),
    "Power and Energy": ("D", 0.90, "NIC D: Electricity, gas, steam and air conditioning supply"),
    "Water Supply, Sewerage and Waste Management": (
        "E", 0.97, "NIC E: Water supply; sewerage, waste management and remediation"),
    "Civil and Construction Works": ("F", 0.95, "NIC F: Construction"),
    "Wholesale and Retail": ("G", 0.95, "NIC G: Wholesale and retail trade; repair of motor vehicles"),
    "Transportation and Storage": ("H", 0.99, "NIC H: Transportation and storage - name identical"),
    "Hotels, Food Service and Catering": ("I", 0.95, "NIC I: Accommodation and food service activities"),
    "IT and Communication": ("J", 0.92, "NIC J: Information and communication"),
    "Finance and Insurance": ("K", 0.97, "NIC K: Financial and insurance activities"),
    "Real Estate Activities": ("L", 0.99, "NIC L: Real estate activities - name identical"),
    "Specialized Professional Services": (
        "M", 0.85, "NIC M: Professional, scientific and technical activities - BROAD, heterogeneous"),
    "Operations and Support": (
        "N", 0.80, "NIC N: Administrative and support service activities - BROAD, heterogeneous"),
    "Public Administration and Defense": (
        "O", 0.97, "NIC O: Public administration and defence; compulsory social security"),
    "Education": ("P", 0.99, "NIC P: Education - name identical"),
    "Health": ("Q", 0.95, "NIC Q: Human health and social work activities"),
    "Arts and Entertainment": ("R", 0.95, "NIC R: Arts, entertainment and recreation"),
    "Other Service Activities": (
        "S", 0.80, "NIC S: Other service activities - RESIDUAL by construction"),
    "Household and Domestic Work": (
        "T", 0.90, "NIC T: Activities of households as employers"),
    # Deliberately unmapped - carries no information about industry at all.
    "Sector Not Specified": (None, None, "No industry information; must remain unallocated"),
}


def parse_nic_sections(pdf_path: Path) -> pd.DataFrame:
    """Extract section codes and titles from the official NIC-2008 PDF."""
    import warnings

    import pdfplumber

    warnings.filterwarnings("ignore")
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join((pg.extract_text() or "") for pg in pdf.pages)
    text = re.sub(r"\s+", " ", text)

    found: dict[str, str] = {}
    for m in SECTION_RE.finditer(text):
        found.setdefault(m.group(1), re.sub(r"\s+", " ", m.group(2)).strip())
    return pd.DataFrame(
        [{"nic_version": "2008", "section_code": k, "section_title_en": v} for k, v in sorted(found.items())]
    )


def build_ncs_sector_to_nic_map(reviewed_at: str) -> pd.DataFrame:
    rows = []
    for name, (code, conf, rationale) in NCS_SECTOR_TO_NIC.items():
        rows.append(
            {
                "ncs_sector_name": name,
                "nic_version": "2008" if code else None,
                "section_code": code,
                "authority": "PROJECT",
                "method": "NAME_ALIGNMENT_VERIFIED_AGAINST_NIC_2008",
                "confidence": conf,
                "rationale": rationale,
                "reviewed_at": reviewed_at,
            }
        )
    return pd.DataFrame(rows)
