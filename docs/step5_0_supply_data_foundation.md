# Step 5.0 — Supply Data Acquisition & Validation

Date: 2026-10-04 · **Acquisition and validation only.** No supply estimation, no demand–supply gap, no
shortage/surplus score, no forecasting, no early warning, no recommendations, no API/frontend/LLM.
No synthetic data. No invented trade → NCO mapping. Nothing bypassed.

---

## Headline

**The project now has real official supply-side data for the first time** — and it came from a source not
previously tried: the **MSDE Annual Report 2023-24** (276 pages, 31 annexures), after the PMKVY district
datasets proved inaccessible.

All **14 reconciliation checks match the source's own published totals exactly** (difference = 0), and
**100% of state names resolve to LGD codes**.

The honest limitation: this data is **state-level**. District-level training data remains **NOT_ACQUIRED**.

---

## 1. Audit before implementation

Verified against the live warehouse, not prior reports:

- **29 tables, 81,459 rows.** Supply-side training tables present: **none**.
- Two registered training sources, **neither acquired**: `PMKVY_DISTRICT_OUTCOMES`, `DGT_ITI_CAPACITY`.
- Step 4.0 outputs intact (175 / 785 / 1,889 / 8 rows). 184 tests passing.
- Existing conventions reused rather than duplicated: `lmis.ingest.acquire` (manifests + sha256),
  `location_master` / `location_alias` for geography, `lmis.validate.schemas` for Pandera contracts,
  `lmis.warehouse.load` for DDL + loading, the `OBSERVED/SUPPORTING/ESTIMATED` status vocabulary.

## 2. Sources investigated

| Priority | Source | Outcome |
|---|---|---|
| 1 | PMKVY district outcomes (`PMKVY-210422.csv`) | **NOT_ACQUIRED** — 404 even on the apex `data.gov.in` host that worked for LGD and Udyam |
| 1 | PMKVY resource pages via SSR `datafile_url` extractor | **NOT_ACQUIRED** — no `datafile_url` published; only a filename |
| 1 | data.gov.in datastore API | **ACCESS_PENDING** — requires a registered API key the project does not hold |
| 1 | **AIKosh (IndiaAI official catalogue)** | **Dead end** — probed its SSR state (346 datasets); it is an AI model/dataset hub, not a statistics catalogue. Only one relevant *category*, containing no training statistics |
| 1 | **MSDE Annual Report 2023-24** | **✅ ACQUIRED** — 4 usable annexures |
| 2 | DGT / NCVT MIS | **UNAVAILABLE** — portal unreachable in Steps 1.5–1.7; no open trade × district dataset located |
| 2 | ITI capacity datasets | **UNAVAILABLE** — figures appear only in parliamentary answers, which conflict between editions |
| 3 | NCVET / NQR | Already held as taxonomy (59 sectors); publishes no training volumes |

## 3. What was acquired, and what each measure actually means

`MSDE_ANNUAL_REPORT_2023-24.pdf`, 7,836,874 bytes, checksummed manifest at
`data/raw/MSDE_ANNUAL_REPORT_2023_24/2026-10-04/`.

| Annexure | Page | Content | Concept |
|---|---|---|---|
| **11** | 232 | State-wise PMKVY 1.0 (2015-16) | Enrolled / Trained / Assessed / Certified / Placed |
| **14** | 237 | State-wise CSSM PMKVY 2.0 STT (as on 2024-03-31) | same five measures |
| **21** | 249–250 | State-wise PMKKs (as on 2024-03-31) | **Infrastructure**: districts, districts with a PMKK, PMKKs allocated, PMKKs established |
| **22** | 251–259 | List of 155 NSQF-compliant trades | **Trade reference**: name, entry qualification, NSQF level, duration, revision year |

**The five concepts are never interchangeable, and the schema enforces it.** They are stored in **long
format** — one row per measure, each carrying its own `measure_definition`, so the concept travels with the
number. A wide table invites `trained == certified`; long format forces the measure to be named at the point
of use.

| Measure | Definition stored on every row |
|---|---|
| `ENROLLED` | candidates registered for training |
| `TRAINED` | candidates who completed the training input |
| `ASSESSED` | candidates who underwent assessment |
| `CERTIFIED` | candidates certified after assessment |
| `PLACED` | **reported placed at point of report; NOT sustained employment** |

Observed funnel across both schemes: **2,856,785 enrolled → 2,819,153 trained → 2,693,772 assessed →
2,112,412 certified → 483,689 placed.** Placement is 16.9% of enrolled and 22.9% of certified. Tests assert
the funnel ordering holds for every state, which is how a column mis-assignment during PDF extraction would
be caught.

**Infrastructure is kept separate** (`unit = count`, not `candidates`): a training centre is not a trainee.
A test asserts the metric vocabularies do not intersect.

## 4. Actual grain — preserved, not forced

| Table | Grain |
|---|---|
| `fact_training_outcome` | `source_annexure × state × measure` (scheme and period as attributes) |
| `fact_training_infrastructure` | `source_annexure × state × metric`, as on 2024-03-31 |
| `dim_training_trade` | `trade_section_index × trade_serial` |

**Not forced into `TIME × STATE × DISTRICT × OCCUPATION`.** There is no district dimension and no occupation
dimension in this source, and none was manufactured. Annexure-21 reports a district *count per state*, which
is not district-level training data.

## 5. Geography standardization

Reused `location_master` + the curated `location_alias` table. **Exact name first, then curated alias, never
fuzzy** — a wrong geography join is invisible once made.

**Result: 350/350 outcome rows and 144/144 infrastructure rows MATCHED. Zero unmatched.**

Two curated aliases were added, both reviewed with a recorded rationale:
`Dadra & Nagar Haveli and Daman & Diu` (ampersand spelling of the merged UT) and `Jammu Kashmir` (the report
omits the conjunction).

One **text-artifact** fix was needed, and is distinguished from a geography match in the code comments: the
report hyphenates across line breaks, so `Andaman And Nicobar Is-\nlands` arrived as one cell. Rejoining a
hyphen followed by whitespace restores the characters the typesetter split — it is not name similarity
matching.

**Historical boundaries:** this data is state-level, and state boundaries are stable over the period
covered, so the district-reorganisation problem documented in Steps 1.7/3.1 does not arise here. Had the
source been district-level, the 125 post-2011 districts would have applied.

## 6. Trade / occupation coding — **UNMAPPED, deliberately**

The source publishes trades with **NSQF level**, entry qualification and duration. **No annexure publishes an
NCO code.**

Therefore `dim_training_trade.nco_2015_code` is **NULL for all 155 trades**, with
`nco_mapping_status = 'UNMAPPED_NO_OFFICIAL_MAPPING'`, and `nco_mapping_authority` /
`nco_mapping_confidence` both NULL. A test asserts any non-null value is a failure.

**No trade → NCO mapping was invented.** What would be needed to build one defensibly:

1. The **NQR Q-File NCO field** per qualification — Step 1 established that NSQF qualifications are *required*
   to carry an NCO code (NCVET report, Annexure IX), and that the code lives on the qualification record.
   Harvesting it per QP would give `authority = OFFICIAL`.
2. A **DGT trade → NSQF qualification** link, since these 155 CTS trades are not the same objects as SSC
   Qualification Packs.
3. Failing both, a PROJECT mapping following the official Downward/Upward Assignment method in the NCVET
   handbook, with per-row confidence — never keyword matching presented as authoritative.

Note the extraction subtlety that mattered: the trade serials **restart at each section** (85 Engineering +
65 Non-Engineering + 5). Keying on the serial alone silently collapsed sections and dropped 70 trades on the
first attempt. The key is now `(section, serial)` and the recovered split is exactly **85 / 65 / 5**, matching
the annexure title.

## 7. Missingness and zero policy

The report prints `-` where it reports nothing. That is loaded as **NULL with `value_status = 'NO_DATA'`,
never 0** — a zero would assert "nobody was placed", which a dash does not say. **5 cells** are affected
(Andaman & Nicobar PLACED in both schemes; Ladakh CERTIFIED and PLACED).

`value_as_published` retains the raw string (`'1,36,635'`, `'-'`) so the parse is auditable and the decision
reversible. A genuine source `0` would be `AVAILABLE` with `value = 0.0` and is therefore distinguishable
from missing — a test asserts this.

## 8. Reconciliation — 14 of 14 exact

| Annexure | Measures reconciled | Result |
|---|---|---|
| 11 (PMKVY 1.0) | all 5 | **exact** (e.g. ENROLLED 1,986,016 = published 1,986,016) |
| 14 (CSSM PMKVY 2.0 STT) | all 5 | **exact** (e.g. CERTIFIED 660,776) |
| 21 (PMKKs) | all 4 | **exact** (districts 785, with-PMKK 707, allocated 818, established 714) |

An independent cross-check worth noting: Annexure-21's own district total is **785**, which equals the
district count in our LGD spine — two unrelated official sources agreeing.

## 9. Tables created

| Table | Rows |
|---|---|
| `fact_training_outcome` | **350** (2 schemes × 36 states × 5 measures) |
| `fact_training_infrastructure` | **144** (36 states × 4 metrics) |
| `dim_training_trade` | **155** |
| `fact_training_reconciliation` | **14** |
| `supply_coverage_summary` | **8** |

Warehouse: **34 tables, 82,137 rows.** Build with `make supply`; full chain `make reproduce`.

## 10. Coverage status (project vocabulary)

| Metric | Value | Status |
|---|---|---|
| training outcome rows | 350 | AVAILABLE |
| states with training outcomes | 36 | AVAILABLE |
| geography unmatched rows | 0 | AVAILABLE |
| measure cells with no data | 5 | NO_DATA |
| trades catalogued | 155 | AVAILABLE |
| **trades mapped to NCO** | **0** | **UNMAPPED** |
| **district-level training data** | **0** | **NOT_ACQUIRED** |
| **PMKVY district resource API** | **0** | **ACCESS_PENDING** |

## 11. Limitations

- **State-level only.** No district training data; the demand side has district outputs, the supply side does
  not, so a district-level gap is not yet computable.
- **No occupation dimension.** Trades carry NSQF level, not NCO, so supply cannot yet be compared to
  occupation-coded demand.
- **Two schemes only.** PMKVY 1.0 and CSSM PMKVY 2.0 STT. Annexures 12/13/16/17/18/20 (PMKVY 2.0 overall,
  3.0, 4.0) use **nested multi-level headers** (STT / RPL / Grand Total sub-columns) and were deliberately
  **not parsed** rather than parsed unreliably.
- **Placement is point-of-report**, and PIB indicates placement tracking was discontinued after PMKVY 3.0 —
  so the 22.9% certified-to-placed rate here is historical, not current.
- **Vintage mix:** PMKVY 1.0 covers 2015-16; Annexures 14 and 21 are as on 2024-03-31.
- **No capacity/seat data.** `fact_training_capacity` was **not created** — nothing acquired measures
  sanctioned seats. An empty table would have implied the concept was covered.

## 12. Unresolved

| Item | Status |
|---|---|
| District × trade training data | **NOT_ACQUIRED** |
| data.gov.in API key | **ACCESS_PENDING** |
| DGT / NCVT MIS ITI capacity | **UNAVAILABLE** |
| Trade → NCO mapping | **UNMAPPED** — evidence required listed in §6 |
| PMKVY 2.0-overall / 3.0 / 4.0 annexures | **NOT_ACQUIRED** (nested headers) |
| Sanctioned seats / capacity | **UNAVAILABLE** |
| Current placement tracking | **UNAVAILABLE** after PMKVY 3.0 |

## 13. Terminology used

**OBSERVED** — every row in all three supply tables; measured and published by MSDE.
**SUPPORTING** — not used in this step; these are direct measurements, not structural proxies.
**ACCESS_PENDING** — PMKVY district resource (needs a registered API key).
**NOT_ACQUIRED** — district-level training data; the nested-header annexures.
**UNAVAILABLE** — DGT/NCVT capacity; sanctioned seats; current placement tracking.
**UNMAPPED** — trade → NCO.

No unavailable dataset is described as estimated anywhere.
