# ADR-0013 — The SUPPORTING publication tier, and locked terminology for the derived allocation signals

- **Status:** Proposed (contract amendment; awaiting review)
- **Date:** 2026-10-05
- **Amends:** ADR-0011 (publication policy), ADR-0012 (dashboard/API information architecture)
- **Supersedes:** nothing. All existing output statuses are preserved unchanged.
- **Contract:** `config/publication_contract.yaml` — version **7.1 → 7.3.1**

## Context

Step 7.3 designed a national labour-force context panel from `analytical_labour_market_context` (PLFS), then
found that the output was **not in the publication contract and the contract had no tier for it**. Step 7.3
was approved in principle on condition that this gap be closed before implementation.

Step 7.3 also established two arithmetic facts about the derived district signals, and the dashboard design
depends on their being locked into the contract rather than left to UI convention:

- **Within a state, output B's district ordering is exactly the Udyam enterprise-share ordering** — 0 of 36
  states differ.
- **Within a district, output C's occupation ordering is exactly the Census-2011 occupation-share ordering** —
  0 of 138 districts differ.

### The tension this amendment had to resolve

The amendment request describes `SUPPORTING` as an "evidence/publication tier". But ADR-0011 and the Step 7.2
implementation bind a principle that pulls the other way: **publication metadata must read evidence status
from the authoritative analytical data, never declare it.** `analytical_labour_market_context` carries
`observation_status = 'OBSERVED'` on all 81 rows. Declaring it `SUPPORTING` *as an evidence status* would be
exactly the config-asserts-evidence failure that Step 7.1 §0.1 was raised to prevent.

**This is not a contradiction, and the project had already solved it.** The analytical layer has modelled
evidence and role as two separate columns since Step 3.0:

- `observation_status` carries **evidence** — `OBSERVED | SUPPORTING`, a closed set enforced by Pandera at
  `src/lmis/validate/schemas.py:118` and asserted with `Check.eq("SUPPORTING")` on the structure tables.
- `not_a_demand_measure` carries **role** — `TRUE` on PLFS, on the Udyam district structure and on the Census
  occupation structure.

`src/lmis/analytics/build.py` sets PLFS to `observation_status = OBSERVED` **and**
`not_a_demand_measure = True` (lines 318, 322), while setting the Udyam and Census structures to
`observation_status = SUPPORTING` (lines 195, 241). So `SUPPORTING` was never a new category — it has been a
first-class, contract-tested value in the analytical layer since Step 3.0, and the **publication** contract
simply never recognised it.

## Decisions

1. **`SUPPORTING` is recognised as a publication *tier*, which is a ROLE, orthogonal to evidence status.**
   Evidence status continues to be read from each table's own column. PLFS is therefore **OBSERVED evidence
   published in a SUPPORTING role**, and the envelope reports both: `evidence_status: ["OBSERVED"]`,
   `tier: "SUPPORTING"`, `is_demand_measure: false`.

2. **The SUPPORTING tier is data-backed, not merely declared.** A SUPPORTING output must declare
   `requires_data_flag: not_a_demand_measure`, and the envelope builder **refuses to publish it if a single
   row does not carry that flag as TRUE**. Declaring `analytical_state_demand` as SUPPORTING raises
   `ContractError`, because the column is absent. The declaration cannot drift from the data.

3. **Tier definition.** SUPPORTING is: *an observed or otherwise evidence-backed contextual dataset, useful
   for interpreting labour-market conditions, that is NOT the primary demand measure, NOT the primary supply
   measure, NOT a vacancy estimate, and NOT a shortage or gap measure. Displaying it does not make it a
   demand or supply conclusion, and it may not be combined, scaled or re-grained to produce one.*
   `may_be_primary_measure: false`, enforced at load.

4. **Five prohibited uses are declared on the tier** and tested: manufacture state or district demand; create
   a demand–supply gap; serve as occupation-level supply; represent as vacancy data; act as independent
   corroboration of a derived output.

5. **PLFS is published as SUPPORTING, national only.** `district_estimates_valid` is FALSE on every row, so
   the envelope carries `district_estimates_valid: false` and `valid_geo_levels: ["NATIONAL"]`; it may not
   appear on a state or district surface. No PLFS-derived metric is created and no PLFS value is modified.

6. **All four tiers are defined as a closed set** — OBSERVED, ESTIMATED, SUPPORTING, UNAVAILABLE — with
   UNAVAILABLE held explicitly distinct: *SUPPORTING data exists and is shown as context; UNAVAILABLE data
   does not exist and is shown as a reason.* No published output may carry the UNAVAILABLE tier; it is a
   capability state.

7. **Every existing status is preserved.** `analytical_state_demand` and `analytical_demand_by_industry`
   remain OBSERVED; the national occupation composition and both district signals remain ESTIMATED. Tested.

8. **Output B's approved label is `District Relative Demand Allocation Signal`**, and output C's is
   `District x Occupation Relative Demand Allocation Signal`. The occupation view's comparison is a
   `Relative Demand Allocation Signal`. Declared in `terminology.preferred_signal_labels`.

9. **The allocation label may not be used without its stored caveat.** Each output declares a
   `required_caveat_column` (`within_state_ranking_caveat`, `within_district_ranking_caveat`), and the
   envelope **refuses to build** if the column is absent or NULL on any row, carrying the caveat text into
   `required_caveat` so no consumer can render the label without it.

10. **Sixteen ranking phrasings are banned outright** in any published label or interpretation —
    "district demand ranking", "district vacancy ranking", "highest-demand districts", "number of vacancies
    by district", "top occupations by vacancies", "highest-demand occupations", "occupation vacancy ranking",
    "occupation shortage ranking", "occupation demand count", "observed demand ranking", "vacancy ranking",
    "shortage ranking" and near variants. **No output may declare `is_observed_vacancy_ranking: true`**; the
    contract refuses to load if one does.

11. **The circularity rule is codified.** A new `derivation_inputs` section declares that
    `analytical_district_structure` is a factor in B and C, and
    `analytical_district_occupation_structure` a factor in C, each with
    `display_role: DERIVATION_DISCLOSURE_ONLY`, permitted section labels ("How this signal is derived",
    "Derivation", "How this is calculated") and five prohibited framings ("supporting evidence for the demand
    signal", "independent validation", "corroborating demand data", "corroborating evidence", "independent
    evidence"). A new linter, `lint_derivation_labels`, catches both a prohibited framing and a derivation
    input shown outside a derivation section. **Derivation inputs are deliberately not output entries** — a
    factor is not a product. This is an interpretation rule: no data is deleted.

12. **The residual rule is codified on the output.** `analytical_state_demand` declares
    `residual_handling` with `default_filter: "is_pan_india_residual = FALSE"`,
    `excluded_from_default_comparison: true`, `must_remain_disclosed: true`, `allocation: PROHIBITED`, and
    the envelope reports `residual_rows: 1` against `default_comparison_rows: 37`. Its value (20,507,320) is
    unchanged, and a test asserts that it still outranks every actual state — which is why the default filter
    exists.

13. **The vintage rule is codified.** `vintage_policy` sets `global_as_of_date: PROHIBITED`,
    `per_output_vintage_required: true` and `time_series_across_vintages: PROHIBITED`, bans "live",
    "real-time", "current", "latest" and "data as of", and records each output's own vintage column. The
    contract refuses to load if either prohibition is relaxed, and a test asserts the vintages remain
    heterogeneous (2024-11-15, 2024-03-31, M202504, 2023-12-21, 2011) so no single date could describe them.

## Options considered

- **Declare SUPPORTING as an evidence status in the contract.** *Rejected* — it would overwrite the data's
  own `observation_status = OBSERVED` for PLFS and break the ADR-0011 principle that config may not assert
  evidence.
- **Change `analytical_labour_market_context.observation_status` to SUPPORTING in the analytical layer.**
  *Rejected* — it would modify an analytical value, which this step forbids, and it would be wrong on the
  merits: PLFS is a genuine observed survey estimate passed through unchanged. Its context role is already
  carried by `not_a_demand_measure`.
- **Drop the PLFS panel instead of amending the contract.** *Rejected* — the data is observed, officially
  published, already correctly flagged, and genuinely useful for interpretation. Nothing about it is unsafe;
  the contract simply lacked a slot.
- **Leave B and C's labels to UI convention.** *Rejected* — the misreading they invite is the project's
  central inferential risk, and a convention is not enforceable. Binding the label to a stored caveat column
  is.
- **Make the derivation inputs SUPPORTING outputs.** *Rejected* — that would make a multiplicand a publishable
  product and invite exactly the corroboration framing decision 11 forbids.

## Consequences

**Positive.** PLFS context becomes publishable with a role that cannot be mistaken for demand, and the role
is enforced against the data rather than asserted. The two arithmetic findings of Step 7.3 are now contract
guarantees instead of design prose: the allocation labels cannot be rendered without their caveats, and a
derivation input cannot be framed as independent evidence. The residual and vintage rules move from
documentation into load-time validation. The amendment recognises a tier the analytical layer already
enforced, closing a gap rather than inventing a concept.

**Negative, and accepted.**

- **The approved labels are long and unwieldy.** "District x Occupation Relative Demand Allocation Signal" is
  not a phrase anyone enjoys reading, and it will not fit comfortably in a chart title. It is accurate, and
  every shorter candidate asserts something the output does not contain.
- **Tier and evidence status are now two fields**, which is one more concept for a consumer to hold. The
  alternative was a single field that lies about one of them.
- Production outputs rise from 11 to 12, and the envelope grows several fields.
- `publication_tiers[SUPPORTING]["prohibited_uses"]` is declarative — it constrains what the contract permits
  and what the lint can catch, but it cannot by itself stop an implementer who recomputes PLFS into something
  else. The stop for that is Step 7.4's gate, not this file.

**Residual inconsistency, reported not resolved.** `analytical_labour_market_context` carries
`observation_status = OBSERVED` while `analytical_district_structure` and
`analytical_district_occupation_structure` carry `observation_status = SUPPORTING` — yet all three carry
`not_a_demand_measure = TRUE`. Step 3.0 used `observation_status` to express both evidence and role, and used
it differently in the two cases. Both values are individually defensible (PLFS is a passthrough survey
estimate; the structures are structural weights), and this amendment does not change either, because doing so
would alter analytical values. **The publication layer is unaffected**, since it reads evidence from the data
and role from the tier. If the analytical layer is ever harmonised, it needs its own step and ADR.

## Verification

No migration, no new table, no analytical module touched, no demand or supply formula or value changed.
40 tables, 82,358 rows, 7 migrations — all unchanged. Tests 329 → **387**, all passing. `make reproduce`
completes clean.
