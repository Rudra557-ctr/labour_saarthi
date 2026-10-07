"""Provenance and warehouse integrity.

The point of these tests is that lineage must be answerable in SQL: for any fact
row, source_id -> source_master and snapshot_file -> source_snapshot must both
resolve, giving the publisher, the URL and the sha256 of the exact bytes.
"""
import pandas as pd
import pytest

from lmis.common.paths import standardized_path
from lmis.common.registry import load_registry
from lmis.warehouse.load import TABLES, apply_schema, connect, load_all


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    db = tmp_path_factory.mktemp("wh") / "test.duckdb"
    c = connect(db)
    apply_schema(c)
    load_all(c)
    yield c
    c.close()


def test_source_master_covers_every_registered_source():
    sm = pd.read_parquet(standardized_path("source_master"))
    assert set(sm.source_id) == set(load_registry())


def test_source_snapshot_has_a_row_per_acquired_file():
    ss = pd.read_parquet(standardized_path("source_snapshot"))
    assert len(ss) > 20
    assert ss.snapshot_id.is_unique
    assert ss.sha256.str.len().eq(64).all()
    assert (ss.size_bytes > 0).all()


def test_publication_vintage_is_never_defaulted_to_download_date():
    """A vintage the source does not state must stay NULL."""
    ss = pd.read_parquet(standardized_path("source_snapshot"))
    assert ss.publication_vintage.isna().all()


def test_every_fact_source_id_resolves_to_source_master():
    sm = set(pd.read_parquet(standardized_path("source_master")).source_id)
    for t in (
        "fact_vacancy_official_by_state",
        "fact_vacancy_official_by_sector",
        "fact_establishment_district",
        "fact_labour_force_estimate",
    ):
        df = pd.read_parquet(standardized_path(t))
        assert set(df.source_id) <= sm, t


def test_every_fact_snapshot_file_resolves_to_a_snapshot():
    ss = pd.read_parquet(standardized_path("source_snapshot"))
    known = set(zip(ss.source_id, ss.file_name))
    for t in (
        "fact_vacancy_official_by_state",
        "fact_vacancy_official_by_sector",
        "fact_establishment_district",
        "fact_labour_force_estimate",
    ):
        df = pd.read_parquet(standardized_path(t))
        assert set(zip(df.source_id, df.snapshot_file)) <= known, t


def test_warehouse_loads_every_table(con):
    counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in TABLES}
    assert counts["location_master"] == 821
    assert counts["occupation_master"] == 3982
    assert counts["sector_master"] == 59
    # NIC-2008 has 21 sections, A..U. This read 20 until Step 3.0, when a
    # fact row referencing section T exposed that the parser's title-length cap
    # had silently dropped it (T's title is 122 characters).
    assert counts["nic_section_master"] == 21
    assert counts["fact_establishment_district"] == 6280
    assert counts["fact_labour_force_estimate"] == 81
    assert counts["source_snapshot"] > 20
    # Step 3.0 analytical layer
    assert counts["fact_census_occupation_workers"] == 48645
    assert counts["analytical_state_demand"] == 38
    assert counts["analytical_district_structure"] == 1570
    assert counts["analytical_district_occupation_structure"] == 12420
    assert counts["analytical_dataset_catalog"] == 5
    # fact_data_quality was created but never LOADED in Step 2.0; the Step 3.0
    # audit of the real database caught it.
    assert counts["fact_data_quality"] > 0
    # Step 5.0 supply foundation
    assert counts["fact_training_outcome"] == 350
    assert counts["fact_training_infrastructure"] == 144
    assert counts["dim_training_trade"] == 155
    assert counts["fact_training_reconciliation"] == 14


def test_lineage_query_resolves_end_to_end(con):
    """One SQL statement from a measure to the sha256 of its source bytes."""
    df = con.execute(
        """
        SELECT f.state_name_as_source, f.vacancies_cumulative, s.publisher_org, ss.sha256
        FROM fact_vacancy_official_by_state f
        JOIN source_master   s  ON s.source_id = f.source_id
        JOIN source_snapshot ss ON ss.source_id = f.source_id
                               AND ss.file_name = f.snapshot_file
        WHERE f.state_name_as_source = 'Maharashtra'
        """
    ).df()
    assert len(df) >= 1
    assert df.sha256.str.len().eq(64).all()
    assert df.publisher_org.notna().all()


def test_establishments_join_to_districts_in_sql(con):
    n = con.execute(
        """
        SELECT count(*) FROM fact_establishment_district e
        JOIN location_master l ON l.lgd_code = e.lgd_code AND l.level='DISTRICT'
        """
    ).fetchone()[0]
    total = con.execute("SELECT count(*) FROM fact_establishment_district").fetchone()[0]
    assert n == total, "every establishment row must join to a district"


def test_ncs_sector_map_is_project_authority_with_confidence(con):
    df = con.execute("SELECT * FROM map_ncs_sector_to_nic_section").df()
    assert set(df.authority) == {"PROJECT"}
    mapped = df[df.section_code.notna()]
    assert mapped.confidence.notna().all()
    assert mapped.confidence.between(0, 1).all()
    assert df.rationale.notna().all()


def test_nco_concordance_is_official(con):
    df = con.execute("SELECT * FROM map_nco2004_to_nco2015").df()
    assert set(df.authority) == {"OFFICIAL"}
    assert (df.confidence == 1.0).all()


def test_data_quality_results_are_recorded():
    dq = pd.read_parquet(standardized_path("fact_data_quality"))
    assert len(dq) >= 6
    assert set(dq.status) <= {"PASS", "FAIL"}
    assert (dq.status == "PASS").all(), dq[dq.status == "FAIL"].to_dict("records")
