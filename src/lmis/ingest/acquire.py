"""Reproducible source acquisition.

Design rules enforced here:
  1. Licence gate - a source must be in config/sources.yaml before it can be
     acquired (lmis.common.registry.get_source raises otherwise).
  2. Immutability - an existing snapshot file is NEVER overwritten. A re-run of
     the same day is a no-op for files already present; a changed upstream file
     lands in a NEW dated snapshot directory.
  3. Every acquisition writes a manifest with sha256, size, http status and the
     source's registry metadata.
  4. Failures are recorded, not hidden: a file that cannot be fetched is
     reported with its reason and left absent. Nothing is fabricated.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests

from lmis.common.paths import CONFIG, raw_dir
from lmis.common.registry import get_source
from lmis.ingest.manifest import FileRecord, Manifest, sha256_file, utc_now_iso

USER_AGENT = (
    "LMIS-SIH2026/0.1 (academic labour-market research prototype; "
    "contact: project maintainer)"
)
TIMEOUT = 120


@dataclass
class FetchOutcome:
    name: str
    url: str
    ok: bool
    path: Path | None = None
    http_status: int | None = None
    reason: str | None = None
    skipped_existing: bool = False


def _ca_bundle_for(src: dict) -> str | bool:
    """Build a CA bundle for a source that needs an intermediate the server omits.

    Returns a path to certifi's roots PLUS the declared intermediate, or True to
    use the default roots. Verification is NEVER disabled - `verify=False` does
    not appear anywhere in this project. See config/certs/README.md.
    """
    name = src.get("tls_intermediate")
    if not name:
        return True
    import certifi

    inter = CONFIG / "certs" / name
    bundle = CONFIG / "certs" / f".bundle_{name}"
    if not bundle.exists() or bundle.stat().st_mtime < inter.stat().st_mtime:
        bundle.write_bytes(
            Path(certifi.where()).read_bytes() + b"\n" + inter.read_bytes()
        )
    return str(bundle)


def _fetch_one(url: str, dest: Path, verify: str | bool = True) -> FetchOutcome:
    name = dest.name
    if dest.exists():
        # Immutability: never overwrite an existing raw byte-stream.
        return FetchOutcome(name=name, url=url, ok=True, path=dest, skipped_existing=True)
    try:
        resp = requests.get(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
            verify=verify,
        )
    except Exception as exc:  # network-level failure
        return FetchOutcome(name=name, url=url, ok=False, reason=f"{type(exc).__name__}: {exc}")

    if resp.status_code != 200:
        return FetchOutcome(
            name=name,
            url=url,
            ok=False,
            http_status=resp.status_code,
            reason=f"HTTP {resp.status_code}",
        )
    if not resp.content:
        return FetchOutcome(
            name=name, url=url, ok=False, http_status=200, reason="empty response body"
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(resp.content)
    return FetchOutcome(
        name=name,
        url=url,
        ok=True,
        path=dest,
        http_status=resp.status_code,
        reason=None,
    )


def acquire(source_id: str, retrieved_date: str | None = None) -> tuple[Path, list[FetchOutcome]]:
    """Acquire every `files:` entry registered for a source.

    Returns the snapshot directory and one FetchOutcome per declared file.
    Sources with no `files:` entry (portal/form/API-only) are a no-op here by
    design - they are handled by source-specific probes, never guessed at.
    """
    src = get_source(source_id)
    retrieved_date = retrieved_date or date.today().isoformat()
    snap = raw_dir(source_id, retrieved_date)

    declared = list(src.get("files") or [])
    # Expand paged_files (a URL template + explicit page list) into concrete
    # file entries. The page list is explicit, never inferred at runtime, so an
    # acquisition is reproducible from config alone.
    for spec in src.get("paged_files") or []:
        for page in spec["pages"]:
            declared.append(
                {
                    "name": spec["name_template"].format(page=page),
                    "url": spec["url_template"].format(page=page),
                    "purpose": spec.get("purpose"),
                }
            )
    outcomes: list[FetchOutcome] = []
    records: list[FileRecord] = []
    verify = _ca_bundle_for(src)

    for entry in declared:
        outcome = _fetch_one(entry["url"], snap / entry["name"], verify=verify)
        outcomes.append(outcome)
        if outcome.ok and outcome.path is not None:
            records.append(
                FileRecord(
                    name=outcome.name,
                    url=entry["url"],
                    sha256=sha256_file(outcome.path),
                    size_bytes=outcome.path.stat().st_size,
                    http_status=outcome.http_status,
                    # The source does not machine-declare its vintage; left None
                    # rather than guessed. Recorded in notes where known.
                    publication_vintage=entry.get("publication_vintage"),
                    notes=entry.get("purpose"),
                )
            )

    failures = [o for o in outcomes if not o.ok]
    man = Manifest(
        source_id=source_id,
        retrieved_at=utc_now_iso(),
        access_method=src.get("access_method"),
        licence=src.get("licence"),
        publisher_org=src.get("publisher_org"),
        landing_url=src.get("landing_url"),
        verification_status=src.get("verification_status"),
        files=records,
        notes=(
            None
            if not failures
            else "FAILED: " + "; ".join(f"{o.name} ({o.reason})" for o in failures)
        ),
    )
    if records or declared:
        man.write(snap)
    return snap, outcomes
