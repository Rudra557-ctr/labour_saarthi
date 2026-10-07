# LMIS — Labour Market Intelligence System

Demand–supply gap intelligence for MSDE skilling capacity planning. SIH 2026.

**Current state: Step 1 complete, Steps 1.5–1.7 (demand-data investigation and validation) complete — verified sources, immutable snapshots, master/reference tables,
profiling, tests and documentation.** No index, forecast, gap score, API or dashboard yet; those are
later steps by design.

## Quickstart

```bash
make setup      # venv + dependencies
make sources    # list the source registry
make acquire    # fetch immutable raw snapshots (never overwrites)
make verify     # re-hash every snapshot against its manifest
make masters    # build master/reference tables
make profile    # profile every table -> docs/profiling/
make pilot      # validate provisional pilot scope against acquired data
make facts      # build observed fact tables
make validate   # enforce Pandera contracts -> fact_data_quality
make analytical # build the derived analytical layer
make warehouse  # apply DDL, load db/lmis.duckdb
make demand     # build the three approved demand estimates
make supply     # build the OBSERVED supply-side tables
make test       # 285 tests
make reproduce  # verify -> masters -> facts -> analytical -> validate -> warehouse -> profile -> test
```

## What exists

**Dimensions / reference:** `location_master` 821 · `location_alias` 8 · `location_change_event` 0 ·
`occupation_master` 3,982 · `sector_master` 59 · `nic_section_master` 20 · `dim_period` 132

**Mappings:** `map_nco2004_to_nco2015` 3,447 (OFFICIAL) · `map_ncs_sector_to_nic_section` 21 (PROJECT)

**Observed facts:** `fact_vacancy_official_by_state` 114 · `fact_vacancy_official_by_sector` 63 ·
`fact_establishment_district` 6,280 · `fact_labour_force_estimate` 81

**Provenance:** `source_master` 23 · `source_snapshot` 29 · `fact_data_quality` 11

**Analytical (Step 3.0, derived):** `analytical_state_demand` 38 · `analytical_demand_by_industry` 22 ·
`analytical_district_structure` 1,570 · `analytical_district_occupation_structure` 12,420 ·
`analytical_labour_market_context` 81 · `analytical_dataset_catalog` 5 ·
`fact_census_occupation_workers` 48,645 · `map_nco2004_division_to_nco2015_division` 10 ·
`fact_ilo_employment_eco_occ` 715

**Demand estimates (Step 4.0, ESTIMATED):** `demand_national_occupation_composition` 175 ·
`demand_district_relative_signal` 785 · `demand_district_occupation_signal` 1,889 ·
`demand_coverage_summary` 8

None of these is a vacancy count. B and C are **relative ranking signals**; see
[`docs/step4_0_demand_estimation.md`](docs/step4_0_demand_estimation.md) §11 for what they do not mean.

**Supply foundation (Step 5.0, OBSERVED):** `fact_training_outcome` 350 ·
`fact_training_infrastructure` 144 · `dim_training_trade` 155 · `fact_training_reconciliation` 14 ·
`supply_coverage_summary` 8

Plus Step 5.1/5.2 evidence: `map_qualification_to_nco` 1 · `supply_evidence_matrix` 10 ·
`map_trade_to_nco` **4** (OFFICIAL, 8-digit, multi-NCO preserved) · `dim_trade_mapping_status` 155

**Step 6 decision (ADR-0009): no numeric demand–supply gap is identifiable** from accessible official
evidence — an identification failure, not a modelling one. `SUPPLY[state, trade]` is a joint distribution
and we hold only row marginals plus a 21.8% fragment of column marginals from a different scheme. Adopted
instead: a hybrid **Demand Pressure + Training-System indicator** that flags investigation candidates
without inventing supply. See [`docs/step6_methodology_decision.md`](docs/step6_methodology_decision.md).

**Step 5.3** found real national trade/job-role supply quantities already inside the MSDE Annual Report:
`fact_training_trade_outcome` **35** · `fact_trade_supply_reconciliation` **4**. Top-N subsets, national
only — so **demand and supply still share no usable occupation grain**. See
[`docs/step5_3_trade_level_supply_evidence.md`](docs/step5_3_trade_level_supply_evidence.md).

**Step 5.2 found the official trade → NCO link**: DGT prints NCO-2015 codes directly on each CTS trade
curriculum (Fitter `DGT/1002` → 7233.0100 + 7233.0200). 2 of 155 trades mapped; 153 `MAPPING_UNKNOWN`
because no official curriculum index exists. See
[`docs/step5_2_occupation_linkage_resolution.md`](docs/step5_2_occupation_linkage_resolution.md).

Supply is **state × scheme × measure only**. Trade → NCO remains **UNMAPPED** (155/155) and district
training data **STILL_UNRESOLVED**, so **demand and supply share no occupation grain yet** — see
[`docs/step5_1_supply_evidence_resolution.md`](docs/step5_1_supply_evidence_resolution.md) §6 and
[`docs/step5_0_supply_data_foundation.md`](docs/step5_0_supply_data_foundation.md).

See also [`docs/step3_0_analytical_dataset.md`](docs/step3_0_analytical_dataset.md) and
[`docs/analytical_data_dictionary.md`](docs/analytical_data_dictionary.md).

See [`docs/step2_0_data_foundation.md`](docs/step2_0_data_foundation.md) for grain, units and evidence.

## Read these first

- [`docs/verification_report.md`](docs/verification_report.md) — what each official source actually
  publishes and how we know. **Start here.**
- [`docs/step1_5_demand_investigation.md`](docs/step1_5_demand_investigation.md) — the search for a real
  labour-demand signal, and the source evaluation table. Conclusion: state × sector only.
- [`docs/step1_6_district_demand_construction.md`](docs/step1_6_district_demand_construction.md) — how a
  defensible **estimated** district × occupation demand signal can be built from observed inputs.
- [`docs/step1_7_source_validation.md`](docs/step1_7_source_validation.md) — validation of each district
  source, the evidence matrix, and why NCS "sectors" are industry not occupation.
- [`docs/limitations.md`](docs/limitations.md) — what this system cannot tell you, and why.
- [`docs/taxonomy.md`](docs/taxonomy.md) — the NCO-2015 spine and the official-vs-project mapping rule.
- [`docs/decisions/`](docs/decisions/) — ADR-0001 … ADR-0005.
- [`docs/profiling/SUMMARY.md`](docs/profiling/SUMMARY.md) — profiling evidence.

## Two headline findings from Step 1

**1. The qualification → NCO mapping is official.** NCVET's *Report on Mapping of Qualifications with NCO
Codes* (22 Aug 2023) states that every NSQF qualification is required to carry an NCO code, recorded in the
Qualification File Template. There is no separate crosswalk because none is needed — and Annexure VII gives
an official per-awarding-body audit of mapping quality, which becomes our confidence prior rather than an
invented one.

**2. The NCO code encodes whether a qualification exists.** Digits 7–8 of an NCO-2015 code are `00` when no
QP/NOS exists for that job role and `01`–`99` when one does. In our build, 824 of 3,437 occupations carry a
QP/NOS indicator and 2,613 do not.

## Design rules this repository enforces

- **Separate source concepts stay separate.** No giant merged table. `district × occupation × month` is a
  target grain for a *later derived* dataset, never an assumption about any source.
- **Immutable raw.** `acquire()` refuses to overwrite; `make verify` re-hashes against manifests.
- **Missing stays missing.** Nulls are never zero-filled; a vintage the source does not state stays null.
- **Unmapped is retained and counted**, never dropped.
- **Aggregate up, never disaggregate down.**
- **Empty beats wrong.** `location_master` is empty and a test keeps it that way until LGD is acquired —
  populating it from a non-LGD source would silently corrupt every later join.

## Layout

```
config/      sources.yaml (the licence gate) · pilot_scope.yaml
data/raw/    immutable snapshots + committed manifest.json
data/staging/, data/standardized/
mappings/    official/ (extracted GoI artifacts) · project/ · aliases/ · unresolved/
src/lmis/    common · ingest · extract · profile · conform · cli
docs/        verification_report · limitations · taxonomy · data_sources · decisions/ · profiling/
tests/       31 tests incl. immutability, code-structure and anti-fabrication guards
```


## Dashboard and API (Step 7.4)

```bash
make serve     # http://127.0.0.1:8000  — dashboard, and /docs for OpenAPI
```

Read-only. The warehouse connection is opened read-only, and the app computes no
analytical value: every number comes from the warehouse, wrapped in the publication
envelope that `src/lmis/publish/contract.py` produces.

- **Production mode `OPTION_A`** — evidence-qualified demand intelligence.
- **No demand–supply gap, shortage or forecast is published.** Those capabilities are
  served as explicit unavailability — HTTP 200 with `data: null`, a reason code and a
  blocking gate — at `/api/capabilities`. A 404 or an empty array would read as
  "none found" rather than "not computable".
- **`is_measured_shortage` is `false` on every response.** The app refuses to start if
  any envelope says otherwise, or if a published label or UI translation string fails
  the terminology lint (`make lint-terminology`).
- **Outputs B and C are allocation signals, not demand rankings.** Within a state,
  output B's ordering is the Udyam enterprise-share ordering; within a district,
  output C's is the Census-2011 occupation-share ordering. Both render their stored
  caveat directly above the ranking it qualifies.
- The frontend is dependency-free (no Node build step), so the demo runs offline.
