# Step 6 — Supply / Gap Methodology Decision

Date: 2026-10-04 · **Decision document only.** No methodology implemented, no supply estimated, no gap
calculated, no forecast, no early-warning logic, no recommendations, no API/frontend/LLM. **No schema
change and no analytical value changed** — verified by re-running the full pipeline and test suite.

---

## Headline

**No numeric demand–supply gap is identifiable from currently accessible official evidence — at district,
state or occupation level.** This is an identification failure, not a data-cleaning or modelling problem,
and it cannot be fixed by choosing a cleverer estimator.

**Recommended path: Option D — a hybrid, evidence-qualified Demand Pressure + Training-System indicator**,
which answers a meaningful part of the problem statement without inventing supply. **Option A** is the
fallback. **Options B, C and E are rejected on evidence.** **Option F runs in parallel** as a defined
data-acquisition requirement.

---

## 1. Current evidence (fixed)

### Demand

| Product | Grain | Unit | Basis | Status |
|---|---|---|---|---|
`demand_national_occupation_composition` | national × NIC section × NCO division | `lakh_vacancy_equivalent` | cumulative-since-inception composition | ESTIMATED, MEDIUM/LOW |
`demand_district_relative_signal` | district (785) | **`relative_signal_unitless`** | — | ESTIMATED, MEDIUM |
`demand_district_occupation_signal` | district × NCO division | **`relative_signal_unitless`** | — | ESTIMATED, **LOW** |
`analytical_state_demand` | state (+ NATIONAL residual) | `count` | **CUMULATIVE_SINCE_INCEPTION** | OBSERVED |
`analytical_demand_by_industry` | NIC section | `lakh` | **CUMULATIVE_SINCE_INCEPTION** | OBSERVED |

Baseline: **2024-11-15**. PAN-India residual (58.1%) stays NATIONAL, unallocated.

### Supply

| Product | Grain | Unit | Period | Status |
|---|---|---|---|---|
`fact_training_outcome` | **state × scheme × measure** (5 measures) | `candidates` | 2015-16 (PMKVY 1.0); as on 2024-03-31 (CSSM 2.0) | OBSERVED |
`fact_training_trade_outcome` | **national × Top-N trade/job-role/sector × measure** | `candidates` | FY2018-19→23-24; as on 2024-03-31 | OBSERVED, `is_top_n_subset=True` |
`fact_training_infrastructure` | state × PMKK metric | **`count`** (centres) | as on 2024-03-31 | OBSERVED |

### Occupation mapping

`map_trade_to_nco` 4 rows / **2 of 155** trades (OFFICIAL, 8-digit, multi-NCO). `map_qualification_to_nco`
1 row. **The state supply table has no trade dimension**, so the mapping has nothing to attach to.

---

## 2. Identifiability analysis — the core of this step

The requested quantity is:

```
GAP[district, occupation, period] = DEMAND[district, occupation] − SUPPLY[district, occupation]
```

### What we observe on the supply side

1. `S_state[state, scheme, measure]` — row marginals of a state × trade table.
2. `S_trade_topN[trade, measure]` — a **21.8% subset** of column marginals, for a **different scheme**.

### What is required

`S[state, trade]` — the **joint distribution**. From there, district requires a further split.

### Can the joint be identified from the marginals?

**No.** This is the classical contingency-table / ecological-inference problem: row marginals plus column
marginals do not determine an interior. Even with *complete* marginals the joint is identified only under an
additional assumption, typically independence:

```
P(trade | state) = P(trade)        ← "every state trains the same trade mix"
```

Three reasons that assumption fails here:

1. **It is substantively false.** Maharashtra's industrial trade mix is not Uttar Pradesh's; that
   heterogeneity is the entire reason the project exists. Assuming it away would assume away the answer.
2. **It is untestable with what we hold.** There is no state × trade observation anywhere to validate it
   against — not one cell.
3. **We do not even have the column marginals.** The Top-N job-role list covers **514,619 of 2,361,798
   PMKVY 4.0 enrolments = 21.8%**. **78% of enrolment sits in job roles the source does not name.** So
   iterative proportional fitting / raking is not available either: there is nothing to rake to.

A fourth, independent problem: the Top-N *trade* list (apprenticeships, NAPS, FY2018-19→23-24) and the state
totals (PMKVY 1.0 and CSSM 2.0) are **different schemes covering different populations**. They are not row
and column marginals of the same table at all.

> **Conclusion: `SUPPLY[state, trade]` is NOT IDENTIFIABLE. `SUPPLY[district, trade]` is NOT IDENTIFIABLE.
> `SUPPLY[*, NCO]` is NOT IDENTIFIABLE.** The missing dimension is the joint itself, and no transformation
> of the available marginals recovers it.

**Identification ≠ estimation.** A formula can be written — `S_state × P̂(trade)` — and it would return
numbers. Those numbers would be a restatement of the independence assumption, not a measurement. Writing the
formula does not identify the quantity.

---

## 3. Unit compatibility audit

| Proposed equation | Left unit | Right unit | Result unit | Verdict |
|---|---|---|---|---|
NCS vacancies − PMKVY certified | vacancy **postings accumulated since 2015** | **candidates certified** during a scheme window | *none* | **REJECT** |
NCS vacancies − apprentices engaged | postings since 2015 | **apprenticeship engagements** FY2018-19→23-24 | *none* | **REJECT** |
district relative signal − trainees | **unitless index** | candidates | *none* | **REJECT** |
district signal − state trainees | unitless, district | candidates, state | *none* | **REJECT** (grain too) |

Even setting units aside, the semantics do not line up:

- A **vacancy posting is not a job.** NCS counts postings mobilised; reposting and multi-position postings
  inflate it, and 58.1% carries no geography at all.
- A **certified candidate is not a worker entering that occupation.** PIB reports the PMKVY 1.0–3.0 STT
  placement rate at **42.8%**, and placement itself is point-of-report, not sustained employment.
- **Centres are not candidates** (`fact_training_infrastructure` is in `count`, not `candidates`).

**No meaningful common unit exists between the demand stock and any supply measure. Every subtraction form
is rejected.**

---

## 4. Time compatibility audit

| Observation | Type | Period |
|---|---|---|
NCS vacancies | **cumulative stock** since 2015 inception | as on **2024-11-15** |
PMKVY 1.0 outcomes | **flow** over a scheme window | **2015-16** |
CSSM PMKVY 2.0 STT | cumulative flow for that scheme | as on 2024-03-31 |
PMKVY 4.0 (Top-N) | cumulative flow for that scheme | as on 2024-03-31 |
NAPS apprenticeships (Top-N) | **6-year cumulative** flow | FY2018-19 → FY2023-24 |
PMKK infrastructure | point-in-time count | as on 2024-03-31 |
PLFS context | monthly rate | April 2025 |
Census occupation prior | decennial | **2011** |

Three distinct temporal types — **stock, flow and point-in-time count** — are present, over windows that
begin in different years and belong to different schemes. Subtracting across them is invalid regardless of
units. Also unmodelled: **vacancy duration** (a 2015 posting may have been filled nine years ago) and the
**training-to-employment lag** (a 2024 certification cannot answer a 2016 vacancy).

---

## 5. Option-by-option evaluation

### Option A — no numeric gap · **VIABLE (fallback)**
Publish demand and supply as separate evidence-qualified products. Scientifically unimpeachable; fully
explainable; lowest complexity; everything already built. But it answers the PS's "gap" and "early warning"
requirements **not at all** — it informs without prioritising.

### Option B — state-level gap at the available grain · **REJECTED**
A state gap would have to be *all vacancies* minus *all trainees*: no occupation dimension on either side,
so it carries no trade or sector meaning. It fails the unit audit (§3) and the time audit (§4), discards
58.1% of the demand measure, and mixes PMKVY 1.0 (2015-16) with a 2024 demand stock. **Not quantitatively
meaningful. Rejected.**

### Option C — project-estimated occupation supply · **REJECTED for baseline**
Requires `P(trade | state, scheme, period)`, which §2 shows is **not identifiable**: no state × trade
observation exists, the Top-N covers 21.8%, and the only closing assumption (independence) is both false and
untestable. Bias would be **systematic and directional** — it would impute the national mix onto every
state, erasing exactly the regional mismatch the PS asks about, and would do so invisibly because the output
would look like data.

*What would make it identifiable:* a genuine state × trade (or district × trade) training table, or
complete non-Top-N trade marginals **plus** a validated state-level auxiliary, with held-out cells to test
against. **None exists. Rejected — permissible later only as an explicitly labelled sensitivity scenario,
never as a baseline.**

### Option D — hybrid demand-pressure + training-system indicator · **RECOMMENDED**
Constructible **entirely from existing observed or already-labelled-estimated products**, with no invented
supply:

- **Demand pressure** — the existing `demand_district_occupation_signal` rank (ESTIMATED, LOW) and
  `demand_district_relative_signal` rank (ESTIMATED, MEDIUM).
- **Training-system indicators** — derived *only* from observed state × scheme measures, as **ratios within
  the same source and period**, which is unit-safe: certification rate (`certified/enrolled`), placement
  rate (`placed/certified`), assessment rate, and training intensity per working-age population. These
  describe **how the training system performs**, not how much occupation supply exists.
- **Infrastructure coverage** — PMKK districts-with-a-centre over districts, from Annexure-21.
- **Evidence confidence** — the existing weakest-link framework, which will cap the composite at **LOW**.

The output is a **potential-pressure / investigation flag**, explicitly *not* a measured shortage: "this
district ranks high on relative demand for this occupation group, and its state shows weak observed training
throughput — worth investigating." Transparent, reproducible, and every component traceable.

**Its honest limitation:** demand pressure is district × occupation while the training indicator is state ×
scheme with **no occupation dimension**. The flag therefore cannot say *which* trade is short — only that a
district-occupation with high demand sits in a state whose training system performs weakly overall. That
must be stated on the output, not in a footnote.

### Option E — temporal supply/demand analysis · **REJECTED**
- **Demand:** exactly **one** NCS as-on date. No series.
- **Supply:** PMKVY 1.0 (2015-16), CSSM 2.0 and 4.0 (both as on 2024-03-31) are **different schemes with
  different eligibility and coverage**, not one measure repeated over time. Treating them as a series would
  attribute scheme redesign to labour-market change.
- Apprenticeship is a single 6-year cumulative figure.
**Not enough compatible dated observations. Rejected — and no fake series will be constructed.**

### Option F — acquire restricted official data · **ADOPT IN PARALLEL**
Define the requirement explicitly rather than hope. See §8.

---

## 6. Comparison matrix

| Method | Common grain | Requires estimation? | Evidence available? | Main assumptions | Bias risk | PS usefulness | Defensibility |
|---|---|---|---|---|---|---|---|
| **A** no numeric gap | none (parallel products) | No | **HIGH** (built) | none | **LOW** | **LOW** | **HIGH** |
| **B** state gap | state, no occupation | No | HIGH but **incompatible** | that a 2015-cumulative posting stock is comparable to scheme training flows | **HIGH** | LOW | **NOT IDENTIFIABLE** |
| **C** estimated occupation supply | state/district × NCO | **Yes, heavily** | **LOW** (21.8% Top-N; no joint cell) | `P(trade\|state)=P(trade)` — false and untestable | **HIGH, systematic** | HIGH *if true* | **NOT IDENTIFIABLE** |
| **D** hybrid indicator | district × NCO (demand) + state × scheme (system) | Only what is already labelled ESTIMATED | **HIGH** | that state training performance is informative context for district demand pressure | **MEDIUM**, disclosed | **MEDIUM-HIGH** | **MEDIUM-HIGH** |
| **E** temporal | — | Yes | **LOW** (1 demand date; schemes ≠ series) | that scheme changes are market changes | HIGH | MEDIUM | **NOT IDENTIFIABLE** |
| **F** acquire data | would enable district × NCO | No, once acquired | **NOT YET** | that access is granted | LOW | **HIGH** | **HIGH** (conditional) |

---

## 7. Risks of the recommended path

| Risk | Mitigation |
|---|---|
A flag is read as a measured shortage | Name it `POTENTIAL_PRESSURE_FLAG`; store `is_measured_shortage = False`; never render it in the same style as observed data |
The occupation-dimension mismatch is forgotten | Store `supply_indicator_has_occupation_dimension = False` on every row |
Ratios are built across incompatible sources | Compute ratios **only within one source table and period**; enforce by test |
Weakest-link confidence gets averaged away | Reuse the existing `Confidence` class, which already refuses averaging; expect **LOW** |
The 58.1% residual is forgotten | Carry the `41.9% state-attributable` coverage caption onto every screen |
Someone later adds an allocation step | The Step 5.3 regression tests already block state→trade expansion and district-trade values without source evidence |

---

## 8. Additional official data required to unlock a real gap

In order of leverage:

1. **State × trade (ideally district × trade) training outcomes** — *the single missing dimension*. Without
   it nothing else helps. Routes: PMKVY MIS / Skill India Digital Hub via a **registered data.gov.in API
   key**; or a formal MSDE data request.
2. **Complete (non-Top-N) trade-wise distributions** — would supply true column marginals; combined with (1)
   they make the joint observable rather than assumed.
3. **DGT CTS curricula for the remaining 153 trades** — completes trade → NCO. Needs an official curriculum
   index, or an NQR bulk export.
4. **A second dated NCS observation** (≥1 quarter apart, identical measure definition) — the minimum for any
   flow, and the precondition for forecasting.
5. **NCS vacancies by occupation / NCO code** — would remove dependence on the ILO national bridge and give
   demand a directly observed occupation dimension.
6. **Sanctioned seat capacity by trade** — would allow a capacity-vs-demand comparison, which is a different
   and more tractable question than throughput-vs-demand.

With (1) + (4), a genuine district (or state) × NCO gap *flow* becomes identifiable. With (1) alone, a
cross-sectional gap becomes identifiable.

---

## 9. Decision

| | |
|---|---|
| **Primary** | **Option D** — hybrid evidence-qualified Demand Pressure + Training-System indicator |
| **Fallback** | **Option A** — separate products, no composite flag, if D's composite is judged too strong a claim |
| **Parallel** | **Option F** — formal data-acquisition requirement |
| **Rejected** | **B** (unit + time incompatible, no occupation dimension), **C** (not identifiable; 21.8% Top-N; independence false and untestable), **E** (one demand date; schemes are not a time series) |

**What Option D does not do: it does not produce a numeric demand–supply gap.** The PS's "demand-supply gap
forecasting" requirement is **partially unmet**, and saying so is the correct result. What D does deliver is
district/sector intelligence, drill-down, severity *ranking* and an early-warning *trigger* — a meaningful
part of the PS — without a fabricated number anywhere.

---

## 10. Implications for Step 7

If Option D is approved, Step 7 would implement **only**:

1. `analytical_training_system_indicator` — state × scheme ratios computed **within one source and period**
   (certification, assessment, placement rates; training intensity per working-age population).
2. `analytical_infrastructure_coverage` — districts-with-PMKK over districts, per state.
3. `analytical_potential_pressure_flag` — joining the existing district × NCO demand rank to its state's
   training-system indicator, emitting `POTENTIAL_PRESSURE` / `MONITOR` / `INSUFFICIENT_EVIDENCE`, with
   `is_measured_shortage=False` and weakest-link confidence (expected LOW).
4. Reason codes and evidence references on every flag.
5. Tests: no numeric gap column exists; no supply is allocated; ratios never cross sources or periods;
   every flag carries its confidence and its occupation-dimension caveat.

**Forecasting remains out of scope** until requirement (4) in §8 is met. One dated observation cannot support
a trend, and no interpolation will be used to manufacture one.
