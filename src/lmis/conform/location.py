"""Geography spine: location_master, location_alias, location_change_event.

STATUS (Step 1.7): location_master IS now populated, from validated official LGD
data. See ADR-0006.

Step 1 left it empty because lgdirectory.gov.in is a DWR/AJAX application whose
bulk download sits behind a CAPTCHA we will not circumvent. Step 1.7 found a
different, officially published copy of the same directory on data.gov.in
(lgd_states.csv, lgd_districts.csv) and validated it: 36 states/UTs, 785
districts, unique codes, all 36 states present. That is a legitimate alternative
route to the same authority, not a circumvention.

Two limitations are carried on the data itself rather than hidden:
  - vintage is 2023-11-30 / 2023-12-01, while LGD updates monthly, so this is a
    snapshot roughly two years old, recorded in valid_from;
  - 125 of 785 districts (15.9%) have no Census-2011 code because they post-date
    the 2011 census, so they cannot be joined to any Census table.

The CSV exposes no split/merge/rename events, parents or effective dates, so
location_change_event remains EMPTY - absence of a Census-2011 code is the only
change evidence available, and it is recorded per row instead.

The DataMeet Census-2011 candidate set stays in data/staging as a reference only.
Census 2011 district codes are NOT LGD codes; the two are never equated.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from lmis.common.dbf import read_dbf

LOCATION_MASTER_COLUMNS = [
    "lgd_code",
    "level",  # NATIONAL | STATE | DISTRICT | SUBDISTRICT
    "parent_lgd_code",
    "name_en",
    "name_local",
    "state_lgd_code",
    "census_2011_code",
    "valid_from",
    "valid_to",
    "is_current",
    "stable_district_group_id",
    "source_id",
    "ingested_at",
]

LOCATION_ALIAS_COLUMNS = [
    "alias_id",
    "alias_text",
    "normalised_alias",
    "lgd_code",
    "match_method",  # EXACT | ALIAS | FUZZY | HUMAN
    "confidence",
    "source_id",
    "reviewed_by",
    "reviewed_at",
]

LOCATION_CHANGE_EVENT_COLUMNS = [
    "event_id",
    "event_type",  # SPLIT | MERGE | RENAME | TRANSFER
    "parent_lgd_code",
    "child_lgd_code",
    "effective_date",
    "notification_reference",
    "source_id",
    "notes",
]


def empty_location_master() -> pd.DataFrame:
    return pd.DataFrame(columns=LOCATION_MASTER_COLUMNS)


def empty_location_alias() -> pd.DataFrame:
    return pd.DataFrame(columns=LOCATION_ALIAS_COLUMNS)


def empty_location_change_event() -> pd.DataFrame:
    return pd.DataFrame(columns=LOCATION_CHANGE_EVENT_COLUMNS)


def build_census_district_candidates(dbf_path: Path, source_id: str) -> pd.DataFrame:
    """Read the Census-2011 district attribute table into a STAGING candidate set.

    Deliberately named *_candidates: this is not the geography spine.
    """
    names, rows = read_dbf(dbf_path)
    df = pd.DataFrame(rows)
    df.attrs["dbf_fields"] = names
    df["source_id"] = source_id
    df["is_authoritative_for_lgd"] = False
    return df


def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).replace("\ufeff", "").strip().strip('"').strip().lower() for c in df.columns]
    return df


def build_location_master(
    states_csv: Path, districts_csv: Path, source_id: str, ingested_at: str
) -> pd.DataFrame:
    """Build the geography spine from validated official LGD extracts.

    STATE and DISTRICT tiers only. No NATIONAL row is synthesised: LGD does not
    issue a code for the country, and inventing one would put a fabricated key in
    the authoritative table.

    `valid_from` carries the source's own `last_updated`, so the snapshot's age is
    visible on every row rather than buried in documentation. `is_current` is
    True as of that snapshot, not as of today - LGD changes monthly.
    """
    st = _norm_cols(pd.read_csv(states_csv, dtype=str, keep_default_na=False))
    di = _norm_cols(pd.read_csv(districts_csv, dtype=str, keep_default_na=False))

    def blank_to_none(v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        # '000'/'0' is LGD's marker for "no Census-2011 equivalent", i.e. a
        # district created after 2011. That is missing, not zero.
        return None if v in ("", "000", "0") else v

    rows: list[dict] = []
    for _, r in st.iterrows():
        rows.append(
            {
                "lgd_code": r["state_code"].strip(),
                "level": "STATE",
                "parent_lgd_code": None,
                "name_en": r["state_name_english"].strip(),
                "name_local": (r.get("state_name_local") or "").strip() or None,
                "state_lgd_code": r["state_code"].strip(),
                "census_2011_code": blank_to_none(r.get("state_census2011_code")),
                "valid_from": (r.get("last_updated") or "").strip() or None,
                "valid_to": None,
                "is_current": True,
                "stable_district_group_id": None,
                "source_id": source_id,
                "ingested_at": ingested_at,
            }
        )
    for _, r in di.iterrows():
        rows.append(
            {
                "lgd_code": r["district_code"].strip(),
                "level": "DISTRICT",
                "parent_lgd_code": r["state_code"].strip(),
                "name_en": r["district_name_english"].strip(),
                "name_local": (r.get("district_name_local") or "").strip() or None,
                "state_lgd_code": r["state_code"].strip(),
                "census_2011_code": blank_to_none(r.get("district_census2011_code")),
                "valid_from": (r.get("last_updated") or "").strip() or None,
                "valid_to": None,
                "is_current": True,
                # Requires split/merge evidence the source does not publish.
                "stable_district_group_id": None,
                "source_id": source_id,
                "ingested_at": ingested_at,
            }
        )
    out = pd.DataFrame(rows, columns=LOCATION_MASTER_COLUMNS)
    return out.sort_values(["level", "lgd_code"]).reset_index(drop=True)


def build_location_alias(
    alias_csv: Path, location_master: pd.DataFrame, source_id: str, reviewed_at: str
) -> pd.DataFrame:
    """Resolve curated name variants to LGD codes.

    Every alias is a reviewed, reasoned row - no fuzzy matching is applied here,
    because a wrong geography alias is invisible once it has been joined. The
    `rationale` column records WHY each variant maps where it does (a rename, an
    abbreviation, or a territorial reorganisation).

    Note the many-to-one case: NCS still reports "Dadra and Nagar Haveli" and
    "Daman and Diu" separately, while LGD carries the single merged UT. Both
    aliases resolve to the same lgd_code; the source rows stay separate.
    """
    raw = pd.read_csv(alias_csv, dtype=str, keep_default_na=False)
    states = location_master[location_master["level"] == "STATE"]
    by_name = {str(n).strip().lower(): str(c) for n, c in zip(states["name_en"], states["lgd_code"])}

    rows = []
    for i, r in raw.iterrows():
        target = r["lgd_state_name"].strip().lower()
        lgd_code = by_name.get(target)
        if lgd_code is None:
            # An alias whose target is not in LGD is a defect, not something to
            # silently drop - fail loudly so it gets fixed.
            raise ValueError(f"alias target not found in location_master: {r['lgd_state_name']!r}")
        rows.append(
            {
                "alias_id": f"ALIAS_STATE_{i + 1:04d}",
                "alias_text": r["alias_text"].strip(),
                "normalised_alias": r["alias_text"].strip().lower(),
                "lgd_code": lgd_code,
                "match_method": r["match_method"].strip(),
                "confidence": float(r["confidence"]),
                "source_id": source_id,
                "reviewed_by": "project",
                "reviewed_at": reviewed_at,
            }
        )
    return pd.DataFrame(rows, columns=LOCATION_ALIAS_COLUMNS)
