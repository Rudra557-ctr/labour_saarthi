# ADR-0006 — Populate `location_master` from the validated data.gov.in LGD extract

- **Status:** Accepted
- **Date:** 2026-10-02 (Step 1.7)
- **Supersedes:** ADR-0003 (`location_master` stays empty)
- **Step 0 reference:** D-02

## Context

ADR-0003 kept `location_master` empty because LGD's own bulk download sits behind a CAPTCHA, which we will
not circumvent, and because populating the authoritative table from a non-LGD source (Census 2011 codes)
would silently corrupt every later join.

Step 1.7 changed the premise. data.gov.in publishes the same directory as flat CSVs. Two access details
mattered: the resource page embeds a direct, **keyless** file URL in its Nuxt SSR payload, and while the
`www.data.gov.in` host returns HTTP 403, the **apex `data.gov.in` host serves the files**.

This is a different officially published copy of the same authority — not a circumvention of the CAPTCHA.

## Validation performed before populating

| Check | Result |
|---|---|
| `lgd_states.csv` row count | 36 — exactly 28 states + 8 UTs |
| `lgd_districts.csv` row count | 785 |
| `state_code` / `district_code` uniqueness | unique at both tiers |
| States represented in the district file | all 36 |
| Referential integrity | every district's parent state exists |
| Census-2011 crosswalk present | yes — `district_census2011_code` |
| Udyam joinability | 785/785 `lg_dist_code` values match — 100% |

## Decision

Populate `location_master` with the STATE and DISTRICT tiers: **821 rows**.

Three deliberate restraints:

1. **No NATIONAL row.** LGD issues no code for the country, so synthesising one would place a fabricated key
   in the authoritative table. A test enforces this.
2. **`location_change_event` stays empty.** The CSV publishes no split/merge/rename events, parents or
   effective dates. Absence of a Census-2011 code is the only change evidence available, and it is recorded
   per row instead of being inflated into an event table we cannot source.
3. **`stable_district_group_id` stays NULL.** It requires the split/merge evidence the source does not provide.

## Consequences

- District-level joins are now possible. This unblocks the whole district tier of the project.
- **Two limitations ride on the data, not in a footnote.** `valid_from` carries the source's own
  `last_updated` (2023-11-30 / 2023-12-01), so the snapshot's ~2-year age is visible on every row; and 125 of
  785 districts (15.9%) have `census_2011_code` NULL because they post-date the 2011 census and therefore
  cannot be joined to any Census table. In the pilot states: Maharashtra 1 of 36, **Tamil Nadu 6 of 38
  (15.8%)**, Uttar Pradesh 4 of 75.
- The Census-2011 join loss is a hard ceiling on the Census-based occupation prior, and must be reported as
  coverage wherever that prior is used.
- `is_current` is True **as of the snapshot**, not as of today. LGD updates monthly; a refresh is needed before
  any production claim.
