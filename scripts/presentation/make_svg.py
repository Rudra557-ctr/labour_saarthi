"""Hand-written SVG of the architecture diagram.

SVG is text, so no renderer or new dependency is needed. This is the vector
companion to architecture_diagram.png for print or large-format use.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parents[2] / "docs" / "assets" / "architecture_diagram.svg"
W, H = 2400, 1760
INK, MUTED, LINE = "#15171C", "#687080", "#CBD2DE"
PANEL, ACCENT, ACCENT_L = "#F7F8FB", "#1A4FA0", "#E9F0FA"
OBS, OBS_L = "#15543A", "#E2F2EA"
EST, EST_L = "#8A6400", "#FDF3DC"
SUP = "#3C4A63"
UNA, UNA_L = "#9A2A2A", "#FAE8E8"
p = []


def rect(x, y, w, h, fill="#fff", stroke=LINE, sw=2, r=10):
    p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" '
             f'stroke="{stroke}" stroke-width="{sw}"/>')


def txt(x, y, s, size=22, fill=INK, bold=False, anchor="start", mono=False):
    fam = "Menlo, Consolas, monospace" if mono else "Arial, Helvetica, sans-serif"
    p.append(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" fill="{fill}" '
             f'font-weight="{"700" if bold else "400"}" text-anchor="{anchor}">{escape(s)}</text>')


def varrow(x, y0, y1, c=ACCENT, w=4):
    p.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1 - 11}" stroke="{c}" stroke-width="{w}"/>')
    p.append(f'<polygon points="{x-7},{y1-11} {x+7},{y1-11} {x},{y1}" fill="{c}"/>')


def harrow(x0, x1, y, c=LINE, w=3):
    p.append(f'<line x1="{x0}" y1="{y}" x2="{x1 - 9}" y2="{y}" stroke="{c}" stroke-width="{w}"/>')
    p.append(f'<polygon points="{x1-9},{y-5} {x1-9},{y+5} {x1},{y}" fill="{c}"/>')


def marker(x, y, kind, color, size=22):
    if kind == "OBSERVED":
        p.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{color}"/>')
    elif kind == "ESTIMATED":
        p.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" '
                 f'stroke="{color}" stroke-width="3"/>')
        p.append(f'<rect x="{x}" y="{y}" width="{size/2}" height="{size}" fill="{color}"/>')
    elif kind == "SUPPORTING":
        p.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" '
                 f'stroke="{color}" stroke-width="3"/>')
    else:
        p.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" '
                 f'stroke="{color}" stroke-width="3" stroke-dasharray="6 5"/>')


txt(80, 84, "LMIS — Evidence-first architecture", 46, INK, True)
txt(80, 128, "Official sources in, provenance out — nothing invented in between.", 26, MUTED)

CX, CW, LX, LW, RX, RW = 820, 760, 90, 560, 1700, 610
txt(LX, 172, "MASTER / REFERENCE", 24, MUTED, True)
txt(CX, 172, "PIPELINE", 24, MUTED, True)
txt(RX, 172, "EVIDENCE STAMPED", 24, MUTED, True)

stages = [("OFFICIAL SOURCES", "26 registered · 15 acquired · 6 in production"),
          ("RAW SNAPSHOTS + PROVENANCE", "sha256 manifests · immutable · never overwritten"),
          ("STANDARDISATION", "PDF · HTML · XLSX · DBF    NULL ≠ 0 ≠ '-' ≠ 'NA'"),
          ("LOCATION / OCCUPATION / SECTOR NORMALISATION",
           "every mapping carries authority + method + confidence"),
          ("VALIDATION + DATA QUALITY", "Pandera contracts · 14/14 reconciliations exact"),
          ("ANALYTICAL DATASET", "one table per source-concept · native grain · never merged"),
          ("DEMAND INTELLIGENCE", "national composition · district + district×occupation signals")]
ys, y = [], 190
for nm, sub in stages:
    h = 92
    rect(CX, y, CW, h, PANEL)
    txt(CX + CW / 2, y + 42, nm, 27, INK, True, "middle")
    txt(CX + CW / 2, y + 70, sub, 21, MUTED, False, "middle")
    ys.append((y, y + h)); y += h + 30
for i in range(len(ys) - 1):
    varrow(CX + CW / 2, ys[i][1] + 4, ys[i + 1][0])

dims = [("LGD / Location", "821 · 36 states + 785 districts"),
        ("NCO-2015 / Occupation", "3,982 · official 3,447-row concordance"),
        ("NIC-2008 / NCS Sector", "21 sections · 22 NCS sectors"),
        ("Period", "dim_period · 132"),
        ("Source / Provenance", "26 registered · licence gate")]
dy = 230
for nm, sub in dims:
    rect(LX, dy, LW, 76)
    txt(LX + 20, dy + 34, nm, 24, ACCENT, True)
    txt(LX + 20, dy + 62, sub, 21, MUTED)
    dy += 88
norm_y = (ys[3][0] + ys[3][1]) / 2
p.append(f'<line x1="{LX+LW+14}" y1="250" x2="{LX+LW+14}" y2="{dy-30}" stroke="{LINE}" stroke-width="3"/>')
harrow(LX + LW + 14, CX - 6, norm_y)
txt(LX, dy + 28, "consulted during normalisation — not passed through", 21, MUTED)

txt(CX + CW / 2 + 26, ys[0][1] + 20, "LICENCE GATE", 20, ACCENT, True)
txt(CX + CW / 2 + 174, ys[0][1] + 21, "— nothing acquired unless registered", 19, MUTED)

gates = [(ys[1], None, "PROVENANCE attached", ACCENT, ACCENT_L),
         (ys[4], None, "CONTRACTS ENFORCED", ACCENT, ACCENT_L),
         (ys[5], "OBSERVED", "OBSERVED", OBS, OBS_L),
         (ys[6], "ESTIMATED", "ESTIMATED  ·  weakest-link MEDIUM / LOW", EST, EST_L)]
for (y0, y1), mk, lbl, fg, bg in gates:
    cy = (y0 + y1) / 2
    harrow(CX + CW + 6, RX - 8, cy)
    rect(RX, cy - 28, RW, 56, bg, fg, 2, 9)
    tx = RX + 20
    if mk:
        marker(tx, cy - 11, mk, fg); tx += 34
    txt(tx, cy + 8, lbl, 22, fg, True)
    if mk == "OBSERVED":
        marker(RX + 230, cy - 11, "SUPPORTING", SUP)
        txt(RX + 264, cy + 8, "SUPPORTING", 22, SUP, True)

by, bh = ys[-1][1] + 36, 258
rect(LX, by, W - 90 - LX, bh, UNA_L, UNA, 5, 14)
txt(LX + 34, by + 58, "NO-FABRICATION BOUNDARY", 32, UNA, True)
txt(LX + 34, by + 102, "SUPPLY[geography × trade] is a JOINT DISTRIBUTION.  We hold row marginals", 24)
txt(LX + 34, by + 134, "+ a 21.8% column fragment — from a different scheme.", 24)
txt(LX + 34, by + 168, "Marginals never determine an interior.", 25, UNA, True)
txt(LX + 34, by + 214, "NOT estimated.   NOT zero.   NOT 404.   NOT omitted.", 28, UNA, True)
txt(LX + 34, by + 248, "OBSERVED DATA  ≠  DERIVED RELATIVE SIGNAL", 23, INK, True)

bx = 1310
rect(bx, by + 36, 440, 114, "#fff", UNA, 3)
for i, s in enumerate(["numeric demand–supply gap", "shortage · forecast", "occupation-level supply"]):
    txt(bx + 20, by + 70 + i * 28, s, 22)
harrow(bx + 452, bx + 544, by + 92, UNA, 5)
txt(bx + 498, by + 72, "BLOCKED", 20, UNA, True, "middle")
bx2 = bx + 552
rect(bx2, by + 36, W - 124 - bx2, 114, "#fff", UNA, 3)
marker(bx2 + 20, by + 56, "UNAVAILABLE", UNA)
txt(bx2 + 54, by + 74, "UNAVAILABLE", 23, UNA, True)
txt(bx2 + 20, by + 110, "reason_code · blocking_gate G-1…G-9", 19, INK, False, "start", True)
txt(bx2 + 20, by + 134, "data: null   (HTTP 200)", 19, INK, False, "start", True)

sy = by + bh + 34
varrow(CX + CW / 2, by + bh + 2, sy)
rect(CX, sy, CW, 94, ACCENT_L, ACCENT, 3)
txt(CX + CW / 2, sy + 40, "PUBLICATION CONTRACT", 27, ACCENT, True, "middle")
txt(CX + CW / 2, sy + 72, "evidence status READ FROM THE DATA · confidence · coverage · vintage",
    21, INK, False, "middle")
rect(RX, sy + 18, RW, 52, "#fff", ACCENT, 2, 9)
txt(RX + 18, sy + 51, "is_measured_shortage = FALSE", 21, ACCENT, True)
harrow(CX + CW + 6, RX - 8, sy + 44)
txt(CX + CW + 20, sy + 94, "app REFUSES TO START on breach", 19, UNA, True)

ay = sy + 124
varrow(CX + CW / 2, sy + 96, ay)
rect(CX, ay, CW, 72, PANEL)
txt(CX + CW / 2, ay + 34, "FastAPI", 27, INK, True, "middle")
txt(CX + CW / 2, ay + 62, "30 routes — 20 production · 10 blocked", 21, MUTED, False, "middle")

fy = ay + 102
outs = [("DASHBOARD", "8 pages · EN/HI · WCAG 2.1 AA"),
        ("CSV / JSON EXPORT", "11 outputs · caveats in the file header"),
        ("OpenAPI", "/docs")]
ow, gap = 470, 34
ox = CX + CW / 2 - (ow * 3 + gap * 2) / 2
p.append(f'<line x1="{CX+CW/2}" y1="{ay+74}" x2="{CX+CW/2}" y2="{fy-22}" stroke="{ACCENT}" stroke-width="4"/>')
p.append(f'<line x1="{ox+ow/2}" y1="{fy-22}" x2="{ox+ow*2.5+gap*2}" y2="{fy-22}" stroke="{ACCENT}" stroke-width="4"/>')
for i, (nm, sub) in enumerate(outs):
    x = ox + i * (ow + gap)
    varrow(x + ow / 2, fy - 22, fy)
    rect(x, fy, ow, 76, "#fff", ACCENT, 2)
    txt(x + ow / 2, fy + 36, nm, 24, ACCENT, True, "middle")
    txt(x + ow / 2, fy + 64, sub, 19, MUTED, False, "middle")

p.append(f'<line x1="90" y1="{fy+112}" x2="{W-90}" y2="{fy+112}" stroke="{LINE}" stroke-width="2"/>')
txt(90, fy + 148, "Sources: NCS Parliament answers (as on 15 Nov 2024) · Udyam MSME (21 Dec 2023) · "
    "Census 2011 B-24 · LGD · PLFS (Apr 2025) · MSDE Annual Report 2023–24", 20, MUTED)

svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#fff"/>\n'
       + "\n".join(p) + "\n</svg>\n")
OUT.write_text(svg)
print(f"  {OUT.relative_to(OUT.parents[2])}  {len(svg)//1024} KB  {W}x{H}")
