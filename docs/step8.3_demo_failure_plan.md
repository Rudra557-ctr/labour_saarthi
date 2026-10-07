# Demo Failure Plan

One rule above all: **never invent a result.** If the live product cannot show something, say so plainly and
switch to the verified captures. A presenter who handles a failure calmly loses nothing; a presenter who
fabricates loses everything.

**The universal sentence**, which works for almost every failure:

> *"The live app isn't cooperating — let me show you the same screen from the verified build."*

---

## Failure matrix

### F1 · API unavailable

| | |
|---|---|
**Detection** | Every page shows the error card; `curl localhost:8000/api/health` fails |
**Immediate** | One attempt: `make serve` in the spare terminal. Do **not** debug on stage. |
**Say** | *"The backend isn't up — I'll run this from the verified captures instead. These are from the same build, taken this morning."* |
**Fallback** | Screenshot folder, or **PPTX slide 7** which carries four of them |
**Cost** | ~10 s |

### F2 · Frontend unavailable (API fine)

| | |
|---|---|
**Detection** | `/` 404s or renders blank, but `/api/health` returns ok |
**Immediate** | Switch to `localhost:8000/docs` — the API is the product too |
**Say** | *"The dashboard isn't serving, but the API is — and honestly this is the layer that matters. Here are the same outputs with their evidence envelope."* |
**Fallback** | `/docs` → `/api/demand/districts?state=27`, then screenshots |

### F3 · Slow query / page hangs

| | |
|---|---|
**Detection** | Nothing after ~3 s *(normal is well under 100 ms)* |
**Immediate** | **Keep talking** — the script does not depend on the pixels. One sentence of grace. |
**Say** | *(no announcement — just continue, then)* *"While that settles, here's the same screen from the verified build."* |
**Fallback** | Screenshot. **Do not refresh twice.** |

### F4 · Screenshot does not match what you are describing

| | |
|---|---|
**Detection** | The caption or number on screen differs from your sentence |
**Immediate** | **Read what is actually there.** Correct yourself in one clause. |
**Say** | *"— actually that's the figure for a different state; the point holds: the caveat sits above the table."* |
**Never** | Carry on with the rehearsed number. A judge who spots the mismatch will stop trusting everything else. |

### F5 · Browser or network failure

| | |
|---|---|
**Detection** | Browser crash, or wifi drops |
**Immediate** | Reopen the browser. **Network is not needed** — no CDN, no external API, no Node build. |
**Say** | *"No network required for this — it runs entirely locally. One moment."* |
**Fallback** | PPTX |
**Note** | Worth saying out loud even when nothing fails: *"this runs fully offline."* |

### F6 · Wrong filter selected

| | |
|---|---|
**Detection** | Wrong state or district on screen |
**Immediate** | Fix it silently if it takes one click; otherwise narrate the correction |
**Say** | *"Wrong state — here's Maharashtra."* |
**Never** | Describe Maharashtra's numbers while Kerala is on screen |

### F7 · Empty result where you expected rows

| | |
|---|---|
**Detection** | The *"No matching observation"* notice appears |
**Immediate** | **This is a feature — use it** |
**Say** | *"That's actually worth seeing: an available output with nothing matching says 'no matching observation' — which is deliberately different from 'unavailable'. One means we looked and found nothing; the other means the quantity cannot be computed."* |
**Fallback** | None needed — you just demonstrated the evidence framework |

### F8 · Laptop or projector problem

| | |
|---|---|
**Detection** | No signal, wrong resolution, mirroring fails |
**Immediate** | Switch to the backup laptop; otherwise present from the printed deck |
**Say** | *"I'll carry on without the screen — the argument doesn't need it."* |
**Fallback** | The 3-minute script works entirely verbally. Rehearse it at least once with no screen. |
**Prevention** | Test the projector **before** the session; the deck is 16:9 |

### F9 · Dark/light theme mismatch

| | |
|---|---|
**Detection** | The dashboard renders dark (the OS is in dark mode) and washes out on the projector |
**Immediate** | Switch the **operating system** to Light appearance — the page follows `prefers-color-scheme` |
**Say** | *(nothing — fix it in pre-flight)* |
**Fallback** | Use the screenshots, which were captured forced to light mode |
**Prevention** | **Set the laptop to Light appearance during pre-flight.** This is the single most likely cosmetic failure. |

### F10 · Missing font

| | |
|---|---|
**Detection** | PPTX text reflows or looks wrong on the presentation machine |
**Immediate** | Nothing mid-talk |
**Say** | *(nothing)* |
**Prevention** | The deck uses **Arial and Consolas only** — both standard on Windows and macOS. **Open the deck on the actual presentation machine beforehand** (this is the outstanding manual check). |

### F11 · A judge asks for a filter you have not rehearsed

| | |
|---|---|
**Detection** | *"Can you show me Bihar?" / "What about division 3?"* |
**Immediate** | **Do it** — the filters work and it is far more convincing than deflecting |
**Say first** | *"Yes — and I'll read what comes up rather than predict it."* |
**Then** | Navigate, pause, **read the screen aloud** |
**Guard** | If they pick a state with no occupation coverage (anything outside UP, Maharashtra, Tamil Nadu), you will get `NOT_AVAILABLE`. **That is a good outcome:** *"And there's the honest answer — occupation detail covers three states, and this one shows the reason rather than a zero."* |
**Never** | Predict a number before it renders |

### F12 · A judge asks for something the system cannot do

| | |
|---|---|
**Detection** | *"Show me the gap for Pune."* |
**Immediate** | Navigate to `#unavailable`, or `/api/demand-supply-gap` in the API tab |
**Say** | *"I can show you exactly what happens when you ask for that."* → *(the reason code and gate appear)* → *"HTTP 200, data null, reason NOT_IDENTIFIABLE, gate G-1. We don't 404 it, because a 404 would read as 'none found' rather than 'not computable'."* |
**Note** | **This is the strongest possible answer.** It turns the request into a demonstration. |

---

## Decision tree

```
Something failed on screen
        │
        ├─ Is it fixable in ONE action (one click, one command)?
        │        YES → do it silently, keep narrating
        │        NO  ▼
        ├─ Do I have a verified screenshot of this exact screen?
        │        YES → "let me show you the same screen from the verified build" → continue
        │        NO  ▼
        ├─ Can I make the point from the PPTX?
        │        YES → switch to the slide, keep the same sentence
        │        NO  ▼
        └─ Say what you were going to show and why it matters.
           The argument stands without the pixels. NEVER invent the result.
```

---

## Pre-flight checklist (prevents F1, F3, F6, F8, F9, F10)

- [ ] `make serve` running; `/api/health` returns `status: ok`
- [ ] All 8 pages clicked once
- [ ] **OS appearance set to Light**
- [ ] Browser zoom 125–150%
- [ ] District codes re-verified *(they are data-dependent)*
- [ ] Screenshot folder open in a background tab
- [ ] PPTX open in presenter view on the **presentation machine**
- [ ] Projector tested at 16:9
- [ ] Spare terminal open, already in the project directory
- [ ] Wifi off once, to confirm the demo is genuinely offline
