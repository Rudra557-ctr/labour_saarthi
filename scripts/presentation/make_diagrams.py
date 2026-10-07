"""Render the approved Step 8.1 diagram specifications as presentation PNGs.

Presentation assets only. Reads nothing from the warehouse and writes nothing but
images under docs/assets/. Every figure quoted here is carried from the frozen
Step 8.0/8.1 documents.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[2] / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

SANS = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
MONO = "/System/Library/Fonts/Menlo.ttc"
F = lambda p, s: ImageFont.truetype(p, s)

# Palette: one accent, one warning, one block colour. High contrast for projectors.
INK      = (21, 23, 28)
MUTED    = (104, 112, 128)
LINE     = (203, 210, 222)
BG       = (255, 255, 255)
PANEL    = (247, 248, 251)
ACCENT   = (26, 79, 160)
ACCENT_L = (233, 240, 250)
OBS      = (21, 84, 58);  OBS_L  = (226, 242, 234)
EST      = (138, 100, 0); EST_L  = (253, 243, 220)
SUP      = (60, 74, 99);  SUP_L  = (237, 241, 247)
UNA      = (154, 42, 42); UNA_L  = (250, 232, 232)


def box(d, xy, fill=BG, outline=LINE, w=2, r=10):
    d.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=w)


def text(d, xy, s, font, fill=INK, anchor="la"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def arrow(d, x, y0, y1, color=ACCENT, w=4, head=11):
    d.line([(x, y0), (x, y1 - head)], fill=color, width=w)
    d.polygon([(x - head // 2 - 2, y1 - head), (x + head // 2 + 2, y1 - head), (x, y1)], fill=color)


def harrow(d, x0, x1, y, color=LINE, w=3, head=9):
    d.line([(x0, y), (x1 - head, y)], fill=color, width=w)
    d.polygon([(x1 - head, y - head // 2 - 1), (x1 - head, y + head // 2 + 1), (x1, y)], fill=color)


def marker(d, x, y, kind, color, size=22):
    """Tier markers are DRAWN, not glyphs: Arial has no ◪ or ⬚, and a tofu box
    would defeat the point of carrying status by shape rather than colour."""
    x0, y0, x1, y1 = x, y, x + size, y + size
    if kind == "OBSERVED":                       # filled square
        d.rectangle([x0, y0, x1, y1], fill=color)
    elif kind == "ESTIMATED":                    # half-filled square
        d.rectangle([x0, y0, x1, y1], outline=color, width=3)
        d.rectangle([x0, y0, x0 + size / 2, y1], fill=color)
    elif kind == "SUPPORTING":                   # open square
        d.rectangle([x0, y0, x1, y1], outline=color, width=3)
    else:                                        # UNAVAILABLE - dashed square
        step = 6
        for i in range(int(x0), int(x1), step * 2):
            d.line([(i, y0), (min(i + step, x1), y0)], fill=color, width=3)
            d.line([(i, y1), (min(i + step, x1), y1)], fill=color, width=3)
        for j in range(int(y0), int(y1), step * 2):
            d.line([(x0, j), (x0, min(j + step, y1))], fill=color, width=3)
            d.line([(x1, j), (x1, min(j + step, y1))], fill=color, width=3)
    return size


def tick(d, x, y, color, size=26, w=5):
    d.line([(x, y + size * 0.55), (x + size * 0.36, y + size * 0.9),
            (x + size, y + size * 0.12)], fill=color, width=w, joint="curve")


def cross(d, x, y, color, size=26, w=5):
    d.line([(x, y), (x + size, y + size)], fill=color, width=w)
    d.line([(x + size, y), (x, y + size)], fill=color, width=w)


def chip(d, x, y, label, fg, bg, font, pad=9, h=30, dashed=False):
    w = d.textlength(label, font=font) + pad * 2
    d.rounded_rectangle([x, y, x + w, y + h], radius=7, fill=bg, outline=fg, width=2)
    if dashed:  # UNAVAILABLE reads as a dashed outline, mirroring the product
        for i in range(int(x), int(x + w), 8):
            d.line([(i, y), (min(i + 4, x + w), y)], fill=bg, width=3)
    text(d, (x + pad, y + h / 2), label, font, fg, anchor="lm")
    return w


# ===========================================================================
# 1. Architecture diagram
# ===========================================================================
def architecture() -> Image.Image:
    W, H = 2400, 1760
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    f_title = F(BOLD, 46); f_sub = F(SANS, 26)
    f_rail = F(BOLD, 24); f_small = F(SANS, 21); f_mono = F(MONO, 19)
    f_stage = F(BOLD, 29); f_stage_s = F(SANS, 22); f_gate = F(BOLD, 22)
    f_band = F(BOLD, 32); f_bandb = F(SANS, 24)

    text(d, (80, 54), "LMIS — Evidence-first architecture", f_title)
    text(d, (80, 112), "Official sources in, provenance out — nothing invented in between.",
         f_sub, MUTED)

    CX, CW = 820, 760            # centre column
    LX, LW = 90, 560             # left rail  (master dimensions)
    RX, RW = 1700, 610           # right rail (evidence gates)
    top = 190

    text(d, (LX, top - 34), "MASTER / REFERENCE", f_rail, MUTED)
    text(d, (CX, top - 34), "PIPELINE", f_rail, MUTED)
    text(d, (RX, top - 34), "EVIDENCE STAMPED", f_rail, MUTED)

    stages = [
        ("OFFICIAL SOURCES", "26 registered · 15 acquired · 6 in production", 92),
        ("RAW SNAPSHOTS + PROVENANCE", "sha256 manifests · immutable · never overwritten", 92),
        ("STANDARDISATION", "PDF · HTML · XLSX · DBF    NULL ≠ 0 ≠ '-' ≠ 'NA'", 92),
        ("LOCATION / OCCUPATION / SECTOR\nNORMALISATION",
         "every mapping carries authority + method + confidence", 112),
        ("VALIDATION + DATA QUALITY", "Pandera contracts · 14/14 reconciliations exact", 92),
        ("ANALYTICAL DATASET", "one table per source-concept · native grain · never merged", 92),
        ("DEMAND INTELLIGENCE", "national composition · district + district×occupation signals", 92),
    ]
    ys, y = [], top
    for name, sub, h in stages:
        box(d, [CX, y, CX + CW, y + h], PANEL, LINE, 2)
        lines = name.split("\n")
        ty = y + (26 if len(lines) == 1 else 16)
        for ln in lines:
            text(d, (CX + CW / 2, ty), ln, f_stage, INK, anchor="ma"); ty += 34
        text(d, (CX + CW / 2, y + h - 30), sub, f_stage_s, MUTED, anchor="ma")
        ys.append((y, y + h))
        y += h + 30
    for i in range(len(ys) - 1):
        arrow(d, CX + CW / 2, ys[i][1] + 4, ys[i + 1][0] - 2)

    # left rail: master dimensions feeding normalisation
    dims = [("LGD / Location", "821 · 36 states + 785 districts"),
            ("NCO-2015 / Occupation", "3,982 · official 3,447-row concordance"),
            ("NIC-2008 / NCS Sector", "21 sections · 22 NCS sectors"),
            ("Period", "dim_period · 132"),
            ("Source / Provenance", "26 registered · licence gate")]
    dy = top + 40
    for nm, sub in dims:
        box(d, [LX, dy, LX + LW, dy + 76], BG, LINE, 2)
        text(d, (LX + 20, dy + 16), nm, F(BOLD, 24), ACCENT)
        text(d, (LX + 20, dy + 46), sub, f_small, MUTED)
        dy += 88
    norm_y = (ys[3][0] + ys[3][1]) / 2
    d.line([(LX + LW + 14, top + 60), (LX + LW + 14, dy - 30)], fill=LINE, width=3)
    harrow(d, LX + LW + 14, CX - 6, norm_y, LINE, 3)
    text(d, (LX, dy + 10), "consulted during normalisation — not passed through",
         f_small, MUTED)

    # right rail: what each layer stamps on a value
    gates = [
        (ys[1], None, "PROVENANCE attached", ACCENT, ACCENT_L),
        (ys[4], None, "CONTRACTS ENFORCED", ACCENT, ACCENT_L),
        (ys[5], "OBSERVED", "OBSERVED", OBS, OBS_L),
        (ys[6], "ESTIMATED", "ESTIMATED  \u00b7  weakest-link MEDIUM / LOW", EST, EST_L),
    ]
    for (y0, y1), mk, lbl, fg, bg in gates:
        cy = (y0 + y1) / 2
        harrow(d, CX + CW + 6, RX - 8, cy, LINE, 3)
        box(d, [RX, cy - 28, RX + RW, cy + 28], bg, fg, 2, r=9)
        tx = RX + 20
        if mk:
            marker(d, tx, cy - 11, mk, fg); tx += 34
        text(d, (tx, cy), lbl, f_gate, fg, anchor="lm")
        if mk == "OBSERVED":   # SUPPORTING shares this row; draw it clear of the label
            sx = tx + d.textlength("OBSERVED", font=f_gate) + 56
            marker(d, sx, cy - 11, "SUPPORTING", SUP)
            text(d, (sx + 34, cy), "SUPPORTING", f_gate, SUP, anchor="lm")

    # licence gate annotation - beside the first arrow, clear of both rails
    lgx = CX + CW / 2 + 26
    lgy = ys[0][1] + 2
    text(d, (lgx, lgy), "LICENCE GATE", F(BOLD, 20), ACCENT)
    text(d, (lgx + 148, lgy + 2), "— nothing acquired unless registered", F(SANS, 19), MUTED)

    # ---- the no-fabrication boundary -------------------------------------
    by = ys[-1][1] + 36
    bh = 258
    d.rounded_rectangle([LX, by, W - 90, by + bh], radius=14, fill=UNA_L, outline=UNA, width=5)
    text(d, (LX + 34, by + 26), "NO-FABRICATION BOUNDARY", f_band, UNA)
    text(d, (LX + 34, by + 72),
         "SUPPLY[geography × trade] is a JOINT DISTRIBUTION.  We hold row marginals",
         f_bandb, INK)
    text(d, (LX + 34, by + 104),
         "+ a 21.8% column fragment — from a different scheme.", f_bandb, INK)
    text(d, (LX + 34, by + 136),
         "Marginals never determine an interior.", F(BOLD, 25), UNA)

    bx = 1310
    box(d, [bx, by + 36, bx + 440, by + 150], BG, UNA, 3, r=10)
    text(d, (bx + 20, by + 52), "numeric demand–supply gap", F(SANS, 22), INK)
    text(d, (bx + 20, by + 80), "shortage · forecast", F(SANS, 22), INK)
    text(d, (bx + 20, by + 108), "occupation-level supply", F(SANS, 22), INK)
    harrow(d, bx + 452, bx + 544, by + 92, UNA, 5, 12)
    text(d, (bx + 498, by + 56), "BLOCKED", F(BOLD, 20), UNA, anchor="ma")

    bx2 = bx + 552
    box(d, [bx2, by + 36, W - 124, by + 150], BG, UNA, 3, r=10)
    marker(d, bx2 + 20, by + 56, "UNAVAILABLE", UNA, 22)
    text(d, (bx2 + 54, by + 54), "UNAVAILABLE", F(BOLD, 23), UNA)
    text(d, (bx2 + 18, by + 94), "reason_code · blocking_gate G-1…G-9", f_mono, INK)
    text(d, (bx2 + 18, by + 118), "data: null   (HTTP 200)", f_mono, INK)

    text(d, (LX + 34, by + 186), "NOT estimated.   NOT zero.   NOT 404.   NOT omitted.",
         F(BOLD, 28), UNA)
    text(d, (LX + 34, by + 224),
         "OBSERVED DATA  ≠  DERIVED RELATIVE SIGNAL  —  the product never conflates them.",
         F(BOLD, 23), INK)

    # ---- serving layer ----------------------------------------------------
    sy = by + bh + 34
    arrow(d, CX + CW / 2, by + bh + 2, sy - 2)
    box(d, [CX, sy, CX + CW, sy + 94], ACCENT_L, ACCENT, 3)
    text(d, (CX + CW / 2, sy + 18), "PUBLICATION CONTRACT", f_stage, ACCENT, anchor="ma")
    text(d, (CX + CW / 2, sy + 56),
         "evidence status READ FROM THE DATA · confidence · coverage · vintage",
         F(SANS, 21), INK, anchor="ma")
    box(d, [RX, sy + 18, RX + RW, sy + 70], BG, ACCENT, 2, r=9)
    text(d, (RX + 18, sy + 44), "is_measured_shortage = FALSE", F(BOLD, 21), ACCENT, anchor="lm")
    harrow(d, CX + CW + 6, RX - 8, sy + 44, LINE, 3)
    text(d, (CX + CW + 20, sy + 76), "app REFUSES TO START on breach", F(BOLD, 19), UNA)

    ay = sy + 124
    arrow(d, CX + CW / 2, sy + 96, ay - 2)
    box(d, [CX, ay, CX + CW, ay + 72], PANEL, LINE, 2)
    text(d, (CX + CW / 2, ay + 12), "FastAPI", f_stage, INK, anchor="ma")
    text(d, (CX + CW / 2, ay + 46), "30 routes — 20 production · 10 blocked",
         F(SANS, 21), MUTED, anchor="ma")

    fy = ay + 102
    outs = [("DASHBOARD", "8 pages · EN/HI · WCAG 2.1 AA"),
            ("CSV / JSON EXPORT", "11 outputs · caveats in the file header"),
            ("OpenAPI", "/docs")]
    ow, gap = 470, 34
    ox = CX + CW / 2 - (ow * 3 + gap * 2) / 2
    d.line([(CX + CW / 2, ay + 74), (CX + CW / 2, fy - 22)], fill=ACCENT, width=4)
    d.line([(ox + ow / 2, fy - 22), (ox + ow * 2.5 + gap * 2, fy - 22)], fill=ACCENT, width=4)
    for i, (nm, sub) in enumerate(outs):
        x = ox + i * (ow + gap)
        arrow(d, x + ow / 2, fy - 22, fy - 2)
        box(d, [x, fy, x + ow, fy + 76], BG, ACCENT, 2)
        text(d, (x + ow / 2, fy + 14), nm, F(BOLD, 24), ACCENT, anchor="ma")
        text(d, (x + ow / 2, fy + 46), sub, F(SANS, 19), MUTED, anchor="ma")

    d.line([(90, fy + 112), (W - 90, fy + 112)], fill=LINE, width=2)
    text(d, (90, fy + 130),
         "Sources: NCS Parliament answers (as on 15 Nov 2024) · Udyam MSME (21 Dec 2023) · "
         "Census 2011 B-24 · LGD · PLFS (Apr 2025) · MSDE Annual Report 2023–24",
         F(SANS, 20), MUTED)
    return im


# ===========================================================================
# 2. Gap identification gate
# ===========================================================================
def gap_gate() -> Image.Image:
    W, H = 2200, 1020
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    text(d, (80, 52), "When is a demand–supply gap computable?", F(BOLD, 46))
    text(d, (80, 110), "Four components must line up. One missing component blocks the result.",
         F(SANS, 26), MUTED)

    comps = [
        ("DEMAND EVIDENCE", "NCS vacancies\nstate · as on 2024-11-15", True),
        ("SUPPLY EVIDENCE", "state × trade\noutcomes", False),
        ("COMPATIBLE GRAIN", "same geography &\noccupation grain", False),
        ("TIME ALIGNMENT", "same period &\nmeasure basis", False),
    ]
    bw, bh, gap = 460, 240, 44
    x0 = (W - (bw * 4 + gap * 3)) / 2
    y0 = 210
    for i, (nm, sub, have) in enumerate(comps):
        x = x0 + i * (bw + gap)
        fg, bg = (OBS, OBS_L) if have else (UNA, UNA_L)
        box(d, [x, y0, x + bw, y0 + bh], bg, fg, 4, r=12)
        text(d, (x + bw / 2, y0 + 26), nm, F(BOLD, 28), fg, anchor="ma")
        ty = y0 + 80
        for ln in sub.split("\n"):
            text(d, (x + bw / 2, ty), ln, F(SANS, 23), INK, anchor="ma"); ty += 32
        lbl = "HAVE" if have else "MISSING"
        f_mark = F(BOLD, 30)
        tw = d.textlength(lbl, font=f_mark)
        mx = x + bw / 2 - (tw + 40) / 2
        my = y0 + bh - 46
        (tick if have else cross)(d, mx, my + 2, fg, 24, 5)
        text(d, (mx + 40, my), lbl, f_mark, fg)
        if i < 3:
            text(d, (x + bw + gap / 2, y0 + bh / 2), "+", F(BOLD, 44), MUTED, anchor="mm")

    ay = y0 + bh + 40
    arrow(d, W / 2, ay, ay + 56, UNA, 6, 16)

    ry = ay + 70
    d.rounded_rectangle([x0, ry, x0 + bw * 4 + gap * 3, ry + 190], radius=14,
                        fill=UNA_L, outline=UNA, width=5)
    text(d, (W / 2, ry + 26), "GAP NOT IDENTIFIABLE", F(BOLD, 52), UNA, anchor="ma")
    text(d, (W / 2, ry + 96),
         "Supply by state × trade is a joint distribution. We hold row marginals",
         F(SANS, 26), INK, anchor="ma")
    text(d, (W / 2, ry + 132),
         "+ a 21.8% column fragment from a different scheme — margins never determine an interior.",
         F(SANS, 26), INK, anchor="ma")

    gy = ry + 230
    text(d, (W / 2, gy), "UNBLOCKING CONDITION  ·  gate G-1", F(BOLD, 30), ACCENT, anchor="ma")
    text(d, (W / 2, gy + 46),
         "One OBSERVED interior cell of SUPPLY[geography × trade], with complete trade marginals.",
         F(SANS, 26), INK, anchor="ma")
    text(d, (W / 2, gy + 88),
         "More of the same marginals never passes it.", F(BOLD, 25), MUTED, anchor="ma")
    d.line([(80, H - 70), (W - 80, H - 70)], fill=LINE, width=2)
    text(d, (80, H - 50),
         "Source: Step 6 identification analysis · PMKVY 4.0 Top-10 job roles = 514,619 of 2,361,798 enrolments (21.8%)",
         F(SANS, 19), MUTED)
    return im


# ===========================================================================
# 3. Data standardisation
# ===========================================================================
def standardisation() -> Image.Image:
    W, H = 2200, 1060
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    text(d, (80, 52), "Six incompatible sources → one comparable spine", F(BOLD, 46))
    text(d, (80, 110), "Every mapping carries its authority, method and confidence.",
         F(SANS, 26), MUTED)

    srcs = [("NCS", "state · 2024-11-15"), ("Udyam", "district · 2023-12-21"),
            ("Census B-24", "district×occ · 2011"), ("LGD", "geography directory"),
            ("PLFS", "national · Apr 2025"), ("MSDE AR", "state×scheme · 2024-03-31")]
    bw, bh, gy = 300, 92, 26
    sx, sy = 90, 200
    for i, (nm, sub) in enumerate(srcs):
        y = sy + i * (bh + gy)
        box(d, [sx, y, sx + bw, y + bh], PANEL, LINE, 2)
        text(d, (sx + 20, y + 18), nm, F(BOLD, 27), INK)
        text(d, (sx + 20, y + 54), sub, F(SANS, 20), MUTED)
        harrow(d, sx + bw + 8, 760, y + bh / 2, LINE, 2)

    mx, mw = 790, 560
    my, mh = 200, 6 * (bh + gy) - gy
    box(d, [mx, my, mx + mw, my + mh], ACCENT_L, ACCENT, 4, r=12)
    text(d, (mx + mw / 2, my + 26), "CONFORMANCE", F(BOLD, 34), ACCENT, anchor="ma")
    rows = [("NCO-2015", "3,982 occupations"),
            ("NCO-2004 → 2015", "3,447 rows · OFFICIAL"),
            ("LGD geography", "821 · 36 states + 785 districts"),
            ("NIC-2008", "21 sections"),
            ("dim_period", "132"),
            ("provenance", "source_id · vintage · sha256")]
    ry = my + 92
    for nm, sub in rows:
        text(d, (mx + 32, ry), nm, F(BOLD, 24), INK)
        text(d, (mx + 32, ry + 30), sub, F(SANS, 20), MUTED)
        ry += 74

    harrow(d, mx + mw + 10, 1470, my + mh / 2, ACCENT, 4, 12)

    ox, ow = 1500, 620
    panels = [("OBSERVED", "NCS state demand · demand by industry", OBS, OBS_L),
              ("ESTIMATED", "occupation composition · district + district×occupation\nallocation signals", EST, EST_L),
              ("SUPPORTING", "PLFS labour-force context — not a demand measure", SUP, SUP_L),
              ("UNAVAILABLE", "16 capabilities · reason code + gate", UNA, UNA_L)]
    oy = my
    for nm, sub, fg, bg in panels:
        h = 190 if "\n" in sub else 150
        box(d, [ox, oy, ox + ow, oy + h], bg, fg, 3, r=10)
        marker(d, ox + 24, oy + 24, nm, fg, 24)
        text(d, (ox + 60, oy + 20), nm, F(BOLD, 28), fg)
        ty = oy + 64
        for ln in sub.split("\n"):
            text(d, (ox + 24, ty), ln, F(SANS, 21), INK); ty += 32
        oy += h + 22

    text(d, (80, H - 40),
         "Authority is structural: OFFICIAL concordances vs PROJECT alignments (NCS sector → NIC, confidence 0.95). "
         "153 of 155 trades remain MAPPING_UNKNOWN rather than matched by name.",
         F(SANS, 19), MUTED)
    return im


# ===========================================================================
# 4. Future roadmap
# ===========================================================================
def roadmap() -> Image.Image:
    W, H = 2200, 1180
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    text(d, (80, 52), "One dataset unlocks the gap", F(BOLD, 46))
    text(d, (80, 110), "Gated progression. No dates promised — each step needs its evidence.",
         F(SANS, 26), MUTED)

    steps = [
        ("NOW", "Evidence-qualified demand intelligence",
         "observed NCS demand · estimated allocation signals\nprovenance, confidence and coverage on every value", OBS, OBS_L),
        ("NEXT", "Numeric demand–supply gap",
         "needs G-1: one OBSERVED interior cell of\nSUPPLY[geography × trade] + complete trade marginals", UNA, UNA_L),
        ("NEXT", "Temporal forecasting",
         "needs G-4: a SECOND dated NCS observation\nbaselines first · rolling-origin backtesting", UNA, UNA_L),
        ("NEXT", "Validated early warning",
         "needs G-5/6/7/8 · G-7 non-negotiable:\nan occupation dimension on the training axis", UNA, UNA_L),
    ]
    bw, bh = 480, 360
    gap = 60
    x0 = (W - (bw * 4 + gap * 3)) / 2
    y0 = 230
    for i, (tag, title, sub, fg, bg) in enumerate(steps):
        x = x0 + i * (bw + gap)
        box(d, [x, y0, x + bw, y0 + bh], bg if i == 0 else BG, fg, 4, r=12)
        chip(d, x + 24, y0 + 22, tag, fg, bg, F(BOLD, 22), h=34)
        ty = y0 + 86
        for ln in _wrap(d, title, F(BOLD, 28), bw - 48):
            text(d, (x + 24, ty), ln, F(BOLD, 28), INK); ty += 36
        ty += 14
        for ln in sub.split("\n"):
            for w in _wrap(d, ln, F(SANS, 21), bw - 48):
                text(d, (x + 24, ty), w, F(SANS, 21), MUTED); ty += 30
        if i < 3:
            gx = x + bw + gap / 2
            harrow(d, x + bw + 10, x + bw + gap - 10, y0 + bh / 2, ACCENT, 5, 14)
            text(d, (gx, y0 + bh / 2 - 44), "DATA", F(BOLD, 20), ACCENT, anchor="ma")
            text(d, (gx, y0 + bh / 2 - 22), "UNLOCK", F(BOLD, 20), ACCENT, anchor="ma")

    py = y0 + bh + 70
    box(d, [x0, py, x0 + bw * 4 + gap * 3, py + 120], ACCENT_L, ACCENT, 3, r=12)
    text(d, (W / 2, py + 22), "In parallel, no gate required:", F(BOLD, 26), ACCENT, anchor="ma")
    text(d, (W / 2, py + 64),
         "Census 2011 B-24 for the remaining 33 states → district coverage 138 → up to 785, with no formula change.",
         F(SANS, 25), INK, anchor="ma")
    text(d, (80, H - 40),
         "Named blockers: data.gov.in PMKVY district resource ACCESS_PENDING · NCVT MIS, NQR bulk search, "
         "apprenticeshipindia.gov.in UNAVAILABLE",
         F(SANS, 19), MUTED)
    return im


def _wrap(d, s, font, width):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ===========================================================================
# 5. Evidence flow (tier legend + the distinction)
# ===========================================================================
def evidence_flow() -> Image.Image:
    W, H = 2200, 820
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    text(d, (80, 52), "Four evidence states — and the one distinction that matters", F(BOLD, 46))
    text(d, (80, 110), "Carried as text and shape, never colour alone.", F(SANS, 26), MUTED)

    tiers = [("OBSERVED", "OBSERVED", "A published figure attributable to a named\nofficial source document.",
              "analytical_state_demand", OBS, OBS_L),
             ("ESTIMATED", "ESTIMATED", "Derived. The method is named and the\ntransformation depth is shown.",
              "district allocation signals", EST, EST_L),
             ("SUPPORTING", "SUPPORTING", "Real observed data, shown for context.\nNot a demand or supply measure.",
              "PLFS labour-force context", SUP, SUP_L),
             ("UNAVAILABLE", "UNAVAILABLE", "Does not exist and cannot currently be\ncomputed — the reason is given.",
              "numeric gap · forecast", UNA, UNA_L)]
    bw, bh, gap = 480, 330, 50
    x0 = (W - (bw * 4 + gap * 3)) / 2
    y0 = 200
    for i, (gl, nm, body, eg, fg, bg) in enumerate(tiers):
        x = x0 + i * (bw + gap)
        box(d, [x, y0, x + bw, y0 + bh], bg, fg, 4, r=12)
        marker(d, x + 26, y0 + 28, gl, fg, 36)
        text(d, (x + 82, y0 + 30), nm, F(BOLD, 30), fg)
        ty = y0 + 110
        for ln in body.split("\n"):
            text(d, (x + 26, ty), ln, F(SANS, 22), INK); ty += 32
        text(d, (x + 26, y0 + bh - 70), "e.g.", F(SANS, 19), MUTED)
        text(d, (x + 26, y0 + bh - 44), eg, F(MONO, 19), fg)

    cy = y0 + bh + 70
    d.rounded_rectangle([x0, cy, x0 + bw * 4 + gap * 3, cy + 150], radius=14,
                        fill=PANEL, outline=ACCENT, width=4)
    text(d, (W / 2, cy + 26), "“Estimated” means the number exists but was derived.",
         F(BOLD, 30), INK, anchor="ma")
    text(d, (W / 2, cy + 72), "“Unavailable” means it does not exist and cannot currently be computed.",
         F(BOLD, 30), INK, anchor="ma")
    text(d, (W / 2, cy + 116), "Rendering both as a blank is how a tool like this misleads.",
         F(SANS, 24), MUTED, anchor="ma")
    return im


if __name__ == "__main__":
    for name, fn in [("architecture_diagram", architecture),
                     ("gap_identification_gate", gap_gate),
                     ("data_standardization", standardisation),
                     ("future_roadmap", roadmap),
                     ("evidence_flow", evidence_flow)]:
        img = fn()
        p = OUT / f"{name}.png"
        img.save(p, "PNG", optimize=True)
        print(f"  {p.relative_to(OUT.parents[1])}  {img.size[0]}x{img.size[1]}  "
              f"{p.stat().st_size // 1024} KB")
