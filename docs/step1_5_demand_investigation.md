# Step 1.5 — Real Labour-Demand and Geography Data Investigation

Date: 2026-10-02 · **Investigation only.** No synthetic data was generated, no index, forecast, gap score
or model was built, and `location_master` was not populated.

Every verdict below rests on a direct HTTP request or a PDF extraction performed during this step.
Raw probe output: [`probe_results.json`](probe_results.json).

---

## Headline answer

**Situation C applies, close to the D boundary: real official demand data exists, but only at
state × sector granularity, as a cumulative stock, with 58% of it not attributable to any state.**

No source was found — government or otherwise — that provides
`date | state | district | occupation | demand` for India.

---

## 1. Source evaluation table

| Source | Real demand? | Time coverage | Geography | Occupation | Demand measure | Access | Licence | Usable? |
|---|---|---|---|---|---|---|---|---|
| **NCS Parliament answers** (`dge.gov.in`) | **Yes** | Cumulative since 2015 inception, as-on a stated date (verified: 2024-11-15) | **State** (39 rows); 58.1% booked to "Multiple States/PAN India" | **No** — 22 NCS sector categories only, not NCO | Vacancies mobilised (cumulative count) | PDF, direct download | GoI/Parliament published | **VERIFIED — best available. Insufficient granularity for district × occupation** |
| **NCS public API** (`api.ncs.gov.in`) | Partly | Snapshot / `year` param | State list with codes; district list **encrypted** | Skill/title keyword dictionary, no NCO | `totalVacancies` **by company only** | Public unauthenticated JSON | **LICENCE UNCLEAR** — no published terms, no API spec | **PARTIALLY VERIFIED — no location × occupation demand endpoint exists** |
| **NCS static report page** | Unknown | — | — | — | — | Client-rendered SPA: 0 table rows | — | **UNAVAILABLE** |
| **data.gov.in** (NCS state-wise, PMKVY district, LGD mirrors) | Some | PMKVY as-on 2022-04-21 | District (PMKVY) | Scheme training-type only | Trained/certified/placed counts | **API key required; `api.data.gov.in` unreachable from this network** | GODL-India (per resource, unconfirmed) | **UNAVAILABLE — untested, blocked on key** |
| **Indeed Hiring Lab** (`github.com/hiring-lab/*`) | Yes, for covered markets | Daily since Feb 2020 | — | Sector | Index (% change vs 2020-02-01) | GitHub, open | CC-BY-4.0 | **REJECTED — India is not covered.** All 6 repos checked; markets are AU CA DE EA ES FR GB IE IT NL US |
| **e-Shram** | No (supply, not demand) | Cumulative snapshot | State/district published separately | NCO-2015-based, ~400 occupations | Worker registrations | Client-rendered: 0 table rows | — | **UNAVAILABLE** |
| **Naukri datasets** (Kaggle / HuggingFace) | Yes, nominally | 2019 and Oct 2023 snapshots | City/location text | Job titles | Posting records | Direct download | CC BY-NC 4.0 **asserted by an uploader who scraped a third-party site** | **REJECTED** — see §4 |
| **Apify / CrawlFeeds scrapers** | Yes | Live | City | Job title | Postings | Commercial scraping service | Scraping of protected job boards | **REJECTED** — ToS and provenance |
| **PMKVY / PIB decade document** | No (training supply) | To 2025-07-11 | **National only** | None | Candidates trained | PDF | GoI | **INSUFFICIENT GRANULARITY** |
| **MSDE annexures / eparlib** | No (training supply) | 2024–2025 | Possibly state | Sector | Trained counts | `msde.gov.in` annexure **404**; `eparlib.sansad.in` **timed out at 545 s** | GoI | **UNAVAILABLE this session** |
| **DGT / NCVT MIS** | No (training capacity) | — | — | Trade | Seats/admissions | `ncvtmis.gov.in` connection timeout | — | **UNAVAILABLE** |
| **LGD** (geography) | n/a | Monthly updates | State/district/sub-district | n/a | n/a | **CAPTCHA-gated form** | GoI | **VERIFIED TO EXIST — manual human download required** |
| **PLFS** | **No — context only** | Monthly (national), quarterly (state) | National / state; **district invalid** | NCO-2015 | Employment/unemployment **rates**, not vacancies | PDF | GoI | **VERIFIED as context, must never be called demand** |

---

## 2. The best real demand source, in detail

**NCS vacancy statistics published in Parliament answers.** Four PDFs acquired with checksummed manifests
at `data/raw/NCS_PARLIAMENTARY_ANSWERS/2026-10-02/`.

**Exact fields available** (per answer): a gender-wise table (5 categories, in lakh); a **state-wise** table
(39 states/UTs, absolute counts); a **sector-wise** table (22 NCS sector categories, in lakh).

**Reconciliation passed.** The 39 state rows sum to exactly **35,275,833**, matching the published grand
total as on 2024-11-15. The extraction is therefore trustworthy.

**Five verified limitations — each disqualifying for a different reason:**

1. **It is a stock, not a flow.** The measure is "vacancies mobilised **since inception**". A monthly or
   quarterly flow can only be obtained by differencing two dated snapshots, which requires collecting many
   answers at different as-on dates.
2. **58.1% has no geography.** `Multiple States/PAN India = 20,507,320` of 35,275,833. Only **41.9%** is
   state-attributable. Any state-level analysis silently discards the majority of the data.
3. **No joint cross-tabulation.** State-wise and sector-wise are **separate marginal tables**. State × sector
   cannot be derived from them — attempting it would require assuming independence, which would be
   fabrication.
4. **No district, no occupation, no NCO code, no within-document time series.**
5. **Units differ between tables** (absolute for state, lakh for sector).

---

## 3. NCS API investigation (§2 of the brief)

The Step 1 finding — HTTP 200, 0 rows, 0 NCO codes — was correctly *not* treated as proof that NCS has no
data. Re-investigation found that `ncs.gov.in` is an **Angular SPA** and located a real public API host.

**Method, stated plainly:** I read the public unauthenticated homepage, extracted the API URLs it references,
fetched its 39 JS bundles and its Angular SSR state block, and called **only** the endpoints the public page
itself calls. No authentication was used, attempted or bypassed; no credentials; no access control
circumvented; no rate-limit evasion.

**Endpoints found on the public surface:**

| Endpoint | Result | Use to us |
|---|---|---|
| `/api/location/state` | **200** — 39 states with `stateCode` (Bihar 10, Maharashtra 27, Tamil Nadu 33 — standard Indian state numbering) | Useful for the state tier of geography; **not** a substitute for LGD district codes |
| `/employer-service/api/v1/hiring/top-companies?year=&limit=` | **200** — real `totalVacancies` per company (Apna 27,913; Swiggy 13,100 …) | Real demand, but **by employer only** — no location, occupation or date |
| `/api/jobseeker/profiles/career-timeline/get-skills?keyword=` | **200** — `{id, keyword}` job-title/skill dictionary | Input for future title→NCO mapping; **not** demand |
| `/api/locations` | **200 but the payload is encrypted** (opaque ciphertext) | **Unusable** — the district list cannot be read |

**No job-search, vacancy-by-location or vacancy-by-occupation endpoint exists on this public surface.**
No public API specification is published (`/v3/api-docs` → 500, `/openapi.json` → 401, `/swagger-ui` → 401;
`/actuator/health` → 200 confirms a Spring Boot service). Because the surface is undocumented, **terms of
use are UNCLEAR** and must be confirmed with DGE before any published or production use. Registered as
`NCS_API_PUBLIC` with that caveat recorded.

---

## 4. Why the Naukri datasets are rejected

Traced back as the brief requires, rather than accepted because they sit on an aggregator.

- **Provenance:** each is a **scrape of Naukri.com by a third party**, not a release by Naukri or any public
  body. The CC BY-NC 4.0 licence is asserted by the uploader, who is not the rights-holder in the underlying
  listings. A licence someone grants over data they scraped from a site that prohibits scraping does not make
  redistribution lawful.
- **Coverage:** the best-licensed one covers **only Software Engineers and Data Scientists** — useless for
  welders, nurses or machinists.
- **Currency:** snapshots from **2019** and **Oct 2023**. Not a current demand signal.
- **Non-commercial clause** would additionally constrain any downstream government use.

**Verdict: REJECTED on provenance, coverage and currency independently.** Live scraping services (Apify,
CrawlFeeds) are rejected for the same provenance reason plus the explicit instruction not to scrape
protected sites.

---

## 5. Geography / LGD — the blocker is now precisely identified

`lgdirectory.gov.in/downloadDirectory.do` carries a **CAPTCHA** (`/js/captcha.js`, `refreshCaptcha('captchaImageId')`).
Earlier "Session Time Out" responses were the symptom; the CAPTCHA is the cause. **Solving it
programmatically would be circumventing an access control, so we will not.**

This is now an actionable, not a mysterious, blocker. The exact resource is identified from the form itself:

- `DDOption=DFD`, `downloadOption=allDistrictofIndia` → **all districts of India**
- other options: `allStateofIndia`, `allSubDistrictofIndia`, `districtofSpecificState@state`, and per-state variants
- update cadence: monthly (1st of each month)

**Enabling path built this step:** `lmis drop LGD_DIRECTORY <file>` registers a human-downloaded file with
the same sha256-checksummed manifest an automated acquisition gets. One manual download unblocks
`location_master` without weakening provenance.

`staging/census2011_district_candidates` **remains a candidate reference set only**, flagged
`is_authoritative_for_lgd = False`, and `location_master` is still empty and still guarded by a test.

**Mapping demand geography to LGD:** the only demand data found is state-level, and the NCS API's state
codes already match standard Indian state numbering, so state→LGD is straightforward once LGD states are
loaded. City/district/postal-code mapping is **moot for now** because no sub-state demand data was found —
that work should not be built speculatively.

---

## 6. Current vs historical classification (§6 of the brief)

| Source | Correct classification | Must never be called |
|---|---|---|
| NCS vacancies mobilised | **demand signal** (cumulative stock) | a monthly flow, or a district figure |
| NCS top-companies vacancies | **demand signal** (employer-level) | a location or occupation signal |
| PLFS | **labour-market/employment context**, with sampling error | vacancy demand; district-valid |
| Census occupational counts | **historical workforce structure** | current job demand |
| e-Shram registrations | **self-declared cumulative worker-registration stock** | employment, or labour supply |
| PMKVY / DGT | **training supply, capacity and outcomes** | demand |

## 7. Training / supply findings

The brief's training-supply search produced one materially important verified finding, from the PIB
10-year PMKVY document (acquired, 7 pages):

> "Placements were tracked under Short Term Training (STT) component of PMKVY in the first three versions …
> PMKVY 1.0, 2.0 and 3.0 implemented from FY 2015-16 to FY 2021-22. The reported placement rate in STT
> certified candidates till PMKVY 3.0 was 42.8%. **Under PMKVY 4.0, the focus is to empower trained
> candidates to choose their varied career path** …"

**Placement appears to no longer be tracked under PMKVY 4.0.** If confirmed, the absorption ratio
(placed/certified) — a central component of the Step 0 supply index and of the `SATURATION_RISK` flag —
**does not exist for current data**, and 42.8% (national, to FY 2021-22) is the last published figure.
This needs confirmation with MSDE and is now a first-order open question.

Otherwise: the PIB document is national-only with no district or trade tables; the MSDE annexure URL
returned 404; `eparlib.sansad.in` timed out; `ncvtmis.gov.in` timed out. **No current district × trade
training dataset was obtained.**

## 8. NCO mapping (§8 of the brief)

No new demand source provides NCO codes, so no mapping was built. What this step *did* establish:

- The NCS **sector** vocabulary (22 categories) is **neither NCO nor the NQR 59-sector list**. A third
  sector vocabulary now exists in scope and will need its own documented crosswalk.
- The NCS **skills keyword dictionary** (`{id, keyword}`) is a genuine candidate input for a future
  title→NCO cascade, since it is the vocabulary NCS itself uses.
- The official method for title→NCO already exists and is documented: NCVET's Annexure IX handbook
  (Downward and Upward Assignment). Any project mapping should follow that published method rather than
  invent one — and must be labelled `authority='PROJECT'` with a confidence score regardless.

No mapping was created. No keyword matching was passed off as authoritative.
