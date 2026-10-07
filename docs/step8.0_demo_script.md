# SIH Demo Script — LMIS (PS 26246)

Two scripts: a **7-minute main demo** and a **3-minute fallback**. Every screen, click and claim below was
verified against the running application on 2026-10-06. **Nothing in this script requires a feature the
system does not have.**

---

## Before you start

```bash
make serve        # http://127.0.0.1:8000   (dashboard; /docs for OpenAPI)
```

Runs entirely offline — no Node build, no CDN, no external API. Have a second tab on `/docs`.

**Three sentences to have ready, because they are the spine of the whole demo:**

1. *"Every number on this screen carries its evidence status, confidence, coverage, vintage and source
   document."*
2. *"This is a relative allocation signal, not a vacancy count."*
3. *"We do not publish a demand–supply gap, because we proved the available evidence cannot identify one —
   and we publish exactly which dataset would change that."*

---

## Main demo — 7 minutes

### 1 · Landing — the problem and the discipline · 0:00–0:45

**Open** `http://127.0.0.1:8000`

**Point at** the mode chips in the header: `NUMERIC_GAP: NOT_IDENTIFIABLE` ·
`FORECASTING: NOT_SUPPORTED_YET` · `is_measured_shortage: false` · `MODE: OPTION_A` ·
`Demand baseline: 2024-11-15`.

> "India's skilling system sets training targets using labour-market data scattered across NCS, Udyam, PLFS,
> Census and scheme MIS. No single view combines demand with training capacity at district-by-trade
> resolution, so mismatches surface a year too late.
>
> We built the platform that fixes the fragmentation. And before I show you anything, notice what the header
> admits: **we do not publish a demand–supply gap.** I'll show you why, and why that is the most defensible
> thing in this submission."

**Point at** the three coverage statements on the page — 58.13% residual, 41.87% state-attributable, 138 of
785 districts.

> "Those three numbers are read live from the warehouse. They are not written anywhere in our code — a test
> fails the build if they are."

**Why it matters:** sets the frame before any number appears, so nothing later looks like a retreat.

---

### 2 · National — observed vs estimated, kept apart · 0:45–2:15

**Click** `National`.

**Panel 1 — point at the OBSERVED badge (■).**

> "NCS vacancies by sector — **observed**. 22 sectors, cumulative since inception as on 2024-11-15. These
> trace to three named Parliament answers, and we recognised they describe **one** observation, not three, so
> we deduplicated rather than summed."

**Point at** the "— (no NIC mapping)" rows and the PROJECT-mapping note.

> "Two NCS sectors have no NIC section. Our industry filter keys on the NCS sector, not NIC, so those two
> don't silently disappear. And the NCS-to-NIC alignment is **our** mapping at confidence 0.95 — the counts
> are official, the alignment is ours, and the page says so."

**Panel 2 — point at the ESTIMATED badge (◪) and the per-row confidence column.**

> "NCS has **no occupation axis at all.** We found the bridge in ILOSTAT's India series — whose own source is
> PLFS — giving an official probability of NCO division given NIC section. That makes this **estimated**, and
> confidence varies **by row**: 157 rows MEDIUM, 18 LOW. Not one badge for the whole table."

**Panel 3 — point at the banner.**

> "`SUPPORTING CONTEXT — NOT A DEMAND MEASURE`. PLFS labour-force rates, national only. The data itself
> carries a flag saying it is not a demand measure, and our contract **refuses to publish** it as SUPPORTING
> unless every row carries that flag."

**Panel 4 — the residual.**

> "And here is the number most dashboards would quietly drop: **20,507,320 vacancies — 58.13% — are
> PAN-India or multiple-state.** They are not attributable to any state. We never allocate them. If we did,
> every district number on the next screen would be inflated by an invented geography."

**Why it matters:** judges see the observed/estimated/supporting distinction enforced visually, not asserted.

---

### 3 · State — the drill-down, and the self-criticism · 2:15–3:45

**Click** `State`, **select** `Maharashtra`.

**Point at** the observed state total with its share chips.

> "Observed: NCS vacancies attributed to Maharashtra, with its share of the published total."

**Scroll to** the district table. **Point at the amber caveat box directly above it.**

> "Now the part I want you to hold me to. This is the **District Relative Demand Allocation Signal** — and
> read the caveat we print above it:
>
> *'within a state this ordering equals the Udyam enterprise-share ordering; B adds information only across
> states.'*
>
> We measured that. In **0 of 36 states** does the within-state ordering differ from ranking districts by
> Udyam enterprise share. So this is **not** a demand ranking of districts — within a state it is an
> enterprise-density ranking, and the NCS demand component only varies *between* states.
>
> We could have called this 'highest-demand districts' and nobody in this room would have caught it. Instead
> the caveat is stored as a **column on every row**, and our contract refuses to build a response if it's
> missing."

**Point at** the `Udyam enterprise share` column sitting next to the signal.

> "We show the driver alongside — not as corroborating evidence, which would be circular since it's a factor
> in the signal, but as disclosure. It's under a heading that says *'How this signal is derived.'* Our
> terminology lint fails the build if anyone labels it 'independent validation'."

**Scroll to** the training panel.

> "The training system's own reported outcomes, state level, by scheme. Note we never call this **supply** —
> it has no occupation dimension, so it isn't a supply quantity. And a measure the source printed as a dash
> shows as `NO_DATA`, never as zero."

**Why it matters:** this is the credibility moment. Volunteering the weakness earns every other claim.

---

### 4 · District — and honest absence · 3:45–4:45

**Click** any district in the table (e.g. Pune).

**Point at** the signal card: rank *k* of 36, LOW/MEDIUM confidence, Udyam snapshot 2023-12-21, baseline
2024-11-15, transformation depth.

> "One district. Its allocation signal, its rank within its state, and the vintage of **each** input —
> because they differ."

**Scroll to** the occupation panel.

> "**District × Occupation Relative Demand Allocation Signal** — nine NCO-2015 divisions. And again the
> caveat: within a district this ordering **is** the Census-2011 occupation-share ordering. Census 2011 is
> fourteen years before our demand baseline, and the page says so."

**Now navigate to a district without coverage** — type `#district/` + an LGD code from Kerala, or click
through from the Coverage page.

> "And here is what I think is the most important screen in the product. This district has **no occupation
> detail**, and instead of a zero or a blank you get `NOT_AVAILABLE` with the actual reason: *'Census 2011
> table B-24 has not been acquired for this district's state. This is an absence of acquired evidence, not an
> absence of demand.'*
>
> **No row in this system carries a signal of zero.** A district without a prior has no occupation rows at
> all, so a zero cannot be rendered even by accident. 522 districts are in that state; a further **125 are
> post-2011 districts for which a Census prior can never exist** — a different reason, reported differently."

**Why it matters:** "missing is not zero" is the single most common way a dashboard like this becomes
confidently wrong.

---

### 5 · Occupation — the one informative comparison · 4:45–5:15

**Click** `Occupation`, **select** division 7 (Craft and related trades workers).

> "Occupation-facing view. The national composition on top — estimated. Below, districts ranked **within one
> state for this one division.**
>
> That is deliberately the main panel, because it's the **only** comparison in the product that restates
> neither input. Within a state it differs from enterprise share alone, and from occupation share alone, in
> **27 of 27** groups we tested. It's still an estimated allocation signal — never an observed demand
> ranking — but it is the one place the two structures combine to add information."

**Why it matters:** shows we know which of our own comparisons is actually informative.

---

### 6 · Methodology and Coverage · 5:15–6:00

**Click** `Methodology`.

> "Four evidence tiers, each with plain-language meaning. The distinction we work hardest to teach:
> **'estimated' means the number exists but was derived; 'unavailable' means it does not exist and cannot
> currently be computed.** Rendering both as a blank is exactly how a tool like this misleads."

**Scroll to** the gap section.

> "`NUMERIC_GAP: NOT_IDENTIFIABLE`, with the reason. And the five-vintage table — 2024-11-15, 2023-12-21,
> 2024-03-31, April 2025, and 2011. **There is no single 'data as of' date on this site**, because any single
> date would be false."

**Click** `Coverage`.

> "Every coverage metric, each showing the warehouse column it was derived from. Plus 14 pipeline
> data-quality checks, and the fields we **bar** from publication — including one we found stale in our own
> metadata during QA and fixed."

---

### 7 · Unavailable capabilities — the close · 6:00–7:00

**Click** `Unavailable capabilities`.

> "Sixteen capabilities we do not publish, grouped by **reason code** — and the grouping is the point.
>
> **`NOT_ACQUIRED`** means the source exists and we haven't got it — the data.gov.in PMKVY district resource
> needs a registered API key. That's a paperwork problem.
>
> **`NOT_IDENTIFIABLE`** is different. The demand–supply gap sits here. Supply by state and trade is a joint
> distribution. We hold the row totals, plus **21.8%** of the column totals — 78% of PMKVY 4.0 enrolment is
> in job roles the source doesn't name — and that fragment is from a *different scheme*. Row and column
> totals **never** determine the interior. To close it you must assume every state trains the same trade mix,
> which is both false and untestable — and it would erase the exact regional mismatch this problem statement
> exists to find.
>
> So we could produce a number. It would look like data, the error would be invisible, systematically wrong
> in one direction, and it would move real sanctioning money to the wrong districts.
>
> Instead, every one of these carries a **gate**. Gate G-1 condition six: **one observed interior cell of
> supply by geography and trade.** Gate G-4 for forecasting: **a second dated NCS observation** — we have
> exactly one.
>
> That's the ask we'd take to MSDE: **publish state-by-trade training outcomes with complete marginals, and
> this platform computes the gap you asked for without a single formula change.** The architecture is already
> built for it — Census B-24 for the other 33 states would take district coverage from 138 toward 785 with no
> code change at all.
>
> **479 tests, one command to rebuild everything from checksummed raw bytes, and a system that refuses to
> start if any output claims a shortage it cannot measure.**"

**Optional 20 seconds if time allows** — switch to `/docs`:

> "Thirty API routes. Twenty serve data; ten are the blocked ones, and they return HTTP **200** with
> `data: null`, a reason and a gate — not a 404, because a 404 reads as *'none found'* rather than *'not
> computable'*. And every CSV export carries its evidence status, coverage and limitations in the file
> header, so a relative signal cannot become 'vacancies' in someone's slide."

---

## Fallback demo — 3 minutes

Use when time is cut or a page is slow.

| Time | Screen | Say |
|---|---|---|
**0:00–0:30** | **Landing** | "Fragmented labour-market data across six official sources. We conform them onto NCO-2015, LGD and NIC-2008, and every number carries its evidence status, confidence, coverage and source. Note the header: **we do not publish a demand–supply gap**, and I'll explain why that's deliberate." |
**0:30–1:15** | **National** | "Observed NCS vacancies by sector — traceable to three named Parliament answers. Estimated occupation composition, bridged via ILOSTAT/PLFS, with per-row confidence. PLFS as context, explicitly not a demand measure. And **58.13% of vacancies are PAN-India — we never allocate them to districts.**" |
**1:15–2:00** | **State → Maharashtra** | "Districts ranked on a relative allocation signal. Read the caveat we print above it: within a state this ordering **is** the Udyam enterprise-share ordering — 0 of 36 states differ. So it is not a demand ranking, and we say so on the face of the product. The caveat is a column on every row; the contract won't build a response without it." |
**2:00–2:30** | **District (no coverage)** | "A district without Census occupation structure shows `NOT_AVAILABLE` **with the reason** — not a zero. No row in this system carries a signal of zero." |
**2:30–3:00** | **Unavailable capabilities** | "Sixteen capabilities we don't publish, grouped by reason. The gap is `NOT_IDENTIFIABLE`: we hold supply row totals plus 21.8% of column totals from a different scheme, and marginals never determine an interior. Gate G-1 names what would fix it — **state-by-trade training outcomes**. That's our ask to MSDE, and the platform already handles it." |

---

## Demo discipline

**Never say** — and the replacement:

| ✗ Don't say | ✓ Say instead |
|---|---|
"highest-demand districts" | "the highest relative allocation signal within this state" |
"vacancies in this district" | "a relative signal — this is not a vacancy count" |
"we forecast demand" | "forecasting needs a second dated observation; we have one" |
"the skill gap" / "shortage" | "no numeric gap is identifiable from current evidence" |
"training supply" | "training-system outcomes — candidate counts within a named scheme" |
"PLFS shows demand" | "PLFS is national labour-force context, not a demand measure" |
"as of today" / "live data" | "five vintages; each figure carries its own as-on date" |
"58.13% distributed across states" | "58.13% is PAN-India and is never allocated" |

**If a judge pushes hard on the missing gap** — don't defend, agree and redirect:

> "You're right that the problem statement asks for it, and we can't deliver it. What we can deliver is the
> proof of *why*, and the precise dataset that would unlock it. I'd rather hand MSDE a specific, costed data
> request than a number that restates an assumption."

**If something breaks:** `/api/health` confirms the backend in one line; every page is independently
reachable by its hash route; and the Coverage and Unavailable pages need only two API calls each, so they
load even if a heavier page stalls.
