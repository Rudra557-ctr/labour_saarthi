# Step 4.0 — Demand Estimation

Date: 2026-10-04 · **First step producing ESTIMATED values.** No supply estimation, no demand–supply gap,
no shortage/surplus classification, no forecasting, no early warning, no recommendations, no API/frontend/LLM.
No synthetic data. No fabricated time series. The PAN-India residual is never allocated to a district.

---

## 1. Purpose

Implement exactly the three outputs approved in Step 3.1 §9 — and only those. The original single-product
formula was found non-identifiable in Step 3.1 (two of its three terms do not exist), so demand is published
as three separate quantities, each with its own evidence chain and its own confidence.

## 2. Inputs (all verified in the warehouse before coding)

| Input | Table | Rows | Role |
|---|---|---|---|
| NCS vacancies by industry | `analytical_demand_by_industry` | 22 | OBSERVED |
| NCS vacancies by state | `analytical_state_demand` | 38 (37 state + 1 residual) | OBSERVED |
| Industry → occupation bridge | `fact_ilo_employment_eco_occ` | 715 | OBSERVED (ILO/PLFS) |
| District enterprise shares | `analytical_district_structure` | 1,570 | SUPPORTING (Udyam) |
| District occupation structure | `analytical_district_occupation_structure` | 12,420 | SUPPORTING (Census 2011) |
| NCO-2004→2015 division map | `map_nco2004_division_to_nco2015_division` | 10 | derived, purity measured |
| Geography spine | `location_master` | 821 | reference |

**Audit result: no discrepancies.** All 20 NCS-mapped NIC sections exist in the ILO cross-tab — a clean
20/20 overlap, so the join needs no invented industry mapping.

## 3. Formula A — national occupation demand composition

```
estimated_occupation_demand[section s, division d]
    = V_national[s]  ×  P(d | s)

occupation_total[d]       = Σ_s estimated_occupation_demand[s, d]
occupation_share_of_total = occupation_total[d] / Σ_d occupation_total[d]
```

- `V_national[s]` — OBSERVED NCS vacancies for NIC-2008 section `s` (lakh, as published).
- `P(d | s)` — OBSERVED conditional occupation distribution from ILOSTAT `EMP_TEMP_ECO_OCU_NB_A`
  (India, source `BA:14121` = PLFS), **bridge year 2025**, normalised over the cells the source publishes.
- Joined **only** at NIC-2008 section. `Sector Not Specified` is excluded (it carries no industry
  information, so no occupation can be inferred) and reported in coverage instead.
- **No geographic allocation.** Transformation depth 1.

**Grain:** `baseline_period × nic_section_code × nco_2015_division` — 175 rows (20 sections × 9 divisions,
less 5 cells the ILO does not publish).

## 4. Formula B — district relative demand signal

```
relative_demand_signal[district g]
    = V_state_attributable[state(g)]  ×  enterprise_share_within_state[g]
```

- `V_state_attributable` — OBSERVED NCS state vacancies, **residual excluded by construction**. Summed per
  LGD state code first, because two NCS rows (the pre-2020 UTs) resolve to one LGD state.
- `enterprise_share_within_state` — SUPPORTING Udyam share, category `TOTAL`, sums to 1 within state.
- **No occupation dimension.** Transformation depth 1.

**Grain:** `baseline_period × lgd_code` — 785 rows, 785 districts, 36 states.

## 5. Formula C — district × occupation relative demand signal

```
district_occupation_signal[g, d]
    = relative_demand_signal[g]  ×  census_occupation_share[g, d]
```

- Uses the **Census-2011 district occupation share**, not output A. Multiplying by A as well would apply two
  different occupational structures to one quantity and **double-count the occupational signal** — a test
  asserts A's columns are absent from C and that C's arithmetic is exactly B × census share.
- Census cells: `area=TOTAL`, `sex=PERSON`, `row_type=DIVISION_TOTAL`. The `UNCLASSIFIED` bucket has no NCO
  equivalent, so it is **excluded from the product and retained** as
  `unclassified_share_not_allocated` — visible, never redistributed.
- Transformation depth 2.

**Grain:** `baseline_period × lgd_code × nco_2015_division` — 1,889 rows.

## 6. Baseline date

**`2024-11-15`**, read **from the warehouse** at build time, never hard-coded. The builder refuses to run if
more than one NCS as-on date is present, because a second genuine snapshot makes a flow derivable and that
is a methodology question, not something to resolve silently.

`flow_available = false` on every row, with the reason stored. No monthly values, no interpolation, no
extrapolation, no growth rates.

## 7. PAN-India treatment

| Metric | Value |
|---|---|
| Published total | 35,275,833 |
| **PAN-India residual (kept NATIONAL)** | **20,507,320** |
| State-attributable (the only part allocated) | 14,768,513 |
| **State-attributable share** | **41.9%** |

The residual never enters B or C. It is not discarded either — `demand_coverage_summary` reports it, and a
test asserts attributable + residual = published total. **Any dashboard showing district or state demand must
state "41.9% of NCS vacancies are geographically attributable" adjacent to the number.**

## 8. Census coverage — every district accounted for

| `occupation_prior_status` | Districts | Meaning |
|---|---|---|
| `AVAILABLE` | **138** | Census prior exists and is used |
| `CENSUS_NOT_ACQUIRED` | **522** | Has a Census-2011 code, but B-24 not yet acquired for its state — **resolvable** |
| `NO_CENSUS_2011_CODE` | **125** | Post-2011 district; a prior can **never** exist — permanent |
| **Total** | **785** | equals output B exactly |

Within the three pilot states: 138 of 149 available, **11 with no Census code** (Maharashtra 1, Tamil Nadu 6,
Uttar Pradesh 4) — matching Step 3.1 exactly.

**Issue found during implementation:** a first pass reported "125 unavailable" and silently omitted 522
districts entirely. Those are two different situations — *can never have a prior* versus *not acquired yet* —
and merging them both overstated the permanent gap and hid 522 districts. Now each district gets one
explicit row stating which case it is. No zero-filling, no parent inheritance, no national back-fill.

## 9. Confidence methodology

Weakest-link, per Step 3.1 §7. Seven dimensions stored per row plus `overall_confidence`.

| Output | Overall | Driven by |
|---|---|---|
| **A** | **MEDIUM** (157 rows) / **LOW** (18 rows) | `statistical_support = SURVEY_WITHOUT_N`; LOW where the NCS→NIC mapping confidence < 0.85 — exactly the 2 heterogeneous sectors (`Operations and Support`, `Other Service Activities`) × 9 divisions |
| **B** | **MEDIUM** (785 rows) | `geography_coverage = ALLOCATED` |
| **C** | **LOW** (1,889 rows) | `temporal_confidence = HISTORICAL` (2011 prior) — as Step 3.1 predicted |

**Refinement made during implementation:** the Step 3.1 draft had no way to express "this dimension does not
apply". Output B has no occupation dimension *by design*, and scoring that as `NOT_AVAILABLE` wrongly forced
B to LOW — penalising a deliberate design choice as if it were missing evidence. `NOT_APPLICABLE` was added
and excluded from all triggers; `NOT_AVAILABLE` now means only "we wanted this and lack it".

No numeric probabilities are produced. `overall_confidence` is ordinal, and a test asserts it is not numeric.

## 10. What the numbers mean

- **A** — the occupation mix implied by *where NCS vacancies sit across industries*, combined with *how
  employment is distributed across occupations within those industries nationally*. A national composition.
- **B** — a **relative ranking signal** for comparing districts, built from observed state vacancies
  distributed by observed employer presence.
- **C** — a **relative ranking signal** for district × occupation, LOW confidence, usable for ordering only.

## 11. What the numbers DO NOT mean

- **None is a vacancy count.** B and C carry `unit = relative_signal_unitless`; C carries
  `interpretation = RELATIVE_RANKING_SIGNAL_NOT_A_VACANCY_COUNT`. "District X has 4,500 vacancies" is
  forbidden — 4,500 is not observed at district level by any source.
- **A is not an observed occupation vacancy count.** NCS does not publish occupation at all.
- **B's within-state ordering carries no new information.** Because the state multiplier is constant inside
  a state, B's ranking there is *identical* to the Udyam enterprise-share ranking. B adds information only
  **across** states. Stored per row as `within_state_ranking_caveat` and asserted by a test.
- **C's within-district ordering likewise is just the Census-2011 occupation-share ordering.** C adds
  information only **across** districts. Stored as `within_district_ranking_caveat`.
- **A's composition is skewed by NCS portal coverage, not by the Indian labour market.** Finance & Insurance
  alone is 138.24 of 352.76 lakh vacancies (**39%**), which is why Clerks (18.1%) and Professionals (17.9%)
  top the composition. This is a property of what employers post on NCS.

## 12. Limitations

- One as-on date → cross-sectional only.
- 58.1% of the measure has no geography.
- The industry → occupation bridge is **national**, applied to a national output in A (appropriate) and not
  used sub-nationally at all.
- C's occupation prior is **15 years old** and exists for 3 states.
- The NCO-2004→2015 division map is **effectively the identity** (every division maps to the same digit);
  its value is the *measured purity* (0.789–0.998) that quantifies the leakage that identity hides.
- Udyam is a 2023 snapshot; LGD a 2023 snapshot.
- Enterprise presence is a proxy for vacancy generation, not a measurement of it.

## 13. Provenance

Every row carries `source_ids`, `methodology`, `built_at`, the seven confidence dimensions, and
`flow_unavailable_reason`. `source_ids` resolve to `source_master` (asserted by test), which joins to
`source_snapshot` for the sha256 of the exact bytes. Reproduce with:

```bash
make demand        # build the three outputs
make reproduce     # verify → masters → facts → analytical → demand → validate → warehouse → profile → test
```

## 14. Future requirements for time-series estimation

1. **A second NCS as-on date**, ≥1 quarter apart, with the measure definition verified identical before
   differencing. The builder already refuses to proceed silently if a second date appears.
2. 4–6 dated observations before any trend claim; the PAN-India residual must be differenced separately, and
   a change in NCS portal coverage is indistinguishable from a change in labour demand.
3. Census B-24 for the remaining states (pattern `catalog/13648 + census_state_code`) to move 522 districts
   from `CENSUS_NOT_ACQUIRED` to `AVAILABLE`.
4. PLFS unit-level microdata for a **state-level** bridge.
5. An authoritative district parent→child source for the 125 post-2011 districts.
