# Final Demo Script — LMIS · PS 26246

Three versions: **7-minute main**, **3-minute emergency**, **60-second elevator**. Every screen and claim was
verified against the running application. **No step requires a feature the system does not have.**

```bash
make serve      # http://127.0.0.1:8000  ·  /docs for OpenAPI  ·  fully offline
```

**Frame the limitation as evidence discipline, never as apology.** Say it once, early, with confidence —
then spend the demo on what the system does.

---

# A · 7-minute demo

### 0:00–0:35 · Landing — set the frame

**Open** `http://127.0.0.1:8000`. **Point at the header mode chips.**

> "LMIS. Six official labour-market sources, standardised onto one occupation spine and one geography spine.
>
> Before any number: look at the header. **`NUMERIC_GAP: NOT_IDENTIFIABLE`. `is_measured_shortage: false`.**
> The problem statement asks for a demand–supply gap. We proved the available evidence cannot identify one,
> and the system publishes that rather than guessing. I'll show you the proof at the end — it's the strongest
> thing here."

**Point at** the three coverage statements.

> "58.13% · 41.87% · 138 of 785 districts. All read live from the warehouse — a test fails our build if those
> numbers appear as literals in the code."

---

### 0:35–2:00 · National — observed, estimated and context, kept apart

**Click** `National`.

**Panel 1** — point at `OBSERVED ■`.

> "NCS vacancies by sector — **observed**. 22 sectors, cumulative as on 2024-11-15, traceable to three named
> Parliament answers. We recognised those three documents describe **one** observation, not three, so we
> deduplicated rather than summed."

**Point at** a `— (no NIC mapping)` row.

> "Two sectors have no NIC section. Our industry filter keys on the NCS sector, not NIC, so they don't
> silently vanish. And the NCS-to-NIC alignment is **ours** at confidence 0.95 — counts official, alignment
> ours, and the page says so."

**Panel 2** — point at `ESTIMATED ◪` and the per-row confidence column.

> "NCS has **no occupation axis at all.** We found the bridge in ILOSTAT's India series — whose own source is
> PLFS — giving an official probability of NCO division given NIC section. That makes this estimated, and
> confidence varies **by row**: 157 MEDIUM, 18 LOW. Not one badge for the table."

**Panel 3** — point at the banner.

> "`SUPPORTING CONTEXT — NOT A DEMAND MEASURE`. PLFS, national only. The data itself carries that flag, and
> our contract **refuses to publish** it as supporting unless every row does."

**Panel 4** — the residual. *(Slow down here.)*

> "And the number most dashboards quietly drop. **20,507,320 vacancies — 58.13% of the published total — are
> PAN-India or multiple-state.** Attributable to no state. We never allocate them; allocating them is a
> `PROHIBITED` capability with its own blocked route. Every district figure you're about to see rests on the
> remaining **41.87%**, and the page says so."

---

### 2:00–3:30 · State — the drill-down, and the self-criticism

**Click** `State` → **select** `Maharashtra`.

> "Observed NCS vacancies attributed to Maharashtra, with its share of the published total."

**Scroll to the district table. Point at the amber caveat box above it.**

> "Now the part I want you to hold me to. This is the **District Relative Demand Allocation Signal**. Read
> what we print above it:
>
> *'within a state this ordering equals the Udyam enterprise-share ordering.'*
>
> We measured that. In **zero of thirty-six states** does the within-state ordering differ from ranking
> districts by Udyam enterprise share. So within a state this is an **enterprise-density** ranking — the NCS
> demand component only varies *between* states.
>
> We could have called this 'highest-demand districts' and nobody would have caught it. Instead the caveat is
> stored as a **column on every row**, and the contract refuses to build a response without it."

**Point at** the `Udyam enterprise share` column.

> "We show the driver alongside — not as corroborating evidence, which would be circular since it's a
> *factor* in the signal, but as disclosure, under a heading that says *'How this signal is derived.'* Our
> terminology lint fails the build if anyone labels it 'independent validation'."

**Scroll to** the training panel.

> "The training system's own reported outcomes, state level, by scheme. We never call this **supply** — it has
> no occupation dimension, so it can't tell you supply *of what*. And a measure the source printed as a dash
> shows as `NO_DATA`, never zero."

---

### 3:30–4:30 · District — and honest absence

**Click** a district (e.g. Pune).

> "One district: its allocation signal, its rank within its state, and the vintage of **each** input —
> Udyam 2023-12-21, baseline 2024-11-15 — because they differ."

**Scroll to** the occupation panel.

> "**District × Occupation Relative Demand Allocation Signal** — nine NCO-2015 divisions. Same discipline:
> within a district this ordering **is** the Census-2011 occupation-share ordering. Census 2011 is fourteen
> years before our baseline, and the page says so."

**Navigate to a district without coverage** (Coverage page, or a Kerala LGD code).

> "And the most important screen in the product. This district has **no occupation detail** — and instead of a
> zero or a blank you get `NOT_AVAILABLE` with the actual reason: *'Census 2011 table B-24 has not been
> acquired for this district's state. This is an absence of acquired evidence, not an absence of demand.'*
>
> **No row in this system carries a signal of zero.** A district without a prior has no occupation rows at
> all, so a zero can't be rendered even by accident. 522 districts are in that state — and **125 more are
> post-2011 districts for which a Census prior can never exist.** Different reasons, reported differently."

---

### 4:30–5:00 · Occupation — the one informative comparison

**Click** `Occupation` → **division 7**.

> "National composition on top — estimated. Below: districts ranked **within one state for this one
> division.** That's deliberately the main panel, because it's the **only** comparison in the product that
> restates neither input — it differs from enterprise share alone, and from occupation share alone, in **27
> of 27** groups we tested. Still an estimated allocation signal. Never an observed demand ranking."

---

### 5:00–5:45 · Methodology and Coverage

**Click** `Methodology`.

> "Four evidence tiers, each with plain-language meaning. The distinction we work hardest to teach:
> **'estimated' means the number exists but was derived; 'unavailable' means it does not exist and cannot
> currently be computed.** Rendering both as a blank is exactly how a tool like this misleads.
>
> And the five-vintage table — 2024-11-15, 2023-12-21, 2024-03-31, April 2025, and 2011. **There is no single
> 'data as of' date on this site**, because any single date would be false."

**Click** `Coverage` *(10 seconds)*.

> "Every coverage metric showing the warehouse column it came from, 14 pipeline data-quality checks, and the
> fields we **bar** from publication — including one we found stale in our own metadata during QA and fixed."

---

### 5:45–7:00 · Unavailable capabilities — the close

**Click** `Unavailable capabilities`.

> "Sixteen capabilities we don't publish, grouped by **reason code** — and the grouping is the whole point.
>
> **`NOT_ACQUIRED`** means the source exists and we haven't got it — the data.gov.in PMKVY district resource
> needs a registered API key. A paperwork problem.
>
> **`NOT_IDENTIFIABLE`** is different, and the gap sits here. Supply by state and trade is a **joint
> distribution.** We hold the row totals, plus **21.8%** of the column totals — 78% of PMKVY 4.0 enrolment is
> in job roles the source doesn't name — and that fragment comes from a **different scheme.** Row and column
> totals **never** determine the interior. To close it you must assume every state trains the same trade mix:
> false, untestable, and it would erase the exact regional mismatch this problem statement exists to find.
>
> We could produce a number. It would look like data, the error would be invisible and systematically wrong
> in one direction, and it informs seat sanctioning — real money.
>
> So instead, every one of these carries a **gate**. **G-1 condition six: one observed interior cell of
> supply by geography and trade.** **G-4 for forecasting: a second dated NCS observation** — we have exactly
> one.
>
> That's the ask I'd take to MSDE: **publish state-by-trade training outcomes with complete marginals, and
> this platform computes the gap you asked for with no formula change.** Census B-24 for the other 33 states
> would take district coverage from 138 toward 785 — also with no code change.
>
> **479 tests. One command rebuilds everything from checksummed raw bytes. And the application refuses to
> start if any output claims a shortage it cannot measure.**"

**If 20 seconds remain** — switch to `/docs`:

> "Thirty routes. Twenty serve data; ten are the blocked ones, returning HTTP **200** with `data: null`, a
> reason and a gate — not 404, because a 404 reads as *'none found'* rather than *'not computable'*. And every
> CSV export carries its evidence status, coverage and limitations in the **file header**, so a relative
> signal can't become 'vacancies' in someone's slide."

---

# B · 3-minute emergency demo

| Time | Screen | Say |
|---|---|---|
**0:00–0:25** | **Landing** | "Six official sources, standardised onto one occupation and one geography spine. Note the header: **we do not publish a demand–supply gap** — we proved the evidence can't identify one. I'll close on why that's the strongest thing here." |
**0:25–1:05** | **National** | "Observed NCS vacancies by sector — three named Parliament answers. Estimated occupation composition, bridged via ILOSTAT/PLFS, confidence **per row**. PLFS as context, explicitly not a demand measure. And **58.13% of vacancies are PAN-India — never allocated to any district.**" |
**1:05–1:50** | **State → Maharashtra** | "Districts on a relative allocation signal. Read the caveat above the table: within a state this ordering **is** the Udyam enterprise-share ordering — 0 of 36 states differ. So it's not a demand ranking, and we say so on the face of the product. The caveat is a column on every row." |
**1:50–2:20** | **District (no coverage)** | "A district without Census structure shows `NOT_AVAILABLE` **with the reason** — not a zero. No row in this system carries a signal of zero." |
**2:20–3:00** | **Unavailable** | "Sixteen capabilities blocked, grouped by reason. The gap is `NOT_IDENTIFIABLE`: we hold supply row totals plus 21.8% of column totals from a different scheme, and marginals never determine an interior. **Gate G-1 names what fixes it — state-by-trade training outcomes.** That's our ask to MSDE, and the platform already handles it." |

**Cut first:** the Occupation view and `/docs`. **Never cut:** the State caveat and the Unavailable close.

---

# C · 60-second elevator pitch

> "India sets skilling targets using labour-market data spread across six official sources that can't be
> joined — five vintages spanning fourteen years, two occupation schemes, and not one source carrying a
> district-by-occupation vacancy count.
>
> We built **LMIS**: it acquires those sources under a licence gate into an immutable checksummed store,
> conforms them onto NCO-2015, LGD and NIC-2008 through confidence-scored official mappings, and publishes
> demand intelligence where every number carries its evidence status, confidence, coverage, vintage and
> source document. Thirty API routes, eight dashboard pages, 479 tests, and one command rebuilds everything
> from raw bytes.
>
> And we did the part that takes more discipline than building it. The problem statement asks for a
> demand–supply gap. **We proved it isn't identifiable** — supply by state and trade is a joint distribution
> and we hold only its margins, 21.8% of them from a different scheme. So instead of a number that would
> restate an assumption, we publish the finding, and the one dataset that would change it: **state-by-trade
> training outcomes with complete marginals.**
>
> A planner can act on that. They couldn't act safely on a fabricated gap — and they wouldn't know it was
> fabricated."

---

# Demo discipline

| ✗ Never say | ✓ Say instead |
|---|---|
"highest-demand districts" | "the highest relative allocation signal within this state" |
"vacancies in this district" | "a relative signal — not a vacancy count" |
"we forecast demand" | "forecasting needs a second dated observation; we have one" |
"the skill gap" / "shortage" | "no numeric gap is identifiable from current evidence" |
"training supply" | "training-system outcomes — candidates within a named scheme" |
"PLFS shows demand" | "PLFS is national labour-force context, not a demand measure" |
"as of today" / "live data" | "five vintages; each figure carries its own as-on date" |
"58.13% distributed across states" | "58.13% is PAN-India and is **never** allocated" |

**If a judge presses hard on the missing gap** — agree, then redirect:

> "You're right that the PS asks for it, and we can't deliver it. What we can deliver is the proof of *why*,
> and the precise dataset that unlocks it. I'd rather hand MSDE a specific, costed data request than a number
> that restates an assumption."

**If something breaks:** `/api/health` confirms the backend in one line. Every page is independently
reachable by its hash route. The **Coverage** and **Unavailable** pages need only two API calls each, so they
load even if a heavier page stalls — and they carry the argument.
