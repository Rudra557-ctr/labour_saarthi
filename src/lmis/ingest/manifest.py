"""Snapshot manifests: the provenance record for every acquired file.

A manifest is written next to the bytes it describes and is the ONLY thing from
data/raw that is committed to version control. It is what makes the pipeline
reproducible and auditable: sha256 lets us prove the bytes have not changed,
and publication_vintage records what the source itself said it was.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANIFEST_NAME = "manifest.json"
SCHEMA_VERSION = 1


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class FileRecord:
    name: str
    url: str | None
    sha256: str
    size_bytes: int
    content_type: str | None = None
    http_status: int | None = None
    # publication_vintage is what the SOURCE says its data is as-of. It is not
    # the download date, and it is None when the source does not state it.
    publication_vintage: str | None = None
    notes: str | None = None


@dataclass
class Manifest:
    source_id: str
    retrieved_at: str
    schema_version: int = SCHEMA_VERSION
    access_method: str | None = None
    licence: str | None = None
    publisher_org: str | None = None
    landing_url: str | None = None
    verification_status: str | None = None
    retrieved_by: str = "lmis.ingest.acquire"
    files: list[FileRecord] = field(default_factory=list)
    notes: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=False) + "\n"

    def write(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / MANIFEST_NAME
        path.write_text(self.to_json())
        return path


def read_manifest(directory: Path) -> dict[str, Any]:
    return json.loads((directory / MANIFEST_NAME).read_text())


def verify_snapshot(directory: Path) -> list[tuple[str, str]]:
    """Re-hash every file named in the manifest. Returns a list of
    (filename, problem) pairs; empty list means the snapshot is intact."""
    problems: list[tuple[str, str]] = []
    man = read_manifest(directory)
    for rec in man["files"]:
        fp = directory / rec["name"]
        if not fp.exists():
            problems.append((rec["name"], "missing"))
            continue
        actual = sha256_file(fp)
        if actual != rec["sha256"]:
            problems.append(
                (rec["name"], f"sha256 mismatch: manifest={rec['sha256'][:12]} actual={actual[:12]}")
            )
    return problems
