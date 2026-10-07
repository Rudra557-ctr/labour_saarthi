"""Reads config/sources.yaml. This is the licence gate: acquisition code may
only act on a source that is registered here."""
from __future__ import annotations

from typing import Any

import yaml

from lmis.common.paths import PILOT_SCOPE_YAML, SOURCES_YAML

REQUIRED_FIELDS = (
    "source_id",
    "source_name",
    "publisher_org",
    "role",
    "access_method",
    "licence",
    "geo_level_available",
    "occ_coding_scheme",
    "period_grain",
    "is_authoritative",
    "verification_status",
)

VALID_ROLES = {"demand", "supply", "training", "taxonomy", "reference", "context"}
VALID_STATUS = {"VERIFIED_URL", "VERIFIED_EXISTS", "UNVERIFIED"}


class RegistryError(RuntimeError):
    pass


def load_registry() -> dict[str, dict[str, Any]]:
    doc = yaml.safe_load(SOURCES_YAML.read_text())
    out: dict[str, dict[str, Any]] = {}
    for src in doc["sources"]:
        missing = [f for f in REQUIRED_FIELDS if f not in src]
        if missing:
            raise RegistryError(f"{src.get('source_id', '<no id>')}: missing fields {missing}")
        if src["role"] not in VALID_ROLES:
            raise RegistryError(f"{src['source_id']}: invalid role {src['role']!r}")
        if src["verification_status"] not in VALID_STATUS:
            raise RegistryError(
                f"{src['source_id']}: invalid verification_status {src['verification_status']!r}"
            )
        if src["source_id"] in out:
            raise RegistryError(f"duplicate source_id {src['source_id']}")
        out[src["source_id"]] = src
    return out


def get_source(source_id: str) -> dict[str, Any]:
    reg = load_registry()
    if source_id not in reg:
        raise RegistryError(
            f"{source_id} is not in the source registry. Register it in "
            f"config/sources.yaml before acquiring it (licence gate)."
        )
    return reg[source_id]


def load_pilot_scope() -> dict[str, Any]:
    return yaml.safe_load(PILOT_SCOPE_YAML.read_text())
