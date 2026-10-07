# Claims Checklist — read before presenting

Three lists. **If a sentence is not in A, or not in B with its caveat attached, do not say it.**

---

## A · SAFE TO SAY

Verified, no qualifier needed.

| Claim | Evidence |
|---|---|
"We standardised fragmented **official** labour-market evidence." | 26 sources registered, 15 acquired, conformed to NCO-2015 / LGD / NIC-2008 |
"We preserve provenance and evidence status on every value." | `source_ids`, `transformation_depth`, `vintage`, tier on every production row |
"We provide **relative demand allocation signals**." | `demand_district_relative_signal`, `demand_district_occupation_signal` |
"We expose coverage and confidence." | `demand_coverage_summary`; weakest-link `overall_confidence` |
"We explicitly identify unavailable capabilities." | 16 capabilities, each with a reason code and a gate |
"26 official sources registered under a licence gate; nothing acquired unless registered." | `config/sources.yaml`; `src/lmis/common/registry.py` |
"Raw storage is immutable — a fetch never overwrites a snapshot." | sha256 manifests; `src/lmis/ingest/acquire.py` |
"14 of 14 reconciliation checks match each source's own published totals exactly." | `fact_training_reconciliation` |
"NCO-2015 is the occupation spine — 3,982 occupations, bridged from NCO-2004 by the **official** 3,447-row concordance." | `occupation_master`, `map_nco2004_to_nco2015` |
"LGD is the geography spine — 821 rows, 36 states and 785 districts." | `location_master` |
"58.13% of published NCS vacancies are PAN-India or multiple-state and are **never allocated**." | `demand_coverage_summary`; `/api/residual-allocation` → `PROHIBITED` |
"The district signal rests on 41.87% of the published total." | `ncs_state_attributable_share` |
"138 of 785 districts have Census occupation structure." | `districts_with_occupation_signal` |
"No row anywhere in the system carries a signal of zero." | verified by test |
"Missing data is reported with its reason, never as zero." | `occupation_prior_status`, `value_status` |
"Blocked capabilities return HTTP 200 with `data: null`, a reason code and a gate — never 404." | 10 blocked routes |
"`is_measured_shortage` is false on every response, enforced at application startup." | `api/main.py::verify_contract` |
"**There is no machine-learning model in production**, and no ML library is installed." | `pyproject.toml`; no model code in `src/` or `api/` |
"No synthetic data exists anywhere in the system." | all 40 tables |
"We proved NCS's 22 'sectors' are NIC-2008 industry sections, not occupations." | `map_ncs_sector_to_nic_section` |
"Within a state, output B's district ordering **is** the Udyam enterprise-share ordering — 0 of 36 states differ." | `within_state_ranking_caveat`; measured |
"Within a district, output C's occupation ordering **is** the Census-2011 occupation-share ordering — 0 of 138 differ." | `within_district_ranking_caveat`; measured |
"Fuzzy, semantic, embedding and LLM-generated mappings are prohibited project-wide." | 153 of 155 trades remain `MAPPING_UNKNOWN` |
"We bypassed no CAPTCHA, authentication or robots restriction." | licence gate; `microdata.gov.in` refused on a self-signed certificate |
"479 tests pass, and `make reproduce` rebuilds everything from checksummed raw bytes." | `pytest`; `Makefile` |
"30 API routes — 20 production, 10 blocked — with OpenAPI." | `/openapi.json` |
"We found and fixed a reflected XSS in our own dashboard during QA." | `docs/step7.5_sih_demo_readiness.md` §2.1 |

---

## B · SAY WITH CAVEAT

True, but misleading without the attached qualifier. **Say the caveat in the same breath** — not later, not
on the next slide.

| Claim | **Required caveat, said together with it** |
|---|---|
"We estimate national occupation composition." | "…**estimated** from observed NCS industry totals × an ILOSTAT/PLFS industry × occupation structure. Confidence varies **by row** — 157 MEDIUM, 18 LOW. It is not a vacancy count by occupation." |
"We provide district relative allocation signals." | "…**relative**, `relative_signal_unitless`, not a vacancy count. And **within a state the ordering is the Udyam enterprise-share ordering** — the NCS demand component varies only between states." |
"We provide district × occupation signals." | "…for **138 of 785 districts**, at **LOW** confidence, resting on a **2011** Census occupational structure. Within a district the ordering is the Census ordering." |
"The platform is designed to support forecasting when compatible temporal data becomes available." | "…**designed**, not implemented. Forecasting is `NOT_SUPPORTED_YET` — it needs a second dated NCS observation. We have one." |
"We publish training-system outcomes." | "…candidate counts within a **named scheme and period**, at **state** level with **no occupation dimension**. These are not a supply quantity." |
"We cover the whole country." | "…**observed** demand is national — 37 states, 22 sectors. The district signal covers 785 districts; **occupation detail covers 3 states and 138 districts.**" |
"We rank districts." | "…on a **relative allocation signal**, within a state by default. Cross-state comparison carries NCS registration coverage as well as labour demand." |
"We designed an early-warning indicator." | "…**designed, not implemented.** `EXPERIMENTAL_ONLY`. Its flag set collapses from 207 to 0 depending on which training scheme is read, so it is not a production output." |
"We use PLFS." | "…as **national** labour-force context only. `tier = SUPPORTING`, `not_a_demand_measure = TRUE`, and district estimates are not valid for it." |
"We have an industry view." | "…vacancy **counts** are official; the **NCS-sector → NIC-section alignment is ours**, at confidence 0.95." |
"Our data is from November 2024." | "…2024-11-15 is the NCS as-on date. **Five vintages are in play** — Udyam 2023-12-21, PMKK 2024-03-31, PLFS April 2025, Census 2011 — and no single 'data as of' date applies." |
"We have a multilingual interface." | "…the **architecture** is complete; English is complete, Hindi is 21 of 106 keys with English fallback. We do not machine-translate official occupational terminology." |

---

## C · DO NOT SAY

Each is false or unsupported. Use the replacement.

| ✗ Never say | ✓ Correct replacement |
|---|---|
"We calculate the exact skill gap." | "No numeric demand–supply gap is identifiable from current evidence. Gate G-1 — one observed interior cell of supply by geography and trade — would make it computable." |
"We predict the skill gap." | *(same as above)* — and never "predict": nothing in the system predicts anything. |
"We know district-wise vacancies." | "District values are an estimated **relative allocation signal**. NCS publishes vacancies at **state** level only." |
"We forecast labour demand." | "Forecasting is `NOT_SUPPORTED_YET`. We hold one dated demand observation; gate G-4 requires at least two." |
"We know which occupation is in shortage." | "No occupation-level supply quantity exists at any geographic grain, so no shortage is defined — let alone measured." |
"Our district ranking is observed demand." | "It is an **estimated allocation signal**. Within a state its ordering is the Udyam enterprise-share ordering — 0 of 36 states differ." |
"PLFS measures vacancies." | "PLFS is **national labour-force context**, `not_a_demand_measure = TRUE`. It measures participation, employment and unemployment rates." |
"The hybrid indicator measures shortage." | "It is **designed, `EXPERIMENTAL_ONLY`, `implemented: false`**, and absent from the product. Even promoted it would carry `is_measured_shortage = FALSE` and could not name which trade is short." |
"Our AI inferred the missing government data." | "**No model generates any value.** Every number traces to a named official source document. LLM and semantic mapping are prohibited project-wide." |
"We use AI/ML to estimate demand." | "The estimates are deterministic arithmetic on official structures, with the method stored on every row. **No ML model is in production.**" |
"Our synthetic data proves the model." | "**No synthetic data exists**, and no model is trained." |
"58.13% of vacancies were allocated to states." | "58.13% — 20,507,320 vacancies — are PAN-India or multiple-state and are **never** allocated. Allocation is a `PROHIBITED` capability." |
"Training supply by state." | "Training-system **outcomes** — candidate counts within a named scheme. 'Supply' is a reserved word that may not describe them." |
"Data as of today." / "Live data." | "Five vintages, each figure carrying its own as-on date. No single 'data as of' date applies." |
"Highest-demand districts." / "Top occupations by vacancies." | "Highest **relative allocation signal** within this state / for this division." |
"We solved the problem statement." | "We implemented six of ten requirements fully, four partially, and the three that depend on a gap are blocked by evidence — with the unlocking dataset named." |
"This is production-ready for national rollout." | "It is demo-ready and reproducible. There is no deployment, so there are no outcome results." |
"Our platform saved X crore / created Y jobs." | **Never state any impact number.** No deployment exists; any figure would be invented. |
"Our confidence is 83%." | "Confidence is **ordinal** — HIGH / MEDIUM / LOW — never a percentage or probability." |
"The architecture is novel because we used FastAPI." | "FastAPI is an ordinary choice. The novelty is identification-aware analytics and a publication contract enforced in code." |

---

## The three-second test

Before any sentence leaves your mou, ask: **does this assert a quantity we measured, or one we derived?**

- Measured → say it plainly.
- Derived → say "estimated", name the method, and attach the caveat.
- Neither → **don't say it.**
