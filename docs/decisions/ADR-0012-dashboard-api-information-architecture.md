# ADR-0012 — Dashboard and API information architecture

- **Status:** Proposed (design only; awaiting review)
- **Date:** 2026-10-05
- **Builds on:** ADR-0009 (no numeric gap), ADR-0010 (quadrant, no composite), ADR-0011 (publication policy)
- **Supersedes:** nothing
- **Amended by:** ADR-0013 (Step 7.3.1) — adds the SUPPORTING tier that this ADR's PLFS panel required, locks the allocation-signal labels of decisions 2/3, and moves the circularity, residual and vintage rules (decisions 5, 6, 10) into enforced contract validation
- **Specification:** `docs/step7.3_dashboard_api_product_design.md`

## Context

Step 7.2 made a defined set of outputs publishable and enforced the metadata, terminology and unavailability
contract in code. What remained undecided was the **product**: which pages exist, which comparison each one
defaults to, which visualisations are permitted, and which logical API resources exist.

Validating every comparison the brief asks for against the live warehouse produced four findings that
determined the design more than any layout preference.

**1. Two of the three requested comparisons are arithmetic restatements of a single input.** Outputs B and C
are products in which one factor is constant inside the comparison group:

```
B[district]           = observed_state_vacancies × enterprise_share_within_state
C[district, division] = B[district]              × occupation_share_of_district
```

| Comparison | What the ordering is | Differs from that input |
|---|---|---|
Districts within a state | Udyam enterprise share (2023-12-21) | **0 of 36 states** |
Occupations within a district | Census-2011 occupation share | **0 of 138 districts** |
Districts within (state × NCO division) | enterprise share **×** occupation share | **27 of 27 groups**, from *each* input |

The project already knew this: `within_state_ranking_caveat` and `within_district_ranking_caveat` have been
stored on every row since Step 4.0 and say it verbatim. It had simply never been carried into a UX decision.

**2. The PAN-India residual is a row in `analytical_state_demand`.** "Multiple States/PAN India" holds
20,507,320 — **5.2× West Bengal**, the largest actual state. Any state ranking that does not filter
`is_pan_india_residual = FALSE` renders the residual as the top state.

**3. Nothing on the surface is contemporaneous.** Five vintages spanning fourteen years: demand 2024-11-15,
Udyam 2023-12-21, PMKK 2024-03-31, PLFS M202504, Census 2011.

**4. Showing an input beside its own output is circular.** `analytical_district_structure` (Udyam) and
`analytical_district_occupation_structure` (Census) are the factors in B and C; both already carry
`not_a_demand_measure = TRUE`. Presenting either as corroborating context would offer a multiplicand as
independent evidence for its own product.

## Decisions

1. **Eight pages**, with evidence that visibly weakens along the drill-down: Landing · National · State ·
   District · Occupation · Methodology & Evidence · Coverage & Limitations · Unavailable Capabilities. A
   ninth, the experimental surface, is specified as a boundary only and is not implemented.

2. **Within-state remains the default district comparison** (ADR-0011), **but it may not be captioned as a
   demand ranking.** It is an enterprise-density ordering, and the stored caveat is displayed verbatim above
   the table. Likewise a district's occupation panel is captioned as the district's **2011 Census
   occupational structure**, not as occupational demand.

3. **The occupation view's primary panel is districts within a state × NCO division** — the one comparison
   that combines both structures and restates neither input. It is also the comparison Step 7 §6.2 identified
   as free of NCS cross-state registration bias.

4. **No total demand figure anywhere** — not on the landing page, not as a KPI tile, at no grain. The
   published grand total is cumulative NCS registrations of which 58.13% is unattributable; a single large
   number would be read as national labour demand.

5. **Every state ranking filters the residual out**, and the residual is rendered as its own coverage
   disclosure, never as a bar beside states.

6. **No time axis, trend, sparkline, delta or directional glyph on any page.** One dated demand observation;
   the five vintages are not a series. Each number carries its own as-on date, and no page shows a single
   global "data as of".

7. **`state` is a required parameter on the district and district × occupation resources.** Within-state
   becomes the default at the protocol level rather than by UI convention; an unparameterised national
   district list would return a cross-state ranking as though it were neutral. Cross-state is a distinct,
   explicitly named parameter that returns its caveat in `limitations`.

8. **The industry filter keys on `ncs_sector_name` (22), not `nic_section_code`** — two sectors have a NULL
   NIC code, so a NIC-keyed filter would silently drop them. NIC section is a displayed attribute carrying
   its `PROJECT` mapping authority and 0.95 confidence.

9. **Confidence is a per-row badge, never one badge for a view.** Output A is 157 MEDIUM rows across 18 NIC
   sections and 18 LOW rows across 2.

10. **Udyam and Census structures are prohibited as corroborating context** beside B or C. They may appear
    only as explicit derivation disclosure — "this ranking *is* this input".

11. **PLFS is a national-only `SUPPORTING` panel**, badged `NOT A DEMAND MEASURE`, absent from state and
    district pages (`district_estimates_valid = FALSE`).

12. **Four evidence states with distinct visual treatments** — OBSERVED, ESTIMATED, SUPPORTING, UNAVAILABLE —
    and the UI must teach the difference between *"the number exists but was derived"* and *"the number does
    not exist and cannot currently be computed."* Rendering both as a blank or a dash is the specific failure
    this decision forbids.

13. **Unavailable capabilities are surfaced where the user forms the expectation** — the gap question is
    answered on the district and occupation pages, not only on a separate page — grouped by reason code so
    `NOT_IDENTIFIABLE` is visibly distinct from `NOT_ACQUIRED`.

14. **The response envelope reuses the Step 7.2 contract verbatim**, adding only `data`, `query`, `links`,
    `limitations` (populated from the stored caveat columns, never authored in the API layer) and
    `row_status_breakdown`.

15. **Exports carry a mandatory metadata block.** A relative-signal column keeps its name and
    `relative_signal_unitless` unit, no count-like column may be derived from it, unavailable values export
    empty with their reason, and no experimental output may appear.

16. **Taxonomy identifiers are never translated** — NCO, NIC, LGD and Census codes, scheme names, status
    enums, reason codes and source ids stay machine-comparable. Machine translation of official occupation
    titles is prohibited.

17. **Tables are the primary representation and charts the enhancement.** Every chart has a tabular
    equivalent, the choropleth is always accompanied by the ranked table it visualises, and evidence status is
    carried by text plus shape plus position, never colour alone.

## Options considered

- **Caption the within-state ranking as a demand ranking** (the obvious reading of the approved default).
  *Rejected.* It is the enterprise-share ordering in all 36 states; the caption would assert information the
  comparison does not contain.
- **Make cross-state the default so the ranking carries the NCS demand signal.** *Rejected.* It imports
  registration bias, which ADR-0011 decided against, and Step 7 measured its effect — Uttar Pradesh holds
  51.4% of in-scope cells but 10.4% of the national top decile.
- **Drop output B's district ranking entirely, since within-state it restates an input.** *Rejected.* It is
  the only district-level product the project has, it is genuinely informative across states, and the honest
  response is to label what the ordering is rather than withhold it.
- **Show Udyam and Census structures as corroborating context.** *Rejected as circular* (finding 4).
- **A single headline demand number for the landing page.** *Rejected* (decision 4).
- **Omit unavailable capabilities from the UI to keep it clean.** *Rejected.* Silent omission is how a user
  concludes the gap is zero rather than not computable.

## Consequences

**Positive.** No page can be read as a gap, shortage, forecast or supply view. The default comparison is
labelled as what it arithmetically is, using caveats the pipeline already carries, so the UI cannot drift from
the data. The one informative comparison is promoted to the occupation view's main panel. The residual trap
and the circularity trap are closed before implementation rather than after review. Every proposed page
element and API field is backed by a verified existing column.

**Negative, and accepted.**

- **The product is visibly modest.** Its headline capability is a relative ranking whose default view is
  explicitly an enterprise-density ordering. A demo audience expecting a gap dashboard will find careful
  qualification instead.
- **The honest captions are long**, and the caveats compete with the numbers for attention. That is the
  intended trade: a shorter caption would be a false one.
- **Occupation detail reaches 3 of 36 states and 138 of 785 districts**, so the drill-down dead-ends for most
  of the country — with a reason, but it dead-ends.
- **No map is a default view at national grain**, which removes the most expected visual in a
  government dashboard.
- Mandatory metadata adds weight to every response and export.
- Two of the three requested comparisons carry a caveat that substantially qualifies them, which may read as
  the product undermining itself. **It is the product being accurate about what it computed.**

**Reversal condition.** Superseded only by a new ADR. A new metric, filter, visualisation or API field
requires its own design step; an implementer who finds an unbacked page element removes it and reports it
rather than computing a value to fill it.

## Implementation Gate

**Step 7.4 may implement:** the read-only resources R1–R15 (§7), the response envelope (§8), the eight pages
(§4) under the visualisation rules (§5) and filters (§6), the evidence/confidence UX (§9), the
unavailable-capability surfaces (§10), exports (§13), i18n and accessibility (§12), extension of the existing
terminology lint to UI label catalogues and export headers, and tests for every §14 guardrail.

**Step 7.4 must not:** introduce analytical methodology; compute a gap, shortage, surplus, supply or forecast
value; create a composite score or index; create a table or migration; alter an analytical formula or value;
implement the hybrid indicator beyond its boundary; add an unlisted filter, field or visualisation; or relax
any Step 7.1 or 7.2 guardrail.

## Verification

No code written, no implementation file modified, no schema change, no migration, no new table, no analytical
value altered. 40 tables, 82,358 rows, 7 migrations. Full test suite passes (329 tests). Every page element
and API field in the specification was checked against a live column before being written.
