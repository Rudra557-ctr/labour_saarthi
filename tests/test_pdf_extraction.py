from pathlib import Path

import pytest

from lmis.extract.pdf import extract_text_pages, flag_low_yield_pages, page_count

REPORT = Path(
    "data/raw/NCVET_NCO_MAPPING_REPORT/2026-10-02/"
    "Report_on_Mapping_of_Qualifications_with_NCO_Codes.pdf"
)

pytestmark = pytest.mark.skipif(not REPORT.exists(), reason="snapshot not acquired")


def test_report_extracts_readable_text():
    """Regression guard: these PDFs use glyph-indexed subset fonts. Naive stream
    inflation recovers zero readable text; pdfplumber must recover real words."""
    pages = extract_text_pages(REPORT, first=1, last=4)
    joined = " ".join(p.text for p in pages)
    assert "National Classification of Occupations" in joined
    assert "NCO" in joined


def test_report_identity_is_as_expected():
    assert page_count(REPORT) == 58
    first = extract_text_pages(REPORT, 1, 1)[0].text
    assert "22nd August 2023" in first


def test_low_yield_pages_are_flagged_for_manual_check():
    pages = extract_text_pages(REPORT)
    low = flag_low_yield_pages(pages)
    # The cover page is legitimately sparse; the gate must catch it so a human
    # confirms rather than the pipeline assuming.
    assert 1 in low
