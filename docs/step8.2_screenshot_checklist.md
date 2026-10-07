# Screenshot Manifest & Re-capture Guide

**Screenshots were captured automatically** from the running application on 2026-10-06 — no manual
capture is required. This document is the manifest (what each one shows and must not show) and the
command to regenerate them if the product changes.

---

## Re-capture

```bash
make serve &                                   # or: uvicorn api.main:app --port 8090
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
          --blink-settings=preferredColorScheme=1 \
          --screenshot=docs/assets/screenshots/<name>.png \
          --window-size=<W,H> --virtual-time-budget=9000 \
          "http://127.0.0.1:8090/#<route>"
```

`--blink-settings=preferredColorScheme=1` forces light mode; without it Chrome inherits the system
appearance and renders the dark theme, which washes out on a projector. `--virtual-time-budget=9000`
gives the page time to fetch and render before the shot is taken.

**LGD codes are resolved at capture time, not hard-coded** — a district with Census coverage and one
without are selected from the API so the manifest stays correct if coverage changes:

```bash
curl -s "localhost:8090/api/demand/district-occupation?state=27&occupation_prior_status=AVAILABLE" # → with
curl -s "localhost:8090/api/demand/district-occupation?state=32"                                   # → without
```

---

## Manifest

| # | File | Route | Window | Must show | Must NOT show |
|---|---|---|---|---|---|
1 | `01_landing.png` | `#landing` | 1400×900 | Header mode chips: `NUMERIC_GAP: NOT_IDENTIFIABLE`, `FORECASTING: NOT_SUPPORTED_YET`, `is_measured_shortage: false`, `MODE: OPTION_A`, baseline 2024-11-15. The three coverage statements. | Any total demand figure. Any chart. |
2 | `02_national.png` | `#national` | 1400×2600 | Four separately captioned panels — `■ Observed` NCS by sector · `◪ Estimated` occupation composition with **per-row** confidence · `□ SUPPORTING CONTEXT — NOT A DEMAND MEASURE` · the PAN-India residual disclosure. | A combined observed+estimated chart. PLFS presented as demand. |
3 | `03_state_maharashtra.png` | `#state/27` | 1400×2400 | `■ Observed` state total with share chips · the **amber caveat box** reading *"within a state this ordering equals the Udyam enterprise-share ordering"* **above** the table · coverage 41.87% / 58.13% / 785 · `Must not be read as: VACANCY_COUNT · …` · training panel *"not a supply quantity"*. | The residual as a state row. The word "demand ranking". |
4 | `04_district_with_occ.png` | `#district/<covered>` | 1400×1800 | Signal card with rank *k* of *n* · the approved label **District × Occupation Relative Demand Allocation Signal** · the Census-2011 caveat · 9 NCO divisions. | A vacancy count. A zero. |
5 | `05_district_not_available.png` | `#district/<uncovered>` | 1400×1200 | `⬚ Unavailable · NOT_AVAILABLE` · *"Occupation detail not available — CENSUS_NOT_ACQUIRED"* · *"This is an absence of acquired evidence, not an absence of demand."* · the estimated-vs-unavailable explainer. | **Any zero.** An empty table. A blank panel. |
6 | `06_occupation.png` | `#occupation/7` | 1400×2200 | NCO-2015 division code **and** title, untranslated · estimated national composition · districts within one state for that division. | "Top occupations by vacancies". |
7 | `07_methodology.png` | `#methodology` | 1400×2600 | Four evidence tiers with plain-language meanings · `NUMERIC_GAP: NOT_IDENTIFIABLE` with its reason · the five-vintage table · derivation rules incl. their prohibited framings. | A single global "data as of" date. |
8 | `08_coverage.png` | `#coverage` | 1400×2200 | Coverage metrics each showing the warehouse column they derive from · barred fields · 14 data-quality checks. | A coverage gap shown as zero. |
9 | `09_unavailable.png` | `#unavailable` | 1400×2600 | 16 capabilities grouped by reason code · each with reason + `blocking_gate` · `NOT_IDENTIFIABLE` visibly distinct from `NOT_ACQUIRED`. | "No data found". "Coming soon". An empty state. |

---

## Verification after re-capture

```bash
.venv/bin/python - <<'EOF'
from PIL import Image; import glob
for f in sorted(glob.glob('docs/assets/screenshots/*.png')):
    im = Image.open(f).convert('RGB')
    colours = len(set(im.getdata()))
    px = im.getpixel((im.width//2, min(400, im.height-1)))
    print(f, im.size, 'colours', colours,
          'RENDERED' if colours > 80 else 'BLANK — JS did not run',
          'LIGHT' if sum(px) > 600 else 'DARK — add --blink-settings')
EOF
```

**A blank or dark capture is a capture fault, not a product fault.** Re-run with a larger
`--virtual-time-budget` or confirm the colour-scheme flag.

**Never retouch a screenshot.** If a screenshot shows something undesirable, that is a finding about
the product, not about the image — report it rather than editing it.
