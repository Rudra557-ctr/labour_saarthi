"""Load the source registry and snapshot manifests into queryable provenance tables.

This is what makes lineage answerable in SQL rather than by reading YAML: for any
row in any fact table, `source_id` joins to `source_master`, and `snapshot_file`
joins to `source_snapshot` for the sha256, size, URL and retrieval time of the
exact bytes it came from.
"""
from __future__ import annotations

import json

import pandas as pd

from lmis.common.paths import RAW
from lmis.common.registry import load_registry

SOURCE_MASTER_COLUMNS = [
    "source_id", "source_name", "publisher_org", "landing_url", "role",
    "access_method", "licence", "licence_verified", "geo_level_available",
    "occ_coding_scheme", "period_grain", "update_cadence", "is_authoritative",
    "verification_status", "notes",
]

SOURCE_SNAPSHOT_COLUMNS = [
    "snapshot_id", "source_id", "retrieved_at", "retrieved_date", "file_name",
    "file_url", "sha256", "size_bytes", "http_status", "publication_vintage",
    "retrieved_by", "notes",
]


def build_source_master() -> pd.DataFrame:
    rows = []
    for sid, s in load_registry().items():
        notes = " ".join((s.get("notes") or "").split()) or None
        rows.append(
            {
                "source_id": sid,
                "source_name": s["source_name"],
                "publisher_org": s["publisher_org"],
                "landing_url": s.get("landing_url"),
                "role": s["role"],
                "access_method": s["access_method"],
                "licence": s.get("licence"),
                "licence_verified": bool(s.get("licence_verified", False)),
                "geo_level_available": s.get("geo_level_available"),
                "occ_coding_scheme": s.get("occ_coding_scheme"),
                "period_grain": s.get("period_grain"),
                "update_cadence": s.get("update_cadence"),
                "is_authoritative": bool(s.get("is_authoritative", False)),
                "verification_status": s["verification_status"],
                "notes": notes,
            }
        )
    return pd.DataFrame(rows, columns=SOURCE_MASTER_COLUMNS)


def build_source_snapshot() -> pd.DataFrame:
    """One row per file in every manifest under data/raw."""
    rows = []
    for man_path in sorted(RAW.rglob("manifest.json")):
        man = json.loads(man_path.read_text())
        retrieved_date = man_path.parent.name
        for f in man["files"]:
            rows.append(
                {
                    # sha256 prefix keys the snapshot: the bytes identify themselves.
                    "snapshot_id": f"{man['source_id']}:{retrieved_date}:{f['name']}",
                    "source_id": man["source_id"],
                    "retrieved_at": man["retrieved_at"],
                    "retrieved_date": retrieved_date,
                    "file_name": f["name"],
                    "file_url": f.get("url"),
                    "sha256": f["sha256"],
                    "size_bytes": int(f["size_bytes"]),
                    "http_status": f.get("http_status"),
                    "publication_vintage": f.get("publication_vintage"),
                    "retrieved_by": man.get("retrieved_by"),
                    "notes": f.get("notes"),
                }
            )
    return pd.DataFrame(rows, columns=SOURCE_SNAPSHOT_COLUMNS)
