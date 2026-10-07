"""Minimal dBASE III/IV reader (stdlib only).

Used to read a shapefile's .dbf attribute table without pulling in geopandas or
fiona. Reads character/numeric/date/logical fields; anything else is returned as
raw text so nothing is silently coerced.
"""
from __future__ import annotations

import struct
from pathlib import Path


def read_dbf(path: Path, encoding: str = "latin-1") -> tuple[list[str], list[dict]]:
    data = path.read_bytes()
    num_records, header_len, record_len = struct.unpack("<IHH", data[4:12])

    fields: list[tuple[str, str, int]] = []
    offset = 32
    while data[offset] != 0x0D:
        raw = data[offset : offset + 32]
        name = raw[:11].split(b"\x00")[0].decode(encoding).strip()
        ftype = chr(raw[11])
        flen = raw[16]
        fields.append((name, ftype, flen))
        offset += 32

    names = [f[0] for f in fields]
    rows: list[dict] = []
    pos = header_len
    for _ in range(num_records):
        rec = data[pos : pos + record_len]
        pos += record_len
        if not rec or rec[:1] == b"*":  # deleted record
            continue
        cur = 1  # first byte is the deletion flag
        row: dict[str, object] = {}
        for name, ftype, flen in fields:
            val = rec[cur : cur + flen].decode(encoding).strip()
            cur += flen
            if val == "":
                row[name] = None
            elif ftype == "N":
                try:
                    row[name] = int(val) if "." not in val else float(val)
                except ValueError:
                    row[name] = val
            elif ftype == "L":
                row[name] = val.upper() in ("Y", "T")
            else:
                row[name] = val
        rows.append(row)
    return names, rows
