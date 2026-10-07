# Limitations

A labour-market tool that states its limits is more useful to a planner than one that does not.
This file is a deliverable, not an appendix. Everything here is a limitation of **Step 1 as built**.

## What this system cannot tell you yet

1. **It cannot tell you how many vacancies exist in a district for a trade.** No accessible official
   source publishes that, and nothing in this repository estimates it. Any such number would be invented.
2. **It cannot produce a demand–supply gap.** No demand signal has been acquired (see below). The index,
   gap, forecast and flag layers are deliberately not implemented in Step 1.
3. **District keys now exist** (`location_master`, 821 rows, Step 1.7) — but the spine is a **2023 snapshot**
   and **125 of 785 districts have no Census-2011 code**, so the Census-based occupation prior can never
   cover 15.9% of districts.

## Acquisition blockers (all verified, none assumed)

| Source | Blocker | Consequence |
|---|---|---|
| ~~**LGD**~~ **RESOLVED in Step 1.7** | `lgdirectory.gov.in` is CAPTCHA-gated, but data.gov.in publishes the same directory and the **apex host** (not `www.`) serves it | `location_master` populated: 36 states, 785 districts. `location_change_event` stays empty — the source publishes no split/merge events |
| **data.gov.in** — partly resolved | Resource pages embed keyless file URLs in their SSR payload; `www.` 403s, apex host serves. **But `PMKVY-210422.csv` returns 404 even on the apex host** | LGD + Udyam acquired; PMKVY district training outcomes still not acquired |
| **NCS** (demand) | Static report page is client-rendered: 0 table rows, 0 NCO codes | **No demand signal acquired at all.** D-04 unresolved |
| **e-Shram** (worker supply) | Dashboard client-rendered: 0 table rows | No worker-registration data acquired |
| **DGT / NCVT MIS** (ITI capacity) | No open trade × district dataset located; `ncvtmis.gov.in` connection timed out | Long-term training capacity unavailable |

**We did not work around any of these by substituting data.** `location_master` being empty is the
correct outcome: populating it from a non-LGD source and treating those keys as LGD codes would reproduce
the free-text-district failure the architecture exists to prevent, and would silently corrupt every later
join. A test (`test_location_master_is_empty_but_correctly_shaped`) enforces this.

## Limitations of what *was* built

- **`occupation_master` covers divisions 1–9 only.** Division 0 (Armed Forces) is absent from the official
  table. Military occupations are therefore out of scope until a separate source is found.
- **11 NCO-2015 codes are duplicated in the official source** (22 rows), including two that straddle a
  pagination boundary and one with a title duplicated inside a single cell. Exact duplicates are collapsed;
  the underlying source defect is recorded, not fixed silently.
- **13 hierarchy nodes carry more than one distinct title** across source rows (e.g. Family `7222`,
  Group `214`). The first title alphabetically is used and `title_variant_count` records the conflict so it
  is visible rather than hidden.
- **`sector_master.ssc_name` and `ssc_code` are entirely NULL.** The NQR listing page does not publish them.
  They are left NULL rather than guessed, which is why profiling flags those columns as >50% null — that
  flag is expected and correct.
- **No occupation ↔ sector bridge exists.** Step 0 specifies a weighted many-to-many bridge; no official
  weighting basis has been verified, so it is not built. Sector-level aggregation is therefore not possible yet.
- **The Census-2011 district candidate set (641 rows) is not a geography spine.** Census 2011 district codes
  are **not** LGD codes and the two are never equated. It sits in `data/staging/` flagged
  `is_authoritative_for_lgd = False`, as a candidate universe for later alias matching only.
- **`dim_period` assumes the training/academic year shares the April–March fiscal boundary.** True for the
  schemes verified so far; recorded in a separate column so a source that differs can override it.
- **DataMeet licence is unresolved**: the GitHub repository declares MIT, the project website states
  CC-BY 2.5 India. This must be settled before any public redistribution of derived geometry.

## Added by Step 1.5 (demand-data investigation)

- **No source provides `date | state | district | occupation | demand` for India.** This was searched for
  across official, open-data, research and commercial routes. See
  [`step1_5_demand_investigation.md`](step1_5_demand_investigation.md).
- **The best real demand data is state × sector, cumulative since inception, and 58.1% of it has no
  geography** ("Multiple States/PAN India" = 20,507,320 of 35,275,833 as on 2024-11-15). State-wise and
  sector-wise are separate marginal tables, so state × sector cannot be derived without assuming
  independence — which would be fabrication.
- **The NCS public API has no vacancy-by-location or vacancy-by-occupation endpoint.** Its
  `/api/locations` response is encrypted. Its terms of use are undocumented, so any published use needs
  DGE confirmation.
- **LGD is CAPTCHA-gated.** Automated download would mean circumventing an access control, so it requires a
  human download (`lmis drop LGD_DIRECTORY <file>`).
- **`api.data.gov.in` is unreachable from this environment**, so the API-key route is **untested**, not
  merely unauthorised. It must be tested from the user's own network before being relied on.
- **Placement may no longer be tracked under PMKVY 4.0.** PIB states placements were tracked for PMKVY
  1.0–3.0 (to FY 2021-22) at 42.8%, and describes a different approach under 4.0. If confirmed, the
  absorption ratio does not exist for current data — which weakens the Step 0 supply index and the
  `SATURATION_RISK` flag. Needs MSDE confirmation.
- **A third sector vocabulary is now in scope**: NCS uses 22 sector categories, which are neither NCO nor
  the NQR 59 sectors. It will need its own documented crosswalk.
- **Third-party Naukri datasets are rejected**, not merely unused: they are third-party scrapes whose CC
  licence is asserted by someone who is not the rights-holder, they cover only software/data roles, and they
  are 2019/2023 snapshots.

## Added by Step 1.6 (district demand construction)

- **District demand will be ESTIMATED, not OBSERVED.** No public source provides an observed district-level
  vacancy count. Any district demand figure this system produces is a modelled allocation of observed
  state-level demand and must carry `observed_or_estimated`, `allocation_basis`, `coverage_score` and
  `confidence` on every row.
- **The only district x occupation evidence is Census 2011** (B-24/B-27, NCO-2004). It is 15 years old. Using
  it as an occupation-mix weight assumes the 2011 district occupation structure still approximates today's -
  an assumption that must be printed on the output, not buried in a method note.
- **Uncertainty is multiplicative** across state demand -> district weight -> occupation weight. The result is
  a ranking signal, not a count, and should never be presented as a number of jobs.
- **No NCS-sector to NCO crosswalk exists.** The NCS 22-sector vocabulary is a third taxonomy; bridging it to
  NCO would be a PROJECT mapping requiring its own methodology and confidence.
- **data.gov.in file URLs are known but returned 403 from the build environment.** DNS resolves, so this is an
  edge/egress block here, not a wrong URL. It must be re-tested from the user's network rather than recorded
  as unavailable.
- **Udyam registrations are not vacancies.** They are enterprise registrations, usable as an allocation basis
  and context only.

## Added by Step 1.7 (source validation)

- **The NCS 22 "sectors" are NIC-2008 industry sections**, verified against the official NIC-2008 document —
  not an occupation classification. An NCS-sector → NCO crosswalk **cannot exist as a function** and must not
  be invented. The defensible route is an empirical `P(occupation | industry, state)` cross-tabulation from
  PLFS, which codes both NIC and NCO-2015.
- **The Udyam "daily updated" catalogue claim is false.** Every row carries `last_updated = 2023-12-21`.
- **Udyam counts registered enterprises, not vacancies, hiring or employment.** `NA` in `small` (30 districts)
  and `medium` (123) is real missingness and must never be zero-filled.
- **Census B-24/B-27 are not acquired.** `censusindia.gov.in` serves an **incomplete TLS certificate chain**
  (missing emSign intermediate). Certificate verification was not disabled; the fix is to supply the
  intermediate or download via a browser.
- **The NCO-2004 → NCO-2015 concordance is one-to-many** in the direction we need, so applying it to Census
  counts needs an explicit splitting rule. Census publishes at division/group level, so the realistic join is
  2- or 3-digit, where ambiguity largely disappears. Not yet decided.
- **The 58.1% PAN-India NCS residual stays a national residual.** No official allocable field exists; the
  category is a real attribute (employer posted nationwide), not missing data. Report
  "41.9% state-attributable" as coverage; never redistribute it in a baseline.
- **State employment portals are gated.** robots.txt permits crawling on two of three, but the vacancy data
  sits behind reCAPTCHA and login. **robots.txt permission is not data availability.** Not pursued.
- **`location_change_event` is empty**, so time series spanning district boundary changes are not yet safe.

## Definitional cautions carried forward from Step 0

These are not yet relevant to any output, because no such data is loaded — but they are the traps that
matter the moment it is:

- Job postings are a **demand signal**, never a vacancy count, and are platform- and urban-biased.
- e-Shram registrations are a **self-declared cumulative stock** — not employment, not labour supply.
- PLFS is a **sample survey with sampling error**, valid at state/national level only.
- `certified` is **potential** supply; placement is **point-of-report** placement, not sustained employment.
- Training capacity (`sanctioned_seats`) ≠ `enrolled` ≠ `trained` ≠ `certified`. These are distinct measures.

## Publication limits enforced in code (Step 7.1 contract, implemented in Step 7.2)

The approved publication contract is `config/publication_contract.yaml`, enforced by
`src/lmis/publish/` and pinned by `tests/test_publication_contract.py`. What it binds:

- **`is_measured_shortage` is `False` on every output and every unavailable capability.** No route, export
  or envelope in the system can return `True`.
- **`NUMERIC_GAP = NOT_IDENTIFIABLE`, `FORECASTING = NOT_SUPPORTED_YET`, `MEASURED_SHORTAGE = false`.**
  Loading a contract that says otherwise raises `ContractError`.
- **16 capabilities are published as explicit unavailability** — numeric gap, forecast, district/state ×
  occupation supply, district/state × trade supply and the rest — each with a reason code and a blocking
  gate, and with `data: None` so none can be read as "none found".
- **Evidence status is read out of each table's own status column, never declared in config.** A derived
  output cannot be published as `OBSERVED` by editing a config file. `demand_national_occupation_composition`
  is `ESTIMATED`; the genuinely `OBSERVED` demand products are `analytical_state_demand` and
  `analytical_demand_by_industry`.
- **Coverage disclosures are derived from `demand_coverage_summary`, not written in code or config** — the
  PAN-India residual share, the state-attributable share and the 138-of-785 district count each exist in
  exactly one place, the warehouse. A test fails the build if any of those literals appears in `src/` or in
  the contract YAML.
- **Terminology is linted.** `shortage`, `deficit`, `skill gap`, `supply gap` and `demand-supply gap` are
  forbidden in any published label; `supply` may not describe a training measure or an occupation-grain
  quantity; an output whose unit is a relative signal may not be labelled with count language. Scope is
  **published labels and interpretations only** — an internal column may legitimately say `vacancy`, which
  is an observed concept the project really holds. Explicitly permitted negations
  (`...NOT_A_VACANCY_COUNT`) are stripped before matching, so the guardrail does not flag itself.
- **Confidence stays categorical.** A numeric or percentage confidence fails the lint.
- **Within-state district ranking is the default.** Cross-state ranking is retained but carries the caveat
  that the NCS state-attributable signal reflects source/registration coverage and is not directly
  comparable absolute labour demand.
- **The Step 7 hybrid quadrant is `EXPERIMENTAL_ONLY` and is not implemented.** Only its publication
  boundary exists, so it cannot enter a production response or export, and promotion needs gates G-5 to G-8
  plus a new ADR.

### Barred from publication

- **`dim_training_trade.nco_mapping_status`** (`UNMAPPED_NO_OFFICIAL_MAPPING`, all 155 rows). It correctly
  describes MSDE Annexure-22, which carries no NCO column, but it is superseded by
  `dim_trade_mapping_status` after the Step 5.2 DGT CTS linkage. The stored value is **barred, not
  rewritten**; publish `dim_trade_mapping_status.mapping_status` instead.

### Corrected in Step 7.2

- **`supply_coverage_summary.trades_mapped_to_nco`** was a hard-coded `0.0` with status `UNMAPPED`, written
  in Step 5.0 before Step 5.2 found the official linkage. It is now derived from `map_trade_to_nco` and
  `dim_trade_mapping_status`, and the summary is built after the tables it summarises. Two new metrics
  accompany it: `trades_officially_mapped_to_nco` and `trades_mapping_unknown`, which reconcile to
  `training_trades_catalogued`. **`MAPPING_UNKNOWN` remains distinct from `MAPPING_DOES_NOT_EXIST`** — no
  trade is asserted to have no possible NCO code.
