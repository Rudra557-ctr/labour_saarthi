# Step 5.1 — Supply Evidence Resolution

Date: 2026-10-04 · **Evidence resolution only.** No supply estimation, no district allocation or
interpolation, no gap, no forecasting, no early warning, no recommendations, no API/frontend/LLM, no
synthetic data, **no fuzzy or semantic trade → NCO mapping**. Nothing bypassed: no CAPTCHA, no
authentication, no invented credentials, no URL brute-forcing, no private endpoints.

---

## Verdicts

> ### `DISTRICT_SUPPLY_STATUS = STILL_UNRESOLVED`
> ### `TRADE_NCO_MAPPING_STATUS = PARTIALLY_RESOLVED`

Blocker B moved, and it moved on real evidence: **the official qualification → NCO chain is now proven and
loaded.** What remains missing for B is *enumeration*, not the mapping principle. Blocker A did not move.

---

## 1. Audit of Step 5.0 (verified against the live warehouse)

`fact_training_outcome` 350 · `fact_training_infrastructure` 144 · `dim_training_trade` 155 (NCO mapping
**0/155**) · `fact_training_reconciliation` 14 · `supply_coverage_summary` 8. 215 tests passing.
Existing infrastructure reused throughout — `lmis.ingest.acquire`, `location_master`/`location_alias`,
`lmis.validate.schemas`, `lmis.warehouse.load`, the status vocabulary. **Step 5.0 methodology unchanged;
Step 5.1 is purely additive.**

## 2. Blocker B — trade → NCO: **the chain is proven**

The breakthrough was extracting a Q-File acquired back in Step 1 but never opened.

**NQR Q-File field 14 — "Aligned to NCO/ISCO Code/s" — states an 8-digit NCO-2015 code.**

For `QF_SSC2212_Domestic Data Entry Operator_V3.pdf` it reads **`NCO- 2015/4132.0402`**, and that code
survives three independent checks:

| Check | Result |
|---|---|
| Resolves in `occupation_master` at OCCUPATION level? | **Yes** — `4132.0402` |
| NCO title vs qualification name | **Identical** — both "Domestic Data Entry Operator" |
| `qp_nos_indicated` (NCO digits 7-8 ≠ `00`, per the NCVET handbook) | **True** — the code itself says a QP/NOS exists |
| Hierarchy | 4 Clerks → 41 General and Keyboard Clerks → 413 Keyboard Operators → 4132 Data Entry Clerks |

Three sources agree, so this needs no judgement. Loaded to `map_qualification_to_nco` with
`authority='OFFICIAL'`, `mapping_confidence=1.0`, `nco_mapping_level='OCCUPATION'`, citing the exact field
and file.

### Why this does **not** yet map the 155 trades

Two distinct gaps, both honest:

1. **Enumeration.** Q-File URLs cannot be listed by any sanctioned route. NQR's `filter-search` POST returns
   **HTTP 500 Server Error** for every parameter combination tried — including with the page's own CSRF
   token, and `query_type` turns out to be a contact-form field, not a search filter. `robots.txt` permits
   crawling but **no `sitemap.xml` exists**. The Q-File path needs an awarding-body code (`SSC2212`) that is
   not derivable from a trade name, and **URL brute-forcing was not attempted.**
2. **Object mismatch.** The 155 trades are **DGT Craftsmen Training Scheme trades**, not SSC Qualification
   Packs. Even with Q-File access, a published **trade → qualification** link would be required. NCVET's
   Annexure VII shows DGT holds 463 NQR qualifications, so the counterparts very likely exist — but the
   correspondence is not published in anything held.

**Therefore `dim_training_trade` remains UNMAPPED for all 155 trades,** and a test fails if any NCO code
appears on a trade. A partial chain was not converted into a mapping.

### Mapping granularity, not overclaimed

The evidence supports the **full 8-digit NCO occupation level** where a Q-File states a code — recorded as
`nco_mapping_level='OCCUPATION'`. Where no code is stated, no row is produced. No division-only or
sector-only fallback was invented.

## 3. Blocker A — district training data: **still unresolved**

| Route | Outcome |
|---|---|
| **data.gov.in PMKVY district resource** | **ACCESS_PENDING** — page names `PMKVY-210422.csv` but publishes no `datafile_url`; the constructed path **404s even on the apex host** that successfully served LGD and Udyam. A registered API key is required; the project holds none, and none was invented. |
| **data.gov.in ITI resources** | **REJECTED** — published at **state/UT level only**; there is no district dimension to acquire. |
| **AIKosh (IndiaAI official catalogue)** | **REJECTED** — probed its SSR state (346 datasets). It is an AI model/dataset hub; its single education-and-skill category holds no training statistics. |
| **DGT (`dgt.gov.in`)** | **REJECTED** — notices and circulars only; no ITI directory, capacity or admissions dataset. Its `robots.txt` itself returns HTTP 403. |
| **NCVT MIS** | **UNAVAILABLE** — host unreachable (connection timeout) in Steps 1.5–1.7 and again here. |
| **MSDE Annexure-21 (PMKK)** | **ACQUIRED in 5.0, but not district supply** — it reports a district **count per state**. |

### The distinction the brief insists on, preserved

`DISTRICT × CENTRE COUNT` ≠ `DISTRICT × TRAINEE SUPPLY`, and `DISTRICT × SEATS` ≠ `DISTRICT × COMPLETED
TRAINEES`. Annexure-21 gives counts of districts and of PMKK centres per state. It is stored in
`fact_training_infrastructure` with `unit='count'` (versus `'candidates'` for outcomes), `geo_level='STATE'`,
and the evidence matrix marks it `district_available = False` with the reason stated. A test asserts this.

**No district geography work was required**, because no district-level training data was acquired. The
785-district LGD spine and the 125 districts without Census-2011 codes are therefore untouched by this step.

## 4. Evidence matrix

Stored as data in `supply_evidence_matrix` (10 rows) so the decisions are queryable, not just narrated:
**ACQUIRED 3 · REJECTED 3 · UNAVAILABLE 2 · ACCESS_PENDING 1 · PARTIALLY_ACQUIRED 1.** Every negative
decision carries a concrete reason, and a test enforces that.

## 5. Tables created

| Table | Rows | Note |
|---|---|---|
| `map_qualification_to_nco` | **1** | OFFICIAL, 8-digit, triple-corroborated |
| `supply_evidence_matrix` | **10** | the matrix above |

Warehouse: **36 tables**. Step 5.0 tables untouched (asserted by test).

## 6. The question that matters

> **At what common grain can demand and supply now legitimately be compared?**

**None by occupation, and none by district.** Concretely:

| | Demand side (Step 4.0) | Supply side (Steps 5.0/5.1) | Common? |
|---|---|---|---|
| Geography | district (785, estimated) and state | **state only** | state |
| Occupation | NCO-2015 division (A, C) | **none** | **no** |
| Industry | NIC-2008 section | none | **no** |
| Time | baseline 2024-11-15 | PMKVY 1.0 (2015-16), as-on 2024-03-31 | **poor overlap** |

The only shared dimension is **state**, and comparing a cumulative NCS vacancy stock against PMKVY training
throughput at state level with **no occupation dimension on either side of the join** would be comparing two
unrelated aggregates. It would produce a number, and the number would mean nothing.

**So: `no common occupation grain yet`.** A gap must not be computed in Step 6 as things stand.

## 7. Limitations

- Supply has **no occupation dimension at all** — the binding constraint, more than the district gap.
- **No capacity/seat data**; `fact_training_capacity` deliberately does not exist.
- One Q-File only, so `map_qualification_to_nco` has one row. It is a proof of route, not coverage.
- Temporal mismatch: PMKVY 1.0 is 2015-16; demand baseline is Nov 2024.

## 8. Status vocabulary used

**ACQUIRED** — NQR Q-File chain; MSDE annexures (5.0). **PARTIALLY_ACQUIRED** — the 155 trades (attributes
yes, NCO no). **ACCESS_PENDING** — PMKVY district resource (API key). **UNAVAILABLE** — NCVT MIS; sanctioned
seats. **REJECTED** — ITI state-only data, AIKosh, DGT site, each with a reason. **UNMAPPED** — trade → NCO.

No unavailable dataset is described as estimated anywhere.

## 9. What would resolve each blocker

**Blocker A:** a registered **data.gov.in API key** (then test resource UUIDs as worked for LGD/Udyam); or a
formal MSDE/DGT data request for district × trade training; or NCVT MIS becoming reachable.

**Blocker B:** either (i) an NQR **bulk qualification export** or a working search endpoint, to enumerate
Q-File URLs and harvest field 14 at scale; **plus** (ii) a published **DGT trade → NQR qualification**
correspondence. Failing (ii), the trades could still be mapped by following the official Downward/Upward
Assignment method in the NCVET handbook with per-row confidence and human review — but that is a PROJECT
mapping and needs explicit approval before it is built.
