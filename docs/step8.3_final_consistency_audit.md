# Step 8.3 — Final Repository Consistency Audit

Date: 2026-10-06 · **Audit only. Nothing was changed.** Two genuine discrepancies were found; both are
reported below rather than silently fixed, per the change-control rule.

| | |
|---|---|
**Surfaces audited** | **47** — production code, API, dashboard, publication contract, Step 8.0 / 8.1 / 8.2 docs, PPTX slide text, PPTX speaker notes, architecture diagram source and SVG |
**Checks performed** | **61** across sections A–G |
**PASS** | 59 |
**ISSUE** | **2** — both LOW severity, both in frozen Step 7 documents |
**False positives verified by hand** | 3 |

---

## Authoritative values (read from the repository, 2026-10-06)

| Quantity | Authoritative value | Source of truth |
|---|---|---|
NCS published grand total | **35,275,833** | `demand_coverage_summary.ncs_vacancies_published_total` |
PAN-India / multiple-state residual | **20,507,320** | `…ncs_vacancies_pan_india_residual` |
Residual share | **58.13%** (58.1342) | `1 − ncs_state_attributable_share` |
State-attributable | **14,768,513** | `…ncs_vacancies_state_attributable` |
State-attributable share | **41.87%** (41.8658) | `…ncs_state_attributable_share` |
Districts with occupation structure | **138** of **785** | `…districts_with_occupation_signal` / `…districts_with_relative_signal` |
Tables · migrations · rows | **40 · 7 · 82,358** | warehouse · `db/migrations/` |
Tests | **479** | `pytest --collect-only` |

---

## A · NCS totals — **PASS, with 2 issues**

A regex sweep for near-miss variants of every authoritative figure across all 47 surfaces.

| Figure | Variants found | Verdict |
|---|---|---|
20,507,320 · 14,768,513 · 58.13% · 41.87% · 82,358 · 479 | none | **PASS** |
35,275,833 | **`35,275,830` in 3 places** | 1 benign, **2 issues** |

### ISSUE-1 · `docs/step7.1_indicator_publication_decision.md:108`

| | |
|---|---|
**Current** | `\| NCS published grand total \| 35,275,830 \| any demand total \|` |
**Authoritative** | **35,275,833** |
**Severity** | **LOW** — off by 3 vacancies (0.0000085%); a frozen internal methodology document; not cited by any presentation artifact |
**Recommended action** | Correct in a future maintenance step. **Do not present from this document.** If a judge reads the repository and asks, the answer is: "35,275,833 — that line predates the Step 8.0 correction and is a known stale value." |

### ISSUE-2 · `docs/step7.3_dashboard_api_product_design.md:210`

| | |
|---|---|
**Current** | "The published grand total exists (35,275,830), but it is cumulative NCS registrations…" |
**Authoritative** | **35,275,833** |
**Severity** | **LOW** — identical in nature to ISSUE-1 |
**Recommended action** | As above. |

**Why these were not fixed here:** Step 7 documents are frozen, this step is an audit, and the change-control
rule requires reporting over silent correction. Neither value reaches a slide, a speaker note, the API, the
dashboard or an export — **every presentation surface carries 35,275,833.**

### Benign occurrence (not an issue)

`docs/step8.1_presentation_checklist.md:109` contains `35,275,830` **inside the sentence recording the
correction**: *"the published NCS total, written as 35,275,830, is 35,275,833."* That is the audit trail
working, not a stale value.

---

## B · District coverage — **PASS**

`138 of 785` is consistent across all 20 surfaces that state it, as are the sub-counts **522**
(`CENSUS_NOT_ACQUIRED`) and **125** (`NO_CENSUS_2011_CODE`). No surface states a different pair.

---

## C · System scale — **PASS**

`40 tables` · `7 migrations` · `82,358 rows` · `479 tests` — all match the repository, and no variant
appears anywhere.

---

## D · Capability state — **PASS (9/9)**

| Setting | Contract | Stated in deck |
|---|---|---|
`NUMERIC_GAP` | `NOT_IDENTIFIABLE` | yes |
`FORECASTING` | `NOT_SUPPORTED_YET` | yes |
`MEASURED_SHORTAGE` | `false` | yes |
`HYBRID_PRESSURE_INDICATOR` | `EXPERIMENTAL_ONLY` | **not mentioned — correct** |
`OFFICIAL_ANALYTICAL_MODE` | `OPTION_A` | internal string not printed — correct |
`DEFAULT_DISTRICT_RANKING` | `WITHIN_STATE` | yes |
hybrid `implemented` | `false` | — |
Production ML model | **none installed, none in code** | stated explicitly on slide 10 |
Synthetic data | **0 columns, 0 rows** | stated |

**Note on the hybrid:** it appears nowhere in the deck. That is deliberate and correct — an experimental
output must not be raised unprompted. It is covered in the judge Q&A if asked.

---

## E · Production outputs — **PASS**

The contract declares **12** production outputs. The three with approved custom labels are used **verbatim**
in the deck:

- `District Relative Demand Allocation Signal`
- `District x Occupation Relative Demand Allocation Signal`
- `Labour-force context (PLFS) — CONTEXT, NOT A DEMAND MEASURE`

Each appears in 5–6 Step 8 documents with identical wording. No surface uses an unapproved alias.

---

## F · Blocked capabilities — **PASS**

The contract declares **16**; the deck surfaces **6 headline rows** and the Q&A covers the rest. Reason codes
match the contract exactly:

| Capability | Reason code |
|---|---|
`demand_supply_gap_numeric` | `NOT_IDENTIFIABLE` |
`forecast` | `NOT_SUPPORTED_YET` |
`district_trade_supply` | `NOT_ACQUIRED` |
`state_occupation_supply` | `NOT_IDENTIFIABLE` |
`pan_india_residual_allocation` | `PROHIBITED` |

Live verification: all 10 blocked routes return **HTTP 200 with `data: null`**, a reason code and a gate.

---

## G · Terminology — **PASS (10/10, after verifying 2 false positives)**

| Rule | Result |
|---|---|
Approved "Allocation Signal" label used | PASS |
`relative_signal_unitless` stated | PASS |
All four tiers present (OBSERVED / ESTIMATED / SUPPORTING / UNAVAILABLE) | PASS |
"demand ranking" never asserted | PASS |
"we forecast" never asserted | PASS |
"skill gap" never asserted | **PASS** — see FP-1 |
training never called "supply" | **PASS** — see FP-2 |

### Verified false positives

**FP-1 · slide 12** — *"We don't manufacture a **skill gap** from incomplete data."* A negation, and the
approved Step 8.1 closing line.

**FP-2 · notes 9** — *"**Supply by state** and trade is a joint distribution."* The identification argument,
naming the quantity that does not exist.

**FP-3 · `data_sources.md`** — a grep initially suggested the grand total was described as the residual. The
full sentence reads *"20,507,320 of 35,275,833 vacancies (58.1%)"* and is **correct**; the truncation was an
artefact of the search window.

---

## Operational verification (live, 2026-10-06)

| Check | Result |
|---|---|
API starts | **PASS** (< 1 s) |
Dashboard, static assets, `/docs` | **PASS** (200) |
11 representative routes incl. a blocked one | **PASS** (200 each) |
Exports CSV + JSON | **PASS** |
Hybrid export refused | **PASS** (403) |
Filter domains | **PASS** — 36 states · 3 with occupation detail · 9 divisions · 22 sectors |
Test suite | **479 passed** |
Terminology lint | **PASS** — 0 violations |
Warehouse | 40 tables · 7 migrations · 82,358 rows — **unchanged** |

---

## Conclusion

**The presentation surface is internally consistent and matches the running product.** The two issues are
stale copies of one figure in frozen Step 7 methodology documents, off by three vacancies, not reachable from
any slide, note, API response, dashboard screen or export. They do not block submission or presentation.

**Nothing in this audit was changed.**
