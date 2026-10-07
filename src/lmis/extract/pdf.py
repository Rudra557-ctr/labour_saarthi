"""PDF extraction with validation.

Why this is a first-class module rather than a one-liner: the official PDFs we
depend on use subset fonts with glyph-indexed text. Naive stream inflation
recovers zero readable text from them (verified: inflating all 64 streams of the
NCVET report yielded 4.2 MB containing no occurrence of "NCO"). pdfplumber
resolves the ToUnicode CMaps correctly, but extraction quality still has to be
checked rather than assumed - hence extract_text_pages() reports per-page
character counts and flag_low_yield_pages() surfaces pages that produced
suspiciously little text for manual review.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pdfplumber

warnings.filterwarnings("ignore", module="pdfplumber")
warnings.filterwarnings("ignore", module="pdfminer")


@dataclass
class PageText:
    page_no: int
    n_chars: int
    text: str


def extract_text_pages(pdf_path: Path, first: int = 1, last: int | None = None) -> list[PageText]:
    out: list[PageText] = []
    with pdfplumber.open(pdf_path) as pdf:
        end = last or len(pdf.pages)
        for i in range(first - 1, min(end, len(pdf.pages))):
            text = pdf.pages[i].extract_text() or ""
            out.append(PageText(page_no=i + 1, n_chars=len(text), text=text))
    return out


def page_count(pdf_path: Path) -> int:
    with pdfplumber.open(pdf_path) as pdf:
        return len(pdf.pages)


def flag_low_yield_pages(pages: list[PageText], min_chars: int = 200) -> list[int]:
    """Pages that yielded little text. Not necessarily an error (title pages,
    figure-only pages), but each must be eyeballed before the extraction is
    trusted - this is the manual spot-check gate."""
    return [p.page_no for p in pages if p.n_chars < min_chars]


def extract_tables(pdf_path: Path, page_no: int) -> list[list[list[str | None]]]:
    with pdfplumber.open(pdf_path) as pdf:
        return pdf.pages[page_no - 1].extract_tables()


def tables_to_frame(
    pdf_path: Path, page_numbers: list[int], expected_cols: int | None = None
) -> pd.DataFrame:
    """Concatenate tables across pages, using the first page's header row.

    Rows whose column count does not match the header are NOT coerced - they are
    returned in a separate '_malformed' marker column so nothing is silently
    dropped or padded.
    """
    header: list[str] | None = None
    rows: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno in page_numbers:
            for tbl in pdf.pages[pno - 1].extract_tables():
                for raw_row in tbl:
                    cells = [(c or "").replace("\n", " ").strip() for c in raw_row]
                    if header is None:
                        header = cells
                        continue
                    if expected_cols and len(cells) != expected_cols:
                        rows.append({"_malformed": True, "_raw": " | ".join(cells), "_page": pno})
                        continue
                    if cells == header:
                        continue
                    rec = dict(zip(header, cells))
                    rec["_malformed"] = False
                    rec["_page"] = pno
                    rows.append(rec)
    df = pd.DataFrame(rows)
    if header:
        df.attrs["header"] = header
    return df
