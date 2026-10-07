# Step 1.6 — District-Level Demand Construction Investigation

Date: 2026-10-02 · **Investigation and design only.** No synthetic data was generated. No demand index,
supply index, gap score, forecast, threshold or recommendation was implemented. `location_master` was not
populated. No CAPTCHA, authentication, encryption or access control was bypassed.

Machine-readable probe records: [`probe_results.json`](probe_results.json),
[`datagovin_resource_probe.json`](datagovin_resource_probe.json).

---

## Headline

**District-level analysis can be maintained — but district demand will be ESTIMATED, not OBSERVED.**

Three discoveries this step change the position materially:

1. **A keyless route to LGD district codes exists.** data.gov.in resource pages embed a direct file URL in
   their SSR payload. `lgd_districts.csv` is identified, with an API UUID as a second route. This bypasses
   the LGD CAPTCHA **legitimately** — it is a different, officially published copy, not a circumvention.
2. **A real, daily-updated, district-level signal keyed by LGD codes exists**: district-wise Udyam MSME
   registrations. It is an *establishment* signal, not demand, but it is a defensible allocation basis.
3. **Real district × occupation data exists and we can already decode it.** Census 2011 tables B-24/B-27
   give occupational classification of workers by NCO division/group **to district level**, in **NCO-2004** —
   and we already hold an **OFFICIAL** NCO-2004→NCO-2015 concordance (3,447 rows) built in Step 1.

The honest cost: the only district × occupation evidence is **2011 workforce structure**, and the only
current demand is **state × sector cumulative**. District demand is therefore a *modelled allocation*, and
must be labelled `ESTIMATED` everywhere it appears.

---

## 1. Source evaluation table

| Source | Real/Derived | Time | Geography | Occupation | Signal | Transformation possible | Licence | Role |
|---|---|---|---|---|---|---|---|---|
| **NCS Parliament answers** | **Real observed** | Cumulative since 2015, as-on dated (2024-11-15 verified) | State (58.1% unattributable) | 22 NCS sectors | Vacancies mobilised | **Cumulative → flow** by differencing two dated answers | GoI published | **Demand — the only real current demand** |
| **Udyam district MSME** | **Real observed** | Cumulative, daily updated | **District, LGD-coded** | None | Registered enterprises (micro/small/medium) | Counts → **district shares within state**; counts → per-capita | GODL-India (to confirm) | **Industry/establishment context → allocation basis** |
| **Census 2011 B-24 / B-27** | **Real observed** | **2011 only** | **District** (urban to city) | **NCO-2004 division & group** | Main workers by occupation | NCO-2004 → **NCO-2015 via our OFFICIAL concordance**; counts → occupation shares | ORGI published | **Historical workforce structure → district × occupation allocation basis** |
| **LGD districts (data.gov.in)** | Real observed | Snapshot, monthly | District + state codes | n/a | n/a | n/a | GODL-India (to confirm) | **Geography spine** |
| **NCO-2015 + NCO-2004 concordance** | Real observed (held) | n/a | n/a | NCO-2015, 5 levels | n/a | Already built | GoI | **Occupation spine + version crosswalk** |
| **NQR sectors (59)** | Real observed (held) | n/a | n/a | Sector | n/a | Needs crosswalk to the 22 NCS sectors | GoI | Sector dimension |
| **PLFS** | Real observed (held) | Monthly (national), quarterly (state) | National/state; **district invalid** | NCO-2015 | LFPR/WPR/UR **rates** | Rates as state-level calibration bounds | GoI | **Labour-market context only** |
| **PMKVY district outcomes** | Real observed | As-on 2022-04-21 | District | Scheme training type | Enrolled→certified→placed | Counts → fill/completion/certification rates | GODL-India | Training supply |
| **State employment portals (MH/UP/TN)** | Unverified | Unknown | **District (claimed)** | Unknown | Vacancies | Unknown | **Unknown** | **Lead — potentially real district demand** |
| **e-Shram** | Real, inaccessible | Cumulative | District & occupation published separately | NCO-2015-based, ~400 occupations | Worker registrations | Would give district × occupation supply | — | Worker-supply context |
| **NCS public API** | Real observed | Snapshot | State codes only; `/api/locations` encrypted | Skill keywords | Vacancies **by company** | Title dictionary for mapping input | **Unclear** | Reference |
| **Indeed Hiring Lab** | Real | Daily since 2020 | — | Sector | Postings index | — | CC-BY-4.0 | **Rejected — no India** |
| **Naukri scraped datasets** | Real but unlawfully relicensed | 2019, Oct 2023 | City text | Job titles | Postings | — | **Invalid** | **Rejected — provenance** |
| **DGT / NCVT MIS** | Real, inaccessible | — | — | Trade | Seats/admissions | — | — | Unavailable |

---

## 2. Findings grouped as the brief requires

### A. REAL OBSERVED DATA (acquired and in the repository)
NCO-2015 occupation spine (3,982 nodes) · official NCO-2004→NCO-2015 concordance (3,447) · NQR 59 sectors ·
NCVET mapping-quality audit by awarding body · NCS state × sector cumulative vacancies (4 Parliament
answers) · PLFS bulletins · Census-2011 district candidate list.

### B. REAL DATA THAT CAN BE TRANSFORMED
- **NCS cumulative → flow.** `cumulative(t2) − cumulative(t1)` is valid *only* because both figures measure
  the identical quantity ("vacancies mobilised since inception") on the same portal. Requires collecting
  answers at several as-on dates. Caveat: the 58.1% PAN-India residual must be differenced separately, never
  silently redistributed.
- **Census 2011 NCO-2004 → NCO-2015** through the official concordance already held. Confidence is
  `OFFICIAL` for the code translation itself; the *currency* of the underlying counts is a separate problem.
- **Counts → shares and rates** (district share within state; per working-age population) — standard,
  dimensionless, and what makes heterogeneous signals comparable.

### C. REAL DATA THAT CAN SUPPORT DISTRICT ALLOCATION
| Allocation evidence | What it supports | Why defensible | Weakness |
|---|---|---|---|
| **Udyam MSME district counts** (LGD-coded, daily) | Where *employers* are, by district | Employer presence is the mechanism that generates vacancies | Registrations ≠ hiring; skews to newly formalised firms |
| **Census 2011 B-24/B-27 district × NCO** | District **occupation mix** | Only real district × occupation evidence that exists | 2011 — 15 years stale |
| **Working-age population by district** | Per-capita normalisation | Prevents metro-vs-small-district nonsense | Projection needed post-2011 |
| **PMKVY district training outcomes** | Where training capacity already sits | Real district administrative data | 2022 vintage |

### D. ESTIMATED DATA THAT COULD BE DERIVED (candidate only, not implemented)
A district × occupation × time demand estimate of the form:

```
estimated_demand[district d, occupation o, period t]
    = observed_state_demand[state(d), sector(o), t]      <- OBSERVED (NCS, flow by differencing)
    x district_employer_weight[d, t]                     <- OBSERVED Udyam share within state
    x occupation_mix_weight[d, o]                        <- OBSERVED Census 2011 share, NCO-2015 mapped
```

**Assumptions this makes, each of which must be stated on the output, not buried:**
1. Vacancies distribute across districts in proportion to employer presence.
2. The 2011 occupation mix still approximates today's district occupation structure.
3. The NCS 22-sector vocabulary can be crosswalked to NCO occupation groups — **no such crosswalk exists
   yet**; it would be a PROJECT mapping with a confidence score.
4. The 58.1% PAN-India residual is either excluded or allocated by an explicitly stated rule.

**Uncertainty is multiplicative across three layers**, so the result is a *ranking signal*, not a count.
Validation is possible but only indirectly — e.g. back-testing district rankings against PMKVY district
training uptake, or against state portal vacancy counts if those become accessible. Coverage and confidence
must be attached per cell, and any cell failing the coverage gate returns `INSUFFICIENT_DATA`.

### E. DATA STILL UNAVAILABLE
Current (post-2011) district × occupation structure · any observed district-level vacancy count · occupation-
coded demand of any kind · a demand *flow* without manual multi-snapshot collection · current district × trade
training capacity · e-Shram occupation × district joint extract · DGT/ITI trade × district · confirmation that
PMKVY 4.0 still tracks placement.

---

## 3. Candidate architecture (design only — not implemented)

```
REAL SOURCES
  NCS Parliament answers      Udyam district MSME      Census 2011 B-24/B-27     LGD districts
  (state x sector, cumul.)    (district, LGD-coded)    (district x NCO-2004)     (geography spine)
        |                            |                        |                       |
        v                            v                        v                       v
STANDARDISATION  - parse, type, unit-normalise (lakh vs absolute), record native grain per row
        |
        v
LGD MAPPING      - state name -> LGD state code (NCS API codes already match standard numbering)
                 - district name -> LGD district code via lgd_districts.csv + alias table
                 - Census district code -> LGD district code: CROSSWALK REQUIRED, never equated
        |
        v
NCO MAPPING      - Census NCO-2004 -> NCO-2015  [OFFICIAL concordance, confidence 1.0]
                 - NCS 22 sectors -> NCO groups [PROJECT mapping, does not exist yet, needs confidence]
                 - NQR 59 sectors -> NCO        [per-qualification NCO field, OFFICIAL]
        |
        v
TIME ALIGNMENT   - dim_period; NCS cumulative -> flow by differencing dated snapshots
                 - Census 2011 held as a STATIC structural weight, explicitly flagged as 2011 vintage
        |
        v
REAL DEMAND SIGNALS     [OBSERVED]  state x sector x period flow
        |
        v
DISTRICT ESTIMATION     [ESTIMATED] apply Udyam district weight x Census occupation-mix weight
  - every output row carries: observed_or_estimated, allocation_basis, coverage_score,
    confidence, source_ids, vintage of each input
        |
        v
DISTRICT x OCCUPATION x TIME   [ESTIMATED, labelled]
        |
        v
DEMAND INDEX   <-- NOT IMPLEMENTED. Weights, components and thresholds deferred for review.
```

**Architecture is unchanged from Step 0.** This adds no new tables beyond what Step 0 already specified
(`fact_demand_signal_monthly` holds the observed state-level rows; the estimated district rows belong in a
derived table with `allocated=true`, exactly as Step 0 decision D-02 requires). No data model was modified.

---

## 4. Answers to the final decision questions

1. **Can we maintain district-level analysis?** **Yes — as ESTIMATED district demand**, built from observed
   state demand and observed district allocation evidence, with uncertainty and coverage attached. We cannot
   maintain *observed* district demand; no such public data exists.
2. **Real district-level demand signals found?** **None that is demand.** The real district-level signals
   found are an establishment signal (Udyam, daily, LGD-coded) and a 2011 workforce-structure signal
   (Census B-24/B-27). State employment portals are an unverified lead that may yield real district vacancies.
3. **Additional internet sources found?** Udyam district MSME (×2 resources); LGD districts/states/sub-districts
   via keyless data.gov.in file URLs plus API UUIDs; Census 2011 B-series; AIKosh catalogue; three state
   employment portals. Indeed Hiring Lab and the Naukri datasets were examined and rejected.
4. **Can state demand be defensibly allocated to districts?** **Yes, with documented methodology** — §2D.
   Not with arbitrary percentages: the weights come from observed Udyam district counts and observed Census
   occupation shares, both citable.
5. **What real data supports the allocation?** Udyam district MSME counts (LGD-coded); Census 2011
   district × NCO occupation shares; district working-age population; PMKVY district training outcomes.
6. **Can we obtain district × occupation?** **Yes, but only historical** — Census 2011 B-24/B-27 at NCO-2004
   division/group, translatable via our OFFICIAL concordance. It is workforce structure, never demand.
7. **Which transformations are mathematically valid?** Cumulative→flow by differencing the same measure;
   counts→shares; counts→rates per working-age population; NCO-2004→NCO-2015 via official concordance;
   standardisation of components within occupation and within district. **Not valid:** deriving state × sector
   from two marginal tables; treating Census 2011 as current; redistributing the PAN-India residual without a
   stated rule.
8. **Which outputs would be OBSERVED?** State × sector vacancy flows; district enterprise counts; district ×
   NCO-2004 worker counts (2011); district training outcomes; LGD codes; all master tables.
9. **Which outputs would be ESTIMATED?** District demand; district × occupation demand; any post-2011
   district occupation mix; anything derived from the PAN-India residual.
10. **What is still genuinely unavailable?** §2E.
11. **Is synthetic data actually necessary?** **No — not for the demand pipeline.** A real, defensible
    district × occupation × time *estimate* can be constructed from observed inputs alone. Synthetic data
    would only be needed to demonstrate behaviour that no real source supports at all.
12. **If synthetic data were eventually needed, exactly which fields?** Only these, and only if the user
    chooses to show them: (a) **sub-annual within-year movement** in training supply, since training data is
    annual; (b) **monthly granularity before the first NCS snapshot pair** we can difference; (c) **employer-
    level or posting-level records**, which no accessible source provides; (d) **post-2011 district occupation
    mix**, if we wanted to show drift rather than hold 2011 constant. Everything else can be real or
    real-derived. No synthetic data was generated in this step.

---

## 5. Immediate acquisition dependencies

| Dependency | Exact action | Unblocks |
|---|---|---|
| `lgd_districts.csv` returns **403 from this environment** (DNS resolves; edge/egress block, not a bad URL) | Re-test from the user's network: `https://www.data.gov.in/files/ogdpv2dms/s3fs-public/datafile/lgd_districts.csv` — or use API UUID `37231365-78ba-44d5-ac22-3deec40b9197` with a registered key. Then `lmis drop LGD_DISTRICTS_DATAGOVIN <file>` | `location_master`, every district join |
| Udyam district CSVs — same 403 | Same re-test; URLs in `config/sources.yaml` | District allocation weights |
| Census B-24/B-27 | Download per-state XLSX from the ORGI catalogue | District × occupation structure |
| NCS multi-date answers | Collect further Parliament answers at different as-on dates | Cumulative → flow |
| State portals | Human browser check + terms-of-use review | Possibly real district vacancies |
