"""Build the final SIH deck from the APPROVED Step 8.1 slide content.

Narrative, wording and numbers come from docs/step8.1_*. Nothing new is claimed
here. Presentation assets only - no implementation file is read or written.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pptx_writer import Para, Run, Shape, Slide, write_pptx  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "assets"
SHOTS = ASSETS / "screenshots"

INK = (21, 23, 28); MUTED = (104, 112, 128); LINE = (203, 210, 222)
PANEL = (247, 248, 251); ACCENT = (26, 79, 160); ACCENT_L = (233, 240, 250)
OBS = (21, 84, 58); OBS_L = (226, 242, 234)
EST = (138, 100, 0); EST_L = (253, 243, 220)
SUP = (60, 74, 99); SUP_L = (237, 241, 247)
UNA = (154, 42, 42); UNA_L = (250, 232, 232)
W, H = 13.333, 7.5


def title(txt, sub=None, y=0.42):
    sh = [Shape("text", 0.62, y, W - 1.3, 0.72,
                [Para([Run(txt, 30, True, INK)], space_after=0)], v_anchor="ctr", margin=0)]
    if sub:
        sh.append(Shape("text", 0.62, y + 0.74, W - 1.3, 0.42,
                        [Para([Run(sub, 15, False, MUTED)], space_after=0)],
                        v_anchor="ctr", margin=0))
    return sh


def source(txt):
    return Shape("text", 0.62, H - 0.56, W - 1.3, 0.34,
                 [Para([Run(txt, 10.5, False, MUTED)], space_after=0)],
                 v_anchor="ctr", margin=0)


def card(x, y, w, h, head, lines, fg=INK, bg=None, line=LINE, head_sz=15, body_sz=12.5):
    paras = [Para([Run(head, head_sz, True, fg)], space_after=5)]
    for ln in lines:
        paras.append(Para([Run(ln, body_sz, False, INK)], space_after=3))
    return Shape("text", x, y, w, h, paras, fill=bg, line=line, radius=True, margin=0.16)


def pic(path, x, y, w, h):
    return Shape("pic", x, y, w, h, image=path)


def fit(path: Path, x, y, max_w, max_h):
    """Scale an image into a box, preserving aspect ratio and centring it."""
    from PIL import Image
    iw, ih = Image.open(path).size
    s = min(max_w / iw, max_h / ih)
    w, h = iw * s, ih * s
    return pic(path, x + (max_w - w) / 2, y + (max_h - h) / 2, w, h)


S = []

# ---------------------------------------------------------------- 1 Title --
S.append(Slide(shapes=[
    Shape("text", 0.62, 1.55, W - 1.3, 1.9, [
        Para([Run("AI-Enabled Labour Market Intelligence", 40, True, INK)], space_after=8),
        Para([Run("From fragmented official data to evidence-backed skill demand signals",
                  21, False, ACCENT)], space_after=0)], v_anchor="ctr", margin=0),
    Shape("text", 0.62, 3.6, W - 1.3, 0.5,
          [Para([Run("Smart India Hackathon 2026  ·  PS ID 26246  ·  Ministry of Skill "
                     "Development and Entrepreneurship", 14, False, MUTED)], space_after=0)],
          v_anchor="ctr", margin=0),
    card(0.62, 4.45, 2.95, 1.0, "26", ["official sources, under a", "licence gate"], ACCENT, PANEL, LINE, 15, 12),
    card(3.74, 4.45, 2.95, 1.0, "40 tables · 82,358 rows", ["conformed warehouse"], ACCENT, PANEL, LINE, 15, 12),
    card(6.86, 4.45, 2.95, 1.0, "30 API routes", ["20 production · 10 blocked"], ACCENT, PANEL, LINE, 15, 12),
    card(9.98, 4.45, 2.73, 1.0, "479 tests", ["one command rebuilds", "everything"], ACCENT, PANEL, LINE, 15, 12),
    source("Every figure in this deck is verified against the running repository."),
], notes=(
    "PS 26246 asks for a demand-supply gap forecasting engine. We built the platform such an "
    "engine requires - and we will show you something most teams will not: exactly which number "
    "the evidence cannot support, and why that matters more than a confident guess.\n\n"
    "Keep this slide to 20 seconds. Do not open with the limitation; open with the build.")))

# -------------------------------------------------------------- 2 Problem --
rows = [("NCS", "state", "2024-11-15"), ("Udyam", "district", "2023-12-21"),
        ("Census B-24", "district x occupation", "2011"),
        ("LGD", "geography directory", "monthly"),
        ("PLFS", "national only", "Apr 2025"),
        ("MSDE AR", "state x scheme", "2024-03-31")]
sh = title("Targets are set on data that cannot be joined",
           "Six official sources feed production. None of them is directly comparable with another.")
for i, (nm, grain, vin) in enumerate(rows):
    x = 0.62 + (i % 3) * 4.08
    y = 1.85 + (i // 3) * 1.25
    sh.append(card(x, y, 3.85, 1.05, nm, [f"grain: {grain}", f"vintage: {vin}"],
                   INK, PANEL, LINE, 16, 12.5))
sh += [
    Shape("text", 0.62, 4.5, W - 1.3, 1.5, [
        Para([Run("Five vintages spanning fourteen years.  Two occupation schemes.  "
                  "Three statistical natures.", 17, True, INK)], space_after=8),
        Para([Run("No source carries a district x occupation vacancy count — which is exactly "
                  "what the finest requirement needs.", 17, True, UNA)], space_after=0)],
          fill=UNA_L, line=UNA, radius=True, v_anchor="ctr", margin=0.3),
    source("Sources: NCS Parliament answers · Udyam MSME · Census 2011 B-24 · LGD · PLFS · "
           "MSDE Annual Report 2023-24"),
]
S.append(Slide(shapes=sh, notes=(
    "Before a state sanctions seats, it needs to know which district-and-trade combinations are "
    "heading for shortage or oversupply. Today that judgement is last year's targets plus a bit.\n\n"
    "The data exists - in five vintages across fourteen years, two occupation schemes, and three "
    "different statistical natures. Not one source carries a district-by-occupation vacancy count.")))

# ------------------------------------------------- 3 Why it is difficult --
S.append(Slide(shapes=title(
    "Why the problem is technically difficult",
    "A gap is computable only when four components line up. One missing component blocks it.") + [
    fit(ASSETS / "gap_identification_gate.png", 0.62, 1.55, W - 1.3, 5.2),
    source("Source: Step 6 identification analysis · PMKVY 4.0 Top-10 job roles = 514,619 of "
           "2,361,798 enrolments (21.8%)"),
], notes=(
    "Three failure modes recur in work on this problem. Scraping job portals - richest data, least "
    "defensible: postings are not vacancies, and it breaches terms of service. Treating a "
    "classification as a crosswalk - we proved NCS's 22 'sectors' are NIC-2008 industry sections, "
    "not occupations, so no sector-to-occupation mapping can exist as a function. And filling the "
    "gap with an assumption and calling it a model.\n\n"
    "We have the demand side. We do not have supply at a compatible grain - and that single missing "
    "component is what blocks the result.")))

# -------------------------------------------- 4 Evidence-first architecture --
S.append(Slide(shapes=title(
    "Evidence-first architecture",
    "Official sources in, provenance out — nothing invented in between.") + [
    fit(ASSETS / "architecture_diagram.png", 0.5, 1.4, W - 1.0, 5.4),
], notes=(
    "Left to right is unremarkable. Two things are not.\n\n"
    "The publication contract near the bottom: evidence status, confidence, coverage and "
    "prohibited interpretations are part of the response contract, and the application refuses "
    "to start if any output breaches it.\n\n"
    "And the red boundary: where compatible supply evidence is missing, the pipeline BLOCKS "
    "rather than estimates. Do not read the boxes aloud - point at those two things.")))

# ------------------------------------------- 5 Official data -> standardised --
S.append(Slide(shapes=title(
    "Official data → standardised intelligence",
    "Every mapping carries its authority, method and confidence.") + [
    fit(ASSETS / "data_standardization.png", 0.62, 1.5, W - 1.3, 5.25),
    source("Sources: DGE NCO-2015 · official NCO-2004 concordance · LGD · NIC-2008 · "
           "DGT CTS curricula"),
], notes=(
    "NCO-2015 is the occupation spine - 3,982 occupations. Census is coded in NCO-2004, so it is "
    "bridged through the OFFICIAL 3,447-row concordance, and division purity is measured rather "
    "than assumed.\n\n"
    "Our one official trade-to-NCO link came from DGT's own CTS curriculum PDFs, which carry a "
    "Trade Code and an NCO-2015 field - that gave us two trades. The other 153 remain "
    "MAPPING_UNKNOWN. We could have matched all 155 by name resemblance in an afternoon. Fuzzy, "
    "semantic and LLM mapping are prohibited project-wide, because the result would be invented.")))

# ------------------------------------------------- 6 Current outputs --------
outs = [
    ("OBSERVED", "NCS state demand", "state (37 + 1 residual)", "OBSERVED", OBS, OBS_L),
    ("OBSERVED", "NCS demand by industry", "22 NCS sectors", "OBSERVED", OBS, OBS_L),
    ("ESTIMATED", "National occupation composition", "NIC section x NCO division",
     "157 MEDIUM / 18 LOW", EST, EST_L),
    ("ESTIMATED", "District Relative Demand Allocation Signal", "785 districts", "MEDIUM", EST, EST_L),
    ("ESTIMATED", "District x Occupation Relative Demand Allocation Signal",
     "138 of 785 districts", "LOW", EST, EST_L),
    ("SUPPORTING", "Labour-force context (PLFS)", "national only",
     "not a demand measure", SUP, SUP_L),
]
sh = title("Current analytical outputs",
           "Two observed products, three estimated signals, one context panel — each labelled "
           "on the face of the product.")
y = 1.75
for tier, nm, grain, conf, fg, bg in outs:
    sh.append(Shape("text", 0.62, y, 1.65, 0.62,
                    [Para([Run(tier, 11, True, fg)], align="ctr", space_after=0)],
                    fill=bg, line=fg, radius=True, v_anchor="ctr", margin=0.04))
    sh.append(Shape("text", 2.42, y, 5.75, 0.62,
                    [Para([Run(nm, 14.5, True, INK)], space_after=0)], v_anchor="ctr", margin=0.08))
    sh.append(Shape("text", 8.25, y, 2.3, 0.62,
                    [Para([Run(grain, 12, False, MUTED)], space_after=0)], v_anchor="ctr", margin=0.05))
    sh.append(Shape("text", 10.62, y, 2.09, 0.62,
                    [Para([Run(conf, 11, True, fg)], align="ctr", space_after=0)],
                    v_anchor="ctr", margin=0.04))
    y += 0.72
sh += [
    Shape("text", 0.62, y + 0.08, W - 1.3, 0.62, [
        Para([Run("Unit of the signals:  relative_signal_unitless  —  not a count. "
                  "Occupation axis bridged via ILOSTAT/PLFS  P(NCO division | NIC section).",
                  13.5, True, ACCENT)], space_after=0)],
          fill=ACCENT_L, line=ACCENT, radius=True, v_anchor="ctr", margin=0.18),
    source("Source: publication contract 7.3.1 · NCS Parliament answers as on 15 Nov 2024"),
]
S.append(Slide(shapes=sh, notes=(
    "NCS has no occupation axis at all. We found the bridge in ILOSTAT's India series - whose own "
    "source is PLFS - giving an official probability of NCO division given NIC section. That makes "
    "the occupation composition estimated, and confidence varies by row, not one badge per table.\n\n"
    "Note the product names: Allocation Signal. Never 'demand ranking'. A terminology lint fails "
    "the build if anyone writes that.")))

# ------------------------------------------------- 7 Drill-down journey -----
sh = title("National → State → District → Occupation",
           "The live product. Evidence weakens as you drill down, and the interface says so.")
shots = [("02_national.png", "NATIONAL", "observed + estimated + context, kept apart"),
         ("03_state_maharashtra.png", "STATE", "districts within state, with the caveat above the table"),
         ("05_district_not_available.png", "DISTRICT", "NOT_AVAILABLE with a reason — never a zero"),
         ("06_occupation.png", "OCCUPATION", "districts within state x NCO division")]
for i, (f, tag, cap) in enumerate(shots):
    x = 0.62 + i * 3.14
    sh.append(Shape("text", x, 1.62, 2.95, 0.34,
                    [Para([Run(tag, 12, True, ACCENT)], space_after=0)], v_anchor="ctr", margin=0.04))
    sh.append(fit(SHOTS / f, x, 2.0, 2.95, 3.35))
    sh.append(Shape("text", x, 5.45, 2.95, 0.85,
                    [Para([Run(cap, 10.5, False, MUTED)], space_after=0)], v_anchor="t", margin=0.04))
sh.append(source("Screenshots of the running application · publication contract 7.3.1"))
S.append(Slide(shapes=sh, notes=(
    "Three minutes live: national evidence, a district drill-down with its caveat, and the page "
    "listing what we cannot compute.\n\n"
    "Open with the header mode chips - NUMERIC_GAP: NOT_IDENTIFIABLE, is_measured_shortage: false "
    "- so the frame is set before any number appears. The app runs fully offline.")))

# --------------------------------------- 8 Provenance / coverage / confidence --
sh = title("Provenance, coverage and confidence travel with every value",
           "Transparency controls, not caveats bolted on at the end.")
sh += [
    card(0.62, 1.7, 3.9, 1.65, "58.13%",
         ["PAN-India / multiple-state residual.", "20,507,320 vacancies, attributable",
          "to no state — NEVER allocated."], ACCENT, PANEL, ACCENT, 26, 12.5),
    card(4.72, 1.7, 3.9, 1.65, "41.87%",
         ["state-attributable — 14,768,513.", "This is the ENTIRE base of the",
          "district allocation signal."], ACCENT, PANEL, ACCENT, 26, 12.5),
    card(8.82, 1.7, 3.89, 1.65, "138 / 785",
         ["districts have Census occupation", "structure. 522 not acquired;",
          "125 can never have one."], ACCENT, PANEL, ACCENT, 26, 12.5),
    fit(ASSETS / "evidence_flow.png", 0.62, 3.55, W - 1.3, 2.9),
    source("All three figures are read live from the warehouse — a test fails the build if they "
           "appear as literals in the code."),
]
S.append(Slide(shapes=sh, notes=(
    "Most dashboards would quietly drop the residual. Twenty and a half million vacancies belong "
    "to no state. We never allocate them; allocating them is a PROHIBITED capability with its own "
    "blocked route.\n\n"
    "And the distinction we work hardest to teach: 'estimated' means the number exists but was "
    "derived; 'unavailable' means it does not exist and cannot currently be computed. Rendering "
    "both as a blank is exactly how a tool like this misleads.")))

# -------------------------------------------- 9 What cannot be measured ----
sh = title("What cannot yet be measured — and why we say so",
           "16 capabilities are published as explicitly unavailable, each with a reason and a gate.")
blocked = [("Numeric demand–supply gap", "NOT IDENTIFIABLE", "G-1", UNA, UNA_L),
           ("Forecast", "NOT SUPPORTED YET", "G-4", UNA, UNA_L),
           ("District x trade supply", "NOT ACQUIRED", "G-2", EST, EST_L),
           ("State x occupation supply", "NOT IDENTIFIABLE", "G-3", UNA, UNA_L),
           ("Measured shortage", "FALSE — always", "permanent", UNA, UNA_L),
           ("PAN-India residual allocation", "PROHIBITED", "permanent", UNA, UNA_L)]
y = 1.78
for nm, st, gate, fg, bg in blocked:
    sh.append(Shape("text", 0.62, y, 5.5, 0.6,
                    [Para([Run(nm, 14.5, True, INK)], space_after=0)], v_anchor="ctr", margin=0.1))
    sh.append(Shape("text", 6.25, y, 3.3, 0.6,
                    [Para([Run(st, 12.5, True, fg)], align="ctr", space_after=0)],
                    fill=bg, line=fg, radius=True, v_anchor="ctr", margin=0.04))
    sh.append(Shape("text", 9.7, y, 3.0, 0.6,
                    [Para([Run(f"gate {gate}", 12, False, MUTED)], space_after=0)],
                    v_anchor="ctr", margin=0.1))
    y += 0.68
sh += [
    Shape("text", 0.62, y + 0.1, W - 1.3, 0.95, [
        Para([Run("Blocked routes return HTTP 200 with data: null, a reason code and a gate.",
                  14, True, INK)], space_after=5),
        Para([Run("A 404 would read as “none found”. The truth is “not computable”.",
                  14, True, UNA)], space_after=0)],
          fill=PANEL, line=UNA, radius=True, v_anchor="ctr", margin=0.22),
    source("Source: publication contract 7.3.1 · /api/capabilities"),
]
S.append(Slide(shapes=sh, notes=(
    "The grouping is the point. NOT_ACQUIRED means the source exists and we have not got it - the "
    "data.gov.in PMKVY district resource needs a registered API key. A paperwork problem.\n\n"
    "NOT_IDENTIFIABLE is different. Supply by state and trade is a joint distribution. We hold the "
    "row totals plus 21.8% of the column totals, from a different scheme. Row and column totals "
    "never determine the interior. To close it you must assume every state trains the same trade "
    "mix - false, untestable, and it would erase the exact regional mismatch this PS exists to find.")))

# --------------------------------------------------- 10 Innovation ---------
sh = title("Identification-aware analytics",
           "Not the framework. These are the things we believe are genuinely uncommon.")
inns = [("1", "We distinguish “missing” from “not identifiable”",
         "NOT_ACQUIRED is a paperwork problem. NOT_IDENTIFIABLE is a mathematical result."),
        ("2", "A publication contract enforced in code",
         "Evidence, confidence, coverage and prohibited readings are part of the response contract. "
         "The app refuses to start on a breach."),
        ("3", "Evidence status is read from the data, never declared",
         "A derived output cannot be relabelled OBSERVED by editing config. A test forges a lying "
         "config and proves it."),
        ("4", "Caveats stored as data — and self-criticism we published",
         "Within a state our district ordering IS the Udyam ordering — 0 of 36 states differ. "
         "We print that above the table."),
        ("5", "A terminology lint over the published surface",
         "Reserved words and forbidden phrasings fail the build — translation files included.")]
y = 1.72
for num, head, body in inns:
    sh.append(Shape("text", 0.62, y, 0.62, 0.84,
                    [Para([Run(num, 20, True, ACCENT)], align="ctr", space_after=0)],
                    fill=ACCENT_L, line=ACCENT, radius=True, v_anchor="ctr", margin=0.02))
    sh.append(Shape("text", 1.4, y, 11.3, 0.84, [
        Para([Run(head, 14.5, True, INK)], space_after=2),
        Para([Run(body, 11.8, False, MUTED)], space_after=0)], v_anchor="ctr", margin=0.08))
    y += 0.89
sh += [
    Shape("text", 0.62, y + 0.05, W - 1.3, 0.6, [
        Para([Run("There is no machine-learning model in production, and no ML library is "
                  "installed. Every ML capability this PS implies is blocked by the same missing "
                  "evidence — not by modelling.", 12.5, True, UNA)], space_after=0)],
          fill=UNA_L, line=UNA, radius=True, v_anchor="ctr", margin=0.18),
    source("Verified: no scikit-learn, LightGBM, XGBoost, PyTorch, TensorFlow or statsforecast; "
           "no model code in src/ or api/."),
]
S.append(Slide(shapes=sh, notes=(
    "The honest innovation is the discipline, and it is measurable. We found that our own district "
    "ranking was really an enterprise-density ranking, and instead of hiding that we printed it "
    "above the table and built a contract that will not let anyone remove it.\n\n"
    "If asked where the AI is: be direct. There is no model in production. Forecasting needs two "
    "dated observations; we have one. A learned gap model needs a target variable; the target is "
    "not identifiable. An early-warning classifier needs labels; none exist.")))

# --------------------------------------------------- 11 Roadmap -----------
S.append(Slide(shapes=title(
    "One dataset unlocks the gap",
    "Gated progression. No dates promised — each step needs its evidence first.") + [
    fit(ASSETS / "future_roadmap.png", 0.62, 1.5, W - 1.3, 5.25),
], notes=(
    "Nine objective gates, published inside the product itself. The decisive one is G-1 condition "
    "six: one observed interior cell of supply by geography and trade. The other five conditions "
    "are harmonisation problems that better data solves. Condition six is why this is an "
    "identification failure - more of the same marginals never passes it.\n\n"
    "Note the parallel track: Census B-24 for thirty-three more states is pure acquisition. The "
    "architecture already handles the full grid - 138 to 785 districts with no formula change.")))

# --------------------------------------------------- 12 Conclusion --------
S.append(Slide(shapes=title("Impact", "What a planner can do today — and what we are asking for.") + [
    card(0.62, 1.65, 3.9, 1.95, "Today",
         ["Inspect official demand evidence", "with full provenance.",
          "Compare districts within a state.", "See exactly what is not covered."],
         OBS, OBS_L, OBS, 16, 12.5),
    card(4.72, 1.65, 3.9, 1.95, "For MSDE",
         ["A specific, costed data request:", "state x trade training outcomes",
          "with complete marginals.", "Addressed to the data owner."], ACCENT, ACCENT_L, ACCENT, 16, 12.5),
    card(8.82, 1.65, 3.89, 1.95, "Not claimed",
         ["No deployment exists, so no", "policy savings, no jobs created,",
          "no efficiency percentages.", "Any such figure would be invented."], UNA, UNA_L, UNA, 16, 12.5),
    Shape("text", 0.62, 3.95, W - 1.3, 1.75, [
        Para([Run("We don’t manufacture a skill gap from incomplete data.", 21, True, INK)],
             align="ctr", space_after=8),
        Para([Run("We build the evidence infrastructure that makes the gap computable "
                  "when the right data becomes available.", 21, True, ACCENT)],
             align="ctr", space_after=0)],
          fill=PANEL, line=ACCENT, radius=True, v_anchor="ctr", margin=0.3),
    Shape("text", 0.62, 5.95, W - 1.3, 0.62, [
        Para([Run("40 tables · 82,358 rows   ·   30 routes   ·   11 exports with caveats in the "
                  "file header   ·   16 capabilities blocked with reasons   ·   479 tests   ·   "
                  "is_measured_shortage = false, enforced at startup", 11.5, False, MUTED)],
             align="ctr", space_after=0)], v_anchor="ctr", margin=0.1),
], notes=(
    "A fabricated gap would be worse than none: the error would be invisible, systematically wrong "
    "in one direction, and it informs seat sanctioning - real money.\n\n"
    "So we did not manufacture the missing number. We built the infrastructure that tells "
    "decision-makers what the evidence supports, and exactly what evidence is required to go "
    "further.\n\nHappy to take the hardest question you have.")))

if __name__ == "__main__":
    out = write_pptx(S, ROOT / "docs" / "step8.2_final_sih_presentation.pptx")
    print(f"  {out.relative_to(ROOT)}  {len(S)} slides  {out.stat().st_size // 1024} KB")
    print(f"  slides with speaker notes: {sum(1 for s in S if s.notes)}")
