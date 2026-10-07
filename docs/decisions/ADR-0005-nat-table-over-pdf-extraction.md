# ADR-0005 — Build `occupation_master` from the DGE NAT HTML table, not from the NCO PDFs

- **Status:** Accepted
- **Date:** 2026-10-02
- **Step 0 reference:** S1.4, finding F5

## Context

Step 1 planned to build `occupation_master` by extracting the NCO-2015 PDF volumes. Those PDFs use subset
fonts with glyph-indexed text: inflating all 64 compressed streams of one official report produced 4.2 MB
containing **zero** occurrences of "NCO" as plain text.

While reading the NCVET report, Annexure IX Note 1 named a MoLE search engine. Following it led to
`https://dge.gov.in/nat` — a paginated HTML table with exactly the columns needed:
`S.No. | Occupational Title | NCO 2015 | NCO 2004 | Division | Sub Division | Group | Family`, 3,447 rows
across pages 0–6.

## Decision

Build `occupation_master` from the NAT HTML table. Keep the three PDF volumes as acquired snapshots for
cross-checking and for the occupation descriptions the table does not carry.

## Consequences

- Structured, official, parseable with a stdlib HTML parser — no OCR, no glyph-mapping risk.
- Yields an **official NCO-2004 ↔ NCO-2015 concordance** as a bonus (present for 77.9% of rows), stored as
  `map_nco2004_to_nco2015` with `authority='OFFICIAL'`.
- The page list is **explicit in config**, not discovered at runtime, so acquisition is reproducible.
- PDF extraction remains a real capability (`lmis.extract.pdf`) with a low-yield-page gate for manual
  spot-checks; it was used to extract Annexure VII.
- Known source defects are recorded rather than silently fixed: 11 duplicated codes, 13 hierarchy nodes with
  conflicting titles, Division 0 absent.
