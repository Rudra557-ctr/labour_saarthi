# ADR-0007 — Supply evidence: what grain the data actually supports

- **Status:** Accepted
- **Date:** 2026-10-04 (Step 5.1)
- **Step reference:** 5.0 acquisition, 5.1 evidence resolution

## Context

Step 5.0 acquired real state-level MSDE training data. Two blockers remained: no district-level training
data, and no trade → NCO-2015 mapping. Step 5.1 investigated both exhaustively.

## Decision — the grains the evidence supports

| Candidate grain | Supported? | Evidence |
|---|---|---|
| **A. state × trade supply** | **NO** | The acquired outcome annexures carry **no trade dimension** at all — they are state × scheme × measure. `dim_training_trade` is a standalone reference list with no volumes attached. |
| **B. district × trade supply** | **NO** | Neither dimension is available together; district training data is not published. |
| **C. state × NCO supply** | **NO** | No trade → NCO mapping exists for the 155 trades, and the outcome tables have no occupation dimension to map in the first place. |
| **D. district × NCO supply** | **NO** | Both blockers apply. |
| **E. capacity / enrolment / completion / certification / placement** | **PARTIALLY — at state × scheme only** | Enrolled, Trained, Assessed, Certified and Placed are all observed, state-level, for 2 schemes. **Capacity (sanctioned seats) is NOT available** — no acquired source measures it. |

**So the only supported supply grain is `state × scheme × measure`.** Nothing finer is claimed.

## What Step 5.1 did establish

**The official qualification → NCO evidence chain is proven.** NQR Q-File field 14, "Aligned to NCO/ISCO
Code/s", states a full 8-digit NCO-2015 code. For the one Q-File held it reads `NCO-2015/4132.0402`, which
resolves in `occupation_master` to the **identical title** ("Domestic Data Entry Operator") and whose
`qp_nos_indicated` flag is True — three independent corroborations. Recorded in
`map_qualification_to_nco` with `authority='OFFICIAL'`, confidence 1.0.

This matters because it shows the route to Blocker B is real and official. What is missing is **enumeration**
and the **trade → qualification link**, not the mapping principle.

## Consequences

- `dim_training_trade` stays **UNMAPPED for all 155 trades**. A test fails if any NCO code appears on a trade.
- A **district-level demand–supply gap is not computable**, and must not be attempted.
- A **state-level gap by occupation is also not computable**, because supply has no occupation dimension.
- Step 6 must either operate at a grain both sides share, or acquire the missing evidence first (see
  `docs/step5_1_supply_evidence_resolution.md` §9).
