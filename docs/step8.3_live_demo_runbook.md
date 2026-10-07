# Live Demo Runbook

**Every route, filter and expected result below was executed against the running application on
2026-10-06.** Nothing here requires a feature the system does not have.

---

## Pre-flight (do this 10 minutes before)

```bash
cd /path/to/LMIS
make serve                      # http://127.0.0.1:8000
curl -s localhost:8000/api/health
```

**Expect:** `{"status":"ok","contract_version":"7.3.1","production_outputs":12,
"unavailable_capabilities":16,"is_measured_shortage":false, …}`

| Check | Expected |
|---|---|
`/` loads, header mode chips visible | `NUMERIC_GAP: NOT_IDENTIFIABLE`, `is_measured_shortage: false` |
All 8 nav items clickable | landing · national · state · district · occupation · methodology · coverage · unavailable |
Browser zoom | **125–150%** — the audience is 10 m away |
Second tab | `localhost:8000/docs` |
Third tab | `docs/assets/screenshots/` open in a file viewer — **the fallback** |
Network | **none needed.** No CDN, no external API. Turn wifi off to prove it if asked. |

**Resolve the two district codes before you start** — they are data-dependent, not fixed:

```bash
curl -s "localhost:8000/api/demand/district-occupation?state=27&occupation_prior_status=AVAILABLE" \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['data'][0]; print('WITH:', d['lgd_code'], d['district_name_lgd'])"
curl -s "localhost:8000/api/demand/district-occupation?state=32" \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['data'][0]; print('WITHOUT:', d['lgd_code'], d['district_name_lgd'])"
```

On the verified build these resolve to **490 / Pune** (with coverage) and **554 / Alappuzha** (without).
**Write both on your hand.**

---

## A · Normal path — 1 m 45 s inside the 7-minute talk

### A1 · `#national` — 25 s

| | |
|---|---|
**Route** | `http://127.0.0.1:8000/#national` |
**Filter** | none |
**Expect** | 4 panels: `■ Observed` NCS by sector (22 rows) · `◪ Estimated` occupation composition (175 rows, per-row confidence) · `□ SUPPORTING CONTEXT — NOT A DEMAND MEASURE` · the residual disclosure |
**Say** | *"Observed NCS vacancies by sector — three named Parliament answers, describing one observation, so we deduplicated rather than summed. Below, estimated occupation composition: NCS has no occupation axis, so we bridged it through ILOSTAT's India series — and confidence varies by row, not one badge for the table. And here: twenty and a half million vacancies, fifty-eight per cent, are PAN-India. They belong to no state. We never allocate them."* |
**If it does not load** | → §C1 |

### A2 · `#state/27` — 35 s · **the credibility moment**

| | |
|---|---|
**Route** | `#state/27`, or click **State** then select **Maharashtra** |
**Filter** | State = Maharashtra (LGD 27) |
**Expect** | `■ Observed` 15,33,463 · the **amber caveat box** above the table · 36 districts ordered by `rank_within_state` · an `Udyam enterprise share` column · `Must not be read as: VACANCY_COUNT · …` |
**Say** | *"Districts in Maharashtra. Read the caveat we print above the table — 'within a state this ordering equals the Udyam enterprise-share ordering.' In zero of thirty-six states does it differ. So within a state this is enterprise density; the demand component only varies between states. We could have called it 'highest-demand districts' and nobody would have caught it."* |
**Do** | **Point at the amber box before the table.** This is the single most persuasive moment in the demo. |
**If slow** | → §C2 |

### A3 · District **without** coverage — 25 s

| | |
|---|---|
**Route** | `#district/554` *(Alappuzha — verify the code at pre-flight)* |
**Expect** | `⬚ Unavailable · NOT_AVAILABLE` · *"Occupation detail not available — CENSUS_NOT_ACQUIRED"* · *"This is an absence of acquired evidence, not an absence of demand."* |
**Say** | *"This district has no occupation detail. Instead of a zero or a blank, you get NOT_AVAILABLE with the actual reason. No row in this system carries a signal of zero."* |
**If wrong district** | → §C6 |

### A4 · `#unavailable` — 20 s

| | |
|---|---|
**Route** | `#unavailable` |
**Expect** | 16 capabilities grouped by reason code; `NOT_IDENTIFIABLE` visibly distinct from `NOT_ACQUIRED`; each with `blocking_gate` |
**Say** | *"Sixteen capabilities we don't publish, grouped by reason. NOT_ACQUIRED is a paperwork problem. NOT_IDENTIFIABLE is a mathematical result. The gap sits in the second group."* |

### A5 · Optional 20 s if ahead — `/docs`

> *"Thirty routes. Ten are blocked, and they return HTTP 200 with `data: null`, a reason and a gate — not
> 404, because a 404 reads as 'none found' rather than 'not computable'."*

**Optional instead:** open a downloaded CSV and point at the `#` header lines.

---

## B · Fast path — 50 s

Two screens only.

| Order | Route | Say |
|---|---|---|
1 | `#state/27` | *"Districts ranked on a relative allocation signal — and the caveat above the table says within a state this ordering IS the Udyam enterprise-share ordering. Zero of thirty-six states differ. We print our own weakness above the number."* |
2 | `#unavailable` | *"And sixteen capabilities we don't publish, each with a reason and a gate. The demand–supply gap is NOT_IDENTIFIABLE — supply by state and trade is a joint distribution and we hold only its margins."* |

**Cut:** national, district, occupation, `/docs`. **Never cut** the caveat box or the unavailable page.

---

## C · Failure fallback — **never invent a result**

The screenshots in `docs/assets/screenshots/` were captured from **this same verified build**. Say so, and
keep going. See `docs/step8.3_demo_failure_plan.md` for the full matrix.

### C1 · A page does not load

> *"The live app isn't cooperating — let me show you the same screen from the verified build."*

→ Switch to the screenshot tab or the PPTX (slide 7 carries four of them). **Continue the same script.**

### C2 · A page is slow (> 3 s)

Keep talking over it — the narration above does not depend on the pixels appearing. If it has not arrived
after one sentence, go to §C1. **Do not refresh twice in front of judges.**

### C3 · Backend down

```bash
curl -s localhost:8000/api/health || make serve
```

> *"I'll run the rest from the verified captures rather than spend your time on a restart."*

### C6 · Wrong district (shows data when you expected NOT_AVAILABLE, or vice versa)

Do **not** improvise a story about the district. Say:

> *"That's a district that does have Census coverage — the one I meant is here."*

Navigate to the correct code, or go to screenshot `05_district_not_available.png`. **The district codes are
data-dependent; re-verify them at pre-flight.**

---

## What you must never do

- **Never type a filter you haven't rehearsed** while narrating. If a judge asks for one, see §C9 of the
  failure plan: do it, but **read what appears** rather than predicting it.
- **Never explain a number that isn't on screen.** If the page didn't load, switch to the screenshot first.
- **Never say a screenshot is live.** Say *"this is from the verified build."*
- **Never refresh more than once.** Two failed refreshes in front of judges costs more than the fallback.
