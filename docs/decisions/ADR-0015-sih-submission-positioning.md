# ADR-0015 — SIH submission positioning

- **Status:** Proposed (positioning decision; awaiting review)
- **Date:** 2026-10-06
- **Rests on:** ADR-0009 (no identifiable gap) · ADR-0010 (quadrant, no composite) · ADR-0011 (publication
  policy) · ADR-0012 (information architecture) · ADR-0013 (SUPPORTING tier, allocation-signal terminology) ·
  ADR-0014 (demo readiness)
- **Supersedes:** nothing. No methodology, schema, formula or analytical value changed.
- **Package:** `docs/step8.0_sih_solution_story.md` · `docs/step8.0_requirement_mapping.md` ·
  `docs/step8.0_demo_script.md` · `docs/step8.0_judge_qa.md`

## Context

PS 26246 is titled *"AI-Enabled Labour Market Intelligence and Skill Demand–Supply Forecasting Engine"* and
asks for gap forecasting at district and sector granularity, severity ranking and early warning.

The implemented system does **not** produce a numeric gap, a forecast, a shortage score, an early-warning
flag, or any occupation-level supply quantity — and it cannot, because Step 6 established that
`SUPPLY[geography × trade]` is not identifiable from evidence of the shape that exists. There is also **no
machine-learning model in production**: verified on 2026-10-06, no ML library is installed and no model code
exists in `src/` or `api/`.

So this submission faces a presentational choice with an ethical edge. The project could be positioned as a
gap-forecasting engine, leaning on the architecture's readiness and on language vague enough to survive a
first reading. Or it could be positioned as what it is.

## Decision

**Official positioning:**

> **LMIS is an evidence-first Labour Market Intelligence platform.** It standardises fragmented official
> labour-market evidence onto shared NCO-2015, LGD and NIC-2008 dimensions, and produces transparent,
> provenance-aware demand intelligence in which every value carries its evidence status, confidence,
> coverage, vintage and source documents. It **explicitly identifies the evidence required** to progress to
> defensible demand–supply gap analysis and forecasting, and refuses to publish those outputs until that
> evidence exists.

Four supporting decisions:

1. **The absent gap is presented as a finding, not an apology.** It is a reproducible identification result —
   row and column marginals never determine an interior, the 21.8% column fragment comes from a different
   scheme, and the closing assumption `P(trade|state) = P(trade)` is both substantively false and untestable.
   It leads the narrative rather than hiding at the end.

2. **The AI/ML position is stated plainly: no model is in production.** The documents say so in those words.
   Every ML capability the PS implies is blocked by the same missing evidence, not by modelling choice —
   forecasting needs two dated observations, a learned gap model needs an identifiable target, an
   early-warning classifier needs labels that do not exist. Naming a model we do not run would contradict the
   discipline that is the rest of the submission, and would collapse under one question.

3. **Requirement mapping is brutally honest.** Of ten requirements: **6 IMPLEMENTED, 4 PARTIALLY_IMPLEMENTED,
   3 DATA_BLOCKED, 2 NOT_SUPPORTED_YET, 1 EXPERIMENTAL** (a requirement may carry more than one status
   across its parts). R3 — forecast the gap — is **NOT_SUPPORTED_YET**, never IMPLEMENTED.

4. **Innovation claims are confined to seven defensible items** — identification-aware analytics, a
   publication contract enforced in code, a terminology lint over the published surface including translation
   files, evidence status read from the data rather than declared, caveats stored as data, measured
   self-criticism of our own signals, and full reproducibility from checksummed snapshots. **Ordinary FastAPI
   and dashboard functionality is not called novel AI.**

## Options considered

- **Position as a completed gap-forecasting engine.** *Rejected.* It would be false. It would also not
  survive the first competent question — *"what is your state × trade source?"* has no answer — and the
  failure would then discredit the parts that are genuinely strong.
- **Position vaguely: "AI-powered skill gap intelligence".** *Rejected.* Vagueness is the same claim with
  deniability. It invites judges to infer a gap and a model, which is the misreading the entire publication
  contract was built to prevent.
- **Lead with the dashboard and mention limitations at the end.** *Rejected.* It inverts the argument. The
  limitation is the intellectual contribution; burying it makes the submission look like an incomplete
  dashboard instead of a completed piece of evidence reasoning.
- **Build the hybrid indicator to have something gap-shaped to show.** *Rejected.* Its classification flips
  on an undecidable choice between two source schemes — 207 flags under PMKVY 2.0, 0 under PMKVY 1.0,
  cross-scheme rank correlation +0.005. Shipping it would manufacture exactly the false confidence we spent
  the project avoiding.
- **Position as evidence-first intelligence with an explicit unlock path.** *Adopted.* It is true, it is
  defensible under adversarial questioning, and it hands MSDE something actionable: one named dataset.

## Consequences

**Positive.** Every claim survives scrutiny, because each was verified against the repository before being
written. The honesty is itself differentiating — most submissions to this PS will show a gap number, and ours
can explain why theirs is not identifiable. The missing-evidence register is a concrete deliverable addressed
to the ministry that owns the data. The demo script contains no step the application cannot perform. And the
Q&A anticipates the hard questions — *"where is the AI?"*, *"isn't your ranking just enterprise density?"* —
with answers that concede the point and then show the measurement.

**Negative, and accepted.**

- **We will likely lose on first impression** to a submission showing a confident district-level gap heatmap.
  Ours shows a relative ranking at LOW confidence over 17.6% of districts, and its most striking page lists
  what cannot be computed.
- **"No ML model" is a real risk against an "AI-Enabled" title.** A judge scanning for a model will not find
  one. We mitigate by explaining exactly what blocks each ML capability and what would unblock it, but the
  risk is not removable without lying.
- **The honest labels are unwieldy.** "District × Occupation Relative Demand Allocation Signal" with two
  caveats above its table is not a crisp visual.
- **The strongest part of the work is the hardest to demo** — an identification argument does not screenshot
  well.
- **A judge may read the discipline as incompleteness.** Q41 and the demo's closing redirect exist for that
  moment, but it may not land with every panel.

We accept all of this. A system that misleads a planner about where to send training money is worse than one
that loses a competition, and the error in a fabricated gap would be invisible, directional, and
unrecoverable.

## Claims we must never make

| ✗ Never say | ✓ Correct statement |
|---|---|
"We predict the skill gap." | "No numeric demand–supply gap is identifiable from current evidence. We publish the gate — one observed interior cell of supply by geography and trade — that would make it computable." |
"We know the number of vacancies in every district." | "District values are an estimated **relative allocation signal**, `relative_signal_unitless`. NCS publishes vacancies at state level only." |
"We know which occupation is in shortage." | "No occupation-level supply quantity exists at any geographic grain, so no shortage is defined — let alone measured." |
"Our district ranking is observed demand." | "It is an estimated allocation signal. **Within a state its ordering is the Udyam enterprise-share ordering** — 0 of 36 states differ. The NCS component varies only between states." |
"Our PLFS data measures vacancies." | "PLFS is national labour-force context, `tier = SUPPORTING`, `not_a_demand_measure = TRUE`. It is not a demand or supply measure and has no district validity." |
"Our hybrid indicator measures shortage." | "It is designed, `EXPERIMENTAL_ONLY`, `implemented: false`, and absent from the product. Even promoted it would carry `is_measured_shortage = FALSE` and could not name which trade is short." |
"Our system forecasts demand." | "Forecasting is `NOT_SUPPORTED_YET`. We hold one dated demand observation; gate G-4 requires at least two of the same measure and basis." |
"58.13% of vacancies were allocated to states." | "58.13% — 20,507,320 vacancies — are PAN-India or multiple-state and are **never** allocated. Allocating them is a `PROHIBITED` capability. The district signal rests on the remaining 41.87%." |
"Our synthetic data proves the model." | "No synthetic data exists anywhere in the system, and no model is trained. Every value traces to a named official source document." |
"Our AI inferred the missing government data." | "No model generates any value. Fuzzy, semantic, embedding and LLM-generated mappings are prohibited project-wide — which is why 153 of 155 trades remain `MAPPING_UNKNOWN` rather than being matched by name." |
"Data as of today." | "Five vintages: NCS 2024-11-15, Udyam 2023-12-21, PMKK 2024-03-31, PLFS April 2025, Census 2011. No single 'data as of' date applies." |
"Training supply by state." | "Training-system outcomes — candidate counts within a named scheme and period. 'Supply' is a reserved word that may not describe them." |

## Implementation Gate

Step 8.0 is documentation only. **No implementation file, analytical module, API route, frontend asset,
database table, migration, configuration file or test was modified.**

**A later step may** produce slide/presentation artifacts from these documents, extend Hindi with reviewed
translations, implement the within-state choropleth, and run a manual screen-reader pass.

**It may not** introduce a numeric gap, a forecast, a supply quantity, a composite score, a trained model or
the hybrid indicator; change an analytical formula or value; add a table or migration; or make any claim in
the presentation that these documents do not support.

## Verification

479 tests passing. 40 tables, 7 migrations, 82,358 rows — unchanged. No analytical formula or value changed.
No synthetic data. No model. No gap. No forecast. No unsupported supply. `is_measured_shortage = false`
everywhere. Hybrid remains `EXPERIMENTAL_ONLY`, `implemented: false`. Every quantitative claim in the four
Step 8.0 documents was checked against the live repository before being written.
