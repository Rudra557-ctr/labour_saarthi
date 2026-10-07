# Final Submission Checklist

Date: 2026-10-06 · Verified live against the running system unless marked **MANUAL CHECK**.

| | Count |
|---|---|
**PASS** | 44 |
**MANUAL CHECK** | 8 |
**FAIL** | **0** |

---

## Repository

| | Item | Status | Evidence |
|---|---|---|---|
☑ | `README.md` present | **PASS** | includes `make serve`, `make reproduce`, `make setup` |
☑ | `pyproject.toml` with pinned dependencies | **PASS** | 12 runtime, 2 dev |
☑ | `Makefile` with a single reproduce entry point | **PASS** | `make reproduce` |
☑ | Startup instructions documented | **PASS** | 3 commands in README |
☑ | API starts | **PASS** | `/api/health` → `status: ok` in < 1 s |
☑ | Frontend serves | **PASS** | `/`, `/static/app.js`, `/static/styles.css`, both i18n files — all 200 |
☑ | OpenAPI generates | **PASS** | `/docs` and `/openapi.json` → 200, 30 paths |
☑ | Database available | **PASS** | 40 tables · 7 migrations · 82,358 rows |
☑ | Configuration present | **PASS** | `config/sources.yaml` (26 sources), `config/publication_contract.yaml` (v7.3.1) |
☑ | Tests pass | **PASS** | **479 passed** |
☑ | Terminology lint passes | **PASS** | 0 violations, 13 outputs + 2 UI catalogues |
☑ | Full rebuild reproducible | **PASS** | `make reproduce` clean |
☑ | `.gitignore` present | **PASS** | — |
☐ | **Repository initialised and pushed** | **MANUAL CHECK** | **No `.git` exists.** Must `git init`, review `git status` before the first commit, and push. |
☐ | Decide whether to ship `db/lmis.duckdb` | **MANUAL CHECK** | Shipping gives a fast demo start; omitting keeps the repo clean. Either works — it rebuilds from raw. |
☐ | Raw data licences reviewed before republishing | **MANUAL CHECK** | 35 files, 50.5 MB; licences recorded in `config/sources.yaml` |

---

## Presentation

| | Item | Status | Evidence |
|---|---|---|---|
☑ | PPTX exists | **PASS** | `docs/step8.2_final_sih_presentation.pptx`, 12 slides, 1.9 MB |
☑ | PPTX structurally valid | **PASS** | 59 XML parts well-formed, no dangling relationships |
☑ | Speaker notes on every slide | **PASS** | 12 of 12 (292–550 chars) |
☑ | Architecture diagram rendered | **PASS** | PNG **and** SVG |
☑ | Supporting diagrams | **PASS** | 4 more, each a distinct concept |
☑ | Screenshots of the running product | **PASS** | 9, captured 2026-10-06, all verified non-blank |
☑ | 7-minute script | **PASS** | `step8.3_rehearsal_script.md` |
☑ | 3-minute script | **PASS** | `step8.3_3_minute_script.md` |
☑ | 60-second pitch | **PASS** | `step8.3_60_second_pitch.md` |
☑ | Live demo runbook | **PASS** | `step8.3_live_demo_runbook.md` — every route executed |
☑ | Demo failure plan | **PASS** | 12 scenarios with exact sentences |
☑ | Judge Q&A — full | **PASS** | 49 questions (8.0) + 20 answers (8.1) |
☑ | Judge Q&A — rapid sheet | **PASS** | `step8.3_judge_rapid_sheet.md` |
☑ | Hard-question prep | **PASS** | 15 in `step8.3_hard_judge_questions.md` |
☑ | Team roles assigned | **PASS** | `step8.3_team_roles.md` (5 / 3 / 2 / 1 variants) |
☐ | **Deck opened on the presentation machine** | **MANUAL CHECK** | **The PPTX was never rasterised.** Required before presenting. |
☐ | Rehearsed to time, with the demo | **MANUAL CHECK** | 7-minute and 3-minute both |
☐ | Projector tested at 16:9 | **MANUAL CHECK** | — |

---

## Compliance

| | Item | Status | Evidence |
|---|---|---|---|
☑ | PS ID stated | **PASS** | 26246, on slide 1 |
☑ | Requirement mapping complete and honest | **PASS** | 6 implemented · 4 partial · 3 data-blocked · 2 not-supported · 1 experimental. **R3 is NOT_SUPPORTED_YET, not green.** |
☑ | Source attribution on quantitative slides | **PASS** | 9 of 12 carry a source line; slides 4 and 11 carry it inside the diagram; slide 12 is self-descriptive |
☑ | Provenance preserved end to end | **PASS** | `source_ids`, vintage, transformation depth on every production row; named PDFs on the methodology page |
☑ | Licensing recorded for every source | **PASS** | `config/sources.yaml` licence gate |
☑ | No unsupported claims | **PASS** | 0 prohibited claims across 24 PPTX surfaces |
☑ | No synthetic data anywhere | **PASS** | 0 synthetic rows or columns in 40 tables |
☑ | No synthetic data represented as real | **PASS** | none exists to misrepresent |
☑ | No credentials or secrets | **PASS** | `step8.3_security_submission_audit.md` |
☑ | No numeric gap published | **PASS** | `NUMERIC_GAP: NOT_IDENTIFIABLE` |
☑ | No forecast published | **PASS** | `FORECASTING: NOT_SUPPORTED_YET` |
☑ | `is_measured_shortage = false` everywhere | **PASS** | enforced at application startup |
☑ | Hybrid remains experimental | **PASS** | `implemented: false`, absent from API, dashboard, exports and deck |
☑ | No ML model claimed | **PASS** | absence stated explicitly on slide 10 |
☑ | Cross-surface numeric consistency | **PASS** | 59 of 61 checks; 2 LOW issues in frozen Step 7 docs, reported not fixed |

---

## Demo

| | Item | Status | Evidence |
|---|---|---|---|
☑ | API starts | **PASS** | < 1 s |
☑ | Frontend starts | **PASS** | 8 pages reachable |
☑ | Database available | **PASS** | read-only connection |
☑ | Filters work | **PASS** | 36 states · 3 with occupation detail · 9 divisions · 22 sectors |
☑ | Drill-down works | **PASS** | national → state → district → occupation |
☑ | `NOT_AVAILABLE` path works | **PASS** | district 554 shows the reason, never a zero |
☑ | Blocked routes behave | **PASS** | HTTP 200 + `data: null` + reason + gate |
☑ | Exports work | **PASS** | CSV and JSON, with the metadata header |
☑ | Hybrid export refused | **PASS** | 403 |
☑ | Runs offline | **PASS** | no CDN, no Node build, no external API |
☑ | Fallback screenshots available | **PASS** | 9, of this build |
☐ | **OS set to Light appearance** | **MANUAL CHECK** | The dashboard follows `prefers-color-scheme`; dark washes out on a projector |
☐ | District codes re-verified on the day | **MANUAL CHECK** | They are data-dependent. Pre-flight commands in the runbook. |

---

## The 8 manual checks, in priority order

1. **Open the PPTX on the presentation machine.** *(highest priority — never rasterised)*
2. **Set the OS to Light appearance** before the demo.
3. **Re-verify the two district codes** at pre-flight.
4. **Rehearse to time**, both the 7-minute and 3-minute versions.
5. **Test the projector** at 16:9.
6. **`git init`**, review `git status`, push.
7. **Decide on shipping `db/lmis.duckdb`.**
8. **Review raw-data licences** before republishing.

**None of these is a defect.** All are ordinary pre-presentation and pre-publication steps.
