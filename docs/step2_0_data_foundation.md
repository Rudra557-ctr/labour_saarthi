# Step 2.0 — Real Data Foundation

Date: 2026-10-04 · **Implementation.** Observed data only. No demand index, no district estimation,
no forecasts, no gap scores, no recommendations, no API/frontend/LLM, no synthetic data.

---

## What was built

A DuckDB warehouse (`db/lmis.duckdb`) with **16 tables**, loaded from 11 checksummed raw snapshots,
with Pandera contracts enforced and SQL-queryable lineage from any measure back to the sha256 of the
bytes it came from.

```
make verify      # re-hash every snapshot against its manifest
make masters     # dimensions + mappings + provenance
make facts       # observed fact tables
make validate    # Pandera contracts -> fact_data_quality
make warehouse   # apply DDL, load DuckDB
make reproduce   # all of the above + profile + test
```

## Tables and grain

### Dimensions and reference

| Table | Rows | Grain | Source |
|---|---|---|---|
| `location_master` | **821** | one row per geography node | LGD (36 states/UTs + 785 districts) |
| `location_alias` | **8** | one row per curated name variant | project, reviewed |
| `location_change_event` | **0** | — | LGD publishes no change events |
| `occupation_master` | **3,982** | one row per NCO-2015 node | DGE NAT table |
| `sector_master` | **59** | one row per NQR sector | NQR |
| `nic_section_master` | **20** | one row per NIC-2008 section | NIC-2008 PDF |
| `dim_period` | **132** | one row per calendar month | generated |

### Mappings

| Table | Rows | Authority |
|---|---|---|
| `map_nco2004_to_nco2015` | **3,447** | **OFFICIAL** (published concordance, confidence 1.0) |
| `map_ncs_sector_to_nic_section` | **21** | **PROJECT** (name alignment verified against NIC-2008; 1 deliberately unmapped) |

### Observed facts

| Table | Rows | Grain | Measure | Unit |
|---|---|---|---|---|
| `fact_vacancy_official_by_state` | **114** | snapshot_date × state (or NATIONAL residual) × source file | `vacancies_cumulative` | count |
| `fact_vacancy_official_by_sector` | **63** | snapshot_date × NCS sector × source file | `vacancies_cumulative` | **lakh, as published** |
| `fact_establishment_district` | **6,280** | snapshot_date × district × enterprise_category × size_class | `enterprise_count` | count |
| `fact_labour_force_estimate` | **81** | period × NATIONAL × area × sex × age_group × indicator | `value_percent` | percent |

### Provenance and quality

| Table | Rows | Purpose |
|---|---|---|
| `source_master` | **22** | every registered source with licence, granularity, verification status |
| `source_snapshot` | **26** | one row per acquired file: sha256, size, URL, HTTP status, retrieval time |
| `fact_data_quality` | **6** | Pandera contract results per table per run |

## Design rules enforced in code, not just documented

- **`observed_or_estimated` is NOT NULL on every fact.** Step 2.0 loads `OBSERVED` /
  `OBSERVED_SURVEY_ESTIMATE` only. The column exists so estimation can never arrive unlabelled.
- **Missing stays missing.** `'NA'` in Udyam becomes NULL — **352 rows**. A zero would silently assert
  "no medium enterprises in this district". A test pins the exact count.
- **Units are explicit and never silently converted.** NCS sector figures stay in **lakh** as published;
  state figures are counts.
- **The two NCS tables are not joinable.** They are independent marginal tables; a test asserts they
  share no dimension beyond snapshot metadata, so a joint state × sector cross-tab cannot be derived.
- **PLFS is NATIONAL only.** The Pandera schema rejects any other `geo_level`, because a district or
  state row would be a statistically invalid claim.
- **The PAN-India residual is kept, flagged and never redistributed.** 20,507,320 of 35,275,833
  (58.1%) carries `geo_level='NATIONAL'`, `lgd_code IS NULL`, `is_pan_india_residual=true`.
- **`publication_vintage` stays NULL** unless the source states it — never defaulted to the download date.

## Verification evidence

**Reconciliation against the published figure.** `fact_vacancy_official_by_state` rows for
`RS_UQ2798_2024-12-19.pdf` sum to exactly **35,275,833**, the grand total the answer prints. The
state-attributable share computes to **41.9%**, independently reproducing the Step 1.5 finding.

**PLFS values spot-checked against the printed bulletin**, encoded as parametrised tests:
LFPR rural male 15-29 = 63.5 · LFPR r+u person 15+ = 55.6 · WPR r+u person 15+ = 52.8 ·
WPR urban male 15+ = 71.0 · UR urban female 15-29 = 23.7 · UR rural person all ages = 4.5.

**Geography resolution: 0 unresolved state names.** Both pre-2020 UTs that NCS still reports separately
("Dadra and Nagar Haveli", "Daman and Diu") resolve through `location_alias` to the single merged LGD UT.
Many-to-one, documented, with the 2019 merger Act cited as the rationale.

**Establishment join: 6,280/6,280 rows join to a district** in `location_master`.

**Lineage in one SQL statement:**

```sql
SELECT f.state_name_as_source, f.vacancies_cumulative,
       s.publisher_org, ss.file_name, ss.sha256, ss.size_bytes
FROM fact_vacancy_official_by_state f
JOIN source_master   s  ON s.source_id = f.source_id
JOIN source_snapshot ss ON ss.source_id = f.source_id AND ss.file_name = f.snapshot_file;
```

## Parser hardening worth noting

The PLFS bulletin defeated two simpler parsers before this one. Its area label sits on the **second**
row of each three-row block (so "last label seen" drops each block's first row), the area order is
**not consistent between statements** (Statement 3 leads with urban), a statement **spans two pages**,
and its header is **repeated on the continuation page**. The parser now groups rows into blocks by the
age-group cycle and takes each block's area from whichever row carries the label, asserting the cycle
and raising if a block has no recoverable label — so a future layout change breaks the build instead of
producing mislabelled facts.

## Remaining blockers (unchanged from Step 1.7, documented as pending)

1. **Census B-24/B-27 not acquired** — `censusindia.gov.in` serves an incomplete TLS chain (missing
   emSign intermediate). Certificate verification was not disabled.
2. **No PLFS occupation × industry cross-tabulation** — needed for the only defensible industry →
   occupation bridge. The monthly bulletin does not contain it.
3. **PMKVY district outcomes** — `PMKVY-210422.csv` returns 404 even on the apex host.
4. **125 of 785 districts have no Census-2011 code** — permanent ceiling on any Census-based prior.
5. **`location_change_event` empty** — district splits/merges unmodelled; cross-boundary time series unsafe.
6. **Only one PLFS month loaded** (April 2025). More bulletins are needed for any time series.
7. **NCS flow not derivable yet** — three answers share the same as-on date (2024-11-15), so differencing
   yields nothing. Answers at different as-on dates are required.
8. **Udyam and LGD are 2023 snapshots**, not live feeds.
9. **Licences unconfirmed** per data.gov.in resource (GODL-India assumed).
10. **e-Shram, DGT/ITI trade × district** still unavailable.
