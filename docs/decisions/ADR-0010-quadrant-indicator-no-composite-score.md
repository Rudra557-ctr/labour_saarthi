# ADR-0010 — Hybrid indicator is a quadrant classification, not a composite score

- **Status:** Proposed (design only; awaiting review)
- **Date:** 2026-10-04
- **Supersedes:** nothing. **Implements:** ADR-0009 (Option D)
- **Design document:** `docs/step7_hybrid_indicator_design.md`

## Context

ADR-0009 selected Option D — a hybrid evidence-qualified Demand Pressure + Training-System indicator — after
Step 6 established that no numeric demand–supply gap is identifiable from accessible official evidence.
Step 7 had to specify *how* such an indicator combines a district × NCO demand estimate with a state × scheme
training observation.

Four measurements of the actual data decided the design:

1. **The normalisation functional form is irrelevant to ranking.** National percentile, raw min-max and log
   min-max are pairwise rank-identical (Spearman 1.000). Raw min-max is nonetheless disqualified: median
   0.0275, and a 0.90 cut selects **1 of 1,242** cells. What changes the answer is the *reference population*
   (top-decile Jaccard 0.325–0.443 across variants).

2. **Cross-division comparison is not like-for-like**, and the occupation axis is thin. Division median
   signals span 6.4× (431 to 2,757). Variance decomposition of the log signal: district 61.2%, occupation
   30.7%, interaction — the only district-*specific* occupational information — **8.1%**.

3. **National cross-state normalisation imports NCS registration bias.** Uttar Pradesh holds 51.4% of
   in-scope cells but 10.4% of the national top decile, because the district signal sums to the state NCS
   total by construction (UP 14,782 vacancies per district vs TN 45,139, MH 42,596).

4. **The two eligible training indicators contradict each other and are unstable across schemes.**
   Maharashtra is at the 91st percentile on `certified/enrolled` and the 18th on `placed/certified`.
   Cross-scheme rank correlation between PMKVY 1.0 and 2.0: `certified/enrolled` **+0.034**,
   `placed/certified` **+0.005**, `assessed/enrolled` **−0.022**. Median absolute shift in `placed/certified`
   between schemes: 0.213. `trained/enrolled` is identical in **35 of 35** states under PMKVY 1.0 (IQR 0.000).

## Options considered

- **A — Two-dimensional quadrant.** Four named cells from two thresholds. No weights.
- **B — Rule-based binary flag.** A threshold rule emitting a status.
- **C — Composite priority score.** `priority = f(demand_pressure, training_system_signal)`.
- **D — Rank-based priority.** Combine ordinal positions to order an investigation queue.

## Decision

**Adopt A as the conceptual frame, B as the stored field, and D as the presentation layer. Reject C.**

- **Demand normalisation:** percentile within **(state × NCO division)** as primary — it removes both the
  division incomparability of finding 2 and the NCS state bias of finding 3. Percentile within division
  nationally is stored as an explicitly caveated secondary for cross-state views. **Raw and log min-max
  rejected.** No per-capita normalisation (no compatible 2024 population denominator exists for the 138
  in-scope districts).
- **Training indicators:** `placed/certified` primary, `certified/enrolled` secondary, from **one declared
  scheme**, reported side by side and **never blended**. `trained/enrolled`, `assessed/enrolled`,
  `certified/assessed` and PMKK coverage are supporting context that cannot trigger a flag.
- **Geography propagation:** `training_system_signal[state(district)]` as a **lookup**, never an estimate.
  Identical for every district in a state, declared on every row, enforced by a regression test asserting
  zero within-state variance.
- **No composite score anywhere.** Confidence is `LOW` by construction. `is_measured_shortage = FALSE` is
  enforced by a database constraint and a regression test.
- **Thresholds** are quantile-based, versioned in config, and **not committed in this step**. Natural breaks
  are rejected on evidence: the largest log-gap in the upper half of the distribution is ×1.427 and is a
  single outlier cell.

### Why C is rejected

Not on taste — on finding 4. Any composite must weight two indicators that rank the same state near-oppositely.
**Equal weighting is therefore not a neutral default but a decisive and arbitrary intervention**: it would
place Maharashtra mid-pack, the one description no single piece of evidence supports. No alternative weighting
is defensible either — there is no outcome label, no official guidance, and no statistical criterion (the two
indicators correlate −0.043 and +0.353, so neither PCA nor any correlation argument recommends a blend). A
composite would also blend a **1,242-valued** axis with a **3-valued** axis while presenting them as co-equal,
and a continuous "priority score" built from a demand measure and a training measure is structurally the hidden
gap that Step 7's brief forbids, whatever units are declared.

## Consequences

**Positive.** No weights to defend. The state-level nature of the training axis is structurally visible rather
than concealed. Each quadrant carries a distinct, statable policy meaning. Rejecting min-max removes
outlier fragility. The within-state primary reference makes the output immune to NCS registration bias.
Robust to the indicator contradiction, because the axes never merge.

**Negative, and material.**

- **The output is scheme-dependent.** Identical rules and thresholds yield **0 flags under PMKVY 1.0 and 207
  under PMKVY 2.0**. The declared scheme matters more than any threshold, and the evidence cannot choose it.
  Every result must ship with this sensitivity beside it, and every flagged row carries
  `indicator_stability = LOW`.
- **`certified/enrolled` is inert in the current pilot** — all three in-scope states are at or above the
  national median, so it can trigger nothing.
- **PMKK coverage cannot separate the pilot states** — at ceiling (1.000) for both Maharashtra and Uttar
  Pradesh.
- **The training axis has no occupation dimension**, so a flag can never identify which occupation or trade
  is underserved. Structural, not a coverage gap.
- Coverage is **138 of 785 districts (17.6%)** and 3 of 36 states.
- Confidence is `LOW` for every row and cannot be improved by better methodology.
- A quadrant is less immediately rankable than a single score — accepted deliberately, with Design D
  ordering the investigation queue by demand rank only.

**Open for the reviewer.** Whether to publish the indicator at all, given scheme dependence, or to hold at
Option A (no numeric gap, documented) until a scheme-independent training observation exists. The design is
sound; its inputs are weak, and declining to publish on that basis is a legitimate choice.

## Verification

No schema change, no analytical value changed, no new table, no flag computed. 40 tables, 82,356 rows, 7
migrations unchanged. Full test suite passes.
