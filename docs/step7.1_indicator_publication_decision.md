# Step 7.1 — Indicator Publication Decision

Date: 2026-10-05 · **Decision and documentation only.** No code, no schema change, no new score, no new
threshold, no synthetic data. No analytical value altered.

Governs: what the LMIS dashboard and API are **permitted to publish**, what must remain **experimental**, and
what must be reported as **explicitly unavailable**.

| Setting | Value |
|---|---|
| `OFFICIAL_ANALYTICAL_MODE` | **`OPTION_A`** — evidence-qualified demand intelligence |
| `HYBRID_PRESSURE_INDICATOR` | **`EXPERIMENTAL_ONLY`** |
| `NUMERIC_GAP` | **`NOT_IDENTIFIABLE`** |
| `MEASURED_SHORTAGE` | **`FALSE`** |
| `FORECASTING` | **`NOT_SUPPORTED_YET`** |

Upstream: Step 6 / ADR-0009 (no identifiable numeric gap; Option D designed), Step 7 / ADR-0010 (quadrant,
no composite). This step does **not** reopen the identification argument. Two discrepancies were found while
validating against the live database; **neither disturbs it.** Both are recorded in §10.

---

## 0. Two discrepancies found during validation

Reported here because this step's entire subject is publication accuracy, and both would otherwise be
published as fact.

### 0.1 Output A is `ESTIMATED`, not `OBSERVED` — terminology correction

The Step 7.1 brief describes output A as *"National occupation composition — OBSERVED × NATIONAL_PROXY"*.
The table disagrees with itself being called observed:

```
demand_national_occupation_composition.observed_or_estimated = 'ESTIMATED'   (all 175 rows)
overall_confidence                                           ∈ {MEDIUM, LOW}
```

Output A is a **derived composition**: observed NCS industry vacancy totals combined with an ILOSTAT/PLFS
national industry × occupation structure. The observed part is the industry total; the occupation split is
estimated. Calling the product "observed" would overstate it by one full inferential step.

**The genuinely `OBSERVED` demand products are different tables:** `analytical_state_demand` and
`analytical_demand_by_industry`, both carrying `observation_status = 'OBSERVED'`. §1 therefore separates
them into their own publication tier, which the brief's three-output framing had merged.

This is a labelling correction, not a methodological one. **It does not change any value, any grain, or the
identification argument.**

### 0.2 `supply_coverage_summary` publishes a stale zero — must not be cited

| Table | Says | Status |
|---|---|---|
| `supply_coverage_summary` | `trades_mapped_to_nco = 0`, note *"no official trade→NCO mapping published; none invented"* | **STALE — wrong** |
| `dim_trade_mapping_status` | 2 trades `OFFICIAL_MULTI_NCO`, 153 `MAPPING_UNKNOWN` | **CURRENT** |
| `map_trade_to_nco` | 4 rows, `mapping_authority = OFFICIAL`, `mapping_confidence = 1.0` | **CURRENT** |

The value is hard-coded at `src/lmis/cli.py:684`, written during Step 5.0 — before Step 5.2 found the
official trade → NCO linkage on DGT CTS curricula. Two trades are in fact officially mapped: **Electrician
(DGT/1001)** → NCO 7411.0100, 7412.0200 and **Fitter (DGT/1002)** → NCO 7233.0100, 7233.0200.

**Consequence for this policy:** `supply_coverage_summary.trades_mapped_to_nco` is **barred from publication**
(§3, row S-7). The authoritative count is `dim_trade_mapping_status`. The hard-coded constant is listed in
§9 as a permitted Step 7.2 fix.

**Does this change the identification argument? No.** 2 of 155 trades mapped leaves 153 unmapped and does not
create a single `state × trade` or `district × trade` supply cell. The Step 6 conclusion stands unchanged.

---

## 1. Section A — Production / official outputs

### 1.1 What may be published

**Tier 1 — OBSERVED.** Published counts, directly attributable to a named official document.

| Output | Grain | Unit | Vintage | Confidence | Publishable |
|---|---|---|---|---|---|
| `analytical_state_demand` | state (+ 1 NATIONAL residual row) | `count` | 2024-11-15 | OBSERVED | **Yes** |
| `analytical_demand_by_industry` | NIC section | `lakh` | 2024-11-15 | OBSERVED | **Yes**, with the mapping caveat below |
| `fact_training_outcome` | state × scheme × measure | `candidates` | per scheme | OBSERVED | **Yes**, as training-system facts — **never as "supply"** |
| `fact_training_infrastructure` | state | `count` | as on 2024-03-31 | OBSERVED | **Yes** |
| `fact_training_trade_outcome` | **national** × Top-N trade | `candidates` | per scheme | OBSERVED | **Yes**, and must be labelled "Top-N, not a complete distribution" |

**Mapping caveat on the industry view:** `analytical_demand_by_industry` carries
`mapping_authority = 'PROJECT'`, `mapping_method = 'NAME_ALIGNMENT_VERIFIED_AGAINST_NIC_2008'`,
`mapping_confidence = 0.95`. The vacancy counts are observed; **the NCS-sector → NIC-section alignment is
the project's own.** Any industry view must say so. It may not be presented as an official NIC-coded
statistic.

**Tier 2 — ESTIMATED, publishable with mandatory qualification.**

| Output | Grain | Unit | Confidence | Coverage | Publishable |
|---|---|---|---|---|---|
| **A** `demand_national_occupation_composition` | national × NIC section × NCO division | `lakh_vacancy_equivalent` | MEDIUM / LOW | national only | **Yes**, qualified |
| **B** `demand_district_relative_signal` | district (785) | `relative_signal_unitless` | **MEDIUM** | **41.87%** of published NCS vacancies | **Yes**, qualified |
| **C** `demand_district_occupation_signal` | district × NCO division | `relative_signal_unitless` | **LOW** | **138 / 785 districts (17.6%)**, 3 / 36 states | **Yes**, heavily qualified |

**Tier 3 — Coverage and quality metadata. Publication is mandatory, not optional.**
`demand_coverage_summary` (8 rows), `supply_coverage_summary` (8 rows, **excluding** the row named in §0.2),
`fact_data_quality` (14 rows), `source_master` / `source_snapshot` provenance.

### 1.2 Mandatory coverage disclosures

These are facts from `demand_coverage_summary` and must appear wherever the corresponding output appears:

| Fact | Value | Where it must appear |
|---|---|---|
| NCS published grand total | 35,275,830 | any demand total |
| **PAN-India residual, never allocated** | **20,507,320 (58.13%)** | any district or state demand view |
| State-attributable portion | 14,768,513 (41.87%) | any district view — this is output B's entire base |
| Districts with a relative signal | 785 | output B |
| **Districts with an occupation signal** | **138** | output C — always beside the 785 |
| Districts with no Census 2011 code | 125 | output C: *a prior can never exist* — not "missing data" |
| Districts where B-24 is not acquired | 522 | output C: *not acquired* — distinct from "no demand" |

**The 58.13% residual is the single most load-bearing disclosure in the system.** A district view built on
41.87% of the published total, presented without that number, invites the reader to believe they are seeing
national demand.

### 1.3 Exact permitted terminology

| Concept | **Permitted wording** | **Forbidden wording** |
|---|---|---|
| Output B / C values | "relative demand signal", "demand signal (relative)", "relative demand rank", "demand pressure percentile" | "vacancies", "jobs", "openings", "demand (count)", "number of vacancies", "demand volume", "jobs available" |
| Output A values | "estimated occupation composition of vacancies", "vacancy-equivalent composition" | "vacancies by occupation", "occupation-wise vacancy count" |
| `analytical_state_demand` | "NCS vacancies mobilised, cumulative since inception, as on 2024-11-15" | "vacancies in 2024", "current vacancies", "annual vacancies", "open positions" |
| Any cumulative measure | "cumulative since inception", "stock as on &lt;date&gt;" | "this year", "monthly", "current", "latest", "new" |
| Estimated values | "estimated", "derived", "modelled" + the method named | "measured", "actual", "reported", "official figure" |
| Training measures | "candidates enrolled / trained / assessed / certified / placed", "training-system outcome", "reported placement" | **"supply"**, "workers produced", "skilled workers available", "workforce supply", "trained workforce" |
| Training ratios | "certification rate within &lt;scheme, period&gt;", "reported placement rate within &lt;scheme, period&gt;" | "training quality", "state performance", "training capacity", "efficiency" |
| PMKK counts | "districts with a PMKK, as on 2024-03-31" | "training capacity", "seats", "coverage of skilling" |
| Confidence | the four categories `HIGH` / `MEDIUM` / `LOW` / `INSUFFICIENT_EVIDENCE`, verbatim | any percentage, probability, star rating, "83% confident", "high accuracy" |
| Coverage | the explicit fraction and its denominator ("138 of 785 districts") | "nationwide", "pan-India", "all districts", "comprehensive" |
| Unavailable | `NOT_ACQUIRED` / `ACCESS_PENDING` / `NO_CENSUS_2011_CODE` / `CENSUS_NOT_ACQUIRED` / `MISSING_NOT_REPORTED` / `NOT_APPLICABLE` — the specific reason | "no data", "0", "—" with no reason, blank, "not applicable" used as a catch-all |

**Rule T-1.** A relative signal is never rendered with a unit that implies persons. No "vacancies" axis label,
no "× 1,000", no count formatting, no currency-style thousands separators on a unitless score.

**Rule T-2.** "Supply" is a reserved word. It may not appear in any label, column header, tooltip, API field
name or chart title anywhere in the system, because no supply quantity exists at any occupation or trade
grain. Training-system outcomes are named as what they are.

**Rule T-3.** Every estimated number carries its transformation depth in reach of the reader. Output C is
`transformation_depth = 2` on a base that is itself derived — three inferential steps from an observation.

**Rule T-4.** Missing is never zero, never blank, and never a dash alone. The specific status is shown.

### 1.4 What the dashboard may say

- "Districts ranked by relative demand signal, as on 2024-11-15. Covers 41.87% of published NCS vacancies;
  the 58.13% PAN-India residual is not allocated to any district."
- "Within Uttar Pradesh, this district ranks 4th of 71 on the relative demand signal for NCO division 7."
- "Estimated relative demand signal. LOW confidence. Derived from state NCS vacancies, Udyam establishment
  structure and Census 2011 occupation structure."
- "Occupation detail is available for 138 of 785 districts (3 states). For the remaining 647, the Census
  occupation table has not been acquired or no 2011 code exists — this is not an absence of demand."
- "Certification rate 0.759 within PMKVY 2.0 CSSM STT (2016-20, as on 2024-03-31)." *(state level)*
- "No demand–supply gap is published. The evidence required to compute one is listed under Data Gaps."

### 1.5 What the dashboard must NEVER say

1. Any vacancy, job or opening **count** at district or district × occupation level.
2. Any shortage, surplus, deficit, gap, skill gap or mismatch **number**.
3. "X workers needed", "X workers short", "shortfall of X".
4. Any forecast, projection, trend, growth rate, "rising", "falling", or "expected".
5. Any statement that training supply is insufficient or sufficient for an occupation.
6. The word **"supply"** for a training measure (Rule T-2).
7. A confidence expressed as a number or a probability.
8. "Nationwide" / "all districts" / "pan-India" for an output covering 138 districts or 41.87% of vacancies.
9. A district-level training value — no such value exists (Step 7 §13.1 item 5).
10. A comparison of PMKVY 1.0 against PMKVY 2.0 as change over time (Step 7 §11 item 5).
11. A zero where the status is `NOT_ACQUIRED`, `ACCESS_PENDING` or `NO_CENSUS_2011_CODE`.
12. Any ranking of districts across states on output C without the NCS-registration-bias caveat (§1.6).

### 1.6 View labelling by level

| View | Default basis | Mandatory label |
|---|---|---|
| **National** | `analytical_state_demand` + `analytical_demand_by_industry` (OBSERVED) + output A for occupation composition | "Cumulative since inception, as on 2024-11-15. Occupation composition is ESTIMATED from a national industry × occupation structure." |
| **State** | `analytical_state_demand` (OBSERVED) | "Observed NCS vacancies mobilised, cumulative, as on 2024-11-15. Excludes the 58.13% PAN-India residual, which is not state-attributable." |
| **District** | output B | "ESTIMATED relative demand signal. MEDIUM confidence. Base = 41.87% of published vacancies. Not a vacancy count." |
| **District × occupation** | output C | "ESTIMATED relative demand signal. **LOW confidence.** 138 of 785 districts. Not a vacancy count, not a shortage." |
| **Occupation** | output A (national) + output C (3 states) | "National composition is estimated; district detail exists for 3 states only." |
| **Cross-state district comparison** | output B / C | **"Cross-state comparison reflects NCS registration practice as well as labour demand. Within-state ranking is the more defensible comparison."** |

Rule V-1: the **within-state** ranking is the default district comparison everywhere. The cross-state view is
reachable but never the landing state, because the demand signal sums to each state's NCS total by
construction (Step 7 §4.3: UP 14,782 vacancies per district against TN 45,139).

---

## 2. Section B — Experimental outputs

### 2.1 Decision: the Step 7 quadrant is retained, as `EXPERIMENTAL_ONLY`

**Retained** — the design is sound, reproducible and built only from already-labelled products, and
discarding it would lose the one honest answer the project has to the prioritisation question.

**Not promoted** — on Step 7's own evidence: identical rules and thresholds yield **207 flags under PMKVY 2.0
and 0 under PMKVY 1.0**, and cross-scheme rank correlation is **+0.034** (certification) and **+0.005**
(placement). An output whose existence depends on an un-decidable choice between two source schemes is not a
production indicator.

**Separation requirements.** The experimental surface is a distinct, labelled area — not a tab beside
production views, not a column in a production table, not a default. It carries no numeric gap, no score, no
severity, no ranking presented as priority. It is excluded from every export and every production API
response. Reaching it requires an explicit action that states what it is.

### 2.2 Exact permitted labels

| Element | Required value |
|---|---|
| Surface banner | **`EXPERIMENTAL — NOT AN OFFICIAL OUTPUT`** |
| Status, flagged | **`POTENTIAL_PRESSURE`** |
| Status, other quadrants | `DEMAND_LED_MONITOR` · `TRAINING_SYSTEM_REVIEW` · `NO_FLAG` · `INSUFFICIENT_EVIDENCE` |
| Mandatory guard | **`NOT_MEASURED_SHORTAGE`** (display) / `is_measured_shortage = FALSE` (data) |
| Confidence | **`LOW`** — on every row, by construction |
| Stability | **`indicator_stability = LOW`** with `stability_note` |
| Training axis grain | **`STATE`**, with `training_signal_is_district_specific = FALSE` |
| Declared scheme | named in full on every row and in every view |

### 2.3 Mandatory interpretation notice

Shown adjacent to the output, not behind a link:

> **This is not a shortage, a deficit, a skill gap, a vacancy estimate, or a demand–supply gap.** It
> identifies where an *estimated relative* demand signal coincides with a *state-level* training-system
> ratio from one declared scheme. It does not say how many workers are missing — no supply quantity exists
> at occupation or trade level, so no shortage is defined, let alone measured. It cannot say *which*
> occupation is underserved: the training axis has **no occupation dimension**. The classification **changes
> if the other PMKVY scheme is declared** (207 flags against 0). Confidence is LOW. Treat every flag as a
> prompt to investigate, never as a finding.

### 2.4 Current coverage limitations

| Limitation | Value |
|---|---|
| Districts | 138 of 785 (**17.6%**) |
| States | 3 of 36 (Uttar Pradesh 71, Maharashtra 35, Tamil Nadu 32) |
| Cells | 1,242 (138 × 9 NCO divisions) |
| Demand base | 41.87% of published NCS vacancies |
| Training axis distinct values | **3** — one per in-scope state |
| Training axis occupation dimension | **none** |
| Confidence | LOW on 100% of rows |
| Scheme dependence | 207 flags (PMKVY 2.0) vs 0 (PMKVY 1.0) |
| Inert indicator | `certified/enrolled` — all 3 states at or above the national median, triggers nothing |
| Non-discriminating indicator | PMKK coverage — at ceiling 1.000 for Maharashtra and Uttar Pradesh |
| Temporal distance | demand 2024-11-15 vs PMKVY 2.0 cohort closing 2020 |

### 2.5 Evidence required before promotion

All four, conjunctively — see the gates in §4 and the decision tree in §7:

1. **Scheme-independent or stable training evidence** — gate G-5.
2. **Materially better geographic coverage** — gate G-6.
3. **An occupation or trade dimension on the training axis** — gate G-7. Without it the indicator can never
   name what is short, and "pressure on occupation X" stays structurally unsupported.
4. **A stability demonstration** — gate G-8.

---

## 3. Section C — Unavailable / blocked outputs

Every row is reported to the user **as explicitly unavailable, with its reason and its unblocking gate**.
None is hidden, and none is approximated.

| # | Blocked output | Status | Why | Gate |
|---|---|---|---|---|
| **S-1** | Numeric demand–supply gap, any grain | `NOT_IDENTIFIABLE` | Joint distribution not recoverable from row marginals + a 21.8% column fragment from a different scheme | **G-1** |
| **S-2** | District × occupation supply | `NOT_IDENTIFIABLE` | No district × trade or district × occupation supply evidence exists | **G-2** |
| **S-3** | State × occupation supply | `NOT_IDENTIFIABLE` | Training data has no occupation dimension; 153 of 155 trades unmapped to NCO | **G-3** |
| **S-4** | District × trade supply | `NOT_ACQUIRED` | PMKVY district resource `ACCESS_PENDING`; NCVT MIS and DGT portals `UNAVAILABLE` | **G-2** |
| **S-5** | State × trade supply | `NOT_IDENTIFIABLE` | Row marginals plus 21.8% Top-N column fragment; raking unavailable | **G-1** |
| **S-6** | Forecast / projection / trend, any measure | `NOT_SUPPORTED_YET` | One dated demand observation (2024-11-15); PMKVY 1.0 → 2.0 is not a time series | **G-4** |
| **S-7** | Shortage or surplus count | `NOT_IDENTIFIABLE` | No supply quantity ⇒ no shortage is defined | **G-1** |
| **S-8** | Vacancy count at district level | `NOT_AVAILABLE` | NCS publishes state totals; district values are an estimated relative signal | **G-9** |
| **S-9** | Vacancy count at district × occupation level | `NOT_AVAILABLE` | Doubly derived; `relative_signal_unitless` | **G-9** |
| **S-10** | NCO-coded vacancy counts, any grain | `NOT_AVAILABLE` | NCS vacancies are not NCO-coded; the occupation axis is a Census-2011 prior | **G-9** |
| **S-11** | Occupation-level seats, capacity or enrolment | `NOT_AVAILABLE` | Published at national × Top-N trade only; Top-N may not become a distribution | **G-3** |
| **S-12** | Any allocation of the 58.13% PAN-India residual | `PROHIBITED` | Not state-attributable; allocating it would invent geography | **permanent** |
| **S-13** | Early-warning alert lifecycle | `NOT_SUPPORTED_YET` | Requires a production indicator and a time dimension; has neither | **G-4 + promotion** |
| **S-14** | Seat-allocation recommendations | `NOT_SUPPORTED_YET` | Requires a gap or an elasticity; has neither | **G-1** |
| **S-15** | Trade-level or occupation-level training supply for the 153 unmapped trades | `MAPPING_UNKNOWN` | Distinct from "does not exist" — no official mapping acquired | **G-3** |
| **S-16** | `supply_coverage_summary.trades_mapped_to_nco` | **`BARRED — STALE`** | Hard-coded 0; contradicted by `dim_trade_mapping_status` (§0.2) | §9 fix |
| **S-17** | Monthly or quarterly demand series | `NOT_SUPPORTED_YET` | Measure is a cumulative stock at a single as-on date | **G-4** |
| **S-18** | Any district-level training or performance value | `PROHIBITED` | Training evidence is state level; district variation would be invented | **G-7** |

**Rule U-1.** A blocked output is rendered as its status plus its reason plus its gate. It is never rendered
as `0`, blank, `—`, "N/A", an empty chart, or an omitted row.

**Rule U-2.** `NOT_IDENTIFIABLE` ≠ `NOT_ACQUIRED` ≠ `ACCESS_PENDING` ≠ `MAPPING_UNKNOWN`. The first is a
property of the evidence structure and is not fixed by acquiring more of the same data; the others are
access or coverage problems. The distinction is published, because it is the difference between "we cannot
know this" and "we have not got this yet".

---

## 4. Section D — Data-condition gates

Objective, auditable, and **no new numerical threshold is invented** — every number carried here already
exists in Step 6 or Step 7.

### G-1 · Numeric demand–supply gap

All six, conjunctively:

| # | Condition | Current |
|---|---|---|
| 1 | Demand and supply at the **same time grain** | **FAIL** — cumulative stock as on 2024-11-15 vs scheme cohort flows 2015-16 / 2016-20 |
| 2 | Same **geography** | **FAIL** — demand district (138) / state; supply state only |
| 3 | Same **occupation or trade grain** | **FAIL** — demand NCO division; supply has no occupation dimension |
| 4 | Same **unit** | **FAIL** — `relative_signal_unitless` / `lakh_vacancy_equivalent` vs `candidates` |
| 5 | Same **population definition** | **FAIL** — NCS registrants vs scheme beneficiaries; neither is the labour force |
| 6 | **At least one observed interior cell** of `SUPPLY[geography × trade]` | **FAIL** — zero exist |

**Condition 6 is the binding one.** Conditions 1–5 are reconcilable with better data; condition 6 is what
makes the problem an identification failure rather than a harmonisation one. Row and column marginals never
determine an interior, and the closing assumption `P(trade|state) = P(trade)` is both substantively false
and untestable (Step 6). **Until an interior cell is observed, G-1 cannot be passed by any methodology.**

### G-2 · District × occupation or district × trade supply

1. Actual district × trade (or district × occupation) supply evidence from an official source, **acquired**,
   not allocated from state totals.
2. Measure-specific (enrolled / trained / assessed / certified / placed kept distinct; no inference along
   the cascade unless the source states the relationship).
3. Resolvable to LGD district codes.
4. A named vintage.

**Explicitly insufficient:** any state total distributed by population, enterprise share, district count,
centre count, or any other proxy. That is allocation, not evidence, and would manufacture the variation the
output claims to measure.

### G-3 · State × occupation supply

1. Trade-level supply at state grain with **complete** trade marginals — not a Top-N subset. (78% of PMKVY 4.0
   enrolment currently sits in unnamed job roles; Top-N cannot become a distribution.)
2. Official trade → NCO mapping coverage sufficient to carry the measure. **Current: 2 of 155 trades**
   (`dim_trade_mapping_status`). 153 are `MAPPING_UNKNOWN`.
3. Mappings `authority = OFFICIAL`. No fuzzy, semantic, embedding, LLM or name-resemblance mapping, ever
   (Step 5.1 / 5.2 constraints remain binding).

### G-4 · Forecasting

1. **At least two defensible dated demand observations** of the same measure, same basis, same geography,
   from the same source — enough for a difference; more for a trend.
2. The measure must be a **flow**, or two dated stocks differenceable into one. Currently
   `flow_available = FALSE` on every demand row, reason recorded: *"measure is a cumulative stock and all
   acquired snapshots share one as-on date; differencing requires two different dated snapshots."*
3. Temporal comparability: no scheme redesign, definition change or geography change between observations
   that would be attributed to labour-market movement.
4. **PMKVY 1.0 → PMKVY 2.0 does not satisfy this**, permanently. They are different schemes, and their
   state orderings are unrelated (Spearman +0.005). Treating them as a series would attribute scheme
   redesign to labour-market change.
5. Rolling-origin backtesting against mandatory naive baselines before any forecast is published.

### G-5 · Scheme-independent or stable training evidence

Either:
- **(a)** a training measure not tied to a single scheme cohort — e.g. an annual, scheme-independent state
  series; **or**
- **(b)** demonstrated stability across the schemes already held: cross-scheme rank correlation materially
  above the current **+0.034** (certification) and **+0.005** (placement), judged against a pre-registered
  criterion set before the recomputation, not after.

### G-6 · Coverage for promotion

1. Occupation-bearing demand coverage materially above the current **138 / 785 districts (17.6%)** and
   **3 / 36 states** — requires Census B-24 for further states or an equivalent district occupation table.
2. Demand base materially above the current **41.87%** of published NCS vacancies, or a defensible treatment
   of the PAN-India residual that does not allocate it.
3. A training axis with more than **3** distinct values in scope.

### G-7 · Occupation dimension on the training axis

Training outcomes resolvable to NCO or to trades that are officially NCO-mapped, at state grain or finer.
**Without this gate the indicator can never state which occupation is under pressure**, regardless of
coverage or stability — so G-7 is required for promotion even if G-5 and G-6 pass.

### G-8 · Stability demonstration

The sensitivity grid of Step 7 §14.2 re-run, showing that the classification of a material share of flagged
cells does not change under: alternative scheme, alternative indicator, threshold perturbation, and
alternative normalisation. The criterion must be pre-registered. **Current result: the flag set collapses
from 207 to 0 under scheme substitution — an unambiguous failure.**

### G-9 · Observed vacancy counts at district or district × occupation level

1. An official source publishing vacancy counts at district grain (and NCO-coded, for the occupation grain).
2. A named vintage and a defined universe.
3. A declared measure basis — flow or stock, and the window.

Estimation does not pass this gate. **A relative signal can never be promoted to a count** — the deficiency
is the absence of a measured quantity, not the quality of the estimate.

---

## 5. Section E — PS compliance and transparency

### 5.1 What the problem statement asks

PS 26246 (MSDE) asks for **demand–supply gap forecasting at district and sector granularity**, with
early-warning flags and severity ranking.

### 5.2 What the evidence supports

**Not a defensible numeric gap — at any grain.** Step 6 established this as an identification failure:
`SUPPLY[state, trade]` is a joint distribution, the project holds row marginals plus a 21.8% column fragment
**from a different scheme**, and marginals never determine an interior. Independently, all four candidate
subtraction forms fail the unit and time audits.

**Nor forecasting**, for a separate and simpler reason: there is **one** dated demand observation. A single
point cannot support a trend, and the two PMKVY schemes are not a time series.

### 5.3 What the system does instead

1. **Publishes what is observed**, as observed — NCS state and industry vacancy totals, training-system
   outcomes, infrastructure counts.
2. **Publishes what is estimated**, labelled as estimated, with its method, its transformation depth, its
   confidence and its coverage — the three demand signals.
3. **Publishes the missing evidence as a first-class output.** §3 is a user-visible register: each blocked
   capability, its status, its reason, and the objective condition that would unblock it.
4. **Retains the hybrid indicator as experimental**, clearly fenced, with its scheme dependence stated on
   its face.
5. **Refuses to publish a number it cannot defend**, and says so in the place where a reader would look for
   that number.

### 5.4 Why this is a strength, not a shortfall

A fabricated gap would be **more dangerous than no gap**, and specifically:

- **The error would be invisible.** A plausible district × occupation gap table looks exactly like data. No
  reader could detect that `P(trade|state) = P(trade)` had been assumed, and nothing in the output would
  reveal it.
- **The error would be systematic and directional, not random.** Imputing the national trade mix onto every
  state erases precisely the regional mismatch the PS exists to find. A planner would be told that every
  state has the same skill profile — the one conclusion guaranteed to be wrong, and the one that makes the
  tool useless exactly where it matters.
- **It would misdirect real money.** These outputs are meant to inform seat sanctioning. A confident wrong
  ranking moves capacity to the wrong districts and withdraws it from the right ones.
- **It would not survive scrutiny.** The first question from a statistically literate reviewer — "what is
  your state × trade source?" — has no answer. A system that cannot answer that in a Parliament question
  has a worse problem than an incomplete one.
- **The missing-evidence register is itself actionable.** §3 and §4 tell MSDE exactly which dataset to
  publish to make the requested gap computable: **state × trade (ideally district × trade) training
  outcomes with complete trade marginals.** That is a concrete, costed ask addressed to the ministry that
  owns the data — arguably more useful than a number that merely restates an assumption.

**Stated plainly: the PS's gap-forecasting requirement is partially unmet. The system reports this rather
than concealing it.** §3 and §4 constitute the gap analysis the PS asked for, expressed as an evidence
specification instead of a fabricated quantity.

---

## 6. Section F — Dashboard publication contract

| output | status | allowed_label | grain | confidence | coverage | user_interpretation | prohibited_interpretation |
|---|---|---|---|---|---|---|---|
| `analytical_state_demand` | **PRODUCTION** | "NCS vacancies mobilised, cumulative since inception, as on 2024-11-15" | state (+1 NATIONAL residual) | OBSERVED | 37 states + residual; 41.87% state-attributable | Official published count of vacancies mobilised through NCS since inception | Current vacancies · annual vacancies · labour demand · open positions |
| `analytical_demand_by_industry` | **PRODUCTION** | "NCS vacancies by NIC section, cumulative, as on 2024-11-15 (project NIC alignment, confidence 0.95)" | NIC section | OBSERVED, PROJECT mapping | 21 sections | Observed vacancy totals under the project's NCS→NIC alignment | Official NIC statistic · industry employment · sector demand |
| **A** `demand_national_occupation_composition` | **PRODUCTION (qualified)** | "Estimated occupation composition of vacancies, national" | national × NIC section × NCO division | MEDIUM / LOW | national only | Estimated split of observed industry vacancies across NCO divisions | Vacancies by occupation · occupation-wise demand count · district demand |
| **B** `demand_district_relative_signal` | **PRODUCTION (qualified)** | "Relative demand signal (estimated)" | district (785) | **MEDIUM** | 41.87% of published vacancies; residual unallocated | Districts ranked on an estimated relative demand signal, best read within state | Vacancy count · demand volume · jobs · shortage |
| **C** `demand_district_occupation_signal` | **PRODUCTION (heavily qualified)** | "Relative demand signal by occupation (estimated) — LOW confidence" | district × NCO division | **LOW** | **138/785 districts (17.6%), 3/36 states** | Within a state and occupation, which districts show a higher estimated relative signal | Vacancy count · shortage · supply gap · occupation demand count · forecast |
| `fact_training_outcome` | **PRODUCTION** | "Training-system outcomes: enrolled / trained / assessed / certified / placed, by state and scheme" | state × scheme × measure | OBSERVED | 36 states; 5 `NO_DATA` cells | Officially published candidate counts within a named scheme and period | **Supply** · skilled workers available · training capacity · workforce |
| Training ratios | **PRODUCTION (qualified)** | "Certification rate / reported placement rate within &lt;scheme, period&gt;" | state × scheme | OBSERVED input, derived ratio | 33–35 states per ratio | Within one scheme cohort, the share converting between two stages | Training quality · state capability · supply efficiency · capacity |
| `fact_training_infrastructure` | **PRODUCTION** | "PMKKs allocated / established; districts with a PMKK, as on 2024-03-31" | state | OBSERVED | 36 states | Count of centres and districts covered | Training capacity · seats · occupation supply |
| `fact_training_trade_outcome` | **PRODUCTION (qualified)** | "Top-N trades / job roles, national — **not a complete distribution**" | national × Top-N trade | OBSERVED | Top-10 subsets; 21.8% of PMKVY 4.0 enrolment | The largest named trades as published | Trade distribution · trade shares · state or district trade supply |
| `demand_coverage_summary`, `fact_data_quality` | **PRODUCTION (mandatory)** | "Coverage and data quality" | — | OBSERVED | — | What the system does and does not cover | — |
| **Hybrid quadrant** | **EXPERIMENTAL_ONLY** | **`EXPERIMENTAL` · `POTENTIAL_PRESSURE` · `NOT_MEASURED_SHORTAGE`** | district × NCO division (demand) × state (training) | **LOW**, `indicator_stability = LOW` | 138/785 districts, 3/36 states, 3 training values | Where an estimated relative demand signal coincides with a state-level training ratio in one declared scheme — a prompt to investigate | **Shortage · deficit · skill gap · vacancy estimate · demand–supply gap · forecast · which occupation is short** |
| Numeric gap | **UNAVAILABLE** | `NOT_IDENTIFIABLE` | — | — | — | Reported as not identifiable, with gate G-1 | Any numeric gap |
| District/state × occupation or trade supply | **UNAVAILABLE** | `NOT_IDENTIFIABLE` / `NOT_ACQUIRED` | — | — | — | Reported with reason and gate | Any supply quantity |
| Forecast | **UNAVAILABLE** | `NOT_SUPPORTED_YET` | — | — | — | Reported with gate G-4 | Any projection or trend |
| `supply_coverage_summary.trades_mapped_to_nco` | **BARRED** | — | — | — | — | Do not publish; cite `dim_trade_mapping_status` | Any claim that 0 trades are mapped |

---

## 7. Section G — API contract

### 7.1 Mandatory metadata envelope

Every analytical response carries this block. A response without it is a contract violation.

```jsonc
{
  "data": [ /* ... */ ],
  "meta": {
    "output_id": "demand_district_occupation_signal",
    "publication_status": "PRODUCTION",     // PRODUCTION | EXPERIMENTAL | UNAVAILABLE
    "evidence_status": "ESTIMATED",         // OBSERVED | SUPPORTING | ESTIMATED | UNAVAILABLE
    "confidence": "LOW",                    // HIGH | MEDIUM | LOW | INSUFFICIENT_EVIDENCE
    "confidence_binding_dimension": "statistical_support",
    "coverage": {
      "unit": "districts",
      "covered": 138,
      "total": 785,
      "fraction": 0.176,
      "excluded": [
        { "reason": "CENSUS_NOT_ACQUIRED",  "count": 522 },
        { "reason": "NO_CENSUS_2011_CODE",  "count": 125 }
      ],
      "demand_base_note": "41.87% of published NCS vacancies; 58.13% PAN-India residual unallocated"
    },
    "grain": { "geo_level": "DISTRICT", "occupation_level": "NCO_2015_DIVISION", "period_grain": "SNAPSHOT" },
    "unit": "relative_signal_unitless",
    "measure_basis": "CUMULATIVE_SINCE_INCEPTION",
    "baseline_period": "2024-11-15",
    "source_vintage": "2024-11-15",
    "provenance": {
      "source_ids": ["NCS_PARLIAMENTARY_ANSWERS","UDYAM_DISTRICT_MSME","CENSUS_2011_B24","LGD_DISTRICTS_DATAGOVIN"],
      "source_documents": ["LS_UQ2225_2024-12-09.pdf","LS_UQ933_2024-12-02.pdf","RS_UQ2798_2024-12-19.pdf"],
      "transformation_depth": 2,
      "methodology_url": "/docs/methodology#output-c",
      "mapping_authority": "PROJECT",
      "mapping_confidence": 0.95
    },
    "is_measured_shortage": false,
    "forecast_available": false,
    "forecast_unavailable_reason": "NOT_SUPPORTED_YET: one dated demand observation; see gate G-4",
    "flow_available": false,
    "flow_unavailable_reason": "measure is a cumulative stock and all acquired snapshots share one as-on date",
    "interpretation": "RELATIVE_RANKING_SIGNAL_NOT_A_VACANCY_COUNT",
    "prohibited_interpretations": ["VACANCY_COUNT","SHORTAGE","SUPPLY_GAP","FORECAST"],
    "index_version": "…", "built_at": "…"
  }
}
```

### 7.2 Field rules

| Field | Rule |
|---|---|
| `publication_status` | Exactly one of three values. `EXPERIMENTAL` responses are served only from `/experimental/*` and never from a production route |
| `evidence_status` | Per value, not per response, where a response mixes kinds. `UNAVAILABLE` rows carry a reason, never a zero |
| `confidence` | Ordinal category only. **A numeric confidence or probability is a contract violation** |
| `coverage` | Non-optional. Must carry the denominator and the exclusion breakdown with reasons |
| `is_measured_shortage` | Non-nullable, **`false` on every response in the system**. No route may return `true` |
| `forecast_available` | Currently `false` everywhere, with the reason and the gate |
| `provenance.transformation_depth` | Mandatory on estimated outputs |
| `prohibited_interpretations` | Machine-readable, so a consumer cannot plead ignorance |
| `meta` on exports | CSV/XLSX exports carry a header block and a sidecar manifest with the same fields. **An export without the envelope is prohibited** — it is the likeliest route by which a relative signal becomes "vacancies" in someone's slide |

### 7.3 Blocked-route behaviour

A blocked capability returns **HTTP 200 with an explicit unavailability document**, not 404 and not an empty
array:

```jsonc
{
  "data": null,
  "meta": {
    "output_id": "demand_supply_gap",
    "publication_status": "UNAVAILABLE",
    "evidence_status": "UNAVAILABLE",
    "reason_code": "NOT_IDENTIFIABLE",
    "reason": "SUPPLY[geography x trade] has no observed interior cell; marginals do not determine an interior.",
    "blocking_gate": "G-1",
    "unblocking_conditions_url": "/docs/step7.1#g-1",
    "is_measured_shortage": false
  }
}
```

A 404 or an empty array would read as "no gap found" rather than "no gap computable" — the exact
misreading this policy exists to prevent.

---

## 8. Section H — Promotion criteria

### 8.1 EXPERIMENTAL → PRODUCTION (the hybrid indicator)

```
START: hybrid indicator, EXPERIMENTAL_ONLY
  │
  ├─ G-7 · Does the training axis have an occupation/trade dimension?
  │        NO ──▶ STAY EXPERIMENTAL. Without it the indicator can never name
  │               what is under pressure. Non-negotiable; no other gate substitutes.
  │        YES ─▼
  ├─ G-5 · Is the training evidence scheme-independent, OR stable above a
  │        pre-registered criterion (vs +0.034 / +0.005 today)?
  │        NO ──▶ STAY EXPERIMENTAL.
  │        YES ─▼
  ├─ G-6 · Is coverage materially above 138/785 districts, 3/36 states,
  │        41.87% demand base, and >3 training values?
  │        NO ──▶ STAY EXPERIMENTAL (may widen within experimental).
  │        YES ─▼
  ├─ G-8 · Does the Step 7 §14.2 sensitivity grid hold against a
  │        pre-registered criterion?
  │        NO ──▶ STAY EXPERIMENTAL.
  │        YES ─▼
  ├─ Is weakest-link confidence now above LOW?
  │        NO ──▶ may publish as PRODUCTION only if labelled LOW and
  │               `is_measured_shortage = FALSE` is retained.
  │        YES ─▼
  └─ PROMOTE: publication_status = PRODUCTION.
     Retains forever: `is_measured_shortage = FALSE`, `POTENTIAL_PRESSURE`
     (never "shortage"), and the state/district asymmetry disclosure.
```

**Promotion never converts the indicator into a gap.** Even fully promoted it remains a prioritisation
instrument. G-1 is a separate gate and is not implied by any combination of G-5 through G-8.

### 8.2 UNAVAILABLE → AVAILABLE

```
START: blocked capability
  │
  ├─ Which status?
  │   ├─ NOT_ACQUIRED / ACCESS_PENDING ──▶ acquire via a permitted route.
  │   │     No bypassing of authentication, CAPTCHA, robots, ToS or TLS controls.
  │   │     Register in config/sources.yaml (licence gate) ▶ immutable snapshot
  │   │     + sha256 ▶ profile ▶ validate ▶ reconcile to the source's own
  │   │     published totals ──▶ then re-enter at the capability's gate.
  │   │
  │   ├─ MAPPING_UNKNOWN ──▶ acquire an OFFICIAL mapping only.
  │   │     Fuzzy / semantic / embedding / LLM / name-resemblance mapping is
  │   │     permanently prohibited. 153 of 155 trades currently unmapped.
  │   │
  │   └─ NOT_IDENTIFIABLE ──▶ acquisition alone is insufficient.
  │         Requires a structural change in the evidence: at least one observed
  │         interior cell of SUPPLY[geography × trade] (G-1 condition 6).
  │         More of the same marginals never passes this.
  ▼
  Capability-specific gate (G-1 … G-9) fully satisfied?
  │   NO  ──▶ remains UNAVAILABLE; update the reason and the gate, publish the change.
  │   YES ─▼
  ├─ Independent audit: unit, time, geography, occupation grain and population
  │   definition all compatible, each confirmed against the data, not asserted.
  │   FAIL ──▶ remains UNAVAILABLE.
  │   PASS ─▼
  ├─ Reconciliation against the source's own published totals passes.
  ├─ Pandera contract + regression tests added and passing.
  ├─ ADR recorded: what changed, which gate, what evidence.
  └─ PUBLISH, at the confidence the weakest link allows — which may still be LOW.
```

**Audit requirements, binding on every promotion:** the gate evaluation is recorded in an ADR citing the
specific evidence; every criterion is re-checkable from the immutable snapshot store; any pre-registered
criterion is fixed **before** the recomputation that tests it; and no gate may be weakened to pass an output
— weakening a gate requires its own ADR superseding this one.

---

## 9. Implementation Gate

**Step 7.2 is permitted to implement exactly the following, and nothing else.**

| # | Permitted | Detail |
|---|---|---|
| 1 | The publication-status metadata layer | `publication_status`, `evidence_status`, `confidence`, `coverage`, `baseline`/`vintage`, `provenance`, `is_measured_shortage`, `forecast_available` and the reason/gate fields of §7, attached to existing outputs as metadata |
| 2 | The unavailability register | §3 as a queryable table or config: output, status, reason, blocking gate. **Reasons and gates only — no values** |
| 3 | The §7.3 blocked-route response | HTTP 200 + explicit unavailability document |
| 4 | Terminology enforcement | §1.3 as a lint/test: forbidden tokens (`supply`, `shortage`, `gap`, `vacancies` on a relative signal, numeric confidence) fail the build if they appear in a label, header, API field or export |
| 5 | **Fix the §0.2 stale constant** | Replace the hard-coded `0.0` at `src/lmis/cli.py:684` with the computed count from `dim_trade_mapping_status`, add a regression test pinning it, and add a test asserting the two tables agree. **This changes one metadata value from 0 to 2 — the only value change authorised by this document, and it corrects a known error** |
| 6 | Coverage-disclosure components | The §1.2 disclosures rendered beside their outputs |
| 7 | Experimental fencing | Separate route/surface, banner, §2.3 notice, exclusion from production responses and exports |
| 8 | Doc updates | `docs/limitations.md`, `docs/methodology.md`, `docs/analytical_data_dictionary.md` aligned to this contract |

**Step 7.2 is explicitly forbidden from:** computing any pressure score or flag (that is Step 8, and only on
the §8.1 gates); creating any gap, shortage, supply or forecast value; altering any existing analytical
value except item 5; adding a migration that changes an existing table's semantics; creating a composite
score; building the dashboard or API surface itself beyond the contract and its tests; promoting any output
between tiers.

**Promotion of the hybrid indicator to production is not authorised by this document and cannot occur in
Step 7.2.** It requires G-5, G-6, G-7 and G-8, and a new ADR.
