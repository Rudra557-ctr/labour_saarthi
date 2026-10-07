# Analytical Data Dictionary

Generated for Step 3.0. Column-level reference for the derived analytical layer.
Status values: **OBSERVED** (measured by the source) · **SUPPORTING** (real, but structural/contextual —
not demand) · **ESTIMATED** (*not present in this layer by design*).

## Shared metadata columns

Present on every analytical table:

| Column | Meaning |
|---|---|
| `observation_status` | OBSERVED or SUPPORTING. Never ESTIMATED at this stage |
| `source_id` | joins to `source_master` |
| `source_vintage` | what the SOURCE states its data is as-of |
| `transformation` | how the row was produced |
| `geo_level` / `occupation_level` / `industry_level` | the level the row is actually valid at; `NONE` means the dimension is absent, not unknown |

---

## `analytical_state_demand`
**Grain:** `snapshot_date × state_name_as_source` · **Status:** OBSERVED · **Source:** NCS Parliament answers

| Column | Type | Notes |
|---|---|---|
| `snapshot_date` | date | the "as on" date the answer states |
| `state_name_as_source` | text | name exactly as published |
| `lgd_code` | text | resolved via exact match then `location_alias`; **NULL for the PAN-India residual** |
| `geo_level` | text | STATE, or NATIONAL for the residual |
| `vacancies_cumulative` | int | **cumulative since 2015 inception — a stock, not a flow** |
| `measure_basis` | text | `CUMULATIVE_SINCE_INCEPTION` |
| `is_pan_india_residual` | bool | true for the one unallocatable row (20,507,320 vacancies) |
| `share_of_published_total` | float | denominator includes the residual |
| `share_of_state_attributable` | float | denominator excludes the residual; **NULL on the residual row** |
| `n_source_documents` | int | 3 — identical figures in three answers |
| `flow_available` | bool | **always false here** |
| `flow_unavailable_reason` | text | why differencing is impossible |

## `analytical_demand_by_industry`
**Grain:** `snapshot_date × ncs_sector_name` · **Status:** OBSERVED · **Source:** NCS answers + NIC-2008

| Column | Type | Notes |
|---|---|---|
| `ncs_sector_name` | text | as published (22 rows incl. `Sector Not Specified`) |
| `nic_section_code` | text | NIC-2008 section A–U; **NULL where deliberately unmapped** |
| `vacancies_cumulative` | float | **unit is `lakh`, as published — not converted** |
| `mapping_authority` / `mapping_method` / `mapping_confidence` | text/float | PROJECT name alignment verified against NIC-2008 |
| `is_heterogeneous_or_residual` | bool | true where unmapped or confidence < 0.9 — do not treat as occupationally specific |
| `occupation_level` | text | **always `NONE`: industry is not occupation** |

## `analytical_district_structure`
**Grain:** `snapshot_date × lgd_code × enterprise_category` · **Status:** SUPPORTING · **Source:** Udyam + LGD

| Column | Type | Notes |
|---|---|---|
| `enterprise_category` | text | TOTAL or SERVICES |
| `micro` / `small` / `medium` / `total` | int | **NULL where the source writes `'NA'`** |
| `enterprise_share_within_state` | float | sums to 1 within state × category |
| `enterprise_share_of_national` | float | sums to 1 within category |
| `*_share_of_district` | float | size composition; **NULL when the numerator is NULL, never 0.0** |
| `not_a_demand_measure` | bool | always true — counts registered **enterprises** |
| `measure_basis` | text | `CUMULATIVE_REGISTRATIONS` |

## `analytical_district_occupation_structure`
**Grain:** `census_year × census_state_code × census_district_code × nco_2004_division × area × sex`
**Status:** SUPPORTING (historical) · **Source:** Census 2011 B-24

| Column | Type | Notes |
|---|---|---|
| `census_district_code` | text | **Census-2011 code, NOT an LGD code** — join via `location_master.census_2011_code` |
| `nco_2004_division` | text | 1–9, or `X` = workers not classified by occupation |
| `nco_2015_division` | text | via derived crosswalk; **NULL for `X`** |
| `division_map_confidence` | float | measured purity (as low as 0.789) |
| `row_type` | text | `DIVISION_TOTAL` or `UNCLASSIFIED` only — totals and sub-divisions excluded to prevent double counting |
| `main_workers` | int | persons/males/females per `sex` |
| `occupation_share_of_district` | float | sums to 1 per district × area × sex cell; **NaN where that cell's total is 0** (fully urban districts have no rural workers) |
| `universe` | text | `MAIN_WORKERS_NON_HOUSEHOLD_INDUSTRY` — not all workers |
| `is_historical` | bool | always true (2011) |

## `analytical_labour_market_context`
**Grain:** `period_id × area × sex × age_group × indicator` · **Status:** OBSERVED · **Source:** PLFS

| Column | Type | Notes |
|---|---|---|
| `indicator` | text | LFPR, WPR or UR |
| `value_percent` | float | a **rate**, not a count |
| `std_error` | float | always NULL — not published per cell |
| `geo_level` / `valid_geo_level` | text | **NATIONAL only** |
| `district_estimates_valid` | bool | always false |
| `approach` / `statistical_basis` | text | CWS / `SAMPLE_SURVEY_CWS` |

## `map_nco2004_division_to_nco2015_division`
**Grain:** `nco_2004_division` · **Authority:** `PROJECT_DERIVED_FROM_OFFICIAL`

| Column | Notes |
|---|---|
| `nco_2015_division` | modal target division; NULL for `X` |
| `confidence` | share of concorded codes landing in the modal division (0.789–0.998) |
| `n_concorded_codes` / `n_in_modal_division` | the evidence behind the confidence |
| `alternative_divisions` | where the remainder goes, e.g. `3:104; 7:38` |
| `method` | `FIRST_DIGIT_TRUNCATION_OF_OFFICIAL_CONCORDANCE` |

## `fact_ilo_employment_eco_occ`  *(added Step 3.1)*
**Grain:** `ref_area × year × nic_2008_section × isco_08_major_group` · **Status:** OBSERVED_SURVEY_ESTIMATE
**Source:** ILOSTAT `EMP_TEMP_ECO_OCU_NB_A`, India rows, survey source `BA:14121` = PLFS

This is the **evidence** that makes an industry → occupation bridge possible. The bridge itself
(`P(occupation | industry)`) is **specified in `step3_1_estimation_methodology.md` §9 but deliberately not
built** — that is Step 4.

| Column | Type | Notes |
|---|---|---|
| `ref_area` | text | `IND` only |
| `year` | text | 2022–2025 at this granularity |
| `nic_2008_section` | text | from ISIC-Rev.4 section; NIC-2008 is the Indian adaptation |
| `isco_08_major_group` | text | 1–9 |
| `nco_2015_division` | text | **equal to the ISCO-08 major group** — one-to-one per NCVET Annexure IX §3 |
| `employment_thousands` | float | **thousands of persons**; NULL for the 45 cells the source does not publish |
| `measure_basis` | text | `EMPLOYMENT_STOCK_SURVEY_ESTIMATE` — employment, **not vacancies** |
| `geo_level` | text | **`NATIONAL` — there is no state dimension**, so `P(occ|industry,state)` is unavailable |
| `survey_source_label` | text | `LFS - Periodic Labour Force Survey` — the provenance that justifies use |

**Aggregates excluded on load** (3,443 rows): ISIC-Rev.3 rows, `ECO_AGGREGATE_*`, skill-level rows,
`TOTAL` and `X` buckets — so nothing double-counts.

## `analytical_dataset_catalog`
**Grain:** one row per analytical table. The table a dashboard reads to explain any number: grain,
sources, vintage, levels, status, transformations, row count, coverage note, limitations.

## Publication envelope (`data/publication/publication_contract.json`)
**Grain:** one envelope per contracted output, plus the unavailability register. Emitted by
`lmis publish-contract`; **not a warehouse table**, so no migration was needed.

| Field | Meaning |
|---|---|
| `publication_status` | `PRODUCTION` · `EXPERIMENTAL_ONLY` · `UNAVAILABLE` |
| `evidence_status` | read from the table's own `observation_status` / `observed_or_estimated` — never declared |
| `confidence` | categorical list from the table's `overall_confidence`, or the evidence status for observed facts |
| `coverage` | the output's mandatory disclosures, each resolved from `demand_coverage_summary` with `derived_from` |
| `vintage` / `vintage_source` | the baseline or as-on date, and the column it came from |
| `provenance` | `source_ids`, provenance columns, `transformation_depth`, `mapping_authority` |
| `unit`, `measure_basis`, `grain` | what the number is, and at what grain |
| `interpretation` | the single permitted reading |
| `prohibited_interpretations` | machine-readable, so a consumer cannot plead ignorance |
| `is_measured_shortage` | **always `false`** |
| `forecast_available` | **always `false`**, with the reason and gate G-4 |
| `default_ranking` | `WITHIN_STATE`, the column, and the cross-state caveat |

Unavailable capabilities carry `data: null`, a `reason_code`
(`NOT_IDENTIFIABLE` · `NOT_ACQUIRED` · `ACCESS_PENDING` · `NOT_AVAILABLE` · `NOT_SUPPORTED_YET` ·
`PROHIBITED`) and a `blocking_gate` — never an empty result.
