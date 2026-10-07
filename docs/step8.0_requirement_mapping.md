# PS 26246 — Requirement Mapping

**Brutally honest status of every problem-statement requirement against the implemented system.**
Verified against the repository on 2026-10-06. Status vocabulary:
`IMPLEMENTED` · `PARTIALLY_IMPLEMENTED` · `DATA_BLOCKED` · `NOT_SUPPORTED_YET` · `EXPERIMENTAL`.

| Status | Count |
|---|---|
**IMPLEMENTED** | 6 |
**PARTIALLY_IMPLEMENTED** | 4 |
**DATA_BLOCKED** | 3 |
**NOT_SUPPORTED_YET** | 2 |
**EXPERIMENTAL** | 1 |

---

## 1. Requirement-by-requirement

### R1 · Aggregate and normalise demand signals from fragmented sources — **IMPLEMENTED**

**Built:** 26 sources registered under a licence gate; 15 acquired as immutable sha256-checksummed snapshots
(35 files, 50.5 MB); conformance to NCO-2015 (3,982 occupations), LGD (821 geographies), NIC-2008 (21
sections), `dim_period` (132); 40 warehouse tables, 82,358 rows; Pandera contracts plus **14 of 14
reconciliations matching each source's own published totals exactly**.

**Evidence:** NCS Parliament answers, Udyam MSME, Census 2011 B-24, LGD, PLFS bulletin, MSDE Annual Report
2023-24, ILOSTAT, DGE NAT table, DGT CTS curricula, NCVET NQR.

**Limitation:** job-portal postings are deliberately excluded (terms of service, and postings ≠ vacancies).
Of 26 registered sources, 2 remain `UNVERIFIED` and several are portal-only.

**Future unlock:** a permitted aggregator API, or NCS publishing machine-readable district data.

---

### R2 · Cross-reference demand against training capacity by sector/trade/district — **DATA_BLOCKED**

**Built instead:** both sides are published, **side by side but never subtracted** — observed state training
outcomes (`fact_training_outcome`, 350 rows, 5 measures × 2 schemes × 35 states) and PMKK infrastructure, next
to the demand products. The 17-row `supply_evidence_matrix` records every source tried.

**Why blocked:** no district × trade, state × trade, state × occupation or district × occupation supply exists
in any accessible official source. Training data has **no occupation dimension**, and **153 of 155** DGT trades
have no official NCO mapping. Cross-referencing would require inventing the link.

**Named blockers:** data.gov.in PMKVY district resource → `ACCESS_PENDING` (registered API key required);
NCVT MIS → `UNAVAILABLE`; NQR bulk filter-search → `UNAVAILABLE`; apprenticeshipindia.gov.in →
`UNAVAILABLE`.

**Future unlock:** gates **G-2** (district × trade evidence, acquired not allocated) and **G-3** (complete
trade marginals + official trade → NCO coverage).

---

### R3 · Forward-looking demand–supply gap forecasts at sector + district granularity — **NOT_SUPPORTED_YET**

**This is the requirement we cannot meet, and the reason is in two independent parts.**

**No gap.** `SUPPLY[state, trade]` is a joint distribution; the project holds row marginals plus a **21.8%**
fragment of column marginals (514,619 of 2,361,798 PMKVY 4.0 enrolments named; **78% in unnamed job roles**)
*from a different scheme*. Marginals never determine an interior. Closing it needs
`P(trade|state) = P(trade)` — substantively false and untestable. All four subtraction forms also fail a unit
and time audit (cumulative stock of registrations vs scheme-cohort candidate counts).

**No forecast.** One dated demand observation (2024-11-15). `flow_available = FALSE` on every demand row,
reason stored: *"measure is a cumulative stock and all acquired snapshots share one as-on date; differencing
requires two different dated snapshots."* PMKVY 1.0 → 2.0 is **not** a time series — different schemes, and
their state orderings are unrelated (Spearman **+0.005**).

**Built instead:** every forecast and gap route returns HTTP 200 with `data: null`, a reason code and a gate.
`is_measured_shortage = false` on every response, enforced at startup.

**Future unlock:** **G-1** (an observed interior cell of `SUPPLY[geography × trade]`) for the gap;
**G-4** (≥2 dated demand observations of the same measure and basis) for any forecast.

---

### R4 · Rank trades/geographies by severity of oversupply/undersupply — **PARTIALLY_IMPLEMENTED**

**Built:** district ranking within a state (`rank_within_state`), district × occupation ranking
(`rank_within_district`, `rank_within_occupation_across_districts`), and national state ranking — all on
**relative allocation signals**, each displaying its derivation caveat.

**Not built:** *severity of oversupply/undersupply*, which presupposes a gap. No severity score,
no oversupply/undersupply classification.

**Limitation, stated on the face of the product:** within a state, output B's ordering **is** the Udyam
enterprise-share ordering (0 of 36 states differ); within a district, output C's **is** the Census-2011
occupation-share ordering (0 of 138 differ). The occupation view therefore promotes the one comparison that
restates neither input — districts within a state × NCO division, which differs from both inputs in **27 of
27** groups.

**Future unlock:** G-1 for true severity; G-6 for wider coverage.

---

### R5 · Interactive dashboard, national → state → district drill-down — **IMPLEMENTED**

**Built:** 8 pages — Landing, National, State, District, Occupation, Methodology, Coverage, Unavailable
capabilities. Full drill-down with `state` required at the protocol level so within-state is the default
comparison by construction. Ranking tables, relative-signal bars, evidence/coverage badges, source-vintage
panels. Dependency-free (no Node build) so it runs offline.

**Limitation:** **no map component** (designed in Step 7.3, not built). Not a false claim and nothing is
unreachable: tables are the only representation. No charts beyond signal bars — most chart forms are
prohibited here by design (no demand-vs-supply bars, no shortage heatmaps, no forecast curves).

---

### R6 · Documented methodology for combining heterogeneous sources — **IMPLEMENTED**

**Built:** 35 in-repo markdown documents including 15 ADRs; an in-product Methodology page rendering each
output's **stored** methodology string, provenance, transformation depth and limitations; and a
machine-readable `config/publication_contract.yaml`. Every mapping row carries `authority` + `method` +
`confidence`; OFFICIAL and PROJECT mappings are structurally separated.

**This requirement is arguably the best-served**, because the methodology had to be explicit for the
identification argument to be checkable.

---

### R7 · Early-warning flags for saturation / acute shortage — **EXPERIMENTAL (not implemented)**

**Designed, deliberately not built.** The Step 7 hybrid Demand-Pressure / Training-System quadrant is
specified in full (`docs/step7_hybrid_indicator_design.md`) and declared in the contract as
`EXPERIMENTAL_ONLY`, `implemented: false`. It is absent from the API surface, the dashboard, exports and
OpenAPI.

**Why not built:** identical rules and thresholds yield **207 flags under PMKVY 2.0 and 0 under PMKVY 1.0**.
Cross-scheme rank correlation is **+0.034** (certification) and **+0.005** (placement). An output whose
existence depends on an undecidable choice between two source schemes is not a production indicator. The
training axis also has **no occupation dimension**, so a flag could never name *which* trade is short.

**Future unlock:** gates **G-5** (scheme-independent or stable training evidence), **G-6** (coverage),
**G-7** (an occupation dimension on the training axis — non-negotiable), **G-8** (a stability demonstration).
Promotion requires a new ADR and **never converts the indicator into a gap**.

---

### R8 · API / export layer feeding target-setting workflows — **IMPLEMENTED**

**Built:** FastAPI, **30 routes** (20 production, 10 blocked), auto-generated OpenAPI at `/docs`. CSV and
JSON export for 11 production outputs, each carrying 13 mandatory metadata keys plus coverage lines,
limitations, prohibited interpretations and per-column semantics. Experimental outputs are refused (403);
non-production and traversal attempts 404.

**Design decision worth noting:** blocked capabilities return **200 with `data: null`** rather than 404,
because a 404 reads as *"none found"* rather than *"not computable"*.

---

### R9 · Multilingual, accessible interface — **PARTIALLY_IMPLEMENTED**

**Built:** full language-switching architecture, translation-key based labels, English complete (106 keys),
Hindi partial (21). **83 keys fall back to English and 0 raw keys leak.** Official NCO/NIC/LGD/Census codes
are never translated. Accessibility: 20/20 checks — skip link, landmarks, `aria-live`, real tables with
captions and `scope`, caveats bound by `aria-describedby` **so a screen reader reaches the caveat before the
numbers**, 44 px targets, `:focus-visible`, dark mode, and evidence status carried by **text + glyph +
position, never colour alone**.

**Limitation:** Hindi is 20% complete. We will not machine-translate official occupational terminology — a
wrong official term is worse than an untranslated one. No third pilot language. Accessibility is verified
structurally via a DOM harness; a manual screen-reader pass has not been done.

---

### R10 · Cover at least a few pilot sectors and States — **IMPLEMENTED**

**Built:** national coverage for observed demand (37 states, 22 sectors) and the estimated occupation
composition; 785 districts for output B; **3 states / 138 districts** for output C, determined by where
Census B-24 was acquired — Uttar Pradesh (71), Maharashtra (35), Tamil Nadu (32), which matches the stated
provisional pilot exactly.

---

## 2. Additional capabilities not requested but built

| Capability | Why it exists |
|---|---|
**Publication contract enforced in code** | evidence status, confidence, coverage, provenance and prohibited interpretations are part of the response contract; the app refuses to start on a breach |
**Terminology lint over the published surface** | reserved words and forbidden ranking phrasings fail the build, including in translation files |
**16 capabilities published as explicitly unavailable** | each with a reason code and an objective unblocking gate |
**9 objective unblocking gates (G-1 … G-9)** | the missing-evidence specification, as a product surface |
**Full reproducibility** | `make reproduce` from sha256-verified raw bytes to dashboard |
**479 tests** | including regression tests for every QA defect found |

---

## 3. Future unlock roadmap

**Every source named below was already identified during the project's own evidence investigation. No source
is invented here.**

### U1 · State × trade supply — *the keystone*

| | |
|---|---|
**Required evidence** | Training outcomes at **state × trade**, with **complete** trade marginals — not a Top-N subset |
**Required grain** | state × trade × measure, measures kept distinct (no inference along enrolled → certified) |
**Time compatibility** | a named scheme and period; one declared scheme per computation |
**Current blocker** | Only **national × Top-N** exists (`fact_training_trade_outcome`, 35 rows). 78% of PMKVY 4.0 enrolment sits in unnamed job roles, so even raking is unavailable |
**Named sources tried** | `apprenticeshipindia.gov.in` → UNAVAILABLE; NQR bulk filter-search → UNAVAILABLE; MSDE Annual Report Tables 5.10 / 5.54 → `PARTIALLY_ACQUIRED` (Top-N only) |
**Unlocks** | **G-1 condition 6** — the first observed interior cell of `SUPPLY[geography × trade]`. Without this, no methodology produces a defensible gap |

### U2 · District × trade supply

| | |
|---|---|
**Required evidence** | District-level PMKVY/NAPS/ITI outcomes by trade, **acquired, not allocated from state totals** |
**Current blocker** | data.gov.in PMKVY district resource → **`ACCESS_PENDING`** (needs a registered API key the project does not hold); **NCVT MIS** → UNAVAILABLE; `supply_coverage_summary.district_level_training_data = 0`, status `NOT_ACQUIRED` |
**Explicitly insufficient** | any state total distributed by population, enterprise share or centre count. That is allocation, not evidence, and would manufacture the variation it claims to measure |
**Unlocks** | **G-2** — district × occupation and district × trade supply |

### U3 · State × occupation and district × occupation supply

| | |
|---|---|
**Required evidence** | U1 or U2, **plus** official trade → NCO mapping coverage sufficient to carry the measure |
**Current blocker** | **2 of 155** trades officially mapped (Electrician DGT/1001, Fitter DGT/1002, from DGT CTS curricula). **153 `MAPPING_UNKNOWN`** |
**Permitted route only** | OFFICIAL mappings. Fuzzy, semantic, embedding, LLM and name-resemblance mapping are permanently prohibited |
**Named sources** | remaining DGT CTS curriculum PDFs (per-trade, acquirable); NCVET *Report on Mapping of Qualifications with NCO Codes* (acquired); NQR Q-File field 14 (acquired, 1 row) |
**Unlocks** | **G-3** — occupation-level supply, and the occupation dimension the early-warning indicator needs |

### U4 · Numeric demand–supply gap

| | |
|---|---|
**Required evidence** | U1 (necessary) + U3, with demand and supply at the **same** time grain, geography, occupation grain, unit and population definition |
**Current blocker** | all six G-1 conditions fail today. Conditions 1–5 are harmonisation problems; **condition 6 — one observed interior cell — is the identification barrier** |
**Unlocks** | **G-1**. Only then may a gap be published, and only at the grain the evidence supports |

### U5 · Forecasting

| | |
|---|---|
**Required evidence** | **≥2 defensible dated observations** of the same demand measure, same basis, same geography, same source |
**Required compatibility** | a flow, or two dated stocks differenceable into one; no scheme redesign or definition change between observations |
**Current blocker** | one NCS as-on date (2024-11-15). `flow_available = FALSE` everywhere, with the reason stored |
**Explicitly excluded** | PMKVY 1.0 → 2.0, permanently. Different schemes; state orderings unrelated (+0.005) |
**Also required** | rolling-origin backtesting against mandatory naive baselines before any forecast is published |
**Unlocks** | **G-4** — forecasting, trend, and any flow measure |

### U6 · Production early-warning indicator

| | |
|---|---|
**Required evidence** | **G-7** an occupation dimension on the training axis *(non-negotiable — without it a flag can never name what is short)*; **G-5** scheme-independent or stable training evidence; **G-6** coverage materially above 138/785 districts and 3/36 states; **G-8** a pre-registered stability demonstration |
**Current blocker** | cross-scheme rank correlation +0.034 / +0.005; flag set collapses 207 → 0 on scheme substitution; training axis has exactly **3** distinct values for 1,242 cells |
**Unlocks** | promotion of the Step 7 quadrant from `EXPERIMENTAL_ONLY` to production — **still not a gap**, and still `is_measured_shortage = false` |

### U7 · Wider demand coverage

| | |
|---|---|
**Required evidence** | Census 2011 B-24 for the remaining 33 states *(same source, already parsed — a pure acquisition task)*; or a PLFS district occupation table; or **NCO-coded NCS vacancies** |
**Current blocker** | acquisition only for B-24. NCS vacancies are not NCO-coded, which is why output C needs a Census prior at all |
**Unlocks** | output C from **138 → up to 785 districts with no formula change**; removal of the 2011-vintage dependency; and a reduction in the 58.13% unattributable residual if NCS publishes district detail |

---

## 4. The honest summary

Of the ten stated requirements: **6 implemented, 4 partially, and the three that depend on a demand–supply
gap are blocked by evidence rather than by engineering.**

The gap requirement is **not met, and this document does not pretend otherwise**. What exists in its place is
a precise, reproducible account of *why* it cannot be met and *exactly which dataset* would change that —
state × trade training outcomes with complete trade marginals, addressed to the ministry that owns them.

A planner can act on that. A fabricated gap table, they could not.
