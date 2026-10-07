from pathlib import Path

import pytest

from lmis.common.dbf import read_dbf

DBF = Path("data/raw/DATAMEET_DISTRICT_ATTRS/2026-10-02/2011_Dist.dbf")
pytestmark = pytest.mark.skipif(not DBF.exists(), reason="snapshot not acquired")


def test_dbf_reads_fields_and_rows():
    names, rows = read_dbf(DBF)
    assert names
    assert len(rows) > 500
    assert set(rows[0]) == set(names)


def test_dbf_empty_strings_become_none_not_zero():
    """Missing must stay missing - a blank character field must not become 0/''."""
    _names, rows = read_dbf(DBF)
    assert all(v != "" for r in rows for v in r.values())
