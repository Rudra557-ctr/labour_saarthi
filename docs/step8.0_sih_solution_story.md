# LMIS — Labour Market Intelligence System
## SIH 2026 · PS ID 26246 · MSDE — Solution Story

**Every figure in this document was verified against the running repository on 2026-10-06.** Nothing is
projected, rounded up, or claimed from design intent. Where a capability is absent, this document says so.

---

## 1. Executive summary

India's skilling system allocates training targets, sanctions centres and revises NSQF curricula using
labour-market information that sits in disconnected silos — NCS, Udyam, PLFS, Census, scheme MIS, DGT. No
single view combines demand signals with training capacity at district × trade resolution, so mismatches
surface only after placement outcomes are reported, a year or more too late to change a target.

**We built an evidence-first labour-market intelligence platform.** It acquires official Government of India
sources into an immutable, checksummed store; conforms them onto shared NCO-2015 occupation, LGD geography
and period dimensions through confidence-scored mappings; keeps every source in its own fact table at its
native grain; derives transparent demand-intelligence products; and serves them through a FastAPI backend and
an accessible bilingual dashboard where **every number carries its evidence status, confidence, coverage,
vintage and source documents.**

**And it does one thing most submissions to this problem statement will not: it declines to publish a
demand–supply gap, because we proved the available evidence cannot identify one.** That is not a gap in our
work. It is the finding our work produced, and the system publishes the exact dataset that would change it.

| What exists today | Verified |
|---|---|
Official sources registered under a licence gate | **26** (17 URL-verified, 7 existence-verified, 2 unverified) |
Sources acquired as immutable checksummed snapshots | **15 sources, 35 files, 50.5 MB** |
Sources feeding production outputs | **6** — NCS, Udyam, Census 2011 B-24, LGD, PLFS, MSDE Annual Report |
Warehouse | **40 tables, 7 migrations, 82,358 rows** (DuckDB) |
NCO-2015 occupations conformed | **3,982** |
NCO-2004 → NCO-2015 official concordance rows | **3,447** |
LGD geography (36 states + 785 districts) | **821** |
Production analytical outputs | **12** |
Capabilities published as explicitly unavailable | **16**, each with a reason code and an unblocking gate |
API routes | **30** (20 production, 10 blocked) |
Tests | **479**, all passing, across 18 files |
Reproducibility | `make reproduce` — raw snapshots → dashboard, clean |

---

## 2. The problem

PS 26246 asks for an *"AI-Enabled Labour Market Intelligence and Skill Demand–Supply Forecasting Engine"*:
aggregate and normalise fragmented labour-demand signals, compare demand against training supply, forecast
the gap at district and sector granularity, rank severity, raise early warnings, and serve it all through a
dashboard and API with a documented methodology.

The decision this serves is concrete. Before a state sanctions seats for the next cycle, it needs to know
which district × trade combinations are heading for oversupply or shortage. Today that judgement is
retrospective and inertial — last year's targets, plus or minus a little.

## 3. Why existing approaches fail

Three failure modes recur in work on this problem.

**Job-portal scraping.** Richest apparent data, and the least defensible. Postings are not vacancies: they
are re-posted, duplicated across platforms, and structurally biased toward white-collar urban roles while
most blue-collar hiring never appears online. Scraping also breaches terms of service, which disqualifies it
for a government-facing tool.

**Treating a classification as a crosswalk.** NCS publishes vacancies against 22 "sectors". We proved those
sectors are **NIC-2008 industry sections**, not occupations — so no NCS-sector → NCO mapping can exist as a
function. An industry is not an occupation, and any pipeline that silently equates them has fabricated its
occupation axis.

**Filling the gap with an assumption and calling it a model.** The tempting move is to impute the national
trade mix onto every state and subtract. That produces a complete, plausible district × occupation gap
table. It is also **systematically wrong in one direction**: it erases exactly the regional mismatch the
problem statement exists to find, and nothing in the output reveals it.

## 4. The data-fragmentation problem

Six sources feed production. They disagree on nearly every axis:

| Source | Grain | Occupation scheme | Unit | Vintage |
|---|---|---|---|---|
NCS (Parliament answers) | state, NIC section | **none** | vacancies (count / lakh) | 2024-11-15 |
Udyam MSME | district | none | registered enterprises | 2023-12-21 |
Census 2011 B-24 | district × occupation | **NCO-2004** | main workers | **2011** |
LGD | state / district | — | — | monthly-updated directory |
PLFS | **national only** | — | percent | M202504 |
MSDE Annual Report | state × scheme; national × Top-N trade | DGT trades | candidates | as on 2024-03-31 |

**Five vintages spanning fourteen years. Two occupation schemes. Three statistical natures** —
administrative registration, sample survey, decennial census. Not one source carries a district × occupation
vacancy count, which is what the problem statement's finest requirement needs.

## 5. Our architecture

```
OFFICIAL SOURCES (26 registered, licence gate: nothing acquired unless registered)
   │
   ▼  INGESTION — per-source fetcher; legitimate TLS only; no CAPTCHA/auth bypass
RAW STORE — data/raw/<source>/<date>/ + manifest.json (sha256, retrieved_at, licence, status)
   │        IMMUTABLE: a fetch never overwrites an existing snapshot
   ▼  PROFILING — columns, dtypes, nulls, cardinality, value inventories (discover reality first)
STAGING — PDF/HTML/XLSX/DBF → typed tables; Indian number formats; NULL ≠ 0 ≠ '-' ≠ 'NA'
   │
   ▼  CONFORMANCE
   ├─ geography  → LGD codes (821: 36 states + 785 districts) + aliases
   ├─ occupation → NCO-2015 (3,982) via the OFFICIAL NCO-2004 concordance (3,447 rows)
   ├─ industry   → NIC-2008 sections (21)
   └─ period     → dim_period (132)   every mapping carries authority + method + confidence
   │
   ▼  VALIDATION — Pandera contracts + reconciliation to each source's OWN published totals
STANDARDISED FACTS — one table per source-concept at its native grain (never merged)
   │
   ▼  ANALYTICAL LAYER — grain-safe views; OBSERVED vs SUPPORTING separated
DEMAND INTELLIGENCE — 3 estimated products, weakest-link confidence, coverage computed
   │
   ▼  PUBLICATION CONTRACT (config/publication_contract.yaml + src/lmis/publish/)
   │   tier · evidence status READ FROM THE DATA · confidence · coverage · provenance ·
   │   vintage · limitations · is_measured_shortage=false · terminology lint
   ▼
API (30 routes) → DASHBOARD (8 pages, EN/HI, WCAG-AA) + CSV/JSON EXPORT
```

**Why separate fact tables.** A survey estimate, an administrative registration count and a decennial census
stock are different *kinds* of fact. Merging them into one table makes an invalid comparison expressible in
SQL — and therefore inevitable. Keeping them apart means any cross-source claim has to be written
deliberately, in the open, in the derived layer.

**Why master dimensions.** `occupation_master`, `location_master`, `sector_master`, `nic_section_master`,
`dim_period` are the only way two sources can meet. Conforming to them is where the hard work is, and it is
auditable: 3,447 NCO-2004 → NCO-2015 rows carry `authority = OFFICIAL`.

**Why derived analytical datasets.** The place where sources are combined is explicit, versioned,
regenerable from the facts, and never the system of record.

**Why provenance travels.** Every production row carries its source ids, transformation depth and vintage, so
any number on screen can be traced to a named PDF — `LS_UQ2225_2024-12-09.pdf`, `LS_UQ933_2024-12-02.pdf`,
`RS_UQ2798_2024-12-19.pdf` for the NCS baseline.

**Why unsupported joins are rejected.** `geo_level`, `occupation_level` and `period_grain` are stored on every
fact. PLFS carries `district_estimates_valid = FALSE`, so a district PLFS value cannot be produced. Udyam and
Census structures carry `not_a_demand_measure = TRUE`. The contract refuses to publish a SUPPORTING output
whose data does not carry that flag.

## 6. Source normalisation

Each source is a different extraction problem, solved and tested:

- **NCS** — three Parliament answers reporting the *same* as-on date and figures. Recognised as three
  documents describing **one** observation, deduplicated rather than summed.
- **Census 2011 B-24** — a division total and its sub-division detail appear in the same table. An early
  parser double-counted by **1,612,514** workers; a `row_type` classifier fixed it, and every reconciliation
  is now exact.
- **PLFS bulletin** — the printed layout cycles age groups across rows and carries the area label on
  whichever row has it. The parser groups rows in blocks of three; all 81 values match the printed bulletin.
- **MSDE Annual Report** — trade serial numbers restart in each section, so keying on serial alone silently
  dropped 70 of 155 trades. The key is now `(section, serial)`.
- **Udyam / LGD** — `www.data.gov.in` returns 403 for its own file paths while the apex domain serves them.
- **censusindia.gov.in** — serves an incomplete TLS chain. We completed it legitimately from the certificate's
  own AIA URL and kept verification **enabled**. We refused `microdata.gov.in`, which presents a self-signed
  certificate.

**14 of 14 reconciliation checks match each source's own published totals exactly.**

## 7. Taxonomy and geography normalisation

**NCO-2015 is the occupation spine** — the only official Indian occupation classification, ISCO-08 aligned.
3,982 occupations conformed from DGE's own NAT table. Census 2011 is coded in NCO-2004, so it is bridged
through the **official** 3,447-row concordance, and division-level purity is measured and stored rather than
assumed (division 2 = 0.998, division 3 = 0.789, division 8 = 0.805; division X maps to NULL, never to a
guess).

**LGD is the geography spine** — 821 rows. `location_master` was deliberately left empty until a validated
LGD download existed; Census codes of `'000'` became NULL rather than a fabricated code; **125 post-2011
districts correctly have no Census code at all.**

**Official vs project mapping is a structural distinction, not a note.** Every mapping row carries
`authority`. The NCO-2004 concordance is `OFFICIAL`. The NCS-sector → NIC-section alignment is `PROJECT` at
confidence 0.95, and the dashboard says so wherever an industry view appears. **Fuzzy, semantic, embedding and
LLM-generated mappings are prohibited project-wide** — which is why 153 of 155 DGT trades remain
`MAPPING_UNKNOWN` rather than being matched by name resemblance.

## 8. Demand evidence

**OBSERVED** — published counts, attributable to named documents:
- `analytical_state_demand` — NCS vacancies mobilised, cumulative since inception, as on 2024-11-15; 37
  states plus **one PAN-India residual row**.
- `analytical_demand_by_industry` — the same total across 22 NCS sectors / 21 NIC sections.

**ESTIMATED** — derived, labelled, with the method stored on every row:
- **A · national occupation composition** — observed NCS industry totals × an ILOSTAT/PLFS national
  industry × occupation structure. 175 rows; confidence **varies by row** (157 MEDIUM, 18 LOW).
- **B · District Relative Demand Allocation Signal** — state NCS vacancies × Udyam within-state enterprise
  share. 785 districts, MEDIUM.
- **C · District × Occupation Relative Demand Allocation Signal** — B × Census-2011 district occupation
  share. 1,889 rows, **LOW**, usable for 138 districts.

**The industry → occupation bridge was the key find.** NCS has no occupation axis. We located the bridge in
ILOSTAT's `EMP_TEMP_ECO_OCU_NB_A` series for India — whose own source is PLFS — giving an official
`P(NCO division | NIC section)` structure. Output A is **not** a factor in output C: using both would
double-count the occupational signal, and the stored methodology string says so explicitly.

## 9. Supply-evidence investigation

We spent four steps trying to build the supply side, and the negative result is a finding, not a failure.

**What exists:** `fact_training_outcome` — two complete five-measure cascades (enrolled → trained → assessed
→ certified → placed) at **state × scheme**, 350 rows, OBSERVED, reconciling exactly.
`fact_training_infrastructure` — PMKK counts per state, as on 2024-03-31.
`fact_training_trade_outcome` — national × **Top-N** trade, 35 rows, every row flagged `is_top_n_subset`.

**What does not exist, after exhaustive search:** district × trade, state × trade, state × occupation or
district × occupation supply — at any vintage, from any accessible official source. The 17-row
`supply_evidence_matrix` records every source tried and why it failed: the data.gov.in PMKVY district
resource is **ACCESS_PENDING** (needs a registered API key); **NCVT MIS**, the **NQR bulk filter-search** and
the **apprenticeshipindia.gov.in** portal are **UNAVAILABLE**.

**What we found instead, and did not invent:** DGT's own CTS curriculum PDFs carry a `Trade Code` and an
`NCO - 2015` field. That yielded **2 officially mapped trades** — Electrician (DGT/1001) and Fitter
(DGT/1002), `authority = OFFICIAL`, confidence 1.0. **153 remain `MAPPING_UNKNOWN`** — deliberately
distinguished from `MAPPING_DOES_NOT_EXIST`, because we have not acquired a mapping, not proved none exists.

## 10. The identification problem

`SUPPLY[state, trade]` is a **joint distribution**. We hold its row marginals (state totals) plus a
**21.8% fragment** of its column marginals — 514,619 of 2,361,798 PMKVY 4.0 enrolments appear in named Top-10
job roles; **78% sit in job roles the source does not name** — and that fragment comes from a *different
scheme* than the row marginals.

**Row and column marginals never determine an interior.** Closing the system requires assuming
`P(trade | state) = P(trade)`: that every state trains the same trade mix. That assumption is

- **substantively false** — regional trade-mix heterogeneity is the very thing the project exists to measure,
  so assuming it away assumes away the answer; and
- **untestable** — not one `state × trade` cell exists to validate against.

Raking is unavailable too: 78% of the column mass is unnamed.

Independently, **all four candidate subtraction forms fail a unit and time audit.** Demand is a *cumulative
stock of vacancy registrations since inception* at one date; supply is *candidates certified within a scheme
cohort window* closing in 2020. Different units, different temporal types, windows starting in different
years. There is no common result unit.

**This is an identification failure, not an estimation difficulty.** A formula can be written and will return
numbers. Those numbers would restate the assumption, not measure anything.

## 11. Why we deliberately do not fabricate the gap

A fabricated gap would be **more dangerous than no gap**:

1. **The error would be invisible.** A plausible district × occupation gap table looks exactly like data. No
   reader could detect that `P(trade|state) = P(trade)` had been assumed.
2. **The error would be systematic and directional.** Imputing the national mix onto every state erases
   precisely the regional mismatch the PS asks about — telling a planner that every state has the same skill
   profile, the one conclusion guaranteed to be wrong.
3. **It would misdirect real money.** These outputs inform seat sanctioning. A confident wrong ranking moves
   capacity to the wrong districts and withdraws it from the right ones.
4. **It would not survive one question.** *"What is your state × trade source?"* has no answer.

So `is_measured_shortage` is `false` on **every** response in the system, enforced by a database constraint,
a contract validator, a startup check and regression tests. **The application refuses to start** if any
output claims otherwise.

## 12. Current production intelligence

What a planner can legitimately do today:

- **Inspect observed demand evidence** — NCS vacancies by state and by sector, cumulative as on 2024-11-15,
  traceable to three named Parliament answers.
- **See an estimated national occupation composition** across NCO-2015 divisions, with per-row confidence.
- **Compare districts within a state** on a relative demand allocation signal, with its derivation stated
  above the table.
- **Drill to district × NCO division** for the 138 districts with Census structure — and get an explicit
  `NOT_AVAILABLE` with a specific reason for the other 647.
- **Read the training system's own reported outcomes** at state level, by scheme and measure, with `NO_DATA`
  shown as `NO_DATA` and never as zero.
- **See national labour-force context** (PLFS) fenced as context, not demand.
- **See exactly what is not covered** — and exactly which dataset would change that.

## 13. Dashboard and API

**30 routes.** 20 production: contract, sources, methodology, filters, coverage, quality, national industry,
national occupation composition, states, districts, one district, district × occupation, PLFS context, state
training, Top-N trades, capabilities, 3 export routes, health. OpenAPI at `/docs`.

**Two protocol-level guarantees, not UI conventions.** `state` is a **required** parameter on the district
and district × occupation routes, so within-state is the default comparison by construction — an
unparameterised national list would return a cross-state ranking as if it were neutral. And `/demand/states`
**excludes the PAN-India residual by default**, because it is an observation rather than a state and would
otherwise rank first, at 5.2× the largest actual state.

**10 blocked routes** — gap, forecast, four supply grains, shortage, two vacancy-count paths, residual
allocation. Each returns **HTTP 200 with `data: null`**, a reason code and a blocking gate. A 404 or an empty
array would read as *"none found"* rather than *"not computable"*, and that misreading is the one thing the
whole contract exists to prevent.

**8 dashboard pages**, dependency-free (no Node build step, so the demo runs offline): Landing, National,
State, District, Occupation, Methodology, Coverage, Unavailable capabilities.

## 14. Evidence and confidence framework

Four tiers, with **evidence status read from each table's own column — never declared in config**:

| Tier | Meaning | Example |
|---|---|---|
**OBSERVED** | published, attributable to a named document | `analytical_state_demand` |
**ESTIMATED** | derived; method named, transformation depth shown | outputs A, B, C |
**SUPPORTING** | real observed data, explicitly **not** a demand or supply measure | PLFS |
**UNAVAILABLE** | does not exist and cannot currently be computed — with the reason | the 16 capabilities |

**Confidence is ordinal and weakest-link** — the *worst* dimension across source quality, allocation depth,
occupation mapping, temporal compatibility, geography coverage and missingness. Never an average, because
averaging lets a strong term mask a fatal one. **No numeric confidence exists anywhere**; a percentage or
probability fails the lint.

The distinction the interface teaches hardest: *"estimated" means the number exists but was derived;
"unavailable" means it does not exist and cannot currently be computed.* Rendering both as a blank is the
failure mode this framework was built to prevent.

## 15. Coverage transparency

Three disclosures appear wherever the output they qualify appears, and all three are **derived from the
warehouse, never hard-coded** — a test fails the build if those literals appear in source or config:

- **58.13%** of published NCS vacancies are PAN-India / multiple-state and are **not attributed to any state
  or district**.
- **41.87%** are state-attributable — this is the *entire* base of the district signal.
- **138 of 785 districts** have Census occupation structure. Of the rest, **522** belong to states whose B-24
  table is not acquired and **125** are post-2011 districts for which a Census prior **can never exist**.
  Those are different reasons and are reported differently.

**No row anywhere carries a signal of zero.** A district without an occupation prior has no division rows at
all, so a zero cannot be rendered even by accident.

## 16. Scalability

The architecture scales along the axis that matters: **adding evidence, not adding scale.**

Adding a source means registering it in `config/sources.yaml` (the licence gate), writing one conformer to
the existing masters, and adding a Pandera contract. Nothing downstream changes shape. Census B-24 for the
remaining 33 states would lift output C from 138 districts toward 785 **without a single formula change** —
the estimator already handles the full grid and reports per-district status.

DuckDB over Parquet handles the current 82,358 rows in milliseconds and would handle two orders more. The
serving layer is stateless and read-only. `make reproduce` rebuilds everything from checksummed raw snapshots
and verifies them first, so results survive a source going offline mid-competition.

## 17. The future unlock path

The system publishes its own unblocking conditions as **nine objective gates (G-1 … G-9)**. The decisive one:

> **G-1, condition 6: at least one *observed interior cell* of `SUPPLY[geography × trade]`.**

Five other conditions — same time grain, geography, occupation grain, unit and population definition — are
harmonisation problems that better data solves. Condition 6 is why this is an identification failure. **More
of the same marginals never passes it.**

In order of decisiveness: **state × trade (ideally district × trade) training outcomes with complete trade
marginals** → the remaining 153 official trade → NCO mappings → Census B-24 for the other 33 states → **a
second dated NCS snapshot** (the only thing that unlocks any forecast) → NCO-coded NCS vacancies.

Items 1 and 2 are *necessary* for a numeric gap. The rest improve it. Full detail, with the named blocked
sources, is in `docs/step8.0_requirement_mapping.md` §3.

## 18. Impact

**Who:** MSDE scheme planners, state skill development missions, Sector Skill Council analysts, district
planning teams, and reviewers who need to trace a number to its source.

**What they can do today:** inspect official demand evidence with full provenance; compare districts within a
state on a transparent allocation signal; see where occupation detail exists and where it does not; export
any production output with its caveats attached; and **take the missing-evidence register to the ministry
that owns the data** as a specific, costed ask.

**What we do not claim.** No deployment exists, so there are no policy savings, no jobs created, no
efficiency percentages. Any such number would be invented, and inventing one here would contradict the
discipline that is the rest of this submission.

The most useful output may be the least glamorous: a precise statement of **which single dataset MSDE would
need to publish** — state × trade training outcomes with complete marginals — to make the gap it asked for
computable.

## 19. Technical stack

**Verified from `pyproject.toml` and the installed environment.**

| Layer | Technology |
|---|---|
Language | Python 3.14 |
Processing / warehouse | **DuckDB** 1.5 over Parquet, pandas 3.0 |
Extraction | pdfplumber, pypdf, stdlib HTML-table and DBF readers |
Validation | **pandera** contracts + reconciliation to source-published totals |
Orchestration | typer CLI + `make` targets; `make reproduce` is the single entry point |
API | **FastAPI** + uvicorn, auto-generated OpenAPI |
Frontend | **dependency-free** HTML/CSS/JS — no Node build step, runs offline |
Contract enforcement | `config/publication_contract.yaml` + `src/lmis/publish/` |
Testing | pytest — **479 tests, 18 files** |

**There is no machine-learning model in production, and no ML library is installed.** That is a deliberate
statement, not an omission — see §20.

## 20. Where AI/ML fits, honestly

The problem statement is titled *"AI-Enabled"*. We will not invent a model to match a title.

**What the system does today is data engineering and statistical reasoning, not machine learning:** source
acquisition under a licence gate, PDF and HTML extraction, taxonomy and geography conformance, contract
validation, deterministic signal construction, weakest-link confidence, and a publication contract enforced
in code. **No model is trained, no model is scored, no prediction is made.** Verified: no scikit-learn,
LightGBM, XGBoost, PyTorch, TensorFlow, statsmodels or statsforecast is installed, and no model code exists
in `src/` or `api/`.

**Where ML becomes appropriate, and what each needs first:**

| Future capability | Blocked on |
|---|---|
Demand forecasting (baselines → pooled global model, rolling-origin backtest) | **≥2 dated NCS observations.** One point cannot support a trend |
Early-warning / anomaly detection | the same temporal evidence, plus a validated indicator |
AI-assisted seat-allocation recommendations | a defensible gap, which needs G-1 |
Grounded LLM query interface over the analytical database | nothing — but it must run over **fixed parameterised queries, read-only, answers grounded in returned rows with their provenance**. Free-form text-to-SQL is rejected: hallucination risk is unacceptable in a government planning tool |

**The honest position:** the hard part of this problem is not model selection. It is making heterogeneous
official evidence comparable without fabricating the comparison — and establishing, rigorously, what cannot
yet be computed. That is what we built, and it is the prerequisite for any model that follows.

## 21. Defensible innovation

Not "novel AI" — these are the things we believe are genuinely uncommon:

1. **Identification-aware analytics.** The system distinguishes *"we have not got this data"* from *"this
   quantity is not identifiable from evidence of this shape"*, and treats the second as a mathematical result
   rather than a backlog item.
2. **A publication contract enforced in code.** `config/publication_contract.yaml` plus `src/lmis/publish/`
   make evidence status, confidence, coverage, provenance and prohibited interpretations part of the response
   contract — and the app **refuses to start** on a breach.
3. **A terminology lint over the published surface.** Reserved words, forbidden ranking phrasings and
   corroboration framings fail the build — including in **translation files**, with negation detection so the
   product can still say *"this is not a vacancy count"*.
4. **Evidence status read from the data, never declared.** A derived output cannot be relabelled OBSERVED by
   editing a config file. A test forges a lying config and proves the envelope still reports ESTIMATED.
5. **Caveats that are data, not prose.** Outputs B and C store their own derivation caveats as columns, and
   the contract refuses to build an envelope if a caveat is missing — so the UI cannot drift from the data.
6. **Arithmetic self-criticism.** We measured that within a state, output B's ordering **is** the Udyam
   enterprise-share ordering (0 of 36 states differ), and within a district, output C's **is** the Census
   occupation-share ordering (0 of 138 differ). Rather than hide that, the UI prints it above every ranking —
   and the occupation view promotes the *one* comparison that restates neither input (districts within a
   state × division, which differs from both inputs in 27 of 27 groups).
7. **Full reproducibility from immutable snapshots.** sha256-verified raw store, append-only facts,
   `make reproduce` from bytes to dashboard.

## 22. Limitations, stated plainly

1. **No numeric demand–supply gap**, at any grain. Not identifiable.
2. **No forecast.** One dated demand observation.
3. **No occupation-level or trade-level supply quantity**, anywhere.
4. **Outputs B and C are relative allocation signals, not demand or vacancy rankings.** Within a state, B's
   ordering is Udyam enterprise share; within a district, C's is Census-2011 occupation share.
5. **Output C covers 138 of 785 districts and 3 of 36 states**, at LOW confidence.
6. **The district demand base is 41.87%** of published NCS vacancies; the 58.13% residual is never allocated.
7. **Census occupational structure is 2011** — fourteen years before the demand baseline.
8. **2 of 155 DGT trades are officially NCO-mapped.**
9. **PLFS is national only** and is not a demand measure.
10. **The hybrid pressure indicator is designed but not implemented**, because its classification flips
    depending on which training scheme is read (cross-scheme rank correlation **+0.005**).
11. **No ML model in production.**
12. **No map component yet** — tables are the only representation, which is also why nothing is unreachable
    without a map.
13. **No deployment, so no outcome evidence.**
14. **Hindi is partial** (21 of 106 keys), falling back to English rather than machine-translating official
    occupational terminology.

## 23. Conclusion

The problem statement asks for a demand–supply gap forecasting engine. We built the platform that such an
engine requires — conformed official evidence, provenance-aware products, a contract that cannot be
accidentally overstated, a dashboard and API — and then we did the part that takes more discipline than
building it: **we established that the gap is not currently identifiable, published the reason, and published
the exact evidence that would change it.**

A system that answers *"we don't know, here is why, and here is what would tell us"* is more useful to a
planner than one that answers confidently and wrongly. Everything here is reproducible from checksummed raw
bytes with one command, and **479 tests** exist to stop the claims from quietly growing.
