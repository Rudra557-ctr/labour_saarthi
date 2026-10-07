"""Automated data profiling.

Purpose (Step 0 layer L3): discover what a dataset actually contains before any
assumption about it is written into code. The profile is evidence, so it is
committed to docs/profiling/.

Profiles report what IS there. Missingness is reported as missingness - this
module never imputes, and never treats null as zero.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    n_rows: int
    n_null: int
    pct_null: float
    n_unique: int
    sample_values: list[str] = field(default_factory=list)
    min_value: str | None = None
    max_value: str | None = None


@dataclass
class TableProfile:
    table: str
    source_path: str
    n_rows: int
    n_cols: int
    columns: list[ColumnProfile]
    duplicate_full_rows: int
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str) + "\n"


def profile_frame(df: pd.DataFrame, table: str, source_path: str) -> TableProfile:
    cols: list[ColumnProfile] = []
    for name in df.columns:
        s = df[name]
        n_null = int(s.isna().sum())
        vals = s.dropna().astype(str)
        mn = mx = None
        if not vals.empty:
            try:
                mn, mx = str(vals.min()), str(vals.max())
            except Exception:
                mn = mx = None
        cols.append(
            ColumnProfile(
                name=str(name),
                dtype=str(s.dtype),
                n_rows=int(len(s)),
                n_null=n_null,
                pct_null=round(100.0 * n_null / len(s), 2) if len(s) else 0.0,
                n_unique=int(s.nunique(dropna=True)),
                sample_values=[v[:60] for v in vals.unique()[:5].tolist()],
                min_value=mn,
                max_value=mx,
            )
        )
    notes: list[str] = []
    if df.empty:
        notes.append("TABLE IS EMPTY - check whether this is by design (see docs/limitations.md)")
    return TableProfile(
        table=table,
        source_path=source_path,
        n_rows=int(len(df)),
        n_cols=int(len(df.columns)),
        columns=cols,
        duplicate_full_rows=int(df.duplicated().sum()),
        notes=notes,
    )


def profile_parquet_dir(directory: Path, out_dir: Path) -> list[TableProfile]:
    out_dir.mkdir(parents=True, exist_ok=True)
    profiles: list[TableProfile] = []
    for pq in sorted(directory.glob("*.parquet")):
        df = pd.read_parquet(pq)
        prof = profile_frame(df, table=pq.stem, source_path=str(pq))
        (out_dir / f"{pq.stem}.profile.json").write_text(prof.to_json())
        profiles.append(prof)
    return profiles


def summary_markdown(profiles: list[TableProfile]) -> str:
    lines = ["| table | rows | cols | dup rows | columns with >50% null |", "|---|---|---|---|---|"]
    for p in profiles:
        high_null = [c.name for c in p.columns if c.pct_null > 50]
        lines.append(
            f"| `{p.table}` | {p.n_rows:,} | {p.n_cols} | {p.duplicate_full_rows} | "
            f"{', '.join(f'`{c}`' for c in high_null) if high_null else '-'} |"
        )
    return "\n".join(lines)


def profile_to_dict(p: TableProfile) -> dict[str, Any]:
    return asdict(p)
