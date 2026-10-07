# ADR-0011 — Indicator publication policy: Option A in production, hybrid indicator experimental only

- **Status:** Proposed (decision/documentation only; awaiting review)
- **Date:** 2026-10-05
- **Builds on:** ADR-0009 (no numeric gap; Option D selected), ADR-0010 (quadrant, no composite)
- **Supersedes:** nothing
- **Specification:** `docs/step7.1_indicator_publication_decision.md`

## Context

Step 6 established that no numeric demand–supply gap is identifiable from accessible official evidence.
Step 7 designed the Option D hybrid indicator and was approved **as a design**. Neither step decided what the
dashboard and API may actually publish, which left the hybrid indicator one implementation step away from
becoming a de-facto production early-warning output by default rather than by decision.

Step 7's own measurements make that default unacceptable:

- Identical rules and thresholds yield **207 flags under PMKVY 2.0 and 0 under PMKVY 1.0**.
- Cross-scheme rank correlation: **+0.034** (certification rate), **+0.005** (reported placement rate).
- Coverage is **138 of 785 districts (17.6%)** and **3 of 36 states**.
- The training axis carries **3 distinct values** for 1,242 cells and has **no occupation dimension**.
- Confidence is **LOW on 100% of rows**, by construction.

Separately, the demand side has a publication hazard independent of the indicator: output B rests on
**41.87%** of published NCS vacancies, with the **58.13% PAN-India residual unallocated**, and outputs B and
C are `relative_signal_unitless` — trivially misread as vacancy counts if published without constraint.

## Decisions

1. **`OFFICIAL_ANALYTICAL_MODE = OPTION_A`.** Production publishes evidence-qualified demand intelligence:
   observed NCS state and industry totals, observed training-system outcomes and infrastructure, and the
   three estimated demand signals — each with mandatory confidence, coverage and provenance.

2. **`HYBRID_PRESSURE_INDICATOR = EXPERIMENTAL_ONLY`.** Retained, not promoted. Fenced on a separate
   surface, excluded from production responses and exports, labelled `EXPERIMENTAL`, `POTENTIAL_PRESSURE`,
   `NOT_MEASURED_SHORTAGE`, `confidence = LOW`, `indicator_stability = LOW`, with its scheme dependence
   stated on its face.

3. **`NUMERIC_GAP = NOT_IDENTIFIABLE`; `MEASURED_SHORTAGE = FALSE`; `FORECASTING = NOT_SUPPORTED_YET`.**
   `is_measured_shortage` is `false` on every response in the system; no route may return `true`.

4. **"Supply" is a reserved word**, prohibited in every label, header, API field name, chart title and
   export column, because no supply quantity exists at any occupation or trade grain. Training outcomes are
   named as candidate counts within a named scheme and period.

5. **A relative signal may never be rendered as a count**, and confidence may never be rendered as a number
   or probability. Both are build-failing lint rules.

6. **Blocked outputs are published as explicit unavailability**, with reason and gate — never as `0`, blank,
   `—`, an empty array, or a 404. `NOT_IDENTIFIABLE` is held distinct from `NOT_ACQUIRED`,
   `ACCESS_PENDING` and `MAPPING_UNKNOWN`, because the first is a property of the evidence structure that
   more of the same data cannot fix.

7. **Nine objective gates (G-1 … G-9)** govern unblocking, and **four (G-5 … G-8)** govern promotion of the
   hybrid indicator. No new numerical threshold was invented; every figure is carried from Step 6 or Step 7.
   **G-7 (an occupation dimension on the training axis) is non-negotiable and cannot be substituted**, since
   without it the indicator can never state what is under pressure. **Promotion never converts the indicator
   into a gap** — G-1 is separate and is not implied by G-5 through G-8.

8. **Cross-state district comparison is never the default.** Within-state ranking is, because the demand
   signal sums to each state's NCS total by construction and so encodes registration practice alongside
   labour demand.

9. **The PS shortfall is published, not concealed.** The unavailability register and the gates constitute the
   gap analysis the PS requested, expressed as an evidence specification instead of a fabricated quantity.

## Discrepancies found while validating against the live database

Both are recorded because this ADR's subject is publication accuracy. **Neither disturbs the identification
argument, which is not reopened.**

**(a) Output A is `ESTIMATED`, not `OBSERVED`.** The Step 7.1 brief described it as
"OBSERVED × NATIONAL_PROXY"; `demand_national_occupation_composition.observed_or_estimated = 'ESTIMATED'` on
all 175 rows, confidence MEDIUM/LOW. The observed component is the industry vacancy total; the occupation
split is estimated from an ILOSTAT/PLFS structure. The genuinely `OBSERVED` demand products are
`analytical_state_demand` and `analytical_demand_by_industry`. The specification separates them into their
own tier. **Labelling correction only; no value, grain or conclusion changes.**

**(b) `supply_coverage_summary.trades_mapped_to_nco` is a stale hard-coded `0`.** Written at
`src/lmis/cli.py:684` during Step 5.0, before Step 5.2 found the official DGT CTS trade → NCO linkage. It is
contradicted by `dim_trade_mapping_status` (2 `OFFICIAL_MULTI_NCO`, 153 `MAPPING_UNKNOWN`) and
`map_trade_to_nco` (4 rows, `authority = OFFICIAL`, confidence 1.0): **Electrician (DGT/1001)** →
7411.0100, 7412.0200 and **Fitter (DGT/1002)** → 7233.0100, 7233.0200. The metric is **barred from
publication** and its correction is the single value change authorised for Step 7.2. **It does not affect
the identification argument** — 2 of 155 trades mapped creates no `state × trade` or `district × trade`
supply cell.

## Options considered

- **Publish the hybrid indicator as a production early-warning output.** *Rejected.* Its flag set collapses
  from 207 to 0 under scheme substitution, so a published flag would be an artefact of an undecidable choice.
  It would also become the system's headline number precisely because it is the only one resembling what the
  PS asked for.
- **Discard the hybrid indicator entirely.** *Rejected.* The design is sound and reproducible, built only from
  already-labelled products, and it is the one honest answer the project has to the prioritisation question.
  Discarding it would leave the PS requirement addressed by nothing at all.
- **Retain as experimental, fenced, with gated promotion.** *Adopted.* Keeps the work available for review
  without lending it authority the evidence does not support.
- **Publish demand outputs without a mandatory metadata envelope.** *Rejected.* Outputs B and C are
  unitless relative signals; without compulsory coverage and interpretation metadata they would be read as
  vacancy counts, which is the project's central inferential risk (Step 0 risk #14).
- **Return 404 or an empty array for blocked capabilities.** *Rejected.* Both read as "none found" rather
  than "not computable" — the exact misreading this policy exists to prevent.

## Consequences

**Positive.** Nothing publishable can be mistaken for a measured gap. Terminology is enforced mechanically
rather than by discipline, at the two points where drift actually happens — labels and exports. Coverage and
provenance travel with every number, so a figure cannot be screenshotted free of its caveats. The gates are
objective and auditable, so promotion is a decision with recorded evidence rather than a drift. The missing
evidence becomes an actionable, costed ask addressed to the ministry that owns the data.

**Negative, and accepted.**

- **The PS's gap-forecasting requirement remains partially unmet**, visibly. A demo audience expecting a gap
  number will not find one, and the explanation is statistical rather than visual.
- **The headline output is a relative ranking at LOW confidence over 17.6% of districts.** That is a modest
  product next to what the PS describes.
- Mandatory metadata adds weight to every response and export.
- The experimental surface risks being read as production anyway; §2.1 fencing and §2.3 notices mitigate but
  cannot eliminate that.
- Nine gates are a high bar, and some may never be passed with publicly available data. **That is the
  intended behaviour, not a defect** — a gate that can be passed by assumption is not a gate.

**Reversal condition.** This ADR is superseded only by a new ADR citing specific gate evidence. No gate may
be weakened to admit an output; weakening a gate is itself a decision requiring its own ADR.

## Implementation Gate

**Step 7.2 may implement, and only this:** (1) the publication-status metadata layer of §7; (2) the
unavailability register of §3 — reasons and gates only, no values; (3) the §7.3 blocked-route response;
(4) terminology enforcement as a build-failing lint over §1.3; (5) **the §0.2 stale-constant fix at
`src/lmis/cli.py:684`** with regression tests — the only authorised value change, correcting 0 to the
computed count; (6) the §1.2 coverage-disclosure components; (7) experimental fencing; (8) alignment of
`limitations.md`, `methodology.md` and `analytical_data_dictionary.md`.

**Step 7.2 may not:** compute any pressure score or flag (Step 8, gated); create any gap, shortage, supply or
forecast value; alter any analytical value except item 5; change an existing table's semantics; create a
composite score; or promote any output between tiers.

**Promotion of the hybrid indicator to production is not authorised by this ADR** and requires G-5, G-6, G-7,
G-8 and a new ADR.

## Verification

No code written, no schema change, no migration, no new table, no analytical value altered. 40 tables,
82,356 rows, 7 migrations unchanged. Full test suite passes (285 tests).
