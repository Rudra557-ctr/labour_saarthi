# Presentation Checklist — LMIS · SIH 2026

Work top to bottom. **Everything in "Blocking" must pass before presenting.**

---

## Blocking — do not present without these

| ✓ | Item | How to verify | Status |
|---|---|---|---|
☐ | **Backend starts** | `make serve` → `curl -s localhost:8000/api/health` returns `status: ok`, contract `7.3.1` | **PASS** (verified) |
☐ | **Dashboard loads** | open `/` — 8 pages reachable, header mode chips visible | **PASS** |
☐ | **Runs offline** | disconnect wifi, reload — no Node build, no CDN, no external API | **PASS** |
☐ | **All 12 slides present** | `docs/step8.1_final_slide_content.md` | **READY** |
☐ | **Architecture diagram drawn** | from `docs/step8.1_architecture_diagram.md`, incl. the **no-fabrication boundary** | **SPEC READY** — needs drawing |
☐ | **7-min demo rehearsed to time** | `docs/step8.1_final_demo_script.md` §A | **READY** |
☐ | **3-min fallback rehearsed** | §B | **READY** |
☐ | **60-sec pitch memorised** | §C / `docs/step8.1_value_proposition.md` | **READY** |
☐ | **20 judge answers reviewed** | `docs/step8.1_final_judge_answers.md` | **READY** |
☐ | **Claims checklist read by every speaker** | `docs/step8.1_claims_checklist.md` | **READY** |

---

## Content ready

| ✓ | Item | Reference |
|---|---|---|
☐ | Requirement mapping slide | `docs/step8.1_ps_compliance_slide.md` — 6 implemented / 4 partial / 3 blocked / 2 not-supported / 1 experimental |
☐ | Innovation slide — 5 claims, none of them "we used a framework" | `docs/step8.1_innovation_slide.md` |
☐ | Future roadmap — gates, **no dates** | `docs/step8.1_future_roadmap_slide.md` |
☐ | Screenshots captured as demo insurance | National · State (with caveat box visible) · District `NOT_AVAILABLE` · Unavailable capabilities · a CSV header |
☐ | `/docs` OpenAPI tab open in a second browser tab | 30 routes |
☐ | One export downloaded in advance | `demand_district_relative_signal.csv` — to show the metadata header offline |

---

## Facts verified against the repository *(re-verified 2026-10-06)*

| ✓ | Fact | Value |
|---|---|---|
☑ | Tables · migrations · rows | **40 · 7 · 82,358** |
☑ | Tests | **479 passing** |
☑ | `make reproduce` | **clean** |
☑ | Published NCS total | **35,275,833** |
☑ | PAN-India residual | **20,507,320 (58.13%)** |
☑ | State-attributable | **14,768,513 (41.87%)** |
☑ | Districts with occupation structure | **138 of 785** (522 not acquired · 125 can never have one) |
☑ | Sources | **26 registered · 15 acquired · 35 files · 50.5 MB · 6 in production** |
☑ | NCO-2015 · concordance · LGD · NIC | **3,982 · 3,447 · 821 · 21** |
☑ | API routes | **30 (20 production · 10 blocked)** |
☑ | Unavailable capabilities | **16** |
☑ | Trades officially NCO-mapped | **2 of 155** (153 `MAPPING_UNKNOWN`) |
☑ | Top-N column coverage | **21.8%** (514,619 of 2,361,798) |
☑ | Reconciliations | **14 of 14 exact** |

---

## Safety checks

| ✓ | Check | Status |
|---|---|---|
☑ | **No unsupported claim** in any slide, script or answer | audited — see Final claims audit below |
☑ | **No synthetic data** referenced or implied | none exists |
☑ | **No accidental gap claim** | `NUMERIC_GAP: NOT_IDENTIFIABLE` throughout |
☑ | **No accidental forecast claim** | `FORECASTING: NOT_SUPPORTED_YET` throughout |
☑ | **No ML model claimed** | stated explicitly as absent in slide 10, Q3 and Q4 |
☑ | **Terminology checked** — no "demand ranking", "shortage", "supply" for training, "highest-demand" | product lint PASS (0 violations); documents hand-audited |
☑ | **Source and vintage on every quantitative slide** | footer rule in the storyboard |
☑ | **No global "data as of" date** | five vintages shown separately |
☑ | **Hybrid stays experimental** | `implemented: false`, absent from API/dashboard/exports |
☑ | **No impact number invented** | no deployment exists; stated as such |

---

## Final-hour run-through (15 minutes)

1. `make serve`, then `curl -s localhost:8000/api/health` → expect `status: ok`.
2. Click all 8 pages once. Confirm the **caveat box** is visible above the State district table.
3. Open one district **with** Census coverage and one **without** — confirm `NOT_AVAILABLE` + reason.
4. Open `/api/demand-supply-gap` → confirm **200** with `data: null` and `blocking_gate: G-1`.
5. Download one CSV → confirm the `#` metadata header is present.
6. Switch the language selector to हिन्दी and back → confirm no raw keys appear.
7. Read **list C** of the claims checklist aloud. Twice.

---

## Who says what

| Section | Owner | Fallback if asked something off-script |
|---|---|---|
Slides 1–3 (problem) | presenter A | "Let me come back to that in the demo." |
Slides 4–7 (architecture, data) | presenter B | defer to `docs/step8.0_sih_solution_story.md` §5–8 |
Live demo | presenter B | switch to screenshots; `/api/health` proves the backend |
Slides 9–12 (transparency, close) | presenter A | this is the strongest ground — stay on it |
**Q&A** | **whoever knows the answer** | *"I don't want to guess at that — the repository has it and I'd rather be exact."* **Never improvise a number.** |

---

## The one rule

> If a judge asks for something the system cannot do: **agree, say why in one sentence, and name the gate.**
> Do not hedge, and do not improvise a capability.

---

## Final claims audit

Every quantitative claim in all nine Step 8.1 documents was checked against the live repository.
**One error was found and corrected during Step 8.0** — the published NCS total, written as 35,275,830,
is **35,275,833**. No other discrepancy was found in Step 8.1.

**Result: all presentation claims pass.**
