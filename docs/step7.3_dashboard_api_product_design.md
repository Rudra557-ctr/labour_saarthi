# Step 7.3 — Dashboard and API Product Design

Date: 2026-10-05 · **Design and documentation only.** No application code, no API route, no table, no
migration, no indicator, no gap, no forecast, no synthetic data. No analytical formula or value touched.

Designs the user-facing product around the outputs Step 7.2 made publishable, under the Step 7.1 contract
(`config/publication_contract.yaml`).

| Setting | Value |
|---|---|
`OFFICIAL_ANALYTICAL_MODE` | `OPTION_A` |
`NUMERIC_GAP` | `NOT_IDENTIFIABLE` |
`FORECASTING` | `NOT_SUPPORTED_YET` |
`MEASURED_SHORTAGE` / `is_measured_shortage` | **`FALSE`** |
`HYBRID_PRESSURE_INDICATOR` | `EXPERIMENTAL_ONLY`, not implemented, outside production |
`DEFAULT_DISTRICT_RANKING` | `WITHIN_STATE` |

> **Amended by Step 7.3.1 (ADR-0013), contract version 7.3.1.** Three things in this document were
> tightened after review and the amended wording governs: `analytical_labour_market_context` is now a
> contracted **SUPPORTING**-tier output (§1.5, §4.2 Panel 3) rather than an uncontracted proposal; output B's
> approved label is **`District Relative Demand Allocation Signal`** and output C's is
> **`District x Occupation Relative Demand Allocation Signal`**, each usable only alongside its stored
> caveat; and the circularity, residual and vintage rules of §1.2–§1.4 are now enforced at contract load
> rather than being design prose. The occupation view's comparison (§4.5 Panel 2) is a **Relative Demand
> Allocation Signal** — informative, but still ESTIMATED, never an observed demand ranking.
>
> **Read §1 first.** Validating every proposed comparison against the warehouse produced one finding that
> changes the design more than any layout choice: **two of the three comparisons the brief asks for are
> arithmetic restatements of a single input.** That is already recorded in the data, in columns the pipeline
> has carried since Step 4.0. It does not reopen the identification argument. It does determine what each
> page is allowed to claim.

---

## 1. Validation findings that constrain the design

All computed read-only against `db/lmis.duckdb`. Nothing was written.

### 1.1 The three comparisons, and what each one actually orders

Outputs B and C are products in which one factor is constant inside the comparison group, so the group's
ordering collapses onto the other factor:

```
B[district]            = observed_state_vacancies × enterprise_share_within_state
C[district, division]  = B[district]              × occupation_share_of_district
```

| Comparison | What the ordering actually is | Orderings differ from that input | Verdict |
|---|---|---|---|
| **Districts within a state** (B) | Udyam **enterprise share**, vintage 2023-12-21 | **0 of 36 states** | restatement of one input |
| **Occupations within a district** (C) | **Census-2011** occupation share | **0 of 138 districts** | restatement of one input |
| **Districts within (state × NCO division)** (C) | enterprise share **×** occupation share | **27 of 27 groups** differ from *each* input alone | **the one informative comparison** |
| **Districts across states** (B or C) | adds the NCS signal, imports registration bias | — | available, caveated |

The project already states this. Two stored columns, carried on every row since Step 4.0, say it verbatim:

- `demand_district_relative_signal.within_state_ranking_caveat` —
  *"within a state this ordering equals the Udyam enterprise-share ordering; B adds information only across states"*
- `demand_district_occupation_signal.within_district_ranking_caveat` —
  *"within a district this ordering equals the Census-2011 occupation-share ordering; C adds information only across districts"*

**Design consequence, binding on every page.** The approved default (within-state) is retained — it is the
only district comparison free of NCS cross-state registration bias. But a within-state district ranking
**may not be captioned as a demand ranking**, because it is an enterprise-density ranking. And a
"top occupations in this district" panel **may not be captioned as occupational demand**, because it is the
district's 2011 Census occupational structure. Both must display their stored caveat verbatim, and the
page's primary informative comparison must be *districts within a state and occupation* (§5.3).

### 1.2 The PAN-India residual is a row in the state table, and would top a naive chart

`analytical_state_demand` holds 38 rows: 37 states and **one `is_pan_india_residual = True` row named
"Multiple States/PAN India"**.

| Rank in a naive chart | Name | `vacancies_cumulative` | Residual? |
|---|---|---|---|
| 1 | **Multiple States/PAN India** | **20,507,320** | **TRUE** |
| 2 | West Bengal | 3,922,741 | false |
| 3 | Tamil Nadu | 1,715,285 | false |
| 4 | Maharashtra | 1,533,463 | false |

Any "top states by demand" bar chart that does not filter `is_pan_india_residual = FALSE` shows the residual
as the largest state, at **5.2× West Bengal**. **Rule: every state ranking filters the residual out, and the
residual is rendered as its own coverage disclosure, never as a bar beside states.**

### 1.3 Showing an input as "context" beside its own output is circular

`analytical_district_structure` (Udyam, 2023-12-21) and `analytical_district_occupation_structure`
(Census 2011) are **the inputs to B and C**. Both already carry `not_a_demand_measure = TRUE`.

Placing either beside B or C as corroborating context would present a factor as independent evidence for the
product it was multiplied into. **Prohibited as corroboration.** They may appear only as **explicit
derivation disclosure** — "this ranking *is* this input" — which is the §1.1 requirement, not context.

### 1.4 Nothing on the surface is contemporaneous

| Element | Vintage | Type |
|---|---|---|
Demand baseline (A, B, C; state and industry) | **2024-11-15** | cumulative stock since inception |
Udyam enterprise structure (input to B) | 2023-12-21 | point-in-time |
PMKK infrastructure | 2024-03-31 | point-in-time |
PLFS labour-force context | **M202504** (April 2025) | monthly survey estimate |
Census occupation structure (input to C) | **2011** | historical census |

Five vintages spanning fourteen years. **No shared time axis may be drawn, and no element may be captioned
"current" or "latest".** Each number carries its own as-on date.

### 1.5 PLFS context is national only

`analytical_labour_market_context`: 81 rows, `geo_level = NATIONAL` exclusively,
`district_estimates_valid = FALSE`, `not_a_demand_measure = TRUE`, indicators LFPR / WPR / UR (CWS). It may
appear **only** on the national page, and only as labour-market context — never as demand, never on a state
or district page.

### 1.6 An industry filter must key on NCS sector, not NIC section

`analytical_demand_by_industry`: 22 rows, 22 NCS sectors, **20 distinct NIC section codes, 2 of them NULL**
("Sector Not Specified"; "Water Supply, Sewerage and Waste Management"), and **5 rows flagged
`is_heterogeneous_or_residual`**.

A NIC-section filter would silently drop two sectors. **The filter domain is `ncs_sector_name` (22, the
source-native unit); `nic_section_code` is a mapped attribute, displayed with its
`mapping_authority = PROJECT` and `mapping_confidence = 0.95`.**

### 1.7 Confidence varies *within* output A, so a table-level badge is wrong

`demand_national_occupation_composition`: 175 rows — **157 MEDIUM across 18 NIC sections, 18 LOW across 2**,
with **27 rows flagged heterogeneous or residual**. **Confidence is a per-row badge, never one badge for the
view.**

### 1.8 Districts without a Census prior have no occupation rows at all

| `occupation_prior_status` | Rows | NULL signal | **Zero signal** | NULL division |
|---|---|---|---|---|
`AVAILABLE` | 1,242 | 0 | **0** | 0 |
`CENSUS_NOT_ACQUIRED` | 522 | 522 | **0** | 522 |
`NO_CENSUS_2011_CODE` | 125 | 125 | **0** | 125 |

**No row anywhere has a signal of zero.** A district without a prior carries **one placeholder row with a
NULL division** — not nine division rows. So the UI cannot render an occupation table skeleton for it; it
must render the status and the reason. This structurally satisfies the "never show zeros" requirement.

---

## 2. Product definition

**What this product is:** an evidence-qualified labour-market **demand intelligence** tool. It shows where
relative demand signals are higher, at what confidence, over what coverage, from which sources.

**What it is not:** a gap tool, a shortage tool, a forecasting tool, or a supply tool. Those capabilities are
rendered as explicit unavailability (§10), not omitted.

**Design principle — evidence is the interface, not a footnote.** Every page's second visual element, above
the fold, is its evidence strip: status, confidence, coverage, vintage. A number that cannot be shown with
its evidence strip is not shown.

**Audience:** MSDE and state skilling planners, SSC analysts, district officers, and reviewers who need to
trace any number to its source document.

---

## 3. Information architecture

```
LANDING  (what this does / does not tell you; the three coverage facts; entry points)
   │
   ├── NATIONAL OVERVIEW ─── OBSERVED industry demand (22 NCS sectors)
   │        │                ESTIMATED occupation composition (per-row confidence)
   │        │                PLFS national context (M202504, not a demand measure)
   │        │                The residual disclosure
   │        ▼
   ├── STATE VIEW ────────── OBSERVED state-attributable demand (37 states, residual excluded)
   │        │                districts within the state (= enterprise-share ordering, labelled)
   │        │                state training-system facts (OBSERVED, state grain)
   │        ▼
   ├── DISTRICT VIEW ─────── relative demand signal + within-state rank
   │        │                occupation panel: AVAILABLE (138) or NOT_AVAILABLE + reason (647)
   │        ▼
   └── OCCUPATION VIEW ───── national composition (A) + districts within state × division (C)
                             ◀── the one informative comparison (§1.1)

   cross-cutting, reachable from every page:
   METHODOLOGY & EVIDENCE · COVERAGE & LIMITATIONS · UNAVAILABLE CAPABILITIES
   separately fenced: EXPERIMENTAL / RESEARCH  (nothing implemented; boundary only)
```

**The journey is National → State → District → Occupation, but the evidence is not uniform along it and the
UI says so at each step:** national industry demand is OBSERVED; state demand is OBSERVED but covers 41.87%;
district demand is ESTIMATED at MEDIUM; district × occupation is ESTIMATED at LOW for 138 of 785 districts.
**Evidence weakens as the user drills down, and the interface must make that progression visible** — a
drill-down that looks equally authoritative at every level is the central design failure to avoid.

---

## 4. Page specifications

### 4.1 Landing page

| | |
|---|---|
**Purpose** | Set the correct expectation before any number is seen. |
**User questions** | What does this tell me? What does it not tell me? How current is it? |
**Data** | `demand_coverage_summary`, `supply_coverage_summary`, contract mode block. |
**Grain** | None — orientation only. |
**Filters** | None. |
**Visualisations** | Three coverage statements as text; four mode chips (`NUMERIC_GAP: NOT_IDENTIFIABLE`, `FORECASTING: NOT_SUPPORTED_YET`, `MEASURED_SHORTAGE: FALSE`, baseline `2024-11-15`); entry points; link to Unavailable Capabilities. |
**Mandatory caveats** | The PAN-India residual share and the state-attributable share; 138 of 785 districts for occupation detail; "cumulative since inception as on 2024-11-15 — not a live feed". |
**Prohibited** | A headline total demand figure. A map. Any KPI tile. Any chart. |

**No national total is shown here or anywhere.** The published grand total exists (35,275,830), but it is
cumulative NCS registrations since inception, of which 58.13% is not geographically attributable — it is not
"national labour demand", and a single large number on a landing page would be read as exactly that.

### 4.2 National overview

| | |
|---|---|
**Purpose** | Separate observed industry evidence from estimated occupation composition, visibly. |
**User questions** | Which industries carry the most NCS vacancy registrations? What occupation composition is estimated for them? What is the national labour-force context? |
**Data** | `analytical_demand_by_industry` (OBSERVED, 22) · `demand_national_occupation_composition` (ESTIMATED, 175) · `analytical_labour_market_context` (OBSERVED, national, not a demand measure) · `analytical_state_demand` residual row. |
**Grain** | NCS sector; NIC section × NCO-2015 division; national. |
**Filters** | NCS sector (22); NCO division (9); evidence status; confidence. |
**Visualisations** | **Panel 1 (OBSERVED):** horizontal bar, vacancies by NCS sector, `lakh`, with `is_heterogeneous_or_residual` marked on 5 rows and the PROJECT NIC-alignment note. **Panel 2 (ESTIMATED):** composition matrix / stacked share by NIC section × NCO division, **per-row confidence badge** (§1.7), units `lakh_vacancy_equivalent`. **Panel 3 (CONTEXT):** PLFS LFPR/WPR/UR, CWS, M202504, badged `NOT A DEMAND MEASURE`. **Panel 4:** residual disclosure. |
**Mandatory caveats** | Panels 1 and 2 are **visually separated and separately captioned** — observed totals vs estimated split. Panel 2 names its bridge: ILOSTAT `EMP_TEMP_ECO_OCU_NB_A` (India, PLFS). Panel 3 carries its own vintage and `not_a_demand_measure`. |
**Prohibited** | A national total demand number. Panels 1 and 2 in one combined chart. Treating PLFS as demand. Any time axis across panels (§1.4). |

### 4.3 State view

| | |
|---|---|
**Purpose** | Show observed state-attributable demand and let districts be compared *within* the state. |
**User questions** | How many NCS vacancies are attributed to this state? How do its districts compare? What does the training system report for this state? What is not covered? |
**Data** | `analytical_state_demand` (37, residual excluded) · `demand_district_relative_signal` filtered to the state · `fact_training_outcome`, `fact_training_infrastructure` (OBSERVED, state grain). |
**Grain** | State; district within state. |
**Filters** | State (36); NCO division where occupation detail exists (3 states only); measure/scheme for the training panel; evidence status; confidence. |
**Visualisations** | State observed total with `share_of_published_total` and `share_of_state_attributable`; **district ranking table, default `rank_within_state` ascending**, showing `relative_demand_signal`, `rank_within_state`, **`enterprise_share_within_state`**, confidence, `census_2011_code` presence; choropleth of districts *within the state only*; training-system panel (candidate counts by measure and scheme, with `value_status` and `NO_DATA` rendered as such). |
**Mandatory caveats** | **The stored `within_state_ranking_caveat`, verbatim, directly above the district table** — this ordering is the enterprise-share ordering (§1.1). The residual is excluded from state totals and rankings and is disclosed separately. Training measures are state-level candidate counts within a named scheme and period, **never "supply"**. |
**Prohibited** | Captioning the within-state district ranking as a demand ranking. Showing Udyam enterprise counts as independent corroboration (§1.3). Any district-level training value. Any demand-vs-training comparison chart. Placing the 2024-11-15 demand beside the 2024-03-31 PMKK figures on one axis. |

### 4.4 District view

| | |
|---|---|
**Purpose** | Everything defensible about one district, with its occupation panel honest about availability. |
**User questions** | Where does this district rank within its state? Is occupation detail available? If not, why not? How confident, and from what sources? |
**Data** | `demand_district_relative_signal` (785) · `demand_district_occupation_signal` (1,889 — 1,242 usable). |
**Grain** | District; district × NCO division where `occupation_prior_status = 'AVAILABLE'`. |
**Filters** | District; NCO division; evidence status. |
**Visualisations** | Signal card: `relative_demand_signal`, `rank_within_state` of *n* in state, `signal_share_of_national`, confidence `MEDIUM`, baseline. **Occupation panel, two states only:** (a) `AVAILABLE` → table of 9 divisions with `district_occupation_signal`, `rank_within_district`, `occupation_share_of_district`, `main_workers`, `unclassified_share_not_allocated`, confidence `LOW`; (b) `CENSUS_NOT_ACQUIRED` or `NO_CENSUS_2011_CODE` → **status panel naming the reason**, with its gate, and no table, no chart, no placeholder row. |
**Mandatory caveats** | **The stored `within_district_ranking_caveat`, verbatim, above the occupation table** — this ordering is the Census-2011 occupation-share ordering (§1.1). `unclassified_share_not_allocated` is displayed (median ≈ 0.137) and stated as excluded, not redistributed. The occupation panel is `LOW` confidence; the district card is `MEDIUM`. Census structure is **2011** while the baseline is **2024-11-15**. |
**Prohibited** | **Zero for a missing occupation signal** — no row has one (§1.8). Calling either signal a vacancy count. A district-level training or PMKK value. A trend, sparkline or change indicator. Any arrow or directional glyph. |

### 4.5 Occupation view

| | |
|---|---|
**Purpose** | The occupation-facing entry, built on the **one informative comparison** (§1.1). |
**User questions** | What national composition is estimated for this NCO division? Across districts in a state, which rank higher for *this* division? What is the evidence? |
**Data** | `demand_national_occupation_composition` (A) · `demand_district_occupation_signal` (C). |
**Grain** | NCO-2015 division × NIC section (national); district × division within a state. |
**Filters** | NCO division (9); NCS sector; state (3 with occupation detail); evidence status; confidence. |
**Visualisations** | **Panel 1 (national, ESTIMATED):** the division's composition across NIC sections, `occupation_share_of_total`, per-row confidence. **Panel 2 (the informative comparison):** districts ranked **within the selected state for the selected division**, which differs from both inputs in 27 of 27 groups — captioned as such. **Panel 3:** coverage — 3 of 36 states, 138 of 785 districts. |
**Mandatory caveats** | Three evidence kinds kept visually distinct: observed source totals, estimated national composition, estimated district × occupation signal. NCO-2015 division code **and** title on every row. Panel 2 defaults to one state; cross-state is opt-in and caveated. Output A is **not** a factor in C — the stored methodology string says so, and the UI must not imply the panels compose. |
**Prohibited** | Implying the district occupation signal is a vacancy count. Mixing NCO-2004 and NCO-2015 labels. Any occupation-level supply, training or capacity figure. Any division-to-trade or division-to-qualification claim. |

### 4.6 Methodology and evidence page

**Purpose:** make any number on screen traceable. **Data:** the Step 7.2 envelope plus each output's stored
`methodology`, `source_ids`, `source_documents`, `transformation_depth`, `mapping_authority`. **Content:**
the three stored methodology strings verbatim (A, B, C); the derivation chain
`NCS → Udyam → Census` with each step's own vintage; the vintage table of §1.4; the weakest-link confidence
explanation; the OBSERVED/ESTIMATED distinction and the Step 7.1 correction that output A is ESTIMATED; named
source documents (`LS_UQ2225_2024-12-09.pdf`, `LS_UQ933_2024-12-02.pdf`, `RS_UQ2798_2024-12-19.pdf`).
**Prohibited:** describing any derived output as observed; a numeric confidence.

### 4.7 Coverage and limitations page

**Purpose:** publish the gaps as a first-class product surface. **Data:** `demand_coverage_summary` (8),
`supply_coverage_summary` (10), `fact_data_quality` (14), `supply_evidence_matrix` (17), `docs/limitations.md`.
**Content:** the residual and state-attributable shares; 785 / 138 / 522 / 125 districts with each reason;
trade mapping state (2 officially mapped, 153 `MAPPING_UNKNOWN`, 155 total) **from
`dim_trade_mapping_status`, not from the barred `dim_training_trade.nco_mapping_status`**; data-quality check
results; the five vintages. **Mandatory caveats:** `MAPPING_UNKNOWN` is explicitly distinguished from
`MAPPING_DOES_NOT_EXIST`. **Prohibited:** presenting any coverage gap as zero.

### 4.8 Unavailable capabilities page

**Purpose:** answer "where is the gap analysis?" directly and honestly. **Data:** the Step 7.2
`unavailability_register` (16 capabilities). **Content:** one card per capability — name, `reason_code`,
reason, `blocking_gate`, link to the gate's unblocking conditions. Grouped by reason code so the user sees
the distinction that matters: `NOT_IDENTIFIABLE` (structural, more of the same data will not fix it) vs
`NOT_ACQUIRED` / `ACCESS_PENDING` (an access problem) vs `NOT_SUPPORTED_YET` (a temporal problem) vs
`PROHIBITED`. **Prohibited:** an empty state, a zero, a 404, "no data found", or a "coming soon" implying a
delivery date.

### 4.9 Experimental / research surface

**Not implemented and not to be implemented in Step 7.4.** The boundary is specified so nothing can cross it
by default: separate route and navigation entry, reached by explicit action; banner
`EXPERIMENTAL — NOT AN OFFICIAL OUTPUT`; `NOT_MEASURED_SHORTAGE` guard adjacent to every value; excluded from
every production response and export; statuses limited to the five contract values; never described as
shortage, deficit, skill gap, vacancy estimate or supply shortage. Promotion needs gates G-5 to G-8 and a new
ADR.

---

## 5. Visualisation rules

### 5.1 Permitted

| Visualisation | Where | Backed by | Condition |
|---|---|---|---|
Horizontal bar, observed counts | national industry, state totals | `analytical_demand_by_industry`, `analytical_state_demand` | residual excluded from state bars (§1.2) |
Ranking table | state districts, district occupations, occupation districts | B, C | the stored caveat above it (§1.1) |
Relative-signal bar (unitless, no count axis) | district panels | B, C | axis labelled relative signal; no count formatting |
Choropleth, **within one state** | state view | B | sequential scale on the relative signal; legend states "relative, not a count" |
Composition / stacked share | national occupation | A | per-row confidence (§1.7) |
Distribution (histogram, box) | occupation view | B, C | describes spread of a relative signal only |
Evidence and coverage badges | every page | Step 7.2 envelope | colour-independent (§8) |
Status panel | missing occupation detail, unavailable capabilities | `occupation_prior_status`, register | reason named |

### 5.2 Prohibited

| Prohibited | Why |
|---|---|
**Demand-vs-supply bars, dumbbells or diverging axes** | No supply quantity exists at any occupation or geographic grain. |
**Shortage or gap heatmap** | Not identifiable; `is_measured_shortage = FALSE`. |
**Forecast curve, projection band, or dashed future segment** | One dated observation. |
**Any time axis, trend line, sparkline or period-over-period delta** | A single baseline; the five vintages are not a series (§1.4). |
**Arrows, chevrons, up/down triangles, "rising"/"falling"** | Implies direction where no second observation exists. |
**Absolute vacancy map at district or district × occupation grain** | Those values are `relative_signal_unitless`. |
**National choropleth of output B across states** | Cross-state comparison imports NCS registration bias; permitted only in the opt-in caveated view, not as a default map. |
**A national total demand KPI tile** | 58.13% is unattributable; it is cumulative registrations, not demand. |
**Udyam or Census structure beside B or C as corroboration** | Circular — they are the inputs (§1.3). |
**PLFS on a state or district page** | National only, `district_estimates_valid = FALSE` (§1.5). |
**The residual as a bar beside states** | It would rank first at 5.2× the largest state (§1.2). |
**One combined chart of observed and estimated values** | Collapses the distinction the product exists to preserve. |
**Numeric confidence, gauge, star rating or percentage** | Confidence is ordinal. |
**Colour as the sole carrier of evidence status** | Accessibility (§8). |

### 5.3 The default comparison, stated once

**Districts within a state** is the default district comparison (approved policy), captioned as an
**enterprise-share-equivalent ordering**. **Districts within a state and NCO division** is the primary
*informative* comparison and is the occupation view's main panel. **Occupations within a district** is
presented as the district's **Census-2011 occupational structure**. **Cross-state** is opt-in, caveated,
never a default or a landing visual.

---

## 6. Filters

Every filter below is backed by a column in the table it filters. Nothing else is offered.

| Filter | Domain | Backing column | Applies to | Note |
|---|---|---|---|---|
State | 36 | `state_lgd_code` / `lgd_code` | state, district, occupation | 3 states only for occupation detail |
District | 785 | `lgd_code` | district | 138 have occupation detail |
NCO-2015 division | 9 | `nco_2015_division` | occupation, district, national A | code + title always shown |
NCS sector | **22** | `ncs_sector_name` | national, occupation | **the filter key — not NIC section (§1.6)** |
NIC section | 20 + 2 NULL | `nic_section_code` | national (display) | displayed with PROJECT mapping authority; **not a filter** |
Baseline / vintage | single value per output | `baseline_period`, `snapshot_date`, `as_on_date`, `source_vintage` | all | a selector, not a range; no interval query |
Evidence status | OBSERVED / ESTIMATED / UNAVAILABLE | `observation_status`, `observed_or_estimated` | all | |
Confidence | MEDIUM / LOW | `overall_confidence` | A, B, C | ordinal; no numeric threshold |
Occupation prior status | 3 values | `occupation_prior_status` | district, occupation | lets a user find what is *not* covered |
Scheme / measure | 2 schemes, 5 measures | `scheme`, `measure` | state training panel | never pooled across schemes |

**Explicitly not offered**, because no column supports them: trade or qualification; NSQF level on a demand
output; period range or month; sub-district; sector on a district output (output B has
`occupation_level = NONE` and no industry dimension); any supply, gap or forecast filter; district filter on
PLFS context; numeric confidence threshold.

---

## 7. API information architecture

Logical resources only. Every field is producible from an existing column or the Step 7.2 envelope.

### 7.1 Resources

| # | Resource | Purpose | Parameters | Output grain | Backing |
|---|---|---|---|---|---|
R1 | `/meta/contract` | the publication contract, modes, terminology rules | — | — | `publication_contract.json` |
R2 | `/meta/sources` | source registry and snapshot provenance | `source_id?` | source | `source_master`, `source_snapshot` |
R3 | `/meta/methodology` | stored methodology strings and derivation chains | `output_id?` | output | `methodology` columns |
R4 | `/coverage` | every coverage disclosure, derived | `domain? = demand\|supply` | metric | `demand_coverage_summary`, `supply_coverage_summary` |
R5 | `/demand/national/industry` | OBSERVED vacancies by NCS sector | `ncs_sector?` | NCS sector | `analytical_demand_by_industry` |
R6 | `/demand/national/occupation-composition` | ESTIMATED occupation composition | `nco_division?`, `nic_section?`, `confidence?` | NIC section × NCO division | `demand_national_occupation_composition` |
R7 | `/demand/states` | OBSERVED state-attributable demand | `include_residual = false` (default) | state | `analytical_state_demand` |
R8 | `/demand/districts` | ESTIMATED district relative signal | `state` (**required**), `sort = rank_within_state` | district | `demand_district_relative_signal` |
R9 | `/demand/districts/{lgd_code}` | one district, full evidence | `lgd_code` | district | B (+ C panel status) |
R10 | `/demand/district-occupation` | ESTIMATED district × division signal | `state` (**required**), `nco_division`, `occupation_prior_status?` | district × division | `demand_district_occupation_signal` |
R11 | `/context/labour-force` | PLFS national context | `indicator?`, `area?`, `sex?`, `age_group?` | national | `analytical_labour_market_context` |
R12 | `/training/states` | OBSERVED training-system facts | `state?`, `scheme?`, `measure?` | state × scheme × measure | `fact_training_outcome`, `fact_training_infrastructure` |
R13 | `/training/trades/top-n` | OBSERVED Top-N national trades | `scheme?` | national × trade | `fact_training_trade_outcome` |
R14 | `/capabilities` | the unavailability register | `capability_id?` | capability | `unavailability_register.json` |
R15 | `/quality` | pipeline data-quality checks | `table?` | check | `fact_data_quality` |

**`state` is a required parameter on R8 and R10 by design** — it makes within-state the default at the
protocol level rather than by UI convention. An unparameterised national district list would hand back a
cross-state ranking as if it were neutral. Cross-state is a distinct, explicitly-named parameter
(`comparison=cross_state`) that returns the caveat in `limitations`.

### 7.2 Per-resource contract

| Resource | Evidence | Confidence | Coverage attached | `is_measured_shortage` | Forecast | Interpretation note |
|---|---|---|---|---|---|---|
R5 | OBSERVED | OBSERVED | — | false | false | cumulative NCS registrations by sector; PROJECT NIC alignment |
R6 | ESTIMATED | MEDIUM / LOW **per row** | — | false | false | estimated occupation split of observed industry totals |
R7 | OBSERVED | OBSERVED | residual + state-attributable shares | false | false | residual excluded by default; disclosed separately |
R8 | ESTIMATED | MEDIUM | residual, state-attributable, 785 | false | false | **within-state ordering equals the enterprise-share ordering** |
R9 | ESTIMATED | MEDIUM (district) / LOW (occupation panel) | all district disclosures | false | false | relative signal, not a vacancy count |
R10 | ESTIMATED (1,242) / UNAVAILABLE (647) | LOW | 138 / 785 / 522 / 125 | false | false | **within-district ordering equals the Census-2011 share ordering** |
R11 | OBSERVED | OBSERVED | — | false | false | **not a demand measure**; national only; M202504 |
R12 | OBSERVED | OBSERVED | `NO_DATA` cells | false | false | candidate counts within a named scheme; **not supply** |
R13 | OBSERVED | OBSERVED | Top-N subset | false | false | **not a complete distribution** |
R14 | UNAVAILABLE | — | — | false | false | reason code and blocking gate |

---

## 8. Response envelope

**Reuses the Step 7.2 envelope exactly; nothing is redefined.** The resource layer adds only `data`,
`query` and `links`.

```jsonc
{
  "data": [ /* rows, or null for an unavailable capability */ ],
  "query": { "state": "27", "nco_division": "7", "comparison": "within_state" },
  "meta": {
    // --- verbatim from src/lmis/publish/contract.py ---
    "output_id": "demand_district_occupation_signal",
    "publication_status": "PRODUCTION",
    "evidence_status": ["ESTIMATED", "UNAVAILABLE"],
    "confidence": ["LOW"],
    "confidence_source": "demand_district_occupation_signal.overall_confidence",
    "coverage": { /* each fact with value, unit, label, derived_from */ },
    "grain": { "geo_level": "DISTRICT", "occupation_level": "NCO_2015_DIVISION" },
    "unit": "relative_signal_unitless",
    "measure_basis": "CUMULATIVE_SINCE_INCEPTION",
    "vintage": ["2024-11-15"],
    "provenance": { "source_ids": [], "transformation_depth": [2], "columns": [] },
    "interpretation": "RELATIVE_RANKING_SIGNAL_NOT_A_VACANCY_COUNT",
    "prohibited_interpretations": ["VACANCY_COUNT", "SHORTAGE", "SUPPLY_GAP", "FORECAST"],
    "is_measured_shortage": false,
    "forecast_available": false,
    "forecast_unavailable_reason": "NOT_SUPPORTED_YET: ... see gate G-4",
    "flow_available": false,
    "default_ranking": { "mode": "WITHIN_STATE", "column": "rank_within_district",
                         "cross_state_caveat": "..." },
    "contract_version": "7.1",
    // --- added by the resource layer ---
    "limitations": [
      "within a district this ordering equals the Census-2011 occupation-share ordering; C adds information only across districts",
      "Census occupation structure is 2011; the demand baseline is 2024-11-15"
    ],
    "row_status_breakdown": { "AVAILABLE": 1242, "CENSUS_NOT_ACQUIRED": 522, "NO_CENSUS_2011_CODE": 125 }
  },
  "links": { "methodology": "/meta/methodology?output_id=...", "coverage": "/coverage?domain=demand" }
}
```

**Rules.** `meta` is non-optional. `limitations` is populated from the output's **stored caveat columns**, not
authored in the API layer. Row-level status travels on the row (`occupation_prior_status`, `value_status`),
never flattened into a table-level badge. `is_measured_shortage` is `false` on every response including
errors. A row whose value is unavailable carries `null` plus its reason — never `0`.

---

## 9. Evidence and confidence UX

### 9.1 The four evidence states

| State | Meaning | Visual | Example |
|---|---|---|---|
**OBSERVED** | A published figure attributable to a named document | filled square ■ + "OBSERVED" | `analytical_state_demand` |
**ESTIMATED** | Derived; the method is named and the depth shown | half square ◪ + "ESTIMATED" + depth | B, C, A |
**SUPPORTING** | Real and observed, but **not a demand measure**; context only | open square □ + "CONTEXT — NOT A DEMAND MEASURE" | PLFS; Udyam structure |
**UNAVAILABLE** | Not present, with a reason | dashed outline ⬚ + reason code | the 647 districts; 16 capabilities |

### 9.2 The distinction the UI must teach

> **"Estimated" means the number exists but was derived** — we can show it, name its method, and tell you
> how far it sits from an observation. **"Unavailable" means the number does not exist and cannot currently
> be computed** — we show you why, and what evidence would change that.

These must never share a visual treatment. The common failure is rendering both as a blank or a dash, which
teaches the user that missing data and derived data are the same thing. **Unavailable is never blank, never
zero, never a dash alone; it is always a reason.**

### 9.3 Confidence

Ordinal only — `MEDIUM` and `LOW` on the current surface, with `HIGH` and `INSUFFICIENT_EVIDENCE` reserved.
Rendered as the word plus a short plain-language expansion, with the binding dimension on hover:

- **MEDIUM** — "derived from observed data through one documented transformation"
- **LOW** — "derived through more than one transformation, or resting on a historical or proxy structure"

**Prohibited:** any percentage, probability, gauge, 1–5 scale or star rating. Weakest-link is explained on the
methodology page: overall confidence is the **worst** dimension, never an average, because averaging lets a
strong term mask a fatal one.

---

## 10. Unavailable capabilities UX

All 16 register entries are surfaced. Each is reachable **from the place a user would look for it** — the gap
question is answered on the district and occupation pages, not only on a separate page, because that is where
the user forms the expectation.

| Capability | Reason code | Where surfaced |
|---|---|---|
Numeric demand–supply gap | `NOT_IDENTIFIABLE` | district, occupation, landing |
Forecast | `NOT_SUPPORTED_YET` | every page showing a baseline |
District × occupation supply · state × occupation supply | `NOT_IDENTIFIABLE` | occupation, district |
District × trade supply | `NOT_ACQUIRED` | coverage |
State × trade supply | `NOT_IDENTIFIABLE` | coverage |
Shortage / surplus count | `NOT_IDENTIFIABLE` | district, occupation |
District / district × occupation / NCO-coded vacancy counts | `NOT_AVAILABLE` | wherever a relative signal appears |
PAN-India residual allocation | `PROHIBITED` | state, national |
District-level training value | `PROHIBITED` | state training panel |

**Required pattern:** reason code · plain-language reason · blocking gate · link to unblocking conditions.
**Forbidden:** empty array, `0`, HTTP 404, "no data found", "coming soon", a disabled control with no
explanation, or silent omission of the capability from navigation.

**The grouping carries the product's most important message:** `NOT_IDENTIFIABLE` is structural — more of the
same data will not fix it — while `NOT_ACQUIRED` is an access problem. A user who cannot tell these apart
will conclude the project is merely incomplete.

---

## 11. Source, vintage and provenance placement

| Element | Placement |
|---|---|
Baseline `2024-11-15` | Persistent header chip on every page: "Demand baseline: 2024-11-15 (cumulative since inception)". |
Per-output vintage | In the evidence strip of each panel; never one global date (§1.4). |
Source id and document | Per panel; named PDFs in a provenance drawer and on the methodology page. |
Transformation depth | Beside ESTIMATED badges. |
Mapping authority / confidence | Wherever a mapped attribute appears (NIC section, NCO-2004→2015). |
Contract version | Footer, with a link to the methodology page. |
Coverage | In the evidence strip, with the denominator. |

**Prohibited:** "live", "real-time", "current", "latest", "updated just now", a relative timestamp
("2 days ago"), an auto-refresh indicator, or a single global "data as of" date spanning the five vintages.

---

## 12. Multilingual and accessibility requirements

**Language.** English + Hindi, plus one pilot-state language. Persistent switcher, locale in the URL,
`lang` on `<html>`, no layout reflow dependence.

**What is translated:** UI chrome; evidence and confidence labels and their plain-language expansions;
caveats and interpretation notes; reason codes' human-readable text; methodology prose; column headers.

**What is never translated** — identifiers must remain machine-comparable and officially citable:
NCO-2015 division codes; NIC section codes; LGD codes; Census 2011 codes; NCO/NIC/NSQF scheme names; source
ids; reason codes, status enums and `publication_status` values (translated text accompanies the code, never
replaces it); source document filenames; the `contract_version`.

**Official taxonomy titles** (NCO division names, NCS sector names) are shown in the source's official
English form, with a reviewed translation **beside** it where an official translation exists. **Machine
translation of official occupation titles is prohibited** — a wrong official term is worse than an untranslated
one in a government planning tool.

**Numeric and date formatting.** Indian digit grouping (lakh/crore) with the digits also available in plain
grouping for export; locale-aware dates with the ISO form always present in the DOM; **a relative signal is
never formatted like a count** — no thousands separators, no unit suffix (rule T-1).

**Accessibility (WCAG 2.1 AA target, GIGW-aligned).**
- Evidence and confidence are carried by **text plus shape plus position**, never colour alone (§9.1) —
  colour-blind users must distinguish OBSERVED from ESTIMATED from UNAVAILABLE without hue.
- Data tables are real `<table>` with `<caption>`, `<th scope>`, and the caveat associated via
  `aria-describedby` so a screen reader reaches the caveat **before** the numbers.
- Every chart has a tabular equivalent reachable without a pointer; the table is the primary representation
  and the chart the enhancement.
- **Map accessibility fallback:** the choropleth is always accompanied by the ranked table it visualises, with
  equivalent ordering and values; the map is never the only route to any number.
- Keyboard operation for every filter and drill-down; visible focus; logical order.
- Live regions announce filter result counts and status changes.
- Target size ≥ 44 px; contrast ≥ 4.5:1; no reliance on hover — every tooltip's content is also reachable
  on focus and present in the DOM.
- Plain-language explanations for every technical term, at the point of use, not only in a glossary.

---

## 13. Export design

**Permitted formats:** CSV and JSON of any production resource.

**Every export carries a metadata header block (CSV comment lines) or `meta` object (JSON):** `output_id`,
`publication_status`, `evidence_status`, `confidence`, full `coverage` with denominators, `unit`,
`measure_basis`, `vintage`, `provenance` (source ids and documents), `interpretation`,
`prohibited_interpretations`, `limitations` (the stored caveats), `is_measured_shortage: false`,
`forecast_available: false`, `contract_version`, export timestamp and the `query` that produced it.

**Row-level columns are preserved, not stripped:** `observation_status` / `observed_or_estimated`,
`overall_confidence`, `occupation_prior_status` / `value_status`, `unit`, `baseline_period`,
`transformation_depth`, and the caveat columns.

**Rules.**
- **A column carrying a relative signal keeps its name and its `unit = relative_signal_unitless`.** It may
  not be renamed to anything count-like, and no "vacancies" column may be derived from it.
- An unavailable value exports as **empty with its reason in the adjacent status column** — never `0`.
- The PAN-India residual row is included in a state export **only with `is_pan_india_residual` present**.
- **No experimental output may appear in a production export** — enforced today by
  `assert_no_experimental_leak`.
- **An export without the metadata block is prohibited.** It is the likeliest route by which a relative
  signal becomes "vacancies" in someone's slide, which is why the header is mandatory rather than optional.

---

## 14. Interpretation guardrails

No example numbers are invented; placeholders stand for values the system would supply.

| ✅ Allowed | ❌ Not allowed |
|---|---|
"District X has a relatively higher demand signal than other districts in the same state." | "District X has N vacancies for occupation Y." |
"Within its state, District X ranks *k* of *n* on the estimated relative demand signal, as on 2024-11-15." | "District X is the *k*-th highest-demand district in India." |
"This within-state ordering is the Udyam enterprise-share ordering; the NCS demand component varies only across states." | "District X has more labour demand than District Z in the same state." |
"For NCO division D, among districts of this state, District X ranks higher on the estimated signal." | "Occupation D is in short supply in District X." |
"These are the division shares of District X's 2011 Census occupational structure, scaled by its district signal." | "These are the occupations most in demand in District X." |
"NCS registered V lakh vacancies in NIC section S, cumulatively since inception, as on 2024-11-15." | "Section S has V lakh job openings." / "Section S added V lakh jobs." |
"Nationally, an estimated share of vacancies in section S corresponds to NCO division D." | "There are N vacancies for division D." |
"58.13% of published NCS vacancies are PAN-India or multiple-state and are not attributed to any state." | "National demand totals M vacancies." |
"Occupation detail is unavailable for this district: its state's Census B-24 table is not acquired." | "This district has no demand for occupation D." / showing `0`. |
"State S reported C candidates certified under scheme P (2016-20)." | "State S produced C skilled workers." / "State S's supply is C." |
"No demand–supply gap is published; the evidence required is listed under Unavailable Capabilities." | "The gap is small / not significant / zero." |
"This is a single observation as on 2024-11-15; no trend is available." | "Demand is rising / stable / falling." |
"Confidence is LOW: the output rests on a 2011 occupational structure." | "Confidence is 62%." |

---

## 15. Dashboard contract table

| page | output | status | grain | default comparison | mandatory caveat | prohibited interpretation |
|---|---|---|---|---|---|---|
Landing | coverage summaries | PRODUCTION | — | none | residual + state-attributable shares; 138/785; baseline 2024-11-15 | a national total demand figure |
National | `analytical_demand_by_industry` | PRODUCTION · OBSERVED | NCS sector | across 22 sectors | PROJECT NIC alignment (0.95); 5 heterogeneous rows | official NIC statistic; sector employment |
National | `demand_national_occupation_composition` | PRODUCTION · ESTIMATED | NIC section × NCO division | within section | **per-row** MEDIUM/LOW; ILOSTAT/PLFS bridge named | occupation-wise vacancy count |
National | `analytical_labour_market_context` | SUPPORTING · OBSERVED | national | across indicators | NOT A DEMAND MEASURE; M202504; national only | demand; any state or district reading |
National | residual row | PRODUCTION · OBSERVED | national | none | not allocated to any state | a state; a demand total |
State | `analytical_state_demand` | PRODUCTION · OBSERVED | state (37) | across states | residual excluded and disclosed | current or annual vacancies |
State | `demand_district_relative_signal` | PRODUCTION · ESTIMATED | district | **within state** | **stored `within_state_ranking_caveat` verbatim** | a demand ranking; vacancy counts |
State | `fact_training_outcome` / `_infrastructure` | PRODUCTION · OBSERVED | state × scheme × measure | within scheme | candidate counts in a named scheme/period | **supply**; capacity; district values |
District | `demand_district_relative_signal` | PRODUCTION · ESTIMATED | district | within state | MEDIUM; baseline; rank of *n* | vacancy count |
District | `demand_district_occupation_signal` | PRODUCTION · ESTIMATED / UNAVAILABLE | district × NCO division | within district (= Census structure) | **stored `within_district_ranking_caveat` verbatim**; LOW; unallocated share; Census 2011 | vacancy count; shortage; **zero for missing** |
Occupation | `demand_national_occupation_composition` | PRODUCTION · ESTIMATED | NIC × division | within division | per-row confidence; A is not a factor in C | actual vacancies by occupation |
Occupation | `demand_district_occupation_signal` | PRODUCTION · ESTIMATED | district × division | **within state × division** | 3/36 states, 138/785 districts; LOW | occupation supply; shortage |
Coverage | coverage, quality, evidence matrix | PRODUCTION · OBSERVED | metric | none | `MAPPING_UNKNOWN` ≠ `MAPPING_DOES_NOT_EXIST` | a gap shown as zero |
Methodology | envelope + stored methodology | PRODUCTION | output | none | A is ESTIMATED, not OBSERVED | any derived output as observed |
Unavailable | unavailability register | UNAVAILABLE | capability | grouped by reason code | reason + gate on every card | "no data found"; coming soon |
Experimental | hybrid quadrant | **EXPERIMENTAL_ONLY · not implemented** | district × division | n/a | `EXPERIMENTAL`; `NOT_MEASURED_SHORTAGE` | shortage; deficit; skill gap; vacancy estimate |

---

## 16. API contract table

| resource | status | grain | parameters | evidence | confidence | coverage | limitations |
|---|---|---|---|---|---|---|---|
`/meta/contract` | PRODUCTION | — | — | — | — | — | contract is authoritative; not analytical data |
`/meta/sources` | PRODUCTION | source | `source_id?` | OBSERVED | — | — | registry state, not availability |
`/meta/methodology` | PRODUCTION | output | `output_id?` | — | — | — | stored strings; not re-derived |
`/coverage` | PRODUCTION | metric | `domain?` | OBSERVED | — | self | derived from the warehouse |
`/demand/national/industry` | PRODUCTION | NCS sector | `ncs_sector?` | OBSERVED | OBSERVED | — | PROJECT NIC alignment; 2 NULL NIC; 5 heterogeneous |
`/demand/national/occupation-composition` | PRODUCTION | NIC × division | `nco_division?`, `nic_section?`, `confidence?` | ESTIMATED | MEDIUM/LOW per row | — | ILOSTAT/PLFS bridge; national only; not a count |
`/demand/states` | PRODUCTION | state | `include_residual=false` | OBSERVED | OBSERVED | residual, state-attributable | residual excluded by default; cumulative stock |
`/demand/districts` | PRODUCTION | district | **`state` required**, `sort`, `comparison?` | ESTIMATED | MEDIUM | residual, state-attributable, 785 | **within-state ordering = enterprise-share ordering** |
`/demand/districts/{lgd_code}` | PRODUCTION | district | `lgd_code` | ESTIMATED | MEDIUM / LOW | all district disclosures | relative signal; occupation panel may be UNAVAILABLE |
`/demand/district-occupation` | PRODUCTION | district × division | **`state` required**, `nco_division`, `occupation_prior_status?` | ESTIMATED / UNAVAILABLE | LOW | 138/785/522/125 | **within-district ordering = Census-2011 share ordering**; 2011 structure |
`/context/labour-force` | SUPPORTING | national | `indicator?`, `area?`, `sex?`, `age_group?` | OBSERVED | OBSERVED | — | **not a demand measure**; national only; M202504 |
`/training/states` | PRODUCTION | state × scheme × measure | `state?`, `scheme?`, `measure?` | OBSERVED | OBSERVED | `NO_DATA` cells | **not supply**; no occupation dimension; never pooled across schemes |
`/training/trades/top-n` | PRODUCTION | national × trade | `scheme?` | OBSERVED | OBSERVED | Top-N subset | not a complete distribution; no geography |
`/capabilities` | UNAVAILABLE | capability | `capability_id?` | UNAVAILABLE | — | — | `data: null`; reason code + gate; never 404 |
`/quality` | PRODUCTION | check | `table?` | OBSERVED | — | — | pipeline checks, not data accuracy |

Every row returns `is_measured_shortage: false` and `forecast_available: false`.

---

## 17. Metrics and views explicitly rejected

Each was considered and rejected because the current evidence cannot support it.

| Rejected | Why |
|---|---|
**National / state / district total labour demand** | 58.13% unattributable; the measure is cumulative NCS registrations since inception, not labour demand. |
**Any time series, trend, growth rate, YoY/QoQ, sparkline, directional arrow** | One dated demand observation; the five vintages are not a series. |
**Demand vs supply chart at any grain** | No supply quantity exists at any occupation or geographic grain. |
**Shortage / surplus / gap metric, heatmap or severity score** | `NOT_IDENTIFIABLE`. |
**Forecast of anything** | `NOT_SUPPORTED_YET`, gate G-4. |
**Vacancy counts at district or district × occupation grain** | Those values are `relative_signal_unitless`. |
**Seeker-to-vacancy ratio** | No jobseeker registration data is acquired. |
**Wage or salary signal** | Not acquired at any grain. |
**Demand per capita / per working-age population** | No 2024-vintage population denominator for the 138 districts; a 2011 Census stock would mix vintages. |
**State or district PLFS indicators** | PLFS is national only; `district_estimates_valid = FALSE`. |
**District-level training, PMKK or certification value** | Training evidence is state level; district variation would be invented. |
**Occupation- or trade-level supply, capacity or seats** | Published at national × Top-N trade only; a Top-N subset may not become a distribution. |
**Trade or qualification filter on any demand output** | No trade or qualification dimension exists on a demand table. |
**NSQF level on a demand output** | No such column. |
**Sector filter on output B** | Output B has `occupation_level = NONE` and no industry dimension. |
**National choropleth of output B as a default view** | Cross-state comparison imports NCS registration bias. |
**Udyam or Census structure as corroborating context beside B or C** | Circular — they are the inputs. |
**Sub-district / block views** | Finest acquired grain is district. |
**Period-range or month filters** | A single baseline; no period dimension on any demand output. |
**Numeric confidence, composite score, or any index not already built** | Confidence is ordinal; no new score is permitted. |

---

## 18. Implementation Gate

**Step 7.4 may implement exactly the following.**

| # | Permitted |
|---|---|
1 | The **read-only API resources R1–R15** of §7, backed solely by existing tables and the Step 7.2 envelope, reusing `src/lmis/publish/contract.py` for all metadata. `state` required on R8 and R10. |
2 | The **response envelope** of §8 — Step 7.2 fields verbatim, plus `data`, `query`, `links`, `limitations` (populated from stored caveat columns) and `row_status_breakdown`. |
3 | The **eight pages** of §4 with the §5 visualisation rules, the §6 filters only, and the §15 caveats rendered from stored columns. |
4 | The **evidence and confidence UX** of §9, including the OBSERVED/ESTIMATED/SUPPORTING/UNAVAILABLE treatment and the "estimated vs unavailable" distinction. |
5 | The **unavailable-capability surfaces** of §10, from the existing register. |
6 | **Exports** per §13, with the mandatory metadata block and the experimental-leak guard. |
7 | **i18n and accessibility** per §12, with taxonomy identifiers untranslated. |
8 | Extension of the **terminology lint** to UI label catalogues and export headers, reusing `src/lmis/publish/terminology.py`. |
9 | Tests: every §14 guardrail, the residual exclusion, the required `state` parameter, zero-never-for-missing, caveat presence, export metadata presence, and no experimental leak. |

**Step 7.4 must not:** introduce any analytical methodology; compute a gap, shortage, surplus, supply or
forecast value; create a composite score or index; create a table or migration; alter an analytical formula or
value; implement the hybrid indicator or any part of the experimental surface beyond its boundary; add a
filter, field or visualisation not listed here; or relax a Step 7.1 or 7.2 guardrail.

**Any new metric requires its own design step and a new ADR.** If an implementer finds a page element that
cannot be backed by an existing column, the correct action is to **remove the element and report it**, never
to compute a value to fill it.
