# Final Slide Content — LMIS · SIH 2026 · PS 26246

**Ready-to-paste text.** Bullets are deliberately short — a slide is a cue, not a document. Long-form
reasoning lives in the speaker notes and in `docs/step8.0_sih_solution_story.md`.

Tier chips: `OBSERVED ■` · `ESTIMATED ◪` · `SUPPORTING □` · `NOT AVAILABLE ⬚`

---

## Slide 1

### LMIS — Labour Market Intelligence System
#### Evidence-first skilling intelligence for MSDE · PS 26246

- Standardises fragmented **official** labour-market evidence
- Publishes **provenance-aware** demand intelligence
- Identifies the evidence required for defensible gap analysis

> `26 official sources` · `40 tables · 82,358 rows` · `30 API routes` · `479 tests`

**Visual:** title + one counter strip. No imagery.
**Notes:** "PS 26246 asks for a demand–supply gap forecasting engine. We built the platform such an engine requires — and we'll show you which number the evidence cannot support, and why that matters more than a confident guess."
**Source:** `config/sources.yaml`; warehouse; `pytest`.

---

## Slide 2

### Targets are set on data that cannot be joined

- **Six** official sources feed production — none directly comparable
- **Five vintages** spanning **fourteen years**
- **Two** occupation schemes; **three** statistical natures
- **No source carries district × occupation vacancies**

| Source | Grain | Vintage |
|---|---|---|
NCS | state | 2024-11-15 |
Udyam | district | 2023-12-21 |
Census B-24 | district × occupation | **2011** |
PLFS | **national only** | Apr 2025 |
MSDE AR | state × scheme | 2024-03-31 |

**Visual:** six disconnected source cards above the table.
**Notes:** "Before a state sanctions seats it needs to know which district-and-trade combinations are heading for shortage. Today that's last year's targets plus a bit. The data exists — it just doesn't align."
**Source:** `docs/data_sources.md`; `source_snapshot`.

---

## Slide 3

### Three reconciliations, three ways to get it wrong

- **Semantic** — "CNC Operator" / "Machinist (Grinder)" / NCO `7223.xxxx`
- **Granularity** — district signals are non-representative; survey truth is state-level
- **Temporal** — the sanctioning decision precedes the outcome

**What we rejected, and why**

- Portal scraping → postings ≠ vacancies; breaches ToS
- NCS "sector" as an occupation → **they are NIC-2008 industry sections**
- Impute the national mix and subtract → plausible, invisible, directionally wrong

**Visual:** three rows; rejected approaches struck through.
**Notes:** "We *proved* the 22 NCS sectors are industry sections, so no sector-to-occupation mapping can exist as a function. Any pipeline equating them has fabricated its occupation axis."
**Source:** `docs/step1_5_demand_investigation.md`; `map_ncs_sector_to_nic_section`.

---

## Slide 4

### Evidence in, provenance out — nothing invented in between

- **Licence gate** — nothing acquired unless registered
- **Immutable raw store** — sha256 manifests; a fetch never overwrites
- **Conformance** — NCO-2015 · LGD · NIC-2008 · period
- **Validation** — Pandera contracts + reconciliation to source totals
- **Publication contract** — evidence, confidence, coverage, provenance travel with every value
- **No-fabrication boundary** — missing compatible supply ⇒ **blocked, not estimated**

**Visual:** the architecture diagram (`docs/step8.1_architecture_diagram.md`).
**Notes:** "Left to right is unremarkable. Two things aren't: the publication contract — the app **refuses to start** if an output breaches it — and the red boundary, where the pipeline blocks rather than estimates."
**Source:** `src/lmis/`, `api/`, `config/publication_contract.yaml`.

---

## Slide 5

### 26 official sources, under a licence gate

- `26` registered · `17` URL-verified
- `15` acquired as immutable snapshots — `35 files · 50.5 MB`
- `6` feed production: NCS · Udyam · Census B-24 · LGD · PLFS · MSDE AR
- **`14 of 14` reconciliations match each source's own published totals exactly**
- No CAPTCHA, authentication or robots bypass — anywhere

**Visual:** funnel `26 → 15 → 6`, plus a manifest fragment showing a sha256.
**Notes:** "censusindia.gov.in serves an incomplete TLS chain; we completed it legitimately from the certificate's own AIA URL with verification left **on**. microdata.gov.in presents a self-signed certificate — **we refused it**."
**Source:** `config/sources.yaml`; `source_snapshot`; `fact_training_reconciliation`.

---

## Slide 6

### One occupation spine, one geography spine — measured, not assumed

- **NCO-2015**: `3,982` occupations · **official** NCO-2004 concordance `3,447` rows
- **LGD**: `821` — 36 states + 785 districts
- **NIC-2008**: `21` sections
- Division purity **measured**: div 2 = `0.998`, div 3 = `0.789`
- **`2 of 155`** DGT trades officially NCO-mapped — **`153` = `MAPPING_UNKNOWN`**

| OFFICIAL | PROJECT |
|---|---|
NCO-2004 → NCO-2015 concordance | NCS sector → NIC section (conf. `0.95`) |
DGT CTS trade → NCO (2 trades) | — |

**Visual:** the two-column authority table.
**Notes:** "Our one official trade-to-NCO link came from DGT's **own** curriculum PDFs. We could have matched all 155 by name in an afternoon — fuzzy, semantic and LLM mapping are prohibited project-wide, because the result would be invented."
**Source:** `occupation_master`, `location_master`, `map_nco2004_to_nco2015`, `dim_trade_mapping_status`.

---

## Slide 7

### What we publish — and how it is labelled

| | Product | Grain | Confidence |
|---|---|---|---|
`■` | NCS state demand | state (37 + 1 residual) | OBSERVED |
`■` | NCS demand by industry | 22 NCS sectors | OBSERVED |
`◪` | National occupation composition | NIC × NCO division | `157` MEDIUM / `18` LOW |
`◪` | **District Relative Demand Allocation Signal** | 785 districts | MEDIUM |
`◪` | **District × Occupation Relative Demand Allocation Signal** | 138 districts | **LOW** |
`□` | Labour-force context (PLFS) | **national only** | not a demand measure |

- Unit of the signals: **`relative_signal_unitless`** — not a count
- Occupation axis via **ILOSTAT/PLFS** `P(NCO division | NIC section)`

**Visual:** this table, tier chips in the first column.
**Notes:** "NCS has **no occupation axis**. We found the bridge in ILOSTAT's India series. Note the product names: *Allocation Signal* — never 'demand ranking'. A terminology lint fails the build if anyone writes that."
**Source:** `config/publication_contract.yaml`; the five demand/context tables.

---

## Slide 8

### Demonstration

`National` → `State` → `District` → `Unavailable capabilities`

- Runs **fully offline** — no Node build, no CDN, no external API

**Visual:** heading + route strip only. Switch to the browser.
**Notes:** Open on the header mode chips so the frame is set before any number appears. Full script: `docs/step8.1_final_demo_script.md`.

---

## Slide 9

### Coverage we disclose — capabilities we block

**Disclosed on every relevant screen**

- **`58.13%`** PAN-India / multiple-state — **never allocated** (20,507,320 of 35,275,833)
- **`41.87%`** state-attributable (14,768,513) — the *entire* district base
- **`138 of 785`** districts have Census occupation structure
  → `522` not acquired · **`125` can never have one** (post-2011 districts)

**Blocked, not blank**

- `16` capabilities `UNAVAILABLE ⬚` — each with a reason code and a gate
- **No row anywhere carries a signal of zero**
- Blocked routes return **HTTP 200 + `data: null`** — a 404 would read as "none found"

**Visual:** two columns; the evidence legend bottom-right.
**Notes:** "Most dashboards would quietly drop the residual. Twenty and a half million vacancies belong to no state. Allocating them is a `PROHIBITED` capability. And all three numbers are read live from the warehouse — a test fails the build if they appear as literals in our code."
**Source:** `demand_coverage_summary`; `/api/capabilities`.

---

## Slide 10

### Identification-aware analytics

1. **We distinguish "we lack data" from "this is not identifiable"** — and treat the second as a result
2. **Publication contract enforced in code** — the app refuses to start on a breach
3. **Terminology lint over the published surface** — translation files included
4. **Evidence status read from the data**, never declared in config
5. **Caveats stored as columns** — the UI cannot drift from the data
6. **Reproducible** — `make reproduce` from sha256-verified bytes

> `SUPPLY[state, trade]` is a joint distribution.
> We hold row marginals + a **21.8%** column fragment — **from a different scheme**.
> **Marginals never determine an interior.**

**Visual:** six cards; the quote as a callout.
**Notes:** "The honest innovation is self-criticism we published. **Within a state, our district ordering IS the Udyam enterprise-share ordering — 0 of 36 states differ.** We print that above the table. The occupation view then promotes the one comparison that restates neither input — 27 of 27 groups differ from both."
**Source:** `docs/step6_methodology_decision.md`; `docs/step7.3_dashboard_api_product_design.md` §1.

---

## Slide 11

### One dataset unlocks the gap

```
NOW        Evidence-qualified demand intelligence
             │
   G-1     + state × trade training outcomes, COMPLETE marginals
             ▼
           NUMERIC DEMAND–SUPPLY GAP
             │
   G-4     + a second dated NCS observation
             ▼
           TEMPORAL FORECASTING
             │
   G-5/6/7/8 + occupation dimension on the training axis · stability · coverage
             ▼
           VALIDATED EARLY WARNING
```

- Also: **Census B-24 for 33 more states → `138 → up to 785` districts, no code change**
- `9` objective gates, published **inside the product**

**Visual:** the progression, gate labels on the arrows. **No dates.**
**Notes:** "G-1 condition six: **one observed interior cell of supply by geography and trade.** The other five conditions are harmonisation problems better data solves. Condition six is why this is an identification failure — more of the same marginals never passes it."
**Source:** `docs/step8.0_requirement_mapping.md` §3.

---

## Slide 12

### What the evidence supports — and what it would take to go further

> **We did not manufacture the missing number.**
> We built the infrastructure that tells decision-makers what the evidence actually supports — and exactly what evidence is required to go further.

- `40 tables · 82,358 rows` · `30 routes` · `11 exports` carrying caveats in the file header
- `16` capabilities blocked with reasons · `479 tests` · `make reproduce`
- **`is_measured_shortage = false`** — enforced at application startup

**Visual:** the quote large; proof strip beneath.
**Notes:** "A fabricated gap would be worse than none: the error would be invisible, directionally wrong, and it informs seat sanctioning — real money. Happy to take the hardest question you have."
**Source:** the whole repository; `docs/step7.5_sih_demo_readiness.md`.
