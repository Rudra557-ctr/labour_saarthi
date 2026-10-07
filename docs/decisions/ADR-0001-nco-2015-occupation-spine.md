# ADR-0001 — NCO-2015 is the occupation spine, 4-digit Family is the canonical analytic unit

- **Status:** Accepted
- **Date:** 2026-10-02
- **Supersedes / superseded by:** —
- **Step 0 reference:** D-01

## Context

Step 0 proposed NCO-2015 at the 4-digit Family level as the canonical occupation unit, marking the exact
code structure as REQUIRES VERIFICATION because the DGE landing page does not describe it and the PDFs
resisted naive text extraction.

## Decision

Adopt NCO-2015 as the primary occupation reference, with the **4-digit Family** as the canonical analytic
unit and mandatory roll-up to Group (3), Sub-Division (2) and Division (1).

## Evidence

The structure is now **verified from a primary source** — NCVET, *Report on Mapping of Qualifications with
NCO Codes* (22 Aug 2023), Annexure IX s.3: 8-digit code, decimal after the first four digits, digits 1/1-2/
1-3/1-4 giving Division/Sub-Division/Group/Family, digits 5-6 the occupation within the Family, digits 7-8
QP/NOS availability.

Crucially, the same official handbook **permits family-level assignment** when no exact occupation matches:
*"a code till first four digits that is upto family level can be assigned"*. The canonical level we chose on
judgement in Step 0 turns out to be the level the official process itself falls back to.

## Consequences

- `occupation_master` carries `level` explicitly; no join may ignore it.
- 4-digit Family is the finest level at which free-text titles will be mapped. Mapping to 8-digit
  occupations is rejected as false precision.
- Division 0 (Armed Forces) is out of scope: it is absent from the official source table.
- `qp_nos_indicated` is exposed as a column (digits 7-8 ≠ 00), giving the future
  `NO_QUALIFICATION_EXISTS` flag a structural basis.
