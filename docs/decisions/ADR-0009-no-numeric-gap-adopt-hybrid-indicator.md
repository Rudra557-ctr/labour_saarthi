# ADR-0009 — No numeric demand–supply gap; adopt a hybrid evidence-qualified indicator

- **Status:** Accepted
- **Date:** 2026-10-04 (Step 6)
- **Relates to:** ADR-0007 (supply evidence grain), ADR-0008 (trade → NCO linkage)
- **Full analysis:** `docs/step6_methodology_decision.md`

## Context

The problem statement asks for demand–supply gap forecasting at sector and district granularity. Steps
5.0–5.3 exhausted the legitimate official routes for supply data. The position is fixed:

- strongest observed supply grain: **state × scheme × measure** (no occupation, no district)
- strongest trade-level supply: **national × Top-N trade/job-role** (21.8% of the population)
- trade → NCO mapping: official but **2 of 155**
- the state supply table has **no trade dimension** for the mapping to attach to

## Decision

**1. No numeric demand–supply gap will be computed.** Not at district × NCO, not at state × NCO, not at
state level.

**2. Adopt Option D** — a hybrid, evidence-qualified **Demand Pressure + Training-System indicator**,
emitting an investigation flag that is explicitly **not** a measured shortage.

**3. Option A** (parallel products, no composite) is the fallback. **Options B, C and E are rejected.**
**Option F** (formal data acquisition) proceeds in parallel.

## Why — the identification argument

`SUPPLY[state, trade]` is a **joint distribution**. We hold row marginals (state totals) and a **21.8%
fragment** of column marginals *from a different scheme*. Row + column marginals never determine an
interior; closing the system requires `P(trade | state) = P(trade)`, which is

- **substantively false** — regional trade mix heterogeneity is the very thing the project exists to measure,
  so assuming it away assumes away the answer; and
- **untestable** — not one state × trade cell exists to validate against.

And raking is unavailable anyway: **78% of PMKVY 4.0 enrolment sits in job roles the source does not name.**

**This is an identification failure, not an estimation difficulty.** A formula can be written and will
return numbers; those numbers would restate the assumption, not measure the world.

Independently, every subtraction form fails the unit and time audits: a **cumulative stock of vacancy
postings since 2015** cannot be differenced against **candidates certified in a scheme window**, and three
temporal types (stock, flow, point-in-time count) are present across windows starting in different years.

## Consequences

- The PS's gap-forecasting requirement is **partially unmet, and stated as such.** Preferable to a
  fabricated result.
- Step 7, if approved, implements only training-system ratios (computed within one source and period),
  infrastructure coverage, and a `POTENTIAL_PRESSURE` flag carrying `is_measured_shortage=False` and
  weakest-link confidence (expected **LOW**).
- The flag's demand side is district × NCO while its training side is state × scheme with **no occupation
  dimension**; that asymmetry is recorded on every row, not footnoted.
- **Forecasting stays out of scope** until a second dated NCS observation exists. One date cannot support a
  trend and none will be interpolated.
- Unlocking a real gap requires, in order: **state/district × trade training outcomes**, complete non-Top-N
  trade marginals, the remaining 153 trade → NCO mappings, a second dated NCS snapshot, and ideally
  NCO-coded NCS vacancies.

## Status of this step

Documentation only. No schema change, no analytical value changed, no new table. Verified by re-running
`make reproduce` and the full test suite.
