"""Minimal stdlib HTML table extractor.

Deliberately dependency-free (no lxml/bs4): the only HTML we parse is a small
number of government report pages, and a stdlib parser keeps the reproducible
environment small.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._tbl: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "table":
            self._tbl = []
        elif tag == "tr" and self._tbl is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            self._row.append(text)
            self._cell = None
        elif tag == "tr" and self._row is not None and self._tbl is not None:
            if self._row:
                self._tbl.append(self._row)
            self._row = None
        elif tag == "table" and self._tbl is not None:
            self.tables.append(self._tbl)
            self._tbl = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def extract_tables(html: str) -> list[list[list[str]]]:
    p = _TableParser()
    p.feed(html)
    return p.tables
