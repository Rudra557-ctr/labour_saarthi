# 7-Minute Rehearsal Script — word-for-word

**Spoken language, not slide bullets.** Italics are stage directions. Timings are cumulative.
Target pace ≈ 135 words/minute — unhurried. If you are ahead, **slow down**; do not add material.

---

## 0:00–0:30 · Opening *(slide 1)*

> "Good morning. We're presenting LMIS — a Labour Market Intelligence System for MSDE, problem
> statement 26246.
>
> The problem statement asks for an engine that forecasts the skill demand–supply gap at district and
> sector level. We built the platform that such an engine needs: twenty-six official sources,
> standardised onto one occupation spine and one geography spine, with every number carrying its evidence
> status, confidence, coverage and source document.
>
> And we did one more thing, which I'll come back to — we established exactly which number the available
> evidence **cannot** support. I think that turns out to be the most useful part."

*(~95 words · 30s)*

---

## 0:30–1:15 · The problem *(slide 2)*

> "Here's the situation a state skilling department is in today.
>
> Before it sanctions training seats for next year, it needs to know which district-and-trade combinations
> are heading for shortage or oversupply. Right now that decision is essentially last year's targets, plus
> or minus a bit — because the evidence it would need sits in six official sources that cannot be joined.
>
> *(gesture at the cards)* Look at the grains and the vintages. NCS gives vacancies at **state** level, as
> on November 2024. Udyam gives enterprise counts at **district** level, December 2023. The Census
> occupational structure is **district by occupation** — but it's from **2011**. PLFS is **national only**.
>
> Five vintages spanning fourteen years. Two different occupation classifications. And critically — **not
> one of these sources carries a district-by-occupation vacancy count**, which is exactly what the finest
> requirement in the problem statement needs."

*(~165 words · 45s)*

---

## 1:15–2:00 · Why it's difficult *(slide 3)*

> "So why not just build it anyway? Because a gap is only computable when four things line up.
>
> You need demand evidence — we have that. You need **supply** evidence at a compatible grain. You need the
> **same** geography and occupation grain on both sides. And you need the **same** time basis.
>
> We have one of the four. *(pause)* And when one component is missing, you don't get an approximate
> answer — you get no answer.
>
> Three approaches are tempting here and all three fail. Scraping job portals: postings aren't vacancies,
> they're duplicated across platforms, and it breaches terms of service. Treating a classification as a
> crosswalk: we actually **proved** that NCS's twenty-two 'sectors' are NIC industry sections, not
> occupations — so no sector-to-occupation mapping can exist as a function. And the third is to impute the
> national trade mix onto every state and subtract. That produces a complete, plausible table. It's also
> systematically wrong in one direction, and nothing in the output would reveal it."

*(~185 words · 45s)*

---

## 2:00–2:45 · Architecture *(slide 4)*

> "This is what we built instead.
>
> *(point top)* Sources come in through a licence gate — nothing can be acquired unless it's registered —
> into an immutable store with sha256 manifests. A fetch never overwrites a snapshot, so one command rebuilds
> everything from raw bytes even if a source goes offline.
>
> *(point left rail)* These are the master dimensions everything conforms to: LGD geography, NCO-2015
> occupations, NIC sections, period, provenance.
>
> *(point right rail)* And this is what makes it different — at every stage the layer **stamps** the value
> with its evidence status, confidence and coverage.
>
> *(point to the red band)* But the part I'd actually like you to look at is this one. Where compatible
> supply evidence is missing, the pipeline **blocks**. It doesn't estimate. The capability comes out as
> explicitly unavailable, with a reason code and an unblocking condition.
>
> And below that — the publication contract. The application **refuses to start** if any output claims a
> shortage it can't measure."

*(~175 words · 45s)*

---

## 2:45–4:30 · Live demonstration *(switch to browser)*

**→ Follow `docs/step8.3_live_demo_runbook.md` §A. Script below is the spoken track.**

**`#national`** *(0:25)*

> "This is the running product. Note the header: `NUMERIC_GAP: NOT_IDENTIFIABLE`,
> `is_measured_shortage: false`.
>
> Observed NCS vacancies by sector — traceable to three named Parliament answers, and we recognised those
> three describe **one** observation, not three, so we deduplicated rather than summed.
>
> Below it, estimated occupation composition. NCS has no occupation axis at all; we found the bridge in
> ILOSTAT's India series. Confidence varies **by row** — not one badge for the table.
>
> And here — twenty and a half million vacancies, fifty-eight per cent of the published total, are PAN-India
> or multiple-state. They belong to no state. We never allocate them."

**`#state/27` → Maharashtra** *(0:35)*

> "Districts in Maharashtra. Now read the caveat we print **above** the table:
>
> *'within a state this ordering equals the Udyam enterprise-share ordering.'*
>
> We measured that. In **zero of thirty-six states** does the within-state ordering differ from ranking
> districts by enterprise share. So within a state this is an enterprise-density ranking — the demand
> component only varies **between** states.
>
> We could have called this 'highest-demand districts' and nobody would have caught it. Instead the caveat
> is stored as a column on every row, and the contract refuses to build a response without it."

**District without coverage** *(0:25)*

> "And this is the screen I'd most like you to see. This district has no occupation detail. Instead of a
> zero or a blank, you get `NOT_AVAILABLE` with the actual reason: the Census table hasn't been acquired for
> this state — *'an absence of acquired evidence, not an absence of demand.'*
>
> **No row in this system carries a signal of zero.**"

**`#unavailable`** *(0:20)*

> "And sixteen capabilities we don't publish, each with a reason and a gate."

*(~280 words + navigation · 1m45s)*

---

## 4:30–5:15 · Evidence and coverage *(slide 8)*

> "So let me be precise about coverage, because this is where most dashboards go quiet.
>
> Fifty-eight point one three per cent of published NCS vacancies — twenty million, five hundred and seven
> thousand — are PAN-India or multiple-state. Never allocated. Allocating them is a prohibited capability
> with its own blocked route.
>
> That means every district figure rests on the remaining **forty-one point eight seven** per cent, and we
> say so wherever a district figure appears.
>
> Occupation detail covers **a hundred and thirty-eight of seven hundred and eighty-five** districts. Five
> hundred and twenty-two are missing because we haven't acquired the Census table for their state. And a
> hundred and twenty-five are post-2011 districts for which a Census prior **can never exist**. Different
> problems, reported differently.
>
> All three numbers are read live from the warehouse — a test fails our build if they appear as literals in
> the code."

*(~160 words · 45s)*

---

## 5:15–6:00 · What's unavailable, and why *(slide 9)*

> "Now the question you're all waiting to ask. Where's the gap?
>
> We don't publish one. Supply by state and trade is a **joint distribution**. We hold the row totals, plus
> twenty-one point eight per cent of the column totals — seventy-eight per cent of enrolment sits in job
> roles the source doesn't name — and that fragment comes from a **different scheme**.
>
> Row and column totals never determine the interior. To close it you'd have to assume every state trains
> the same trade mix. That's false — regional variation is the thing we're asked to measure — and it's
> untestable, because not one state-by-trade cell exists to check against.
>
> So we could produce a number. It would look exactly like data. The error would be invisible,
> systematically wrong in one direction, and it informs seat sanctioning — real money.
>
> *(pause)* Instead, every blocked capability carries a gate. And notice the distinction: `NOT_ACQUIRED` is
> a paperwork problem. `NOT_IDENTIFIABLE` is a mathematical result."

*(~175 words · 45s)*

---

## 6:00–6:35 · Innovation *(slide 10)*

> "If you take one thing from the engineering, take this: the system distinguishes *'we don't have this
> data'* from *'this quantity isn't identifiable from evidence of this shape'* — and treats the second as a
> result, not a backlog item.
>
> That's enforced, not documented. The publication contract is code. Evidence status is **read from the
> data**, never declared — we have a test that forges a config claiming a derived output is observed and
> proves the API still says estimated. The terminology lint fails the build if anyone writes 'demand
> ranking', including inside translation files.
>
> And I should be direct about one thing: **there is no machine-learning model in production.** We won't
> invent one to match a title. Forecasting needs two dated observations and we have one; a learned gap model
> needs a target variable and the target isn't identifiable. Every ML capability this problem statement
> implies is blocked by the same missing evidence — not by modelling."

*(~165 words · 35s)*

---

## 6:35–7:00 · Close *(slides 11 → 12)*

> "So what would change this? *(slide 11)* One dataset. State-by-trade training outcomes with complete
> marginals. That's gate G-1, and with it this platform computes the gap that was asked for — with no
> formula change. In parallel, the Census table for thirty-three more states takes district coverage from a
> hundred and thirty-eight toward seven hundred and eighty-five, also with no code change.
>
> *(slide 12)* So — we don't manufacture a skill gap from incomplete data. We build the evidence
> infrastructure that makes the gap computable when the right data arrives.
>
> I'd rather hand MSDE a specific, costed data request than a number that restates an assumption.
>
> Happy to take the hardest question you have."

*(~130 words · 25s)*

---

## Rehearsal notes

**If you're running long** — compress 1:15–2:00 to the four components and one failed approach; compress
2:00–2:45 to the red boundary and the contract. **Never compress** the live demo or 5:15–6:00.

**If you're running short** — slow down. Add the Census double-counting story (*"an early parser
double-counted by 1,612,514 workers; a row-type classifier fixed it, and every reconciliation is now
exact"*) at 2:00. Don't add new claims.

**Three sentences to deliver cleanly, because the whole talk rests on them:**

1. *"Not one of these sources carries a district-by-occupation vacancy count."*
2. *"In zero of thirty-six states does the within-state ordering differ from enterprise share."*
3. *"Row and column totals never determine the interior."*

**Never say:** "we forecast" · "the skill gap" (except in the negation on slide 12) · "highest-demand
districts" · "training supply" · "PLFS shows demand" · "data as of today".
