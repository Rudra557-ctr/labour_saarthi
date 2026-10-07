"""Canonical filesystem layout. Every module resolves paths through here so the
layout is changed in exactly one place."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

CONFIG = ROOT / "config"
SOURCES_YAML = CONFIG / "sources.yaml"
PILOT_SCOPE_YAML = CONFIG / "pilot_scope.yaml"

DATA = ROOT / "data"
RAW = DATA / "raw"
STAGING = DATA / "staging"
STANDARDIZED = DATA / "standardized"
EXTERNAL = DATA / "external"

DOCS = ROOT / "docs"
PROFILING = DOCS / "profiling"
MAPPINGS = ROOT / "mappings"


def raw_dir(source_id: str, retrieved_date: str) -> Path:
    """Immutable snapshot directory: data/raw/<SOURCE_ID>/<YYYY-MM-DD>/"""
    return RAW / source_id / retrieved_date


def standardized_path(table: str) -> Path:
    return STANDARDIZED / f"{table}.parquet"


PUBLICATION_CONTRACT_YAML = CONFIG / "publication_contract.yaml"
PUBLICATION = DATA / "publication"


def publication_path(name: str) -> Path:
    """Published contract artifacts: data/publication/<name>.json"""
    return PUBLICATION / f"{name}.json"
