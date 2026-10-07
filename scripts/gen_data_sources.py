"""Regenerate docs/data_sources.md from config/sources.yaml.

The registry is the authority; this document is a view of it, so it cannot drift.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lmis.common.paths import DOCS, RAW  # noqa: E402
from lmis.common.registry import load_registry  # noqa: E402

HEADER = """# Data Sources

Generated from `config/sources.yaml` — the registry is the authority, this file is a view of it.
Regenerate with `make docs-sources`.

`verification_status`: **VERIFIED_URL** = URL confirmed reachable · **VERIFIED_EXISTS** = source confirmed,
exact download URL not fixed · **UNVERIFIED** = access not yet established.

| source_id | role | publisher | access | geo available | occupation coding | period grain | status | acquired |
|---|---|---|---|---|---|---|---|---|"""


def acquired_label(source_id: str) -> str:
    base = RAW / source_id
    snaps = sorted(d.name for d in base.iterdir() if d.is_dir()) if base.exists() else []
    if not snaps:
        return "—"
    man = base / snaps[-1] / "manifest.json"
    n = len(json.loads(man.read_text())["files"]) if man.exists() else 0
    return f"{snaps[-1]} ({n} files)" if n else "—"


def main() -> None:
    reg = load_registry()
    lines = [HEADER]
    for sid, s in reg.items():
        lines.append(
            f"| `{sid}` | {s['role']} | {s['publisher_org'][:46]} | {s['access_method']} | "
            f"{s['geo_level_available']} | {s['occ_coding_scheme']} | {s['period_grain']} | "
            f"{s['verification_status']} | {acquired_label(sid)} |"
        )
    lines += ["", "## Per-source notes", ""]
    for sid, s in reg.items():
        lines += [
            f"### `{sid}` — {s['source_name']}",
            "",
            f"- **Landing:** {s['landing_url']}",
            f"- **Licence:** {s['licence']} (verified: {str(s.get('licence_verified', False)).lower()})",
            f"- **Authoritative:** {str(s['is_authoritative']).lower()} · "
            f"**Update cadence:** {s['update_cadence']}",
        ]
        note = " ".join((s.get("notes") or "").split())
        if note:
            lines.append(f"- **Notes:** {note}")
        lines.append("")
    (DOCS / "data_sources.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {DOCS / 'data_sources.md'} ({len(reg)} sources)")


if __name__ == "__main__":
    main()
