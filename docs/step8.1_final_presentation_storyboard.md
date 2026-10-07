# Final Presentation Storyboard — LMIS · SIH 2026 · PS 26246

**12 slides. Every number verified against the repository on 2026-10-06.**

**The narrative arc, one line per beat:**
`FRAGMENTED DATA → STANDARDISATION → EVIDENCE QUALIFICATION → ANALYTICAL SIGNALS → PUBLICATION-SAFE PRODUCT → FUTURE DATA UNLOCK`

**The sentence the whole deck exists to earn:**
> *We did not manufacture the missing number. We built the infrastructure that tells decision-makers what the evidence actually supports — and exactly what evidence is required to go further.*

**Tone:** technically serious, evidence-driven, visually simple, policy-oriented, honest, confident. **Never defensive.** The limitation is a result we produced, not a shortfall we are excusing.

---

## Slide 1 · Title

| | |
|---|---|
**Title** | **LMIS — Labour Market Intelligence System** · *Evidence-first skilling intelligence for MSDE* |
**Objective** | Establish seriousness and the honest frame in 20 seconds. |
**Key message** | "We standardise fragmented official labour-market evidence and publish what it actually supports." |
**Visual** | Clean title. One strip of four counters. No stock imagery, no gradients. |
**Facts to show** | `26 official sources` · `40 tables · 82,358 rows` · `30 API routes` · `479 tests` |
**Do NOT say** | "AI-powered skill gap forecasting engine." "We predict shortages." |
**Speaker notes** | "PS 26246 asks for a demand–supply gap forecasting engine. We built the platform that such an engine requires — and we'll show you something most teams won't: exactly which number the evidence cannot support, and why that matters more than a confident guess." |

---

## Slide 2 · The problem

| | |
|---|---|
**Title** | **Targets are set on data that cannot be joined** |
**Objective** | Make the decision concrete and the pain real. |
**Key message** | "Six official sources, none of which can be compared without deliberate work." |
**Visual** | Six source cards, visually disconnected, each stamped with its own grain and vintage. Deliberately messy. |
**Facts to show** | NCS `state · 2024-11-15` · Udyam `district · 2023-12-21` · Census B-24 `district×occupation · 2011` · LGD `directory` · PLFS `national · Apr 2025` · MSDE AR `state×scheme · 2024-03-31` |
**Do NOT say** | "The data doesn't exist." (It does — it just doesn't align.) |
**Speaker notes** | "Before a state sanctions seats, it needs to know which district-and-trade combinations are heading for shortage or oversupply. Today that judgement is last year's targets plus a bit. The data exists — in five vintages spanning fourteen years, two occupation schemes, and three different statistical natures. **Not one source carries a district-by-occupation vacancy count.**" |

---

## Slide 3 · Why it is technically hard

| | |
|---|---|
**Title** | **Three reconciliations, three ways to get it wrong** |
**Objective** | Show we understand the problem better than the obvious approaches. |
**Key message** | "The hard part isn't the model. It's making heterogeneous evidence comparable without fabricating the comparison." |
**Visual** | Three rows: **Semantic** / **Granularity** / **Temporal** — each with the naive approach struck through and the failure named. |
**Facts to show** | Semantic: "CNC Operator" vs "Machinist (Grinder)" vs NCO `7223.xxxx` · Granularity: demand district but non-representative, survey truth state-level and representative · Temporal: the decision precedes the outcome |
**Do NOT say** | Name competitors or disparage other submissions. |
**Speaker notes** | "Three failure modes recur. Scraping job portals — richest data, least defensible: postings aren't vacancies, and it breaches terms of service. Treating a classification as a crosswalk — **we proved NCS's 22 'sectors' are NIC-2008 industry sections, not occupations**, so no sector-to-occupation mapping can exist as a function. And filling the gap with an assumption and calling it a model." |

---

## Slide 4 · Solution architecture

| | |
|---|---|
**Title** | **Evidence in, provenance out — nothing invented in between** |
**Objective** | Show the whole system in one image. The anchor slide. |
**Key message** | "Every number reaches the screen carrying its evidence status, confidence, coverage, vintage and source document." |
**Visual** | **The architecture diagram** (`docs/step8.1_architecture_diagram.md`). Vertical flow, master dimensions on the left rail, evidence gates on the right, and the **NO-FABRICATION BOUNDARY** drawn as a hard stop. |
**Facts to show** | Licence gate → immutable sha256 raw store → conformance → Pandera validation → analytical layer → publication contract → FastAPI → dashboard/export |
**Do NOT say** | "FastAPI is our innovation." Don't read the boxes aloud. |
**Speaker notes** | "Left to right is unremarkable. **Two things are not.** The publication contract near the bottom: evidence status, confidence, coverage and prohibited interpretations are part of the response contract, and the application refuses to start if any output breaches it. And the red boundary: where compatible supply evidence is missing, the pipeline **blocks** rather than estimates." |

---

## Slide 5 · Data foundation

| | |
|---|---|
**Title** | **26 official sources, under a licence gate** |
**Objective** | Prove the evidence base is real, official and reproducible. |
**Key message** | "Nothing can be acquired unless it is registered, and nothing acquired can be overwritten." |
**Visual** | Funnel: `26 registered` → `15 acquired` → `6 feeding production`. Beside it, a manifest fragment showing a sha256. |
**Facts to show** | `26 registered` (17 URL-verified) · `15 acquired · 35 files · 50.5 MB` · `6 production sources` · `14 of 14 reconciliations match source-published totals exactly` |
**Do NOT say** | "We have all the data we need." |
**Speaker notes** | "Raw storage is immutable — a fetch never overwrites a snapshot, so `make reproduce` works even if a source goes offline mid-competition. Two access notes: censusindia.gov.in serves an incomplete TLS chain, which we completed legitimately from the certificate's own AIA URL with verification left **on**; microdata.gov.in presents a self-signed certificate and **we refused it**." |

---

## Slide 6 · Standardisation

| | |
|---|---|
**Title** | **One occupation spine, one geography spine, measured not assumed** |
**Objective** | Show the hard engineering, and that mapping discipline is enforced. |
**Key message** | "Official mappings and our mappings are structurally separate — and we refused to invent the ones that don't exist." |
**Visual** | Two columns: **OFFICIAL** (NCO-2004→2015 concordance, DGT CTS trade→NCO) vs **PROJECT** (NCS sector→NIC, confidence 0.95). Below: `153 / 155 trades = MAPPING_UNKNOWN`. |
**Facts to show** | `NCO-2015: 3,982 occupations` · `official concordance: 3,447 rows` · `LGD: 821 (36 states + 785 districts)` · `NIC-2008: 21 sections` · division purity measured (div 2 = 0.998, div 3 = 0.789) · `2 of 155 trades officially NCO-mapped` |
**Do NOT say** | "We mapped all trades to occupations." |
**Speaker notes** | "Every mapping row carries authority, method and confidence. Our one official trade-to-NCO link came from DGT's **own** CTS curriculum PDFs, which carry a Trade Code and an NCO-2015 field — that gave us two trades. **The other 153 remain MAPPING_UNKNOWN.** We could have matched all 155 by name resemblance in an afternoon. Fuzzy, semantic and LLM mapping are prohibited project-wide, because the result would have been invented." |

---

## Slide 7 · Demand intelligence

| | |
|---|---|
**Title** | **What we publish, and how it is labelled** |
**Objective** | Show the actual products with their honest tiers. |
**Key message** | "Two observed products, three estimated ones, one context panel — each labelled on the face of the product." |
**Visual** | Five product rows, each with a tier chip: `OBSERVED ■` / `ESTIMATED ◪` / `SUPPORTING □`. Confidence beside each. |
**Facts to show** | **OBSERVED**: state demand (37 states + 1 residual), industry demand (22 NCS sectors) · **ESTIMATED**: national occupation composition (175 rows, 157 MEDIUM / 18 LOW), District Relative Demand **Allocation Signal** (785 districts, MEDIUM), District × Occupation Relative Demand **Allocation Signal** (138 districts, LOW) · **SUPPORTING**: PLFS, national only, `not_a_demand_measure = TRUE` |
**Do NOT say** | "demand ranking" · "highest-demand districts" · "vacancies by district" |
**Speaker notes** | "NCS has **no occupation axis at all**. We found the bridge in ILOSTAT's India series — whose own source is PLFS — giving an official probability of NCO division given NIC section. That makes the occupation composition **estimated**, and confidence varies **by row**, not one badge per table. Note the product names: *Allocation Signal*. The unit is `relative_signal_unitless`." |

---

## Slide 8 · Live demonstration

| | |
|---|---|
**Title** | **Demonstration** |
**Objective** | Hand over to the live product. |
**Key message** | "Three minutes: national evidence, a district drill-down with its caveat, and the page listing what we cannot compute." |
**Visual** | Minimal — just the heading and a 4-step route strip: `National → State → District → Unavailable`. Switch to the browser. |
**Facts to show** | Nothing on the slide. Everything from the running app. |
**Do NOT say** | Don't narrate screens the demo will show anyway. |
**Speaker notes** | See `docs/step8.1_final_demo_script.md`. Open with the header mode chips — `NUMERIC_GAP: NOT_IDENTIFIABLE`, `is_measured_shortage: false` — so the frame is set before any number appears. **Runs fully offline.** |

---

## Slide 9 · Evidence transparency

| | |
|---|---|
**Title** | **Coverage we disclose, and capabilities we block** |
**Objective** | Turn the limitation into the most credible slide in the deck. |
**Key message** | "Missing is never zero. Not-computable is never a 404." |
**Visual** | Left: the three coverage disclosures. Right: the four-state evidence legend with `UNAVAILABLE ⬚` carrying a reason, not a blank. |
**Facts to show** | `58.13% PAN-India residual — never allocated` (20,507,320 of 35,275,833) · `41.87% state-attributable` (14,768,513) — the entire district base · `138 of 785 districts have Census occupation structure` (522 not acquired, **125 can never have one**) · `16 capabilities UNAVAILABLE, each with a reason code and a gate` · `no row anywhere carries a signal of zero` |
**Do NOT say** | "58.13% was distributed across states." Never apologise here — this is the strength. |
**Speaker notes** | "Most dashboards would quietly drop the residual. **Twenty and a half million vacancies — 58.13% — are PAN-India or multiple-state.** They're attributable to no state, we never allocate them, and allocating them is a `PROHIBITED` capability with its own blocked route. All three numbers are read live from the warehouse — a test fails the build if they appear as literals in our code." |

---

## Slide 10 · Innovation

| | |
|---|---|
**Title** | **Identification-aware analytics** |
**Objective** | Name what is genuinely uncommon, without inflation. |
**Key message** | "We distinguish 'we lack this data' from 'this quantity is not identifiable from evidence of this shape' — and treat the second as a mathematical result." |
**Visual** | Five numbered cards (`docs/step8.1_innovation_slide.md`). |
**Facts to show** | `SUPPLY[state,trade]` is a joint distribution; we hold row marginals + a **21.8%** column fragment (514,619 of 2,361,798) **from a different scheme**; marginals never determine an interior · contract + lint enforced in code, app refuses to start on breach · evidence status **read from the data**, never declared · caveats stored as columns · `make reproduce` from sha256-verified bytes |
**Do NOT say** | "FastAPI is innovative." "Our dashboard is novel." "We use AI/LLMs." |
**Speaker notes** | "The honest innovation: we measured our own signals and published the weakness. **Within a state, our district ordering IS the Udyam enterprise-share ordering — zero of thirty-six states differ.** We print that above the table rather than hide it. And the occupation view promotes the one comparison that restates neither input: districts within a state and division, which differs from both inputs in 27 of 27 groups." |

---

## Slide 11 · Roadmap

| | |
|---|---|
**Title** | **One dataset unlocks the gap** |
**Objective** | Convert the limitation into a specific, actionable ask. |
**Key message** | "State-by-trade training outcomes with complete marginals, and this platform computes the gap — with no formula change." |
**Visual** | Linear progression with gate labels (`docs/step8.1_future_roadmap_slide.md`). No dates. |
**Facts to show** | **NOW** evidence-qualified demand intelligence → **G-1** one observed interior cell of `SUPPLY[geography × trade]` → numeric gap → **G-4** a second dated NCS observation → forecasting → **G-5/6/7/8** → validated early warning. Also: Census B-24 for 33 more states takes coverage `138 → up to 785` **with no code change** |
**Do NOT say** | Any date, any timeline, "in six months", or a source we have not already investigated. |
**Speaker notes** | "Nine objective gates, published inside the product. The decisive one is G-1 condition six: **one observed interior cell of supply by geography and trade.** The other five conditions are harmonisation problems better data solves. Condition six is why this is an identification failure — more of the same marginals never passes it. That's the ask I'd take to MSDE." |

---

## Slide 12 · Close

| | |
|---|---|
**Title** | **What the evidence supports — and what it would take to go further** |
**Objective** | Land the central claim and invite the hard question. |
**Key message** | "A system that says 'we don't know, here's why, here's what would tell us' is more useful to a planner than one that answers confidently and wrongly." |
**Visual** | The central sentence, large. Beneath it a compact proof strip. |
**Facts to show** | `40 tables · 82,358 rows` · `30 routes` · `11 exports with caveats in the file header` · `16 capabilities blocked with reasons` · `479 tests` · `make reproduce` from checksummed raw bytes · `is_measured_shortage = false`, enforced at startup |
**Do NOT say** | "We solved the problem statement." "We forecast demand." Don't end on an apology. |
**Speaker notes** | "A fabricated gap would be worse than none: the error would be invisible, systematically wrong in one direction, and it informs seat sanctioning — real money. So we didn't manufacture the missing number. We built the infrastructure that tells decision-makers what the evidence supports, and exactly what evidence is required to go further. **Happy to take the hardest question you have.**" |

---

## Deck mechanics

**Timing (10 min + 5 min Q&A):** S1 0:20 · S2 0:50 · S3 1:00 · S4 1:30 · S5 0:50 · S6 1:10 · S7 1:20 · S8 → live demo 3:00 · S9 1:20 · S10 1:10 · S11 1:00 · S12 0:40. **Trim first:** S3 and S6 (compress to one line each). **Never trim:** S9 and S11 — they carry the argument.

**Visual system.** One accent colour. Evidence tiers always as **text + shape**: `OBSERVED ■` · `ESTIMATED ◪` · `SUPPORTING □` · `NOT AVAILABLE ⬚` — never colour alone, which also mirrors the product's own accessibility rule. Tabular numerals. No icon sets, no stock photography, no 3-D charts.

**Charts permitted:** horizontal bars for observed counts, ranking tables, relative-signal bars with no count axis, the architecture diagram, the roadmap. **Charts forbidden** (same rules as the product): demand-vs-supply bars, shortage heatmaps, forecast curves, directional arrows, absolute-vacancy maps.

**Every slide's footer** carries the source and vintage of anything quantitative on it. **No global "data as of" date** — five vintages span fourteen years.
