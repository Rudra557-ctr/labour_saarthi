# Step 8.3 — Final PPTX Content Audit

Date: 2026-10-06 · Audit of `docs/step8.2_final_sih_presentation.pptx` — **12 slides, 12 speaker notes,
9 embedded images.** Every slide's text, numbers and notes were extracted from the package and checked
against the live repository and the frozen Step 8.1 content.

| | |
|---|---|
**Slides PASS** | **12 of 12** |
**Factual errors** | **0** |
**Unsupported claims** | **0** |
**Required edits** | **none** |
**Advisory observations** | 3 (all non-blocking, listed in §3) |
**Manual visual inspection on the presentation machine** | **REQUIRED — not performed** |

---

## 1. Slide-by-slide

| # | Title | Verdict | Finding | Action |
|---|---|---|---|---|
**1** | AI-Enabled Labour Market Intelligence | **PASS** | Positive framing per the approved Step 8.2 brief; does **not** open with the identification finding. Counters `26 / 40 tables · 82,358 rows / 30 routes / 479 tests` all verified. Source line present. | none |
**2** | Targets are set on data that cannot be joined | **PASS** | Six source cards with correct grains and vintages (2024-11-15 · 2023-12-21 · 2011 · monthly · Apr 2025 · 2024-03-31). Closing banner states no source carries a district × occupation vacancy count. Source line present. | none |
**3** | Why the problem is technically difficult | **PASS** | `gap_identification_gate.png`. Numbers `514,619 of 2,361,798 (21.8%)` verified. Source line present. | none |
**4** | Evidence-first architecture | **PASS** | `architecture_diagram.png`. No slide-level source line — **the diagram carries its own source footer**. | none (see A-1) |
**5** | Official data → standardised intelligence | **PASS** | `data_standardization.png`. Source line names DGE NCO-2015, the official concordance, LGD, NIC-2008 and DGT CTS curricula. | none |
**6** | Current analytical outputs | **PASS** | Six-row tier table. `157 MEDIUM / 18 LOW`, `785 districts`, `138 of 785` verified. Approved labels used **verbatim**. Unit `relative_signal_unitless` stated. Source line present. | none |
**7** | National → State → District → Occupation | **PASS** | Four **real screenshots** of the running build. Captions state the caveat and `NOT_AVAILABLE with a reason — never a zero`. Source line identifies them as screenshots of the running application. | none |
**8** | Provenance, coverage and confidence | **PASS** | `58.13% / 20,507,320`, `41.87% / 14,768,513`, `138 / 785` with `522` and `125` — **all match the warehouse exactly**. Plus `evidence_flow.png`. | none |
**9** | What cannot yet be measured | **PASS** | Six blocked capabilities with reason codes and gates, matching the contract. States the HTTP 200 / `data: null` design and why a 404 would mislead. Source line present. | none |
**10** | Identification-aware analytics | **PASS** | Five innovations. `0 of 36 states differ` verified. Red banner: **"no machine-learning model in production, and no ML library is installed."** Source line lists the libraries verified absent. | none |
**11** | One dataset unlocks the gap | **PASS** | `future_roadmap.png`. No dates. No slide-level source line — **the diagram carries the named blockers in its footer**. | none (see A-1) |
**12** | Impact | **PASS** | Three cards incl. an explicit **"Not claimed"** card (no policy savings, no jobs created). Approved closing statement. Proof strip verified. | none (see A-2) |

**No edits are required to the PPTX.**

---

## 2. Speaker notes

All 12 slides carry notes (292–550 characters). Audited for new or unsupported claims.

| Check | Result |
|---|---|
Notes present on every slide | **12 / 12** |
New claims not in the approved Step 8.1 notes | **0** |
Prohibited claims asserted | **0** |
Numbers in notes matching the repository | **PASS** |

Two automated flags were inspected by hand and are **correct usage**:

- **notes 9** — *"Supply by state and trade is a joint distribution"* — the identification argument, naming
  the quantity that does not exist.
- **slide 12** — *"We don't manufacture a skill gap from incomplete data"* — a negation, and the approved
  Step 8.1 closing line.

---

## 3. Advisory observations — non-blocking

**A-1 · Slides 4 and 11 carry no slide-level source line.**
Both are full-bleed diagrams whose **own footers** carry the attribution (slide 4: the six sources with
vintages; slide 11: the named blocked sources). The Step 8.2 rule — *"every slide containing important
quantitative claims must have a concise source line"* — is satisfied by the image. **No action; noted so a
reviewer does not read it as an omission.**

**A-2 · Slide 12's proof strip has no source line.**
`40 tables · 82,358 rows · 30 routes · 11 exports · 16 capabilities · 479 tests` are self-descriptions of the
system rather than external claims, and all are verified. **Optional:** add
*"Source: this repository, verified 2026-10-06."* if a reviewer prefers absolute uniformity.

**A-3 · The hybrid indicator is not mentioned anywhere in the deck.**
Deliberate and correct — an `EXPERIMENTAL_ONLY`, unimplemented output must not be raised unprompted. It is
covered in the judge Q&A and in `docs/step8.3_hard_judge_questions.md` if asked.

---

## 4. Consistency with Step 8.1 and with the product

| Check | Result |
|---|---|
Narrative order matches the approved 12-slide sequence | **PASS** |
Slide titles match `step8.1_final_slide_content.md` | **PASS** |
Approved product labels used verbatim | **PASS** — all three |
Capability states match `config/publication_contract.yaml` | **PASS** — 6 of 6 |
Blocked reason codes match the contract | **PASS** — 5 of 5 spot-checked |
Screenshots are of the current build | **PASS** — captured 2026-10-06 from the running app |
Numbers match the warehouse | **PASS** — 18 of 18 |

---

## 5. Readability

| Check | Result |
|---|---|
Clipped shapes | **0** |
Overlapping shapes | **0** |
Empty slides | **0** |
Smallest body text | **10.5 pt** (slide 7 captions) — readable at 16:9 on a projector |
Smallest text inside a diagram | ~19 px at native 2200–2400 px width |
Fonts used | **Arial, Consolas** only — both standard; no embedding needed |
Images resolving | **9 of 9** |

---

## 6. Manual visual inspection — **REQUIRED, NOT PERFORMED**

The deck passed **structural validation** (59 XML parts well-formed, no dangling relationships) and
**geometry QA** (no clipping, no overlaps, no empty slides). It was **never rasterised**: this environment
has no PowerPoint, no LibreOffice, and `qlmanage` requires a GUI session and times out.

**Before submission or presentation, a human must open the deck on the presentation machine and confirm:**

1. All 12 slides render with no missing text or images.
2. Diagrams on slides 3, 4, 5, 8 and 11 are legible from the back of the room.
3. Speaker notes appear in presenter view.
4. Arial and Consolas resolve on that machine (substitution would shift line breaks).
5. The 16:9 aspect ratio matches the projector.

**This audit does not and cannot certify visual rendering.**
