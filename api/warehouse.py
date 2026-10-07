"""Read-only warehouse access and the cached publication contract.

The connection is opened read-only so no route can write, and the envelope set is
built once at startup because `build_envelopes` runs a query per output.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import duckdb

from lmis.publish import build_envelopes, build_unavailability_register, load_contract
from lmis.publish.contract import PublicationContract
from lmis.warehouse.load import DB_PATH


@lru_cache(maxsize=1)
def contract() -> PublicationContract:
    return load_contract()


def connect() -> duckdb.DuckDBPyConnection:
    """A read-only cursor. Read-only is the guarantee that the API cannot mutate."""
    return duckdb.connect(str(DB_PATH), read_only=True)


@lru_cache(maxsize=1)
def _cached_envelopes() -> tuple[dict[str, Any], ...]:
    con = connect()
    try:
        return tuple(build_envelopes(con, contract()))
    finally:
        con.close()


def envelopes() -> list[dict[str, Any]]:
    return [dict(e) for e in _cached_envelopes()]


def envelope(output_id: str) -> dict[str, Any]:
    for e in _cached_envelopes():
        if e["output_id"] == output_id:
            return dict(e)
    raise KeyError(output_id)


@lru_cache(maxsize=1)
def _cached_register() -> tuple[dict[str, Any], ...]:
    return tuple(build_unavailability_register(contract()))


def register() -> list[dict[str, Any]]:
    return [dict(r) for r in _cached_register()]


def query(sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    con = connect()
    try:
        cur = con.execute(sql, params or [])
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        con.close()
