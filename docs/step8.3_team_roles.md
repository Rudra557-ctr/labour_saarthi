# Team Roles

**The repository specifies no team members, so no names are invented here.** Roles are defined by
responsibility; assign people to them.

**Assumed default: 5 presenters** (the standard SIH team size). Compressed versions for 3, 2 and 1 follow.

---

## 5-person split

### Presenter 1 — Problem and solution *(slides 1–3, ~1 m 45 s)*

**Owns:** the opening, the fragmentation problem, why it's technically difficult.
**Must land:** *"Not one of these sources carries a district-by-occupation vacancy count."*
**Prepares:** `step8.3_rehearsal_script.md` 0:00–2:00; rapid sheet §A, §B.
**If asked something off-script:** *"Let me come back to that in the demo."*

### Presenter 2 — Architecture and data *(slides 4–6, ~1 m 15 s)*

**Owns:** the architecture diagram, standardisation, the production output table.
**Must land:** the **no-fabrication boundary** on slide 4 — point at it, don't read the boxes.
**Prepares:** rehearsal 2:00–2:45; rapid sheet §B, §D, §F. Knows the NCO/LGD/NIC counts cold.
**Backup for:** Presenter 3 (should be able to run the demo).

### Presenter 3 — Live demonstration *(~1 m 45 s)*

**Owns:** the browser, the pre-flight, and the failure decision.
**Must land:** the amber caveat box on `#state/27`, and `NOT_AVAILABLE` with its reason.
**Prepares:** `step8.3_live_demo_runbook.md` **and** `step8.3_demo_failure_plan.md`, both rehearsed —
including once with the screen deliberately off.
**Sole authority** to decide mid-demo whether to switch to screenshots. Nobody else interrupts that call.
**Owns pre-flight:** OS light mode, zoom, district codes re-verified, screenshots tab open.

### Presenter 4 — Methodology and limitations *(slides 8–9, ~1 m 30 s)*

**The most important speaking role.** Owns coverage, the identification argument, and what is unavailable.
**Must land:** *"Row and column totals never determine the interior."* Say it slowly.
**Prepares:** rehearsal 4:30–6:00; rapid sheet §E; `step8.3_hard_judge_questions.md` Q1, Q6, Q10.
**Tone:** this is the credibility slide — confident, never apologetic.

### Presenter 5 — Innovation, close, and Q&A anchor *(slides 10–12, ~1 m 05 s + Q&A)*

**Owns:** innovation, the roadmap, the closing statement, and the Q&A.
**Must land:** *"There is no machine-learning model in production"* — directly, without hedging.
**Prepares:** the full `step8.3_hard_judge_questions.md`; rapid sheet end to end. Holds the printed sheet.
**In Q&A:** routes each question to whoever knows it best. Answers "where's the AI?" personally.

---

## Compressed splits

### 3 presenters

| Role | Covers | Time |
|---|---|---|
**A** | slides 1–3 (problem) + slides 8–9 (coverage, unavailable) | ~3 m 15 s |
**B** | slides 4–6 (architecture, data) + slides 10–12 (innovation, close) | ~2 m 20 s |
**C** | **live demo only** — plus pre-flight and the failure call | ~1 m 45 s |

Keep the demo as a dedicated role even at three people. It needs undivided attention.

### 2 presenters

| Role | Covers |
|---|---|
**A** | slides 1–6 (problem → outputs), then hands over |
**B** | live demo + slides 8–12 + Q&A |

**B gets the heavier half** — the demo and the identification argument are the two things that must land.

### 1 presenter

Follow `step8.3_rehearsal_script.md` straight through. **Rehearse the demo transition twice** — switching
applications alone is where solo presentations lose time. Keep the rapid sheet face-down beside the laptop.

---

## Q&A protocol

1. **Presenter 5** (or B, or the solo presenter) takes every question first and routes it.
2. **Whoever knows the answer gives it** — seniority is irrelevant.
3. **Nobody improvises a number.** The fallback sentence, for anyone:
   > *"I don't want to guess at that — it's in the repository and I'd rather be exact than approximate."*
4. **Only one person speaks per question.** Corrections come from the same person who answered.
5. If a question exposes a real weakness, **concede it first**, then show the measurement. See
   `step8.3_hard_judge_questions.md`.

---

## Handover lines

Rehearse these — a clean handover looks prepared; an unclear one looks improvised.

| From → To | Line |
|---|---|
P1 → P2 | *"So that's the problem. Here's what we built."* |
P2 → P3 | *"Rather than describe it — here it is running."* |
P3 → P4 | *"So let me be precise about what that covers, and what it doesn't."* |
P4 → P5 | *"Which brings us to what's actually new here."* |
P5 → Q&A | *"Happy to take the hardest question you have."* |

---

## Shared obligations

Everyone presenting must have read **`docs/step8.1_claims_checklist.md`, list C** — the never-say list —
and must know these four:

- Never "we forecast" · never "the skill gap" (except the negation on slide 12)
- Never "highest-demand districts" · never "training supply"
- Never "data as of today" — five vintages, each figure carries its own
- Never an impact number — no deployment exists

**One shared instinct:** if a judge is right, say so first.
