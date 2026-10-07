# Step 5.3 — Trade-Level Supply Evidence Investigation

Date: 2026-10-04 · **Evidence investigation only.** No supply estimated or allocated, no state→trade
allocation, no district/Udyam/Census allocation, no gap, no forecast, no shortage/surplus score, no early
warning, no recommendations, no API/frontend/LLM, no synthetic data. Nothing bypassed.

---

## Verdicts

> ### `TRADE_LEVEL_SUPPLY_STATUS = PARTIALLY_RESOLVED`
> ### `DISTRICT_TRADE_SUPPLY_STATUS = STILL_UNRESOLVED`

**Real official trade- and job-role-level supply quantities DO exist — and were sitting in a file the
project already held.** Step 5.0 parsed the MSDE Annual Report's state-level annexures and never scanned the
report body. The body contains trade-level numbers.

But they are **NATIONAL** and **Top-N subsets**, so the strongest official supply grain is unchanged for
geography.

---

## 1. Audit

Confirmed by query: `fact_training_outcome` (350) and `fact_training_infrastructure` (144) carry **no**
trade/occupation column. `dim_training_trade` 155, `map_trade_to_nco` 4, `map_qualification_to_nco` 1,
`dim_trade_mapping_status` 155, `supply_evidence_matrix` 10. Existing infrastructure reused throughout.

## 2. What was found

| Source table | Grain | Measures | Period | Rows |
|---|---|---|---|---|
| **Table-5.54** p154 | national × **trade** × trade_type | `APPRENTICES_ENGAGED` | FY2018-19 → FY2023-24 | 10 trades |
| **Table-5.10** p89 | national × **job role** | `ENROLLED`, `TRAINED_ORIENTED` | as on 2024-03-31 | 10 job roles |
| **Table-5.9** p89 | national × **sector** | `ENROLLED` | as on 2024-03-31 | 5 sectors |

Top apprenticeship trades: **Electrician 2,14,271 · Fitter 2,06,676** · Retail Trainee Associate 1,59,266 ·
Assembly Line Operator 86,276 · COPA 68,551 …

Top PMKVY 4.0 job roles: Traditional Hand Embroiderer 1,17,340 enrolled · Sewing Machine Operator 70,405 ·
**Domestic Data Entry Operator 60,500** · Electric Vehicle Service Technician 42,666 …

### A pleasing coincidence that is actually useful

The two trades with **official NCO mappings** from Step 5.2 (Electrician `DGT/1001`, Fitter `DGT/1002`) are
the **top two apprenticeship trades by volume**. And the one job role with an official Q-File NCO mapping
from Step 5.1 (Domestic Data Entry Operator → `4132.0402`) is **third** in the PMKVY 4.0 list.

So **3 entities now carry both a real supply quantity and an official NCO code**, connected through the
existing mapping tables by exact name — `nco_link_method = EXACT_NAME_AGAINST_EXISTING_OFFICIAL_MAP`. No new
mapping system was created; a name that does not match exactly links to nothing.

## 3. Critical limitations, each recorded on the data

- **Top-N subsets.** `is_top_n_subset = True` on every row. The rows do **not** sum to the population, so
  **no share, rate or denominator may be derived from them.**
- **National only.** No state or district dimension exists; a test asserts no such column is present.
- **State × trade is NOT derivable.** Table-5.55 gives *Top Ten States × apprentices* with **no trade
  dimension** — a separate **marginal** table alongside Table-5.54. Combining the two would require assuming
  independence. This is precisely the NCS state/sector situation, and it is rejected for the same reason.
- **Measures are not interchangeable.** `APPRENTICES_ENGAGED` (an engagement count under NAPS) is a
  different concept from PMKVY 4.0 `ENROLLED`/`TRAINED_ORIENTED`, from a different scheme. Each row carries
  its own `measure_definition`; the apprenticeship one states explicitly "not training completion".
- **Temporal mismatch with demand.** Apprenticeship data is cumulative FY2018-19→FY2023-24; PMKVY 4.0 is as
  on 2024-03-31; the demand baseline is **2024-11-15**. The PMKVY 4.0 vintage is close; the apprenticeship
  figure is a six-year cumulative total and **must not be read as a current annual flow**.

## 4. Reconciliation

| Source table | Measure | Extracted sum | Published total | Result |
|---|---|---|---|---|
| TABLE_5_54 | APPRENTICES_ENGAGED | 1,047,299 | 1,047,299 | **exact** |
| TABLE_5_10 | ENROLLED | 514,619 | *none printed* | NULL, not 0 |
| TABLE_5_10 | TRAINED_ORIENTED | 105,100 | *none printed* | NULL, not 0 |
| TABLE_5_9 | ENROLLED | 1,291,749 | *none printed* | NULL, not 0 |

Table-5.54's printed "Grand Total" equals the sum of its ten displayed rows exactly — so it is a **subtotal
of the top ten, not a population total**. That is recorded rather than mistaken for coverage.

## 5. Sources rejected, with reasons

| Source | Decision | Reason |
|---|---|---|
| **Table-5.55** Top Ten States × apprentices | **REJECTED** | State-level with **no trade dimension**; a separate marginal — state × trade not derivable |
| **Tables 5.20/5.22** State-wise ITIs affiliated for Drone courses | **REJECTED** | A count of **institutes offering a course**, not trainee supply. Counting institutes and calling it supply is the exact conflation the methodology forbids |
| **NQR** qualification records | **REJECTED** | Publishes qualification **metadata** (NSQF level, NOS, NCO code), not enrolment or certification counts. A Q-File NCO code is **taxonomy** evidence, not supply |
| **bharatskills.gov.in** | **REJECTED** | Client-rendered; exposes curriculum documents only, no quantitative participation data |
| **apprenticeshipindia.gov.in** (the portal cited as the source of Tables 5.54/5.55) | **UNAVAILABLE** | Client-rendered SPA: every path, including `/robots.txt` and `/reports`, returns the same 75 KB shell with 0 table rows, 0 mentions of "trade" and no downloadable files. Protected endpoints were not reverse-engineered |
| **PMKVY district resource** (data.gov.in) | **ACCESS_PENDING** | Registered API key required; none held, none invented |

`supply_evidence_matrix` now holds **17 rows** across three blockers: ACQUIRED 3 · PARTIALLY_ACQUIRED 3 ·
REJECTED 7 · UNAVAILABLE 3 · ACCESS_PENDING 1.

## 6. Final evidence table

| Evidence grain | Available? | Source | Measures | Vintage | Coverage |
|---|---|---|---|---|---|
| **National × trade** | **YES** | MSDE AR Table-5.54 | apprentices engaged | FY2018-19→23-24 | **Top 10 only** |
| **National × job role** | **YES** | MSDE AR Table-5.10 | enrolled, trained/oriented | as on 2024-03-31 | **Top 10 only** |
| **National × sector** | **YES** | MSDE AR Table-5.9 | enrolled | as on 2024-03-31 | Top 5 only |
| State × trade | **NO** | — | — | — | marginals only; not derivable |
| State × job role | **NO** | — | — | — | — |
| State × qualification | **NO** | — | — | — | — |
| District × trade | **NO** | — | — | — | — |
| District × job role | **NO** | — | — | — | — |
| District × qualification | **NO** | — | — | — | — |
| Institute × trade | **NO** | — | — | — | only institute *counts* per course |
| State × scheme × measure | **YES** (Step 5.0) | MSDE AR Annexures 11/14 | enrolled→placed (5) | 2015-16; as on 2024-03-31 | 36 states |

## 7. The eight questions, answered

**Q1 — Did we find official trade/job-role/qualification-level SUPPLY QUANTITIES?**
**Yes** — real, official, quantitative: 10 trades (apprentices engaged), 10 job roles (enrolled,
trained/oriented), 5 sectors (enrolled). All **Top-N subsets**.

**Q2 — At what geographic grain?** **NATIONAL only.** No state or district dimension exists in these tables.

**Q3 — What supply measures?** `APPRENTICES_ENGAGED`, `ENROLLED`, `TRAINED_ORIENTED`. **Not available:**
sanctioned seats/capacity, available seats, assessed, certified, placed *at trade level* (those five exist
only at state × scheme, from Step 5.0).

**Q4 — Time/vintage?** Apprenticeship FY2018-19→FY2023-24 cumulative; PMKVY 4.0 as on 2024-03-31. Demand
baseline is 2024-11-15 — the PMKVY 4.0 vintage is close, the apprenticeship one is a six-year cumulative.

**Q5 — Can the quantities be connected to the official Trade → NCO mapping?**
**Yes, for 3 of 25 entities**, via the existing official maps and exact-name linkage: Electrician and Fitter
(→ `map_trade_to_nco`, 4 NCO codes) and Domestic Data Entry Operator (→ `map_qualification_to_nco`,
`4132.0402`). The remaining 22 are `NO_EXISTING_OFFICIAL_MAP`.

**Q6 — Does the evidence support `STATE × NCO SUPPLY`?** **No.** The trade-level quantities are national,
and the state-level table has no trade dimension. There is no route to state × NCO without allocating a
state total across trades — which is forbidden and is now blocked by a regression test.

**Q7 — Does it support `DISTRICT × NCO SUPPLY`?** **No.** Neither a district nor a trade dimension is
available together at any grain.

**Q8 — Strongest legitimate common grain between demand and supply?**

| | Demand (Step 4.0) | Supply (Steps 5.0–5.3) |
|---|---|---|
| National × NCO division | **yes** (output A) | **partially** — 3 entities with NCO codes, Top-N only |
| National × sector/industry | yes (NIC section) | yes (5 sectors, Top-N) |
| State | yes | yes (scheme × measure, no occupation) |
| District | yes (estimated) | **no** |

**The strongest honest answer is `NATIONAL × NCO occupation`, for a handful of entities, on a Top-N basis —
which is too thin to support a gap.** At state level there is still **no common occupation grain**. So the
Step 5.1/5.2 conclusion stands: **a demand–supply gap must not be computed.**

## 8. Practical stopping point

Per §14 of the brief, the legitimate official routes for trade-level supply are now exhausted:
data.gov.in (API key), DGT, NCVT MIS, bharatskills, NQR, the NAPS portal, MSDE's own annual report, and
state portals (Step 5.1). The remaining obstacles are **access** (a registered API key) and **publication
practice** (MSDE publishes Top-N lists nationally and totals by state, not a trade × state matrix) — not
search effort.

**The next step should be a methodological decision about what the project can legitimately model, not more
searching.**

## 9. Files and tables

**New:** `src/lmis/conform/msde_trade_supply.py`, `db/migrations/007_trade_supply.sql`,
`tests/test_trade_supply_evidence.py`, this document.
**Modified:** `src/lmis/conform/nqr_qfile.py` (+7 evidence rows), `src/lmis/cli.py`,
`src/lmis/warehouse/load.py`, README.

| Table | Rows |
|---|---|
| `fact_training_trade_outcome` | **35** (25 entities × their measures) |
| `fact_trade_supply_reconciliation` | **4** |
| `supply_evidence_matrix` | **17** (was 10) |

No new raw snapshot was needed — the source was already held with a checksummed manifest.

## 10. Remaining blockers

| Blocker | Status |
|---|---|
| State × trade supply | **STILL_UNRESOLVED** — marginals only |
| District × trade supply | **STILL_UNRESOLVED** |
| Exhaustive (non-Top-N) trade supply | **UNAVAILABLE** |
| Trade-level capacity / certified / placed | **UNAVAILABLE** |
| data.gov.in API key | **ACCESS_PENDING** |
| NCO mapping for 153 trades | **MAPPING_UNKNOWN** (Step 5.2) |
