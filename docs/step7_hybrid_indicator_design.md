# Step 7 — Hybrid Demand-Pressure / Training-System Indicator: Design Specification

Date: 2026-10-04 · **Design document only.** No indicator implemented, no score computed, no flag created,
no gap value, no forecast, no early-warning table, no recommendation, no API/frontend/LLM. **No schema
change and no analytical value changed** — verified by re-running the full pipeline and test suite.

Implements the Step 6 decision (ADR-0009): Option D, a hybrid evidence-qualified indicator, replacing a
numeric demand–supply gap that Step 6 proved is not identifiable.

> **Read §4 first.** The empirical work for this step produced four findings that constrain the design more
> than any methodological preference does. Two of them are unfavourable enough that they change what should
> be built, and one of them — §4.4 — means the indicator's output is substantially determined by a choice
> the evidence cannot make for us. That is reported here, at design time, rather than discovered after
> implementation.

---

## 1. Problem definition

### 1.1 The question the indicator answers

> **Where does the available evidence suggest that a high relative labour-demand signal coexists with
> comparatively weak observed training-system indicators?**

It is a **prioritisation instrument for investigation**, not a measurement instrument. Its output ranks
district × occupation combinations for human attention. It does not quantify anything about workers.

### 1.2 The question it does not answer

Step 6 established that no numeric demand–supply gap is identifiable at district, state or occupation level.
This indicator does not relax that finding, work around it, or approximate it. It is a *different* quantity
that is computable from evidence we hold, chosen because the gap is not.

### 1.3 Structural asymmetry — the defining constraint

| | Demand side | Training side |
|---|---|---|
| Grain | district × NCO division | **state × scheme** |
| Occupation dimension | NCO division (9) | **none** |
| Distinct values available | 1,242 | **3** (one per in-scope state) |
| Nature | estimated relative signal | observed administrative ratio |

The two sides do not meet at a common grain, and they never will under present evidence. Every design below
is an answer to the question *"what can honestly be said by placing a 1,242-valued estimate next to a
3-valued observation?"* — and §4.4 is the answer's limiting factor.

---

## 2. Available evidence

### 2.1 Demand — `demand_district_occupation_signal`

| Property | Value |
|---|---|
| Baseline | `2024-11-15` |
| Unit | `relative_signal_unitless` |
| Interpretation (stored) | `RELATIVE_RANKING_SIGNAL_NOT_A_VACANCY_COUNT` |
| Status | `ESTIMATED`, `overall_confidence = LOW` for **all 1,889 rows** |
| Construction | state NCS vacancies → Udyam within-state enterprise share → Census 2011 district occupation share |

**Coverage, measured:**

| `occupation_prior_status` | Rows | Districts | States | Usable signal |
|---|---|---|---|---|
| `AVAILABLE` | 1,242 | **138** | **3** | 1,242 |
| `CENSUS_NOT_ACQUIRED` | 522 | 522 | 33 | 0 |
| `NO_CENSUS_2011_CODE` | 125 | 125 | 21 | 0 |

**The occupation-bearing demand component exists for 138 of 785 districts (17.6%), in exactly three states**
— Uttar Pradesh (71), Maharashtra (35), Tamil Nadu (32) — because Census B-24 was acquired for those three
only. The grid is perfectly rectangular: 138 × 9 divisions = 1,242, every division present for every
district. Unallocated Census division "X" share: min 0.033, median 0.137, max 0.290 — never zero, and
excluded from the denominator rather than redistributed.

The 647 districts without an occupation prior carry a district-level signal in
`demand_district_relative_signal` (785 districts) but **no occupation dimension**.

### 2.2 Training — `fact_training_outcome`

Two complete five-measure cascades, each self-contained within one scheme and one declared period:

| Scheme | Period | As on | States | ENROLLED | TRAINED | ASSESSED | CERTIFIED | PLACED |
|---|---|---|---|---|---|---|---|---|
| PMKVY 1.0 | 2015-16 | *(none published)* | 35 | 1,986,016 | 1,986,016 | 1,951,487 | 1,451,636 | 253,296 |
| PMKVY 2.0 CSSM STT | 2016-20 | 2024-03-31 | 35 | 870,769 | 833,137 | 742,285 | 660,776 | 230,393 |

Ladakh appears only in PMKVY 1.0; Lakshadweep only in PMKVY 2.0; union = 36 states, all LGD-matched
(`geography_status = MATCHED`, zero unmapped rows).

**Missingness is already explicit and must stay that way.** Five cells carry
`value_status = 'NO_DATA'` with `value_as_published = '-'`: A&N Islands PLACED (both schemes), Ladakh
CERTIFIED and PLACED, Lakshadweep PLACED. **None is zero.** A `'-'` in the source means not reported, and
a state that did not report placement is not a state with no placement.

### 2.3 Training — `fact_training_infrastructure`

State level, as on 2024-03-31, 36 states: `DISTRICTS_IN_STATE` (sums to exactly 785, reconciling with
`location_master`), `DISTRICTS_WITH_PMKK` (707), `PMKK_ALLOCATED` (818), `PMKK_ESTABLISHED` (714).

### 2.4 Evidence deliberately excluded

`fact_training_trade_outcome` — PMKVY 4.0 ENROLLED, PMKVY 4.0 TRAINED_ORIENTED, NAPS APPRENTICES_ENGAGED —
is **national × Top-N trade**, with no state dimension. It cannot contribute to a state-level training
signal, and Step 5.3 established that Top-N subsets must not be converted into shares or distributions. It
stays out of the indicator entirely.

---

## 3. Non-identifiability constraint (carried forward, unchanged)

`SUPPLY[state, trade]` is a joint distribution. The project holds row marginals (state totals) plus a
**21.8%** fragment of column marginals (514,619 of 2,361,798) *from a different scheme*. Row and column
marginals never determine an interior. Closing the system requires `P(trade|state) = P(trade)`, which is
substantively false — regional trade-mix heterogeneity is the very thing the project exists to measure — and
untestable, since not one state × trade cell exists to validate against.

**Consequences binding on this design:**

1. No occupation-level or trade-level supply quantity may be produced, at any grain.
2. The training component may never be called "supply".
3. No subtraction of a training quantity from a demand quantity, in any units.
4. The indicator's output is a **status**, not a quantity of workers.

---

## 4. Four empirical findings that constrain the design

All computed read-only against `db/lmis.duckdb`. Nothing was written.

### 4.1 The normalisation *functional form* is irrelevant; the *reference population* decides everything

The raw signal is strongly right-skewed (skew 3.81; `log1p` skew 0.06 — a log transform all but perfectly
symmetrises it). But every monotone transform of the signal — national percentile, raw min-max, log min-max —
is **rank-identical** (Spearman 1.000 pairwise). They cannot disagree about ordering, only about spacing.

What *does* change the answer is the reference population. Top-decile membership overlap against the
national-percentile baseline (125 cells):

| Variant | Cells ≥ 0.90 | Overlap | Jaccard |
|---|---|---|---|
| within-state percentile | 125 | 74 | **0.420** |
| within-division percentile | 126 | 77 | **0.443** |
| within-(state × division) percentile | 144 | 66 | **0.325** |
| raw min-max ≥ 0.90 | **1** | 1 | 0.008 |
| log min-max ≥ 0.90 | 15 | 15 | 0.120 |

**Raw min-max is disqualified outright:** median 0.0275, 95th percentile 0.2193 — 95% of cells are crammed
into the bottom 22% of the range, and a 0.90 cut selects exactly **one cell** out of 1,242. A min-max score
is also hostage to a single outlier, so one new district can shift every other value. Log min-max is better
behaved (median 0.532) but still inherits that fragility and is harder to explain than a percentile.

→ **Choose the reference population on substantive grounds and use percentile for the transform.**

### 4.2 Cross-division comparison is not like-for-like, and the occupation dimension is thin

Median signal by NCO division spans **6.4×**:

| Div | Title | Median | Div | Title | Median |
|---|---|---|---|---|---|
| 1 | Legislators, senior officials, managers | 539 | 6 | Skilled agricultural & fishery | **431** |
| 2 | Professionals | 888 | 7 | Craft & related trades | 2,739 |
| 3 | Technicians & associate professionals | 1,492 | 8 | Plant & machine operators | 1,355 |
| 4 | Clerks | 526 | 9 | Elementary occupations | 2,501 |
| 5 | Service & sales workers | **2,757** | | | |

A division-6 cell at signal 2,000 is exceptional; a division-9 cell at 2,000 is below median. Pooling
divisions in one reference population would rank occupations, not districts.

Variance decomposition of log signal:

| Component | Share of total SS |
|---|---|
| District main effect | **61.2%** |
| Occupation main effect | **30.7%** |
| Interaction — the only district-*specific* occupational information | **8.1%** |

And within-division percentile correlates **+0.941** (Spearman) with the parent district-level signal, but
only **+0.198** with the occupation share itself. Census occupation shares are too similar across districts
to differentiate much: median across-district CV of occupation share is 0.355, and 97 distinct within-district
orderings across 138 districts means ordering does vary — but 91.9% of signal variation is explained by
"which district" and "which occupation" acting independently.

**Honest reading: the district × occupation signal is largely the district signal, repeated nine times with a
division-specific multiplier.** The occupation axis is real but weak. It must not be presented as though it
localises demand to an occupation with any precision.

### 4.3 National cross-state normalisation imports NCS registration bias

Uttar Pradesh holds **51.4%** of in-scope cells but only **10.4%** of the national top decile; Tamil Nadu
holds 23.2% of cells and 47.2% of the top decile.

The cause is arithmetic, not economic. The district signal is `state NCS vacancies × within-state enterprise
share`, so it sums to the state total by construction:

| State | NCS vacancies | Districts | Per district |
|---|---|---|---|
| Tamil Nadu | 1,715,285 | 38 | 45,139 |
| Maharashtra | 1,533,463 | 36 | 42,596 |
| Uttar Pradesh | 1,108,648 | 75 | **14,782** |

A state with more districts and fewer NCS-registered vacancies has every one of its districts scored lower.
NCS registration propensity is an administrative property of state employment-exchange practice, not a
measure of labour demand — a caveat Step 4.0 already recorded in `within_state_ranking_caveat`. A national
reference population would convert that administrative artefact into a policy ranking.

→ **The within-state reference population is the more defensible primary.** It is immune to this artefact by
construction.

### 4.4 The training indicators contradict each other, and are not stable across schemes

This is the finding that most constrains the design.

**(a) Two candidate ratios are degenerate.** In PMKVY 1.0, `ENROLLED == TRAINED` in **all 35 states**, so
`trained/enrolled` is identically 1.000 (IQR 0.000) — the source published the same quantity twice. PMKVY 1.0
`assessed/enrolled` spans 0.980–0.990 at the quartiles (IQR 0.010), near-degenerate.

**(b) Dispersion differs by an order of magnitude.** Inter-quartile range across states:

| Ratio | PMKVY 1.0 | PMKVY 2.0 |
|---|---|---|
| trained / enrolled | **0.000** | 0.058 |
| assessed / enrolled | 0.010 | 0.102 |
| certified / assessed | 0.082 | 0.027 |
| certified / enrolled | 0.080 | 0.104 |
| **placed / certified** | **0.111** | **0.339** |

**(c) The two serious indicators disagree about the same state.** Maharashtra is at the **91st percentile**
nationally on `certified/enrolled` (0.849) and the **18th percentile** on `placed/certified` (0.136). Across
all states, Spearman(`certified/enrolled`, `placed/certified`) = **−0.043** (PMKVY 1.0) and **+0.353**
(PMKVY 2.0). A state strong on certification is not thereby strong on absorption.

**(d) Neither ratio is a stable property of a state's training system.** Rank correlation between the two
schemes, same states:

| Ratio | Spearman (1.0 vs 2.0) | n |
|---|---|---|
| certified / enrolled | **+0.034** | 34 |
| placed / certified | **+0.005** | 33 |
| assessed / enrolled | **−0.022** | 34 |

Median absolute shift in `placed/certified` between schemes: **0.213** — on a measure whose whole observed
range is 0.008–0.709. These ratios describe *a scheme's cohort*, not *a state's capability*.

Even within the three in-scope states the ordering flips: on `placed/certified`, PMKVY 1.0 gives
UP (0.121) < MH (0.140) < TN (0.347), while PMKVY 2.0 gives MH (0.136) < UP (0.191) < TN (0.460). **Maharashtra
and Uttar Pradesh swap places depending on which scheme is read.**

**(e) `certified/enrolled` is inert in the current pilot.** All three in-scope states sit at or above the
national median (MH 91st, TN 57th, UP 54th percentile). No threshold at or below the 50th percentile selects
any of them. As a flag trigger it would fire for nobody.

**(f) PMKK coverage cannot separate the pilot states.** `DISTRICTS_WITH_PMKK / DISTRICTS_IN_STATE` is at the
ceiling 1.000 for **16 of 36 states**, including Maharashtra (36/36) and Uttar Pradesh (75/75); Tamil Nadu is
0.868. It distinguishes two of three in-scope states not at all.

---

## 5. Indicator definitions

Three distinct concepts, named separately and never merged (per brief §8):

| Concept | Field | What it is | What it is **not** |
|---|---|---|---|
| Demand pressure | `demand_pressure_score` | percentile position of an estimated *relative* demand signal within a declared reference population | a vacancy count, a demand volume, a demand level, a demand share |
| Training performance | `training_system_signal` | an observed within-scheme, within-period conversion ratio at **state** level | training capacity, occupation supply, worker availability |
| Infrastructure coverage | `pmkk_district_coverage` | share of a state's districts with a PMKK, as on 2024-03-31 | training capacity, throughput, occupation supply |

### 5.1 Demand semantics — the four terms kept distinct (brief §6)

| Term | Meaning here | Available? |
|---|---|---|
| **Demand level** | an absolute count of vacancies for an occupation in a district | **No.** Never computed; the unit is `relative_signal_unitless` |
| **Demand share** | a district-occupation's fraction of a declared total | Computable, but only within the 138-district scope — not a national share |
| **Demand rank** | ordinal position within a declared reference population | Yes — `demand_rank` |
| **Demand pressure** | normalised ordinal position, i.e. rank expressed on [0,1] | Yes — `demand_pressure_score` |

`demand_pressure_score = 1.0` means **"the highest relative demand signal in its reference population"**, not
"maximum demand". `0.0` means lowest in that population, **not** "no demand" — the observed minimum is 22.5,
and no cell is zero. The score is **not comparable across reference populations** and carries
`demand_reference_population` so it can never be read without one.

---

## 6. Normalisation alternatives

### 6.1 Demand transform

| Option | Verdict | Reason |
|---|---|---|
| **Percentile within a declared population** | **ADOPTED** | Interpretable without a scale; robust to the 3.81 skew; immune to single outliers; rank-equivalent to every other monotone option (§4.1) |
| Raw min-max | **REJECTED** | Median 0.0275; a 0.90 cut selects 1 of 1,242 cells; hostage to one outlier |
| Log-then-min-max | **REJECTED** | Better spacing (median 0.532) but still outlier-dependent and harder to explain for no ranking gain |
| Rank (integer) | **ADOPTED alongside** | Stored as `demand_rank` for transparency; percentile is rank ÷ n |
| Quantile bin | **ADOPTED for display only** | Bins are a presentation of the percentile, never the stored basis |
| z-score | **REJECTED** | Presumes an approximately symmetric scale the raw signal does not have, and invites arithmetic the units do not support |

### 6.2 Reference population — the consequential choice

| Option | Removes | Verdict |
|---|---|---|
| **within (state × NCO division)** | division incomparability (§4.2) **and** NCS cross-state bias (§4.3) | **ADOPTED as primary** |
| within division, national | division incomparability only | **ADOPTED as secondary**, stored and caveated, for cross-state views |
| within state, pooled divisions | state bias only; leaves the 30.7% occupation effect dominating | Rejected as primary |
| national, pooled | nothing | Rejected — ranks occupations and rewards NCS registration intensity |
| within district, across divisions | — | Not a pressure measure; it is `rank_within_district`, which already exists and carries `within_district_ranking_caveat` |

Group sizes under the primary: 71 (UP), 35 (MH), 32 (TN) cells per division. Small, but percentiles over
32 observations are defensible; group size is recorded in `reference_population_n` so a reader can judge.

**Districts of different sizes** (brief §5) are *not* separately normalised per capita. The signal already
embeds establishment share, so a per-capita rescaling would be a second, undocumented transformation of an
already twice-transformed estimate. Working-age population is **not** available for the 138 districts without
a further Census acquisition, and `district_total_main_workers` is a 2011 Census stock — using it as a 2024
denominator would silently mix vintages. Decision: **no per-capita normalisation**; district size is carried
as context (`district_total_main_workers`, flagged Census 2011) and the correlation of pressure with district
size (+0.855 Spearman against the within-division percentile) is disclosed as a known property, not corrected.

### 6.3 Training transform and direction

| Indicator | Direction | Normalisation |
|---|---|---|
| `certified / enrolled` | higher = stronger performance | percentile across the 35 states reporting it **in the same scheme** |
| `placed / certified` | higher = stronger performance | same |
| `pmkk_district_coverage` | higher = broader infrastructure | percentile across 36 states |

**No indicator is inverted.** "Weak" is expressed as *low percentile*, never as a sign-flipped value, so
direction never has to be remembered. Percentiles are computed **within a scheme** and never pooled across
schemes — §4.4(d) shows pooling would average two unrelated orderings.

---

## 7. Training-system indicator assessment

Eligibility requires all five of the brief's §7 tests: same source, same period, compatible
numerator/denominator, clear interpretation, sufficient coverage. A sixth is added on the evidence of
§4.4: **non-degeneracy** — an indicator with no dispersion cannot discriminate, and one whose ordering does
not survive a change of scheme is not measuring the thing its name claims.

| Indicator | Source | Grain | Period | Unit | Interpretation | Eligible? | Reason |
|---|---|---|---|---|---|---|---|
| `certified / enrolled` | MSDE AR, `fact_training_outcome` | state × scheme | within one scheme | ratio | share of enrolled candidates reaching certification | **ELIGIBLE** (PMKVY 2.0) | Same source/period; IQR 0.104; 35 states. **But inert in pilot** — all 3 states ≥ national median (§4.4e) |
| `placed / certified` | same | state × scheme | within one scheme | ratio | share of certified candidates reported placed | **ELIGIBLE — primary** | Widest dispersion (IQR 0.339); closest to the labour-market question. Caveats: cross-scheme Spearman +0.005; 2 states `NO_DATA`; placement is point-of-report, not sustained employment |
| `trained / enrolled` | same | state × scheme | within one scheme | ratio | share of enrolled who were trained | **REJECTED** | **Degenerate in PMKVY 1.0** (identical in 35/35 states, IQR 0.000). IQR 0.058 in PMKVY 2.0 — retained as SUPPORTING_ONLY context |
| `assessed / enrolled` | same | state × scheme | within one scheme | ratio | share reaching assessment | **SUPPORTING_ONLY** | Near-degenerate in PMKVY 1.0 (IQR 0.010); largely redundant with `certified/enrolled` |
| `certified / assessed` | same | state × scheme | within one scheme | ratio | assessment pass rate | **SUPPORTING_ONLY** | IQR 0.027 in PMKVY 2.0 — too compressed to discriminate |
| `pmkk_district_coverage` | MSDE AR, `fact_training_infrastructure` | state | as on 2024-03-31 | ratio | share of districts with a PMKK | **SUPPORTING_ONLY** | Clean denominator (sums to 785), but at ceiling for 16/36 states incl. MH and UP (§4.4f) |
| `pmkk_established / allocated` | same | state | as on 2024-03-31 | ratio | establishment rate against sanction | **SUPPORTING_ONLY** | Median 0.890; measures administrative follow-through, not training performance |
| training intensity per working-age population | — | — | — | — | enrolment relative to population base | **INSUFFICIENT_COVERAGE** | No working-age population series for the 138 districts, and no 2024-vintage state series acquired. Mixing a 2011 Census denominator with a 2016-20 scheme numerator fails the period test |
| any trade-level or occupation-level supply | `fact_training_trade_outcome` | **national** × Top-N trade | — | candidates | — | **REJECTED** | No state dimension; Top-N subset (Step 5.3). Would require inventing a distribution |
| PMKVY 4.0 / NAPS state ratios | — | — | — | — | — | **REJECTED** | Not published at state × measure; no cascade to form a ratio |

**Eligible set: two indicators, one scheme, state grain, no occupation dimension.**

---

## 8. Threshold alternatives

### 8.1 Natural breaks are not available

Examining log-gaps in the sorted signal, the largest gap in the upper half is **×1.427** — and it is the single
top cell (99.9th percentile, 34,777 → 49,614). Elsewhere the largest gaps are ×1.12 and ×1.11, at the 98.5th
and 99.0th percentiles. **The distribution is smooth; there is no natural break to find.** Jenks or
natural-breaks thresholding would manufacture a boundary and present an arbitrary cut as a discovered one.
**Rejected on evidence.**

### 8.2 Demand-side candidate thresholds (within-division percentile, for scale)

| Cut | Cells | % of 1,242 | Districts | Divisions |
|---|---|---|---|---|
| ≥ 0.70 | 378 | 30.4% | 64 | 9 |
| ≥ 0.75 | 315 | 25.4% | 55 | 9 |
| ≥ 0.80 | 252 | 20.3% | 50 | 9 |
| ≥ 0.85 | 189 | 15.2% | 43 | 9 |
| ≥ 0.90 | 126 | 10.1% | 32 | 9 |

### 8.3 Combined yield — and the result that must govern interpretation

Flag yield under the **recommended** normalisation (within state × division), `placed/certified` as the
training axis, across both schemes:

| Scheme | Demand cut | Weak cut | Cells | Districts | States flagged |
|---|---|---|---|---|---|
| PMKVY 1.0 | 0.75 | 0.25 | **0** | 0 | — |
| PMKVY 1.0 | 0.75 | 0.33 | **0** | 0 | — |
| PMKVY 1.0 | 0.80 | 0.25 | **0** | 0 | — |
| PMKVY 1.0 | 0.80 | 0.33 | **0** | 0 | — |
| PMKVY 1.0 | 0.90 | 0.25 | **0** | 0 | — |
| PMKVY 1.0 | 0.90 | 0.33 | **0** | 0 | — |
| PMKVY 2.0 | 0.75 | 0.25 | 81 | 14 | Maharashtra |
| PMKVY 2.0 | 0.75 | 0.33 | 243 | 41 | Maharashtra, Uttar Pradesh |
| PMKVY 2.0 | 0.80 | 0.25 | 72 | 14 | Maharashtra |
| PMKVY 2.0 | 0.80 | 0.33 | **207** | **37** | Maharashtra, Uttar Pradesh |
| PMKVY 2.0 | 0.90 | 0.25 | 36 | 6 | Maharashtra |
| PMKVY 2.0 | 0.90 | 0.33 | 108 | 20 | Maharashtra, Uttar Pradesh |

**Identical rule, identical thresholds, different declared scheme → 0 flags or 207 flags.** Under PMKVY 1.0
no in-scope state falls below even the 33rd national percentile on `placed/certified`; under PMKVY 2.0 two of
three do. Tamil Nadu is never flagged under any configuration.

This is not a tuning problem to be solved by picking better thresholds. It is §4.4(d) — the near-zero
cross-scheme rank stability — surfacing as output. **The scheme choice, which the evidence cannot make for
us, determines more of the result than any threshold does.**

### 8.4 Threshold decision

- **Strategy: quantile-based, on the empirical distribution, declared in versioned config** — not natural
  breaks (§8.1), not policy-defined (no official threshold exists), not sensitivity-optimised (circular).
- **Candidate operating point, for review, not adopted here:** demand ≥ 0.80 within (state × division),
  training ≤ 0.33 national percentile within the declared scheme. It yields 207 cells / 37 districts under
  PMKVY 2.0 — a reviewable volume — and is a round, explicable pair.
- **Both thresholds live in `config/flag_rules.yaml`** with the scheme and reference population beside them.
  A flag whose threshold is unpublished is not evidence.
- **No threshold is committed in this step.** §8.3 is a scale report, not a result.

---

## 9. Missingness rules

Status values, applied to the training component (brief §14):

| Status | Meaning | Source condition |
|---|---|---|
| `AVAILABLE` | ratio computed from two `AVAILABLE` measures in one scheme and period | both present |
| `MISSING_NOT_REPORTED` | source published `'-'` | `value_status = 'NO_DATA'` |
| `NOT_APPLICABLE` | the measure cannot exist for this unit | — |
| `NOT_ACQUIRED` | source exists, snapshot not taken | registry says so |
| `ACCESS_PENDING` | identified, access unresolved | registry says so |

**Binding rules:**

1. **Missing training data never becomes zero performance, and never becomes "weak".** A state with
   `MISSING_NOT_REPORTED` receives `training_signal_status = UNAVAILABLE` and
   `potential_pressure_status = INSUFFICIENT_EVIDENCE` — never `POTENTIAL_PRESSURE`, and never
   `NO_PRESSURE_FLAG` either, because absence of evidence is not evidence of adequacy. Concretely this
   protects A&N Islands, Ladakh and Lakshadweep, whose `'-'` cells would otherwise read as the worst
   performance in the country.
2. **A null demand signal is not a low demand signal.** The 647 districts with
   `CENSUS_NOT_ACQUIRED` or `NO_CENSUS_2011_CODE` are `INSUFFICIENT_EVIDENCE`, carrying the specific reason
   forward, so "we have not acquired the Census table" is never displayed as "demand is low here".
3. **Missing is never imputed, interpolated, or filled from a neighbour, a state mean, or a national mean.**
4. **A ratio is never computed across schemes or periods** to repair a missing numerator or denominator.
5. The unallocated Census division-X share (median 0.137) stays excluded and is reported per cell, not
   redistributed across divisions.

---

## 10. Confidence framework

Weakest-link ordinal confidence, consistent with `src/lmis/demand/confidence.py`. **No probability values are
invented.** Categories: `HIGH`, `MEDIUM`, `LOW`, `INSUFFICIENT_EVIDENCE`.

| Dimension | Assessment | Basis |
|---|---|---|
| Demand source quality | **LOW** | NCS cumulative-since-inception, registration-biased (§4.3) |
| District allocation depth | **LOW** | `transformation_depth` 3: state → enterprise share → occupation share |
| Occupation mapping | **LOW** | Census 2011 NCO-2004 divisions bridged to NCO-2015; division purity 0.789–0.998 |
| Training source quality | **MEDIUM** | Observed, officially published, state totals reconciled |
| Temporal compatibility | **LOW** | Demand 2024-11-15 vs training cohort 2016-20 (§11) |
| Geography coverage | **LOW** | 138 of 785 districts (17.6%), 3 of 36 states |
| Missingness | **MEDIUM** | Explicit and small on the training side; large and explicit on the demand side |
| **Indicator stability** *(new dimension)* | **LOW** | Cross-scheme rank correlation +0.005 (§4.4d); flag set collapses to zero under the alternative scheme (§8.3) |

**`overall_confidence = LOW` by construction, for every row.** The demand input is already LOW for all 1,889
rows, and a weakest-link rule cannot exceed its weakest input. This is not pessimism to be tuned away: a
combination of a LOW-confidence estimate with a state-level observation whose ordering flips between schemes
cannot honestly be anything else.

**A LOW-confidence demand signal may still raise a flag** — if it could not, the indicator would never fire
at all and the step would be pointless. What LOW confidence forbids is presenting the flag as a finding. It
is an invitation to investigate, and `confidence = LOW` travels with it in storage, in the API and on screen.

**A new confidence dimension is proposed:** `indicator_stability`, recording whether the conclusion survives
the sensitivity analysis of §14. It is introduced because §4.4(d) is a failure mode the existing seven
dimensions do not capture — a source can be high quality, correctly mapped and contemporaneous, and still
yield an ordering that means nothing.

---

## 11. Temporal compatibility

| Element | Period | Type |
|---|---|---|
| Demand baseline | **2024-11-15** | cumulative stock since inception |
| PMKVY 1.0 | 2015-16 | cohort flow, no `as_on_date` published |
| PMKVY 2.0 CSSM STT | 2016-20, reported as on 2024-03-31 | cohort flow |
| PMKK infrastructure | as on 2024-03-31 | point-in-time count |

**These are not contemporaneous and the design does not pretend they are.** Rules:

1. **Ratios are formed only within one scheme and one period.** Never `certified` from one scheme over
   `enrolled` from another.
2. **The scheme and period are stored on every row** (`training_scheme`, `training_period`,
   `training_as_on_date`) and must appear in any display. A flag that does not name its training period is
   not interpretable.
3. **A historical training measure is labelled historical.** PMKVY 2.0's cohort window closed in 2020,
   four years before the demand baseline. The flag's wording is therefore *"a district-occupation with a high
   relative demand signal at 2024-11-15, in a state whose 2016-20 PMKVY 2.0 cohort showed comparatively low
   reported placement"* — not *"a district with weak training"*.
4. **Temporal distance caps confidence at LOW** and is one of the dimensions in §10.
5. **PMKVY 1.0 and PMKVY 2.0 are not a time series.** They are different schemes with different designs, and
   §4.4(d) demonstrates empirically that their orderings are unrelated. **No trend, no change, no direction of
   travel may be computed between them** — the project would be attributing scheme redesign to labour-market
   movement. This also forecloses Option E permanently, not just for now.
6. **One declared scheme per run.** The alternative scheme is reported as the sensitivity comparison of §14,
   never blended into the primary.

---

## 12. Candidate designs compared

| | A — Quadrant | B — Rule-based flag | C — Composite score | D — Rank-based priority |
|---|---|---|---|---|
| Output | 1 of 4 named cells | binary status | continuous score | ordered list |
| Needs weights? | **No** | **No** | **Yes** | No |
| Survives §4.4(c) contradiction? | **Yes** — axes stay separate | **Yes** | **No** — the weighting decides the verdict | Yes |
| Risk of gap misreading | Low | Low | **High** — a number invites subtraction semantics | Low |
| Communicates the state/district asymmetry? | **Yes, structurally** | Partly | **No — hides it** | Partly |
| Verdict | **ADOPTED (frame)** | **ADOPTED (stored field)** | **REJECTED** | **ADOPTED (presentation)** |

### Design A — Quadrant · **ADOPTED as the conceptual frame**

| | Training signal **weak** | Training signal **strong** |
|---|---|---|
| **Demand pressure high** | `POTENTIAL_PRESSURE` — investigate first: strong relative demand where the state's reported training conversion is comparatively low | `DEMAND_LED_MONITOR` — demand is high and the state's reported conversion is comparatively good; watch volume, not performance |
| **Demand pressure low** | `TRAINING_SYSTEM_REVIEW` — conversion is comparatively weak without a strong local demand signal; a training-quality question, not a shortage question | `NO_FLAG` — neither signal is remarkable |

Policy meaning of each quadrant is stated above and must ship with the output. The quadrant's decisive virtue:
because the training axis is *state*-level, the quadrant makes it visually obvious that a whole state's
districts move together on that axis. A composite would conceal exactly that.

### Design B — Rule-based flag · **ADOPTED as the stored field**

B is not a rival to A; it is A serialised. The quadrant cell *is* the rule's output, stored as
`potential_pressure_status`. Thresholds come from §8, are versioned in config, and are never chosen without
the distribution analysis that produced §8.2 and §8.3.

### Design C — Composite priority score · **REJECTED**

Rejected on the evidence of §4.4(c), not on taste. Maharashtra is at the 91st percentile on
`certified/enrolled` and the 18th on `placed/certified`. Any composite must weight these, and:

- **Equal weighting is not a neutral default here — it is a decisive and arbitrary intervention.** With the
  two indicators ranking Maharashtra near-oppositely, the equal-weight average places it mid-pack, which is
  the one description no single piece of evidence supports.
- The brief's own §10 warning applies exactly: a composite would **average away a critical weakness**.
- There is no defensible basis to choose other weights: no outcome label, no official guidance, no
  statistical criterion (the two indicators correlate −0.043 / +0.353, so neither PCA nor a correlation
  argument recommends a blend).
- A continuous "priority score" formed from a demand measure and a training measure is, structurally, the
  hidden gap the brief §10 forbids — whatever its units are declared to be.

Also disqualifying on its own: a composite would blend a 1,242-valued axis with a **3-valued** axis and
present them as co-equal contributors.

### Design D — Rank-based priority · **ADOPTED for presentation**

Within the set already classified `POTENTIAL_PRESSURE`, order by `demand_rank` for investigation sequencing.
Ranks are more robust than continuous scores here because the underlying skew is 3.81 and all monotone
transforms are rank-identical anyway (§4.1) — so nothing is lost by working ordinally, and the spurious
precision of a decimal score is avoided. **The rank orders an investigation queue; it does not measure
severity.** No "severity" field is produced, because severity of *what* is precisely the quantity Step 6
proved unidentifiable.

---

## 13. Recommended design — exact specification

**Design A (quadrant) as the frame, B (rule) as the stored status, D (rank) as the presentation — with no
composite score anywhere.**

### 13.1 Specification

| # | Element | Specification |
|---|---|---|
| 1 | **Demand input** | `demand_district_occupation_signal.district_occupation_signal`, rows with `occupation_prior_status = 'AVAILABLE'` only (1,242 cells, 138 districts, 3 states, 9 divisions) |
| 2 | **Demand normalisation** | Percentile rank within **(state × NCO division)** — primary. Also stored: percentile within division nationally (secondary, caveated), integer `demand_rank`, and `reference_population_n` |
| 3 | **Training inputs** | `placed / certified` (primary) and `certified / enrolled` (secondary), from `fact_training_outcome`, **one declared scheme**, state grain. Default declared scheme: **PMKVY 2.0 CSSM STT** (2016-20, as on 2024-03-31) — it is the only one with a published `as_on_date`, it is nearer the demand baseline, and its ratios are non-degenerate (§4.4a–b) |
| 4 | **Training normalisation** | Percentile across the states reporting that measure **within the declared scheme**. No inversion; weak = low percentile. Never pooled across schemes |
| 5 | **Geography propagation** | `training_system_signal[state(district)]` — a **lookup, not an estimate**. Every district in a state receives the identical value. Field `training_signal_grain = 'STATE'` and `training_signal_is_district_specific = FALSE` on every row. **No district variation is created, under any circumstances** |
| 6 | **Threshold / ranking logic** | Quadrant assignment from two thresholds in `config/flag_rules.yaml`; candidate operating point demand ≥ 0.80, training ≤ 0.33 (§8.4, not committed). Within `POTENTIAL_PRESSURE`, order by `demand_rank` |
| 7 | **Missingness** | §9. Missing training ⇒ `INSUFFICIENT_EVIDENCE`, never weak, never strong. Missing demand ⇒ `INSUFFICIENT_EVIDENCE` with the specific reason. No imputation anywhere |
| 8 | **Confidence** | Weakest-link over the eight dimensions of §10, including the new `indicator_stability`. **`LOW` by construction** |
| 9 | **Temporal** | §11. One declared scheme per run; scheme and period on every row and in every display; no trend between schemes |
| 10 | **Output fields** | §13.2 |
| 11 | **Interpretation** | §13.3 |
| 12 | **Non-interpretations** | §13.4 |

### 13.2 Output fields (to be implemented in Step 8, not now)

```
-- geography & occupation
lgd_code, district_name_lgd, state_lgd_code, state_name_lgd, nco_2015_division, nco_name
-- demand component
demand_baseline_period                -- '2024-11-15'
district_occupation_signal            -- carried through, unchanged
demand_pressure_score                 -- percentile within (state x division)
demand_reference_population           -- 'STATE_X_NCO_DIVISION'
reference_population_n                -- 71 / 35 / 32
demand_rank                           -- integer, within the same population
demand_pressure_secondary             -- percentile within division, national
demand_signal_status                  -- AVAILABLE | INSUFFICIENT_EVIDENCE
demand_signal_unavailable_reason      -- CENSUS_NOT_ACQUIRED | NO_CENSUS_2011_CODE | NULL
-- training component (STATE level)
training_scheme                       -- 'PMKVY_2.0_CSSM_STT'
training_period                       -- '2016-20'
training_as_on_date                   -- '2024-03-31'
training_indicator_primary            -- 'PLACED_OVER_CERTIFIED'
training_system_signal                -- percentile within the declared scheme
training_indicator_secondary          -- 'CERTIFIED_OVER_ENROLLED'
training_system_signal_secondary
training_signal_status                -- AVAILABLE | UNAVAILABLE | NOT_ACQUIRED | ACCESS_PENDING
training_signal_grain                 -- 'STATE'  (constant)
training_signal_is_district_specific   -- FALSE   (constant)
-- supporting context, never a trigger
pmkk_district_coverage, pmkk_coverage_at_ceiling
-- classification
potential_pressure_status             -- POTENTIAL_PRESSURE | DEMAND_LED_MONITOR
                                      -- | TRAINING_SYSTEM_REVIEW | NO_FLAG | INSUFFICIENT_EVIDENCE
demand_threshold_applied, training_threshold_applied
-- confidence & provenance
confidence                            -- LOW (by construction)
confidence_binding_dimension          -- which dimension bound it
indicator_stability                   -- LOW | MEDIUM | HIGH, from the sensitivity run
stability_note                        -- e.g. 'status changes under PMKVY_1.0'
evidence_notes, source_ids, index_version, built_at
-- mandatory guard
is_measured_shortage                  -- FALSE, always, non-nullable
```

`is_measured_shortage` is `FALSE` on every row, enforced by a `CHECK` constraint and a regression test, so no
later refactor can silently make it configurable.

### 13.3 Exact interpretation

> `POTENTIAL_PRESSURE` for (district D, NCO division X) means: **D's estimated relative demand signal for
> division X, at baseline 2024-11-15, sits in the upper tier of districts in D's own state for that same
> division; and D's state reported a comparatively low placement-to-certification ratio in the declared
> PMKVY cohort.** Both components are relative. Neither is a count. The conclusion is a recommendation to
> investigate, at LOW confidence.

### 13.4 Explicit non-interpretations

`POTENTIAL_PRESSURE` does **not** mean any of the following, and the output must say so:

1. There is a shortage of workers.
2. A number of workers are missing.
3. Demand exceeds supply.
4. Training capacity is insufficient.
5. Occupation supply in that district is known — it is not known at any grain.
6. The occupation named is the one that is short — the training axis has **no occupation dimension**, so a
   flag can never identify which trade or occupation the training system is failing.
7. Demand is high in absolute terms — only relative to its reference population.
8. The district's training system is weak — the signal is its **state's**, shared with every other district
   there.
9. Anything about the 647 districts outside the Census scope, or the 33 states with no occupation prior.
10. Anything forward-looking. There is one demand observation date; no trend exists.

---

## 14. Validation and sensitivity plan

There is **no ground-truth shortage label**, and none can be constructed from available evidence. Therefore
**predictive validation is impossible and will not be claimed** — no accuracy, no precision/recall, no ROC,
no "validated against outcomes". The appropriate framework is methodological validation plus sensitivity
analysis.

### 14.1 Methodological validation (correctness of construction)

| Check | Pass condition |
|---|---|
| Monotonicity | Higher signal ⇒ weakly higher `demand_pressure_score` within a reference population; no inversions |
| Row conservation | Exactly 1,242 classified rows + 647 `INSUFFICIENT_EVIDENCE` = 1,889; no row created or lost |
| Reference-population integrity | Percentiles computed within declared groups only; `reference_population_n` ∈ {71, 35, 32} |
| State propagation | Every district in a state carries an identical `training_system_signal`; count of distinct values per state = 1 |
| **No district-level training variation** | *Mandated regression test:* `training_system_signal` has no within-state variance. Any variance fails the build |
| **No gap, ever** | *Mandated regression test:* no field is a difference of a demand and a training measure; `is_measured_shortage` is `FALSE` on 100% of rows |
| **No occupation-level supply** | *Mandated regression test:* no output field is keyed by occupation **and** derived from a training measure |
| Missingness integrity | No `MISSING_NOT_REPORTED` state is classified weak; A&N / Ladakh / Lakshadweep are `INSUFFICIENT_EVIDENCE` |
| Unit hygiene | No output carries a worker, candidate, seat or vacancy unit |
| Reproducibility | `make reproduce` checksum stable |

### 14.2 Sensitivity analysis (robustness of conclusion)

| Analysis | Method | Why it matters | Expected, from §4 |
|---|---|---|---|
| **Scheme sensitivity** | recompute under PMKVY 1.0 | **The decisive one** | **Flag set collapses from 207 to 0.** Must be reported beside every result |
| Indicator sensitivity | recompute with `certified/enrolled` as primary | §4.4(c) contradiction | 0 flags — inert in pilot (§4.4e) |
| Threshold sensitivity | demand ∈ {0.70…0.90} × training ∈ {0.25, 0.33, 0.50} | thresholds are a choice | 36–243 cells; see §8.3 |
| Normalisation sensitivity | within-(state×div) vs within-div vs national | §4.1 | Top-decile Jaccard 0.325–0.443 |
| Ranking stability | Spearman and top-N overlap between normalisations | report bands, not positions | Unstable; report a band |
| State-size sensitivity | yield per state ÷ cells per state | §4.3 artefact | UP under-selected nationally; neutralised by the within-state primary |
| Outlier sensitivity | drop the top cell, recompute | min-max fragility (§4.1) | Percentile unaffected; would have broken min-max |
| Missingness sensitivity | re-run treating `NO_DATA` as weak | shows what rule 9.1 prevents | 3 states would flip to flagged — the error the rule averts |
| Weighting sensitivity | **not performed** | there is no composite to weight (§12 C) | n/a |

**Reporting rule:** a `POTENTIAL_PRESSURE` classification whose status changes under scheme sensitivity
carries `indicator_stability = LOW` and `stability_note`. On present evidence **that is every flagged row**,
and the output must say so on its face rather than in a footnote.

---

## 15. Example interpretation (hypothetical — no values invented)

> District **A** in state **S** shows a high relative demand signal for NCO division **X** — it sits in the
> upper tier of S's districts for division X at baseline 2024-11-15. State S reported a comparatively low
> placement-to-certification ratio in the declared PMKVY cohort. The system may therefore classify
> (A, X) as **`POTENTIAL_PRESSURE`, confidence LOW, indicator_stability LOW**.
>
> **This does not mean that any number of division-X workers are missing in district A.** It does not
> establish an occupation-specific shortage: the training signal for A is state S's, shared identically with
> every other district in S, and it carries **no occupation dimension at all** — so it cannot indicate that
> division X in particular is underserved. It does not mean A's training system is weak; it means S's
> reported cohort conversion was comparatively low. And because the classification changes if the other
> PMKVY scheme is declared instead, it is a prompt to look, not a finding.
>
> A second district **B**, also in state S, with a *low* relative demand signal, would receive
> **`TRAINING_SYSTEM_REVIEW`** — same state training signal, different demand tier, and a different policy
> question (training quality, not shortage). A district **C** in a state with `'-'` published for placement
> receives **`INSUFFICIENT_EVIDENCE`**, never "weak".

---

## 16. Explicit limitations

1. **No numeric gap, shortage or surplus is produced, at any grain.** Step 6's identifiability finding stands.
2. **Geographic coverage is 17.6% of districts** (138 of 785) and **3 of 36 states**. 647 districts have no
   occupation dimension; 33 states have none.
3. **The training axis has no occupation dimension.** A flag can never say *which* occupation or trade is
   underserved. This is the deepest limitation and it is structural, not a coverage gap.
4. **The training axis has only 3 distinct values** across all 1,242 cells. It is a state-level gate, not a
   co-equal dimension, and the design says so rather than disguising it.
5. **The conclusion is scheme-dependent.** Identical rules yield 0 or 207 flags depending on which PMKVY
   scheme is declared (§8.3). Cross-scheme rank correlation is +0.005.
6. **`certified/enrolled` is inert in the current pilot** — all three in-scope states are at or above the
   national median, so it can trigger nothing.
7. **PMKK coverage cannot separate the pilot states** — at ceiling for both Maharashtra and Uttar Pradesh.
8. **The demand signal is thrice-transformed and LOW confidence** for all 1,889 rows.
9. **The occupation dimension is weak**: only 8.1% of signal variance is district-specific occupational
   information; 91.9% is "which district" plus "which occupation" independently.
10. **Temporal gap of about four years** between the demand baseline (2024-11-15) and the close of the
    PMKVY 2.0 cohort window (2020).
11. **Placement is point-of-report placement, not sustained employment**, and is not verified employment in
    the trained occupation.
12. **No forecasting.** One demand observation date. No trend may be computed, and PMKVY 1.0 → 2.0 is not a
    time series.
13. **No per-capita normalisation**; `demand_pressure_score` correlates +0.855 with district size, disclosed
    rather than corrected.
14. **No ground-truth validation is possible.** Only methodological validation and sensitivity analysis.
15. **Cross-state demand comparison imports NCS registration bias.** The secondary national percentile is
    provided for cross-state views and is explicitly caveated; the primary avoids it.
16. **The problem statement's gap-forecasting requirement remains partially unmet.** This indicator does not
    close it, and no re-labelling should suggest otherwise.

---

## 17. Implementation specification for Step 8 (if approved)

**Scope.** One new module, one new table, one new config block, one CLI command, one doc update. No change to
any existing demand or supply output.

| Item | Detail |
|---|---|
| Module | `src/lmis/indicator/pressure.py` — `build_potential_pressure()` |
| Table | `analytical_potential_pressure`, migration `008_pressure.sql`, fields per §13.2 |
| Constraints | `CHECK (is_measured_shortage = FALSE)`; `CHECK (training_signal_grain = 'STATE')`; `potential_pressure_status` restricted to the five permitted values |
| Config | `config/flag_rules.yaml` — `demand_pressure_threshold`, `training_weak_threshold`, `declared_scheme`, `demand_reference_population`, `primary_training_indicator` |
| CLI | `lmis build-pressure`; `lmis pressure-sensitivity` emitting the §14.2 grid |
| Pandera | contract for the new table, incl. non-null `confidence` and `potential_pressure_status` |
| Tests | the four mandated regression tests of §14.1 (no district-level training variation; no gap field; no occupation-level supply; `is_measured_shortage` always FALSE), plus row conservation 1,242 + 647 = 1,889, missingness integrity, and reference-population integrity |
| Docs | `docs/methodology.md` section; `docs/limitations.md` additions from §16; `docs/analytical_data_dictionary.md` entry |
| Makefile | `pressure` target, inserted into `reproduce` after `supply` |
| Expected output | ~207 `POTENTIAL_PRESSURE` cells at the candidate operating point, all `confidence = LOW`, all `indicator_stability = LOW` |

**Explicitly not in Step 8:** forecasting, early-warning lifecycle tables, recommendations, API, frontend,
LLM, any supply estimate, any gap value, any ML.

**Decisions needed from the reviewer before Step 8 begins:**

1. **Declared scheme** — PMKVY 2.0 CSSM STT is proposed. Given §8.3, this choice determines whether the
   indicator emits ~207 flags or none. It cannot be settled by evidence and is the reviewer's to make.
2. **Operating point** — demand ≥ 0.80, training ≤ 0.33 proposed (207 cells / 37 districts).
3. **Reference population** — within (state × NCO division) proposed as primary.
4. Whether to publish the indicator **at all** given §16.5, or to hold at Option A (no numeric gap,
   documented) until a second scheme-independent training observation exists. **The design is sound; its
   inputs are weak, and that is a legitimate reason to decline to publish.**

---

## 18. Required final questions

**Q1 · What exactly does the indicator measure?**
The co-occurrence of two relative positions: a district-occupation's percentile position in an *estimated*
relative demand signal within its state and division, and its state's percentile position on an *observed*
within-scheme training conversion ratio. It measures where to look, not what is there.

**Q2 · What does it NOT measure?**
Worker shortage, worker surplus, demand–supply gap, occupation supply, training capacity, absolute demand,
district-level training performance, which occupation is underserved, or anything forward-looking.

**Q3 · Can it ever be interpreted as a worker shortage?**
**No.** Not at any grain, under any threshold, with any wording. No supply quantity exists at occupation or
trade level, so no shortage is defined, let alone measured. `is_measured_shortage = FALSE` is enforced by a
database constraint and a regression test.

**Q4 · Which indicators enter the final classification?**
Two, kept separate and never blended: **`placed/certified`** (primary) and **`certified/enrolled`**
(secondary), from one declared PMKVY scheme at state level; plus the demand pressure percentile. PMKK
coverage, `trained/enrolled`, `assessed/enrolled` and `certified/assessed` are **supporting context only** and
cannot trigger a flag.

**Q5 · Why are those indicators eligible?**
Both pass same-source, same-period, numerator/denominator-compatibility, interpretability and coverage, and
are non-degenerate in the declared scheme (IQR 0.339 and 0.104). Everything else fails a test: `trained/enrolled`
is identical in 35/35 states in PMKVY 1.0; `certified/assessed` has IQR 0.027; training intensity has no
compatible population denominator; trade-level measures have no state dimension and are Top-N subsets.
**Honest qualification:** eligible is not strong. `certified/enrolled` is inert in the current pilot, and
neither ratio is stable across schemes.

**Q6 · How are state-level training signals attached to districts?**
By **lookup**: `training_system_signal[state(district)]`. Every district in a state receives the identical
value. This is **not** an estimate of district training performance, and no district-level variation is
created. Enforced by a regression test asserting zero within-state variance, and declared on every row via
`training_signal_grain = 'STATE'` and `training_signal_is_district_specific = FALSE`.

**Q7 · How are missing values handled?**
With five explicit statuses (§9). Missing never becomes zero, never becomes "weak", and is never imputed,
interpolated, or filled from a mean or a neighbour. A state publishing `'-'` for placement yields
`INSUFFICIENT_EVIDENCE`, not a bottom ranking — which is what protects A&N Islands, Ladakh and Lakshadweep
from being scored the worst in the country for not reporting.

**Q8 · How is confidence determined?**
Weakest-link over eight ordinal dimensions (§10), with a new `indicator_stability` dimension capturing
cross-scheme robustness. No probabilities are invented. The result is **`LOW` for every row by construction**,
because the demand input is LOW for all 1,889 rows and a weakest-link rule cannot exceed its weakest input.

**Q9 · How are thresholds selected?**
Quantile-based on the empirical distribution, declared in versioned config, with the yield at every candidate
cut reported (§8.2–8.3). **Natural breaks are rejected on evidence** — the largest log-gap in the upper half
is ×1.427 at a single outlier cell, so no break exists to find. No threshold is committed in this step.

**Q10 · How will sensitivity analysis be performed?**
Per §14.2: eight analyses across scheme, indicator, threshold, normalisation, ranking stability, state size,
outliers and missingness, emitted by `lmis pressure-sensitivity`. Weighting sensitivity is not performed
because no composite exists to weight. Predictive validation is impossible — no ground-truth shortage label
exists — and will not be claimed.

**Q11 · What would cause `INSUFFICIENT_EVIDENCE` rather than `POTENTIAL_PRESSURE`?**
Any of: `occupation_prior_status` of `CENSUS_NOT_ACQUIRED` (522 districts) or `NO_CENSUS_2011_CODE`
(125 districts); a training measure published as `'-'` (`value_status = 'NO_DATA'`); a state absent from the
declared scheme (Ladakh under PMKVY 2.0, Lakshadweep under PMKVY 1.0); unresolved geography; or absent
confidence metadata. **Absence of evidence never produces `NO_FLAG` either** — not knowing is distinct from
knowing there is nothing.

**Q12 · What data would make a genuine numeric gap identifiable?**
In order of decisiveness:

1. **State × trade training outcomes — ideally district × trade.** The single missing dimension. Without an
   interior cell of the `SUPPLY[state, trade]` table, no amount of methodology recovers the joint
   distribution from its margins.
2. **Complete trade marginals, not Top-N.** 78% of PMKVY 4.0 enrolment sits in unnamed job roles; raking
   needs full margins.
3. **The remaining 153 trade → NCO mappings** (4 of 157 are mapped from official DGT CTS curricula).
4. **Census B-24 for the other 33 states**, or a PLFS district occupation table, to lift demand coverage
   above 17.6%.
5. **A second dated NCS snapshot**, for any flow measure or trend — the current demand measure is a
   cumulative stock at one date.
6. **NCO-coded NCS vacancies**, removing the Census-prior step and the 8.1%-interaction weakness.
7. **A scheme-independent, periodic training measure**, so the conclusion stops depending on which scheme is
   declared (§8.3).

Items 1 and 2 are necessary for a numeric gap. The rest improve it. **Until item 1 exists, no methodology —
including this one — can produce a defensible numeric demand–supply gap.**
