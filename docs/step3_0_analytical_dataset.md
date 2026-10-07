# Step 3.0 — Analytical Dataset

Date: 2026-10-04 · **Analytical construction only.** No synthetic data, no demand index, no district
demand estimate, no forecast, no gap score, no recommendations, no API/frontend/LLM.

---

## 0. Audit of the actual Step 2.0 output (verified, not assumed)

Queried the real `db/lmis.duckdb` rather than trusting the Step 2.0 report. Findings:

| Check | Result |
|---|---|
| Tables present | 16, all loadable |
| Key uniqueness | **every** declared key verified unique (11 tables checked) |
| Geography coverage | 36/36 LGD states have NCS data; 785/785 districts have Udyam; 660/785 have a Census-2011 code |
| Occupation coverage | 3,982 NCO nodes — but **zero occupation-coded facts existed** |
| Time coverage | NCS a single as-on date (2024-11-15); Udyam 2023-12-21; PLFS M202504; LGD 2023-11-30 |

**Two discrepancies found in my own Step 2.0 report, corrected here:**

1. **`fact_data_quality` was 0 rows in the database.** The DDL created it and `validate-tables` wrote the
   Parquet, but the table was missing from the warehouse loader's table list, so it was never loaded. The
   Step 2.0 doc listed it as loaded. Fixed; now 11 rows, with a test asserting it is non-empty.
2. **`nic_section_master` had 20 of NIC-2008's 21 sections.** Section **T** was silently dropped by a
   95-character title cap (T's title is 122 characters). Only exposed when an analytical row referenced
   section T. Fixed; now 21.

Also confirmed: the three NCS Parliament answers report **identical** figures for every geography and
sector (0 disagreements), so they are three documents describing **one** observation.

---

## 1. Analytical grain

The candidate grain `TIME × STATE × DISTRICT × OCCUPATION` is **not yet attainable from observed data**, and
no source was forced into it. Each source stays at its own valid grain:

| Source | Valid grain | Can it support district × occupation × time? |
|---|---|---|
| NCS vacancies | one as-on date × state; separately × industry | **No** — no occupation, no district, single date |
| Udyam | 2023 snapshot × district | **No occupation**, no time series |
| Census B-24 | 2011 × district × NCO-2004 division | **No time**, historical only |
| PLFS | month × NATIONAL | **No district**, no occupation at this grain |

Joining demand (state, industry) to occupation structure (district, 2011) would be an **estimate**, so it is
deliberately not built. That is the demand-estimation step.

### Source facts vs derived analytics

- **A. SOURCE FACT TABLES** — `fact_vacancy_official_by_state`, `fact_vacancy_official_by_sector`,
  `fact_establishment_district`, `fact_labour_force_estimate`, and new in Step 3.0
  `fact_census_occupation_workers`. Native grain, unmodified.
- **B. DERIVED ANALYTICAL TABLES** — the five `analytical_*` tables below, plus
  `map_nco2004_division_to_nco2015_division` and `analytical_dataset_catalog`.

---

## 2. Analytical tables built

| Table | Rows | Grain | Status | Sources |
|---|---|---|---|---|
| `analytical_state_demand` | **38** | snapshot_date × state (or NATIONAL residual) | OBSERVED | NCS answers |
| `analytical_demand_by_industry` | **22** | snapshot_date × NCS sector (NIC-2008 section) | OBSERVED | NCS answers + NIC-2008 |
| `analytical_district_structure` | **1,570** | snapshot_date × district × enterprise_category | **SUPPORTING** | Udyam + LGD |
| `analytical_district_occupation_structure` | **12,420** | census_year × district × NCO-2004 division × area × sex | **SUPPORTING** | Census B-24 |
| `analytical_labour_market_context` | **81** | period × NATIONAL × area × sex × age × indicator | OBSERVED | PLFS |
| `fact_census_occupation_workers` | **48,645** | state × district × division × sub-division × area × sex | OBSERVED | Census B-24 |
| `map_nco2004_division_to_nco2015_division` | **10** | NCO-2004 division | derived, purity measured | official concordance |
| `analytical_dataset_catalog` | **5** | one row per analytical table | metadata | — |

Warehouse now holds **24 tables, 77,883 rows**.

---

## 3. Transformations applied

**Allowed and performed:** de-duplication of identical corroborating documents; shares within an explicit
denominator; size-class composition; pivoting; occupation shares within a district cell; a division-level
crosswalk derived from the official concordance **with measured purity**.

### Census B-24 acquired — TLS chain completed, not bypassed

`censusindia.gov.in` serves only its leaf certificate and omits the emSign intermediate. Resolved by
fetching that intermediate from the CA repository URL the server's **own certificate advertises in its AIA
extension**, and appending it to the certifi roots. The completed chain verifies to the publicly trusted
`emSign Root CA - G1`:

```
openssl s_client -connect censusindia.gov.in:443 -CAfile bundle.pem
Verify return code: 0 (ok)
```

Certificate verification remains **fully enabled**. `verify=False` appears nowhere in the repository
(grep-verified). The intermediate is committed at `config/certs/` with provenance, and `sources.yaml`
declares `tls_intermediate:` so the fix is reproducible rather than a one-off.

Acquired B-24 for the three pilot states: Maharashtra, Tamil Nadu, Uttar Pradesh.

### Census reconciliation (arithmetic proof of faithful extraction)

The table mixes four row kinds in one column pair, so a `row_type` column was added
(`TOTAL_ALL_OCCUPATIONS`, `DIVISION_TOTAL`, `SUB_DIVISION`, `UNCLASSIFIED`). A first attempt over-counted
by 1,612,514 workers because division `X` carries **both** a total and a detail row. After the fix:

| State | Level | TOTAL | Σ(divisions + unclassified) | diff |
|---|---|---|---|---|
| Maharashtra | state & district | 20,223,737 | 20,223,737 | **0** |
| Tamil Nadu | state & district | 15,726,642 | 15,726,642 | **0** |
| Uttar Pradesh | state & district | 16,917,229 | 16,917,229 | **0** |

Sub-divisions also sum exactly to their division totals.

### The NCO-2004 → NCO-2015 division crosswalk is measured, not assumed

Census publishes occupation only at division/sub-division level, while the official concordance keys on
8-digit codes. Truncating both sides to their first digit gives a division relationship whose **purity is
computable** — and it is far from clean:

| NCO-2004 division | → NCO-2015 | purity | codes | where the rest go |
|---|---|---|---|---|
| 1 Legislators/Managers | 1 | 0.975 | 160 | 2:4 |
| 2 Professionals | 2 | **0.998** | 428 | 3:1 |
| 3 Technicians | 3 | **0.789** | 303 | 2:60, 7:4 |
| 4 Clerks | 4 | 0.945 | 91 | 3:5 |
| 5 Service/Sales | 5 | 0.961 | 103 | 4:3, 3:1 |
| 6 Agricultural | 6 | 0.946 | 92 | 7:5 |
| 7 Craft | 7 | 0.903 | 681 | 8:34, 3:32 |
| 8 Plant/Machine | 8 | **0.805** | 727 | 3:104, 7:38 |
| 9 Elementary | 9 | 0.880 | 100 | 5:12 |
| X Unclassified | **NULL** | — | 0 | not mappable |

Divisions 3 and 8 are only ~79–81% pure. That uncertainty is stored as `confidence` on every row, with
`alternative_divisions` recording where the remainder lands. Authority is
`PROJECT_DERIVED_FROM_OFFICIAL` — the inputs are official, the truncation is ours.

## 4. Transformations deliberately NOT applied

- **No district demand.** Allocating state vacancies to districts is an estimate.
- **No cumulative → flow.** All NCS snapshots share one as-on date, so differencing is impossible.
  `flow_available = False` with `flow_unavailable_reason` stated on every row.
- **No state × industry cross-tab.** The two NCS tables are independent marginals; a test asserts they share
  no joinable dimension.
- **No NCS-sector → NCO mapping.** Industry is not occupation.
- **No PAN-India allocation.** It stays one `NATIONAL` row, 20,507,320 vacancies, `lgd_code` NULL.
- **No zero-filling.** No `district × occupation × month` matrix was created.
- **No Census → current.** 2011 structure is marked `is_historical = True`.

## 5. Missing data preserved

| Case | Handling |
|---|---|
| Udyam `'NA'` in small/medium | 352 fact rows NULL; **284 derived shares NULL, never 0.0** |
| Fully urban districts (Mumbai City/Suburban) with zero rural workers | share is `NaN` = unknown, not 0.0; tested explicitly |
| NCO-2004 division `X` | `nco_2015_division` NULL — not forced into a division |
| `Sector Not Specified` | `nic_section_code` NULL and flagged heterogeneous |
| PLFS per-cell standard errors | NULL — the bulletin does not publish them |
| PAN-India residual | `share_of_state_attributable` NULL by definition |

## 6. Coverage and confidence metadata

`analytical_dataset_catalog` carries, per table: grain, source tables, source ids, source vintage,
geography/occupation/industry level, observation status, transformations, row count, coverage note and
limitations. Every analytical row additionally carries `observation_status`, `source_vintage`,
`transformation`, `source_id`, and — where a mapping was used — its authority and confidence.

## 7. Pending (blocked, documented, not substituted)

| Dataset | Status | Reason |
|---|---|---|
| **PLFS industry × occupation cross-tab** | **PENDING** | `microdata.gov.in` serves a chain containing a **self-signed certificate** (openssl error 19) — a privately-rooted chain I will not add trust for. Unit-level microdata also requires registration and a data-use agreement. **Not acquired; cross-tab not created.** |
| Census B-24 for the other 33 states | PENDING | Only pilot states acquired; URL pattern is known (`catalog/13648 + census_state_code`) |
| Census B-27 | PENDING | Not required for the division-level prior |
| NCS flow | PENDING | Needs answers at a second as-on date |
| PMKVY district outcomes | PENDING | `PMKVY-210422.csv` 404s even on the apex host |
| e-Shram, DGT trade × district | PENDING | Unavailable (Steps 1.5–1.7) |
| `location_change_event` | PENDING | LGD publishes no split/merge events |

## 8. Limitations

- **There is still no occupation-coded demand**, and nothing in this layer creates one.
- **The district occupation prior is 15 years old** and covers only 3 states (138 Census-2011 districts).
- **Census districts ≠ LGD districts.** 125 of 785 LGD districts post-date 2011; joining Census to LGD must
  go through `census_2011_code` and will lose those.
- **Division-level mapping is lossy** (divisions 3 and 8 at ~0.79–0.81 purity).
- **B-24's universe is main workers in non-household industry** — not all workers. Recorded per row.
- **Udyam is a 2023 snapshot** advertised as daily; **LGD is a 2023 snapshot** while LGD updates monthly.
- **PLFS is one month**, national only.

## 9. Required before Step 4 (Demand Estimation)

1. **An industry → occupation bridge.** Without `P(occupation | industry, state)` there is no defensible path
   from NCS industry demand to occupation demand. PLFS is the right source; access is the blocker.
2. **A decision on the PAN-India residual** — exclude it, or run it as a labelled scenario. 58.1% of the
   measure depends on this.
3. **A decision on the Census prior's age** — hold 2011 shares constant, or constrain them with a newer
   state-level distribution.
4. **A minimum-confidence policy for the division crosswalk** — divisions 3 and 8 are weak.
5. **Census B-24 for all pilot states' districts mapped to LGD codes**, with the 125-district gap quantified.
6. **A second NCS as-on date** if any flow is to be claimed.
7. **An explicit uncertainty convention**, since the estimate will multiply three uncertain layers.
