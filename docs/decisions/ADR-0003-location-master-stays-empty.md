# ADR-0003 — `location_master` stays empty rather than being populated from a non-LGD source

- **Status:** **Superseded by ADR-0006 (2026-10-02, Step 1.7)** — the premise changed when a validated official LGD copy was found. The reasoning below remains the correct standard for *unvalidated* sources.
- **Date:** 2026-10-02
- **Step 0 reference:** D-02

## Context

LGD is the canonical geography key (D-02). It could not be acquired: `lgdirectory.gov.in` is a DWR/AJAX
application, and its bulk-download form returns "Session Time Out" even when submitted with a valid
`OWASP_CSRFTOKEN` harvested from the live page, as a form field and as a query parameter. The data.gov.in
LGD mirrors are behind a JavaScript SPA and an API key we do not hold.

A Census-2011 district attribute table (641 rows) **was** obtainable.

## Options considered

1. Populate `location_master` from the Census-2011 table and treat its codes as the geography key.
2. Populate it with district **names** only and no codes.
3. Leave `location_master` empty; load the Census-2011 set to staging as an explicitly non-authoritative
   candidate universe.

## Decision

**Option 3.**

## Rationale

Options 1 and 2 reproduce exactly the failure the architecture exists to prevent. Census 2011 district codes
are **not** LGD codes; equating them would silently corrupt every later join, and the corruption would be
invisible because the joins would still *succeed*. An empty authoritative table is honest and loudly
blocking; a wrongly-populated one is neither.

## Consequences

- `location_master`, `location_alias`, `location_change_event` exist with full Step 0 schemas and **0 rows**.
- A test (`test_location_master_is_empty_but_correctly_shaped`) fails if anyone populates it, so the
  shortcut cannot be taken accidentally later.
- **No district-keyed work is possible until LGD is resolved.** This is the top blocker for Step 2.
- The Census-2011 candidate set lives at `data/staging/census2011_district_candidates.parquet` flagged
  `is_authoritative_for_lgd = False`, usable later for alias matching only.
