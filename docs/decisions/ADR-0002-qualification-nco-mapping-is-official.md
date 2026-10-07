# ADR-0002 — Qualification → occupation mapping is OFFICIAL, sourced from the qualification record

- **Status:** Accepted
- **Date:** 2026-10-02
- **Step 0 reference:** D-01, risk R-02

## Context

Step 0's single largest risk (R-02) was that no official NCO ↔ QP crosswalk exists, forcing us to build a
project mapping for the training→occupation edge and weakening every downstream claim.

## Decision

Treat `map_qualification_to_occupation` as **`authority='OFFICIAL'`**, populated by extracting the NCO code
**from each qualification's own record** (Q-File / NQR), not by building a project mapping.

Set per-mapping `confidence` using the **official audit** in Annexure VII of the NCVET report rather than a
uniform constant.

## Evidence

NCVET report (22 Aug 2023), Annexure IX: *"As a standard practice of NSQF alignment, all Qualifications are
required to be mapped to an NCO code. The NCO is also reflected in the Qualification File Template."*

There is no separate crosswalk table **because one is not needed** — the mapping lives on the qualification.

Annexure VII audits 45 awarding bodies for unassigned and wrongly-mapped codes, extracted to
`mappings/official/ncvet_nco_mapping_quality_by_awarding_body.csv`. Quality varies sharply by body
(DGT: 463 qualifications, 0 unassigned, 0 wrongly mapped; ESSCI: 88, 54 unassigned, 20 wrongly mapped),
which is precisely why confidence must be per-body.

## Consequences

- **R-02 is closed.** The strongest methodological citation available to this project.
- Qualification harvesting from NQR becomes a Step 2 task; no bulk export exists, so it is scoped to pilot sectors.
- Where a qualification legitimately has **no** NCO code, that is official practice (the handbook says the
  Standing Committee must be notified), so an UNMAPPED state is retained rather than forced.
