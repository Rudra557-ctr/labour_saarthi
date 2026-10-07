"""Load standardized tables into the DuckDB warehouse.

DuckDB because it needs no server, reads Parquet directly, and lets the grain-safe
joins be expressed and reviewed as plain SQL.

The load is a full replace per table from the standardized Parquet files, so the
warehouse is always reproducible from `data/standardized/` plus the DDL, and never
accumulates state of its own.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

from lmis.common.paths import ROOT, STANDARDIZED

DB_PATH = ROOT / "db" / "lmis.duckdb"
SCHEMA_SQL_FILES = [
    ROOT / "db" / "migrations" / "001_schema.sql",
    ROOT / "db" / "migrations" / "002_analytical.sql",
    ROOT / "db" / "migrations" / "003_demand.sql",
    ROOT / "db" / "migrations" / "004_supply.sql",
    ROOT / "db" / "migrations" / "005_supply_evidence.sql",
    ROOT / "db" / "migrations" / "006_trade_nco.sql",
    ROOT / "db" / "migrations" / "007_trade_supply.sql",
]

# Order matters only for readability; DuckDB has no FK enforcement here.
TABLES = [
    "source_master",
    "source_snapshot",
    "location_master",
    "location_alias",
    "location_change_event",
    "occupation_master",
    "sector_master",
    "nic_section_master",
    "dim_period",
    "map_nco2004_to_nco2015",
    "map_ncs_sector_to_nic_section",
    "fact_vacancy_official_by_state",
    "fact_vacancy_official_by_sector",
    "fact_establishment_district",
    "fact_labour_force_estimate",
    # fact_data_quality was created by the DDL but never loaded in Step 2.0 -
    # found by the Step 3.0 audit of the actual database.
    "fact_data_quality",
    "fact_census_occupation_workers",
    "map_nco2004_division_to_nco2015_division",
    "analytical_state_demand",
    "analytical_demand_by_industry",
    "analytical_district_structure",
    "analytical_district_occupation_structure",
    "analytical_labour_market_context",
    "analytical_dataset_catalog",
    "fact_ilo_employment_eco_occ",
    # Step 4.0 demand estimation (the first ESTIMATED outputs)
    "demand_national_occupation_composition",
    "demand_district_relative_signal",
    "demand_district_occupation_signal",
    "demand_coverage_summary",
    # Step 5.0 supply foundation (OBSERVED training data)
    "fact_training_outcome",
    "fact_training_infrastructure",
    "dim_training_trade",
    "fact_training_reconciliation",
    "supply_coverage_summary",
    # Step 5.1 supply evidence resolution
    "map_qualification_to_nco",
    "supply_evidence_matrix",
    # Step 5.2 occupation linkage
    "map_trade_to_nco",
    "dim_trade_mapping_status",
    # Step 5.3 trade/job-role level supply quantities
    "fact_training_trade_outcome",
    "fact_trade_supply_reconciliation",
]


@dataclass
class LoadResult:
    table: str
    rows: int
    status: str
    detail: str | None = None


def connect(db_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def apply_schema(con: duckdb.DuckDBPyConnection) -> None:
    for sql in SCHEMA_SQL_FILES:
        con.execute(sql.read_text())


def load_all(con: duckdb.DuckDBPyConnection) -> list[LoadResult]:
    results: list[LoadResult] = []
    for table in TABLES:
        pq = STANDARDIZED / f"{table}.parquet"
        if not pq.exists():
            results.append(LoadResult(table, 0, "MISSING", f"{pq.name} not built"))
            continue
        df = pd.read_parquet(pq)
        con.register("_staged", df)
        con.execute(f"DELETE FROM {table}")
        cols = [r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()]
        shared = [c for c in cols if c in df.columns]
        con.execute(
            f"INSERT INTO {table} ({', '.join(shared)}) "
            f"SELECT {', '.join(shared)} FROM _staged"
        )
        con.unregister("_staged")
        n = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        missing_cols = [c for c in cols if c not in df.columns]
        results.append(
            LoadResult(
                table, n, "LOADED",
                None if not missing_cols else f"columns not supplied: {missing_cols}",
            )
        )
    return results


def table_counts(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    rows = []
    for t in TABLES:
        try:
            n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        except Exception:
            n = None
        rows.append({"table": t, "rows": n})
    return pd.DataFrame(rows)
