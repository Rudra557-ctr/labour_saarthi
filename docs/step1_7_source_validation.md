# Step 1.7 — District Data Source Validation

Date: 2026-10-02 · **Validation only.** No estimator, no demand index, no forecast, no API, no dashboard,
no synthetic data. No CAPTCHA, authentication, access control, encryption or robots restriction was bypassed.

Probe records: [`probe_results.json`](probe_results.json) · [`datagovin_resource_probe.json`](datagovin_resource_probe.json)

---

## Headline

**The geography blocker is resolved and `location_master` is now populated with validated official LGD data
(36 states/UTs, 785 districts).** District-level analysis is no longer gated on acquisition.

The decisive technical detail: `www.data.gov.in` returns **HTTP 403** for its own file paths, but the **apex
host `data.gov.in` serves them**. Everything that was "blocked" in Step 1.6 was one hostname away.

Two findings cut the other way, and both matter:

- **The NCS 22 "sectors" are an *industry* classification, not an occupation one.** Verified against the
  official NIC-2008 document: all 20 substantive NCS sector names align one-to-one with NIC-2008 sections
  A–T. So an NCS-sector → NCO crosswalk **cannot exist as a function**, and none should be built.
- **The Udyam catalogue claim is wrong.** It is advertised as "daily updated"; every row carries
  `last_updated = 2023-12-21`. It is a snapshot.

---

## 1. Evidence matrix

| Field | LGD states/districts | Udyam district MSME | Census B-24/B-27 | PLFS | NCS Parliament answers | State portals |
|---|---|---|---|---|---|---|
| **Publisher** | Ministry of Panchayati Raj (via NIC/data.gov.in) | Ministry of MSME | ORGI, Census of India | NSO, MoSPI | Ministry of Labour & Employment | State Directorates of Employment |
| **Resource ID** | `lgd_states.csv`, `lgd_districts.csv`, `lgd_subdistricts.csv`; UUIDs `a71e60f0…`, `37231365…`, `6be51a29…` | `district_level_total_Registered_msme.csv`, `district_level_service_msme.csv`; UUIDs `f8cd85a1…`, `c3dfe7e6…` | NADA catalog (e.g. 13918) | monthly/quarterly bulletins | `2798_e.pdf`, `933_e.pdf`, `2225_e.pdf`, `1264_e.pdf` | rojgar.mahaswayam.gov.in, rojgaarsangam.up.gov.in, tnvelaivaaippu.gov.in |
| **Data type** | Administrative directory | Administrative register | Census full count | Sample survey | Administrative portal counts | Portal listings |
| **Geography** | **State (36), District (785)**, sub-district | **District, LGD-keyed** | **District** (urban to city) | National / **state**; district invalid | State; 58.1% PAN-India | District (claimed) |
| **Time coverage** | Snapshot **2023-11-30 / 2023-12-01** | Snapshot **2023-12-21** | **2011** | Monthly (national), quarterly (state) | Cumulative since 2015, as-on dated | Live listings |
| **Occupation coding** | n/a | **none** | **NCO-2004** division & group | **NCO-2015** | none | unknown |
| **Sector coding** | n/a | size class (micro/small/medium) | — | NIC | **NIC-2008 sections (verified)** | unknown |
| **Units** | codes/names | enterprise counts | person counts | rates (%) + counts | vacancy counts (absolute / lakh) | listings |
| **Update frequency** | mirror static; LGD monthly | **claimed daily, actually a snapshot** | decennial | monthly/quarterly | per question | continuous |
| **Official/third-party** | Official | Official | Official | Official | Official | Official |
| **Observed vs supporting** | **Reference spine** | **Supporting/structural** | **Supporting/structural** | **Supporting/structural** | **Observed demand** | unknown |
| **Potential use** | Geography spine + Census crosswalk | District allocation weight | District × occupation prior | Newer state occupation prior; calibration | Only real demand | Possible district demand |
| **Limitations** | 2-yr-old snapshot; **125/785 districts lack Census code**; no change events | Not demand; snapshot; `NA` in small/medium | **15 years old**; NCO-2004 | **district invalid**; rates not counts | cumulative; marginals only; no occupation | login/CAPTCHA |
| **Licence/access** | GODL-India (to confirm); **apex host works** | GODL-India (to confirm) | ORGI; **TLS chain broken** | GoI | GoI | **gated** |
| **Validation status** | **VALIDATED — in use** | **VALIDATED — not yet used** | **DOCUMENTED, not acquired** | **DOCUMENTED** | VALIDATED (Step 1.5) | **REJECTED for automated access** |

---

## 2. Answers to the final decision questions

### A. Can LGD now be safely used as the geography spine? **Yes — and it is.**

Validated before use: 36 states/UTs (28 S + 8 U), 785 districts, codes unique at both tiers, all 36 states
present in the district file, full referential integrity, and an official `district_census2011_code` crosswalk.
`location_master` holds **821 rows**. Three restraints applied: no synthesised NATIONAL row,
`location_change_event` left empty (the source publishes none), `stable_district_group_id` left NULL.

Caveats carried **on the rows**: `valid_from` = 2023-11-30/2023-12-01 so the snapshot's age is visible, and
`census_2011_code` is NULL for the 125 districts that post-date 2011.

### B. Can Udyam legitimately be used as a district allocation/supporting signal? **Yes, with a hard caveat.**

It joins **785/785 — a clean 100%** — to `location_master`. It is genuinely district-level and genuinely
LGD-keyed. Two resources confirmed: **total** registered MSMEs and **services**; a manufacturing resource also
exists. Fields: `state_name, lg_dist_code, district_name, micro, small, medium, total, last_updated`.

**What it cannot be interpreted as:** labour demand, vacancies, hiring, employment, or anything about
*people*. It counts **registered enterprises**, cumulatively. A district with many registrations may simply
have formalised earlier. `NA` appears in `small` (30 districts) and `medium` (123) — real missingness that
must never be zero-filled. And the "daily updated" claim is false: it is a 2023-12-21 snapshot.

Legitimate use: an evidence-based **district weight** for allocating state-level demand, and a context
feature. Nothing more.

### C. Can Census B-24/B-27 provide the district × occupation prior? **In principle yes; not acquired.**

B-24/B-27 give occupational classification of main workers by **NCO-2004 division and group down to district
level**. Acquisition failed here for a specific, diagnosable reason: **censusindia.gov.in serves an incomplete
TLS certificate chain** — it omits the emSign intermediate CA, so strict clients cannot verify it
(`unable to get local issuer certificate`; subject `CN=censusindia.gov.in`, issuer `emSign SSL CA - G1`).
Browsers usually succeed by fetching the missing intermediate; `requests` does not. **I did not disable
certificate verification.** The fix is to supply the intermediate to the trust store, or download in a browser
— both legitimate; neither is a bypass.

**Known ceiling before we even start:** only **660 of 785 districts (84.1%)** have a Census-2011 code, so
15.9% of districts can never receive a Census-based occupation prior. Tamil Nadu loses 6 of 38 districts.

**Concordance shape** — important and not yet resolved: our `map_nco2004_to_nco2015` has 3,447 rows covering
2,685 non-null NCO-2004 codes, so it is **not one-to-one**. Multiple NCO-2015 occupations can share one
NCO-2004 code, making it **one-to-many in the direction we need** (2004 → 2015). Applying it to counts
therefore requires an explicit splitting rule, which would itself be an assumption. Census tables are
published at **division/group** level anyway, which is coarser than the 8-digit codes the concordance keys on
— so the realistic join is at **2-digit or 3-digit** level, where ambiguity largely disappears. No mapping was
performed.

### D. Is there a newer source that can improve the occupation prior? **Yes — PLFS, at state level only.**

PLFS codes occupation in **NCO-2015** and is current (monthly national, quarterly state). It is the only
newer occupation-structure evidence found. It **cannot** provide a district prior — district estimates are
not statistically valid — so its role is to **update and validate the *state* occupation mix** and to act as a
calibration bound on anything derived from Census 2011. Classification: **SUPPORTING/STRUCTURAL**, never demand.

e-Shram would have been the other candidate (NCO-2015-based, ~400 occupations, district and occupation both
published). Its data.gov.in resource pages returned no datafile URL in the SSR payload, so it remains
**UNAVAILABLE**. It publishes occupation-wise and state-wise **separately**, so even if acquired it may not
give the joint occupation × district table needed.

### E. Is an NCS-sector → NCO mapping available officially? **No — and it cannot be, as a function.**

Verified against the official NIC-2008 document (193 pages, acquired): the NCS sector list is the
**NIC-2008 section list**. All 20 substantive categories align one-to-one:

| NCS sector | NIC-2008 section | | NCS sector | NIC-2008 section |
|---|---|---|---|---|
| Agriculture and Related | A | | Information & Communication (IT and Communication) | J |
| Mining And Quarrying | B | | Finance and Insurance | K |
| Manufacturing | C | | Real Estate Activities | L |
| Power and Energy | D | | Specialized Professional Services | M |
| Water Supply, Sewerage and Waste Management | E | | Operations and Support | N |
| Civil and Construction Works | F | | Public Administration and Defense | O |
| Wholesale and Retail | G | | Education | P |
| Transportation and Storage | H | | Health | Q |
| Hotels, Food Service and Catering | I | | Arts and Entertainment | R |
| Other Service Activities | S | | Household and Domestic Work | T |

**Industry is not occupation.** A welder works in manufacturing, construction *and* mining; manufacturing
employs welders, accountants, drivers and cleaners. The relationship is inherently many-to-many, so no
official crosswalk exists and **none should be invented**.

### F. Most defensible way to create a project mapping later

**Not a crosswalk — an empirical cross-tabulation.** Use a source that observes **both** industry and
occupation for the same workers, and estimate the conditional distribution
`P(occupation | industry, state)` from it.

- **Preferred: PLFS.** It codes both NIC and NCO-2015, it is current, and it is valid at state level — which
  is exactly the level at which the NCS demand data is observed. Industry → occupation shares estimated from
  PLFS would be real, recent and official.
- **Secondary: Census B-series**, which has both industry and occupation tables, for district-level texture.
- **Ambiguous sectors that must NOT be mapped automatically:** `Sector Not Specified` (no information at all),
  `Operations and Support` (NIC N spans clerical, security, cleaning, call-centre and travel occupations),
  `Other Service Activities` (NIC S is residual by construction), `Specialized Professional Services` (NIC M
  spans legal, accounting, architecture, R&D, advertising, veterinary), and `Household and Domestic Work`
  (NIC T, largely informal and under-captured). These should either be left unallocated or carried as an
  explicit residual.
- **Confidence recording:** every row would carry `authority='PROJECT'`, `method='PLFS_CROSSTAB'`, the
  source vintage, the **sample size behind the cell**, and a confidence derived from that sample size —
  low-n cells flagged rather than used. Plus the existing Step 0 fields `coverage_score` and
  `observed_or_estimated`.

**No mapping was created in this step.**

### G. What should happen to the 58.1% PAN-India NCS residual? **Keep it as a separate national residual.**

No official documentation of an allocable field was found. The category means what it says: employers posted
for multiple states or nationwide. That is **a real attribute of the vacancy, not missing data** — the
employer declined to localise it.

Recommended treatment: store with `geo_level='NATIONAL'` and a `pan_india_residual` flag; never redistribute
it in the baseline; report `41.9% of vacancies are state-attributable` as a headline coverage statistic so no
one mistakes the state table for the whole market. If sensitivity analysis is wanted later, allocate it in a
**clearly labelled scenario only**, never as the default. **No allocation percentages were invented.**

### H. Do Mahaswayam / Rojgar Sangam provide additional district demand evidence? **No — not accessibly.**

I checked `robots.txt` first on all three.

| Portal | robots.txt | Public data | Verdict |
|---|---|---|---|
| Mahaswayam (MH) | `User-agent: * / Disallow:` (permits) | **Google reCAPTCHA** + login/registration; no datasets, no public API | **Gated — not pursued** |
| Rojgar Sangam (UP) | permits main site, disallows dev/beta hosts | login required; no datasets, no API refs | **Gated — not pursued** |
| TN Velaivaaippu | 404 (no policy served) | no datasets; points to `tamilnaducareerservices.tn.gov.in` | **Not pursued** |

Crucially, **robots.txt permitting crawling is not the same as the data being publicly available.** The
vacancy data sits behind CAPTCHA and authentication, which I will not bypass. These remain a manual,
human-browser lead, and a formal data request to the state directorates is the realistic route.

### I. Unresolved evidence issues before Step 2

1. **Census B-24/B-27 not acquired** — blocked by the broken TLS chain. Fix the trust chain or download manually.
2. **The 2004 → 2015 concordance is one-to-many**; the join level (2-digit vs 3-digit) must be decided on evidence.
3. **15.9% of districts have no Census-2011 code** — a permanent coverage ceiling on the Census prior.
4. **No industry → occupation cross-tabulation built yet**; PLFS unit-level or published cross-tabs needed.
5. **PLFS state occupation distribution not yet acquired** in tabular form.
6. **Udyam is a 2023 snapshot, not a daily feed** — a refresh path is needed if recency is claimed.
7. **LGD mirror is ~2 years stale**; LGD updates monthly.
8. **`location_change_event` is empty** — district splits/merges are not yet modelled, so time series across
   boundary changes remain unsafe.
9. **Licences unconfirmed** — GODL-India assumed for data.gov.in resources, not verified per resource.
10. **e-Shram occupation × district still unavailable.**
11. **PMKVY district outcomes still not acquired** (`PMKVY-210422.csv` returned 404 even on the apex host).
12. **PMKVY 4.0 placement tracking** still unconfirmed, so the absorption ratio may not exist for current data.
