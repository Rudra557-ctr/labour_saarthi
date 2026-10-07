# Step 7.5 — SIH Demo Readiness: End-to-End QA Audit

Date: 2026-10-06 · **QA, testing and documentation.** No analytical methodology, no gap, no forecast, no
synthetic data, no hybrid implementation, no new dataset. No analytical formula or value changed, and no
publication-contract guardrail weakened.

Audited the full chain: **warehouse → publication contract → API → frontend → export → user interpretation.**

| | |
|---|---|
**Verdict** | **SIH-DEMO-READY** |
**Tests** | 460 → **479**, all passing |
**`make reproduce`** | complete |
**Schema** | 40 tables, 7 migrations, 82,358 rows — unchanged |
**Analytical values** | unchanged (all measure sums identical) |
**Defects found** | **6** — 1 security, 2 correctness, 2 terminology/metadata, 1 accessibility |
**Defects fixed** | **6** (all within the bug-fix policy; none required a methodology or data change) |

---

## 1. Readiness checklist

| # | Item | Status | Evidence |
|---|---|---|---|
1 | **System startup** | **PASS** | `uvicorn api.main:app` serves on first try; the `lifespan` hook re-verifies the contract, terminology lint and both i18n catalogues, and **refuses to start** on any breach or on a non-`false` `is_measured_shortage`. Live run confirmed. |
2 | **API health** | **PASS** | `/api/health` → `status: ok`, contract `7.3.1`, 12 production outputs, 16 unavailable capabilities, `is_measured_shortage: false`. 0.8 ms. |
3 | **Dashboard loading** | **PASS** | `/` 1,688 B, `app.js` 31 KB, `styles.css` 6.5 KB, both i18n files — all HTTP 200. `/docs` and `/openapi.json` 200; 30 paths generated. |
4 | **National view** | **PASS** | 24,996 chars. Four separately-captioned panels: OBSERVED industry (22 NCS sectors), ESTIMATED occupation composition (175 rows, per-row MEDIUM/LOW), SUPPORTING PLFS, residual disclosure. No total-demand figure anywhere. |
5 | **State drill-down** | **PASS** | 36 states selectable; Maharashtra renders 36 districts ordered by `rank_within_state`; residual excluded from the list and disclosed separately; state training panel renders `NO_DATA` as such. |
6 | **District view** | **PASS** | Signal card + rank *k* of *n*; occupation panel resolves to `AVAILABLE` (9 divisions) or `NOT_AVAILABLE` with its specific reason. Verified on all three `occupation_prior_status` values. |
7 | **Occupation view** | **PASS** | 9 NCO-2015 divisions (code + title, untranslated); national composition panel plus the within-state × division district panel; state selector limited to the 3 states that actually have Census structure. |
8 | **PLFS context** | **PASS** | `tier: SUPPORTING`, `evidence_status: ["OBSERVED"]` read from the data, `is_demand_measure: false`, `data_flag {not_a_demand_measure: true}`, `valid_geo_levels: ["NATIONAL"]`, banner `SUPPORTING CONTEXT - NOT A DEMAND MEASURE`. All 81 rows carry the flag. No PLFS-derived field exists — the served field set equals the published column set exactly. |
9 | **Methodology** | **PASS** | 20,751 chars. Four evidence tiers with plain-language definitions; the estimated-vs-unavailable distinction; `NUMERIC_GAP: NOT_IDENTIFIABLE` with its reason; hybrid-is-experimental; the five-vintage table; per-output stored methodology strings; the derivation rules including their prohibited framings. |
10 | **Coverage** | **PASS** | Derived disclosures with their `derived_from` provenance; 18 coverage metrics; barred fields; 14 data-quality checks. |
11 | **Unavailable capabilities** | **PASS** | All 16 rendered, grouped by reason code, each with reason + gate. Ten have real routes returning **HTTP 200 + `data: null`** — never 404, never `[]`, never 0. |
12 | **Exports** | **PASS** | 11 production outputs × CSV + JSON; every file carries the 13 mandatory metadata keys, coverage lines, limitations and prohibited interpretations, plus (new) per-column semantics. Hybrid → **403**; non-production and traversal attempts → **404**. |
13 | **Multilingual** | **PASS** | English complete (106 keys); Hindi partial (21) by design. **83 keys fall back to English and 0 raw keys leak.** No fabricated translation. Official NCO/NIC/LGD codes preserved under translation. The terminology lint runs on **both** catalogues. |
14 | **Accessibility** | **PASS** | 20/20 checks: skip link, landmarks, `aria-live`, labelled select, `:focus-visible`, 44 px targets *(fixed)*, dark mode; 10 tables / 10 captions, 56 `scope="col"`, 11 `aria-describedby`, 60 signal bars with text alternatives, 54 `aria-hidden` glyphs; **caveat precedes its table in DOM order** (3422 < 3900). |
15 | **Terminology safety** | **PASS** | 18 surfaces swept (8 pages, chrome, both i18n files, CSS, OpenAPI, 2 export headers, error bodies) against 14 precise contract rules — **12 PASS, 2 audit-script false positives** verified by hand (§3). B and C carry their approved allocation labels with caveats; no banned ranking phrase appears; no forecast, trend or directional glyph anywhere; confidence never numeric. |
16 | **Source / vintage visibility** | **PASS** | Each output carries its own `vintage` + `vintage_source`; five vintages remain distinct (2024-11-15 / 2023-12-21 / 2024-03-31 / M202504 / 2011). **No global "data as of"** — the only occurrence is the methodology page negating it. |
17 | **Error handling** | **PASS** | Invalid state → 404; invalid district → 404; missing required `state` → 422; bad enums → 422. Frontend renders its error state for a bad deep link rather than an empty page. **Available-but-no-match, not-available and unsupported-capability remain three distinct outcomes** in both API and UI *(UI distinction added)*. |
18 | **Security basics** | **PASS** | No secrets, no `.env`, no debug flag, no CORS exposure, no stack traces (6 hostile inputs → no `traceback`/`duckdb`/`select`/path leakage). SQL is parameterised; the only f-string interpolation is of module constants. Path traversal on exports → 404. **One reflected XSS found and fixed** (§2.1). Warehouse opened **read-only**. |
19 | **Performance basics** | **PASS** | 15 routes × 5 runs: median ≈ 14 ms, slowest `/api/meta/filters` 67 ms, `/api/health` 0.8 ms. Largest JSON payload is the 3.3 MB district×occupation export (a download). Nothing demo-blocking; no optimisation applied. |
20 | **Data integrity** | **PASS** | 40 tables / 7 migrations / 82,358 rows unchanged; all 14 analytical row counts and 7 measure sums identical; no zero substituted for a missing signal; residual still `NATIONAL` and unallocated; no gap/shortage/forecast/surplus column or table exists; no state or district trade supply created. |

**Not applicable:** none of the 20 items. **Partial:** see §4 (map component designed in Step 7.3 but not built in Step 7.4).

---

## 2. Defects found and fixed

All six were implementation or QA defects fixable within the contract. **None required a methodology change,
a data change, or a weakened guardrail.**

### 2.1 Reflected XSS through a route argument — **demo-critical, fixed**

`esc()` escaped `& < > "` but **not `'`**. The occupation page rendered
`onchange="go('occupation', '${esc(d)}')"`, where `d` came from `location.hash`. A payload of
`#occupation/x');alert(document.domain);//` closed the JS string literal inside the inline handler and
executed. Confirmed by executing the real `app.js` in a DOM harness against the live API.

**Fixed in three layers:** `esc()` now also escapes `'` and backtick; `safeArg()` validates every route
argument against `^[A-Za-z0-9][A-Za-z0-9 ._-]{0,63}$` and drops anything else; and the inline handler no
longer interpolates at all — it reads `this.dataset.division`. `t()`'s variable substitution is escaped too,
since translated strings land in `innerHTML`. Five regression tests, including a static assertion that **no
inline handler interpolates anything but a page name from the `PAGES` constant**.

### 2.2 District rank rendered "rank / 0" — **fixed**

The district page read `r.meta.districts_in_state`, which only the *list* route set, behind a ternary
(`… ? '' : ''`) that was inert in both branches. `count('')` → `Number('')` → `0`, so the chip read
*"25 / 0"*. **Fixed** by adding `districts_in_state` to the district-detail envelope and removing the dead
ternary. Now *"25 / 31"*. Two regression tests.

### 2.3 An available output with no matching rows rendered an unexplained empty table — **fixed**

A bogus deep link (`#occupation/99`) produced empty tables with no explanation, blurring
*available-but-no-match* into *unavailable* — the distinction §C requires. **Fixed** with a `noMatch()`
notice that names the state and points to Unavailable capabilities. Also hardened four `Math.max(...)` calls
that returned `-Infinity` on an empty filtered set.

### 2.4 Export mixed a relative signal with an observed count under one declared unit — **fixed**

`demand_district_relative_signal` exports carry both `relative_demand_signal` and
`observed_state_vacancies` (= **2,308** on a district row — the *state* total, repeated). The header declared
a single `unit` for the output, so a reader could take a state total for a district vacancy count. Nothing was
renamed, but the metadata was incomplete. **Fixed** with a `column_notes` block in both CSV header and JSON
meta, naming the measure and flagging each coarser-grain observed input — *"OBSERVED input at STATE grain,
repeated on every district row of that state. It is NOT this district's vacancy count."*

### 2.5 The coverage page displayed a training domain as "supply" — **fixed**

`/api/coverage` emitted `domain: "supply"` for training-evidence rows, and the UI rendered it. "Supply" is a
reserved word that may not name a training measure (Rule T-2). **Fixed** with a `domain_label`
(*"Training evidence"*), which the UI now displays; the `domain=supply` query key is retained for
compatibility and documented as such.

### 2.6 Interactive targets were 38 px, below the 44 px WCAG 2.1 AA minimum — **fixed**

`select`, `.btn`, nav buttons and `summary` raised to `min-height: 44px`.

---

## 3. Terminology audit: the two remaining "failures" are correct behaviour

The precise claim audit reports 12 of 14 rules passing. Both exceptions were inspected in rendered text and
are the methodology page **publishing the prohibitions**, which is the guardrail working:

> *"May be shown under: How this signal is derived · Derivation · How this is calculated.* **Must not be
> labelled:** *supporting evidence for the demand signal · independent validation · corroborating demand
> data · corroborating evidence"*

> *"Figures on this site come from five sources with different as-on dates.* **No single "data as of" date
> applies**, *and no trend may be drawn across them."*

A keyword sweep cannot tell a prohibition from a claim; a human read can. Both are retained deliberately —
removing them would hide the rules from the reader. The third original failure (coverage "supply") **was** a
genuine leak and is fixed (§2.5).

The broad 12-term sweep over 18 surfaces produced 67 allowed negations, 158 identifiers/enum tokens and 3
explanatory uses. Every remaining `vacanc` occurrence belongs to genuinely **OBSERVED** vacancy evidence —
`analytical_demand_by_industry` ("Vacancies (lakh)"), `observed_state_vacancies`, the
`lakh_vacancy_equivalent` unit, or a `prohibited_interpretations` list. Step 7.1 explicitly permits
legitimate observed-vacancy terminology; none of these labels a relative signal.

---

## 4. Known limitations, non-blocking

| Limitation | Status |
|---|---|
**No map component.** Step 7.3 specified a within-state choropleth; Step 7.4 built tables only. The `table.showMap` / `table.mapFallback` keys exist unused. | **PARTIAL.** Not a false claim, and not demo-blocking: tables are the *only* representation, so no value is reachable only via a map — which is exactly what the accessibility fallback requires. Implementing it is a later step. |
**Hindi is 21 of 106 keys.** | By design. Missing keys fall back to English; 0 raw keys leak. Fabricating translations of official terminology is prohibited. |
**No charts.** Relative-signal bars and ranking tables only. | Deliberate — §5.2 of the design prohibits most chart forms here, and no permitted chart type was required for the journey. |
**`/api/meta/filters` is the slowest route (67 ms)** — four `DISTINCT` queries. | Not optimised; far below any demo threshold. |
**The 3.3 MB district×occupation JSON export.** | Acceptable for a download; the UI never fetches it. |
**Occupation detail covers 3 of 36 states, 138 of 785 districts.** | Evidence limit, disclosed everywhere it applies. Not a defect. |

**No defect was left unfixed. No defect required reporting-instead-of-fixing** — none could only have been
fixed by changing methodology or analytical data.

---

## 5. What must NOT be claimed in the demo

1. **No demand–supply gap, shortage, surplus or deficit** — at any grain. `NOT_IDENTIFIABLE`.
2. **No forecast, projection, trend or direction.** One dated demand observation.
3. **Outputs B and C are not demand rankings and not vacancy counts.** Within a state, B's ordering *is* the
   Udyam enterprise-share ordering; within a district, C's *is* the Census-2011 occupation-share ordering.
   Say "relative demand allocation signal".
4. **No national, state or district total labour demand.** 58.13% of published NCS vacancies is
   unattributable, and the measure is cumulative registrations since inception.
5. **Training outcomes are not supply.** Candidate counts within a named scheme and period, with no
   occupation dimension.
6. **PLFS is context, not demand** — and national only.
7. **Udyam and Census structures are derivation inputs, not corroboration.**
8. **"Multiple States/PAN India" is not a state** and is never allocated.
9. **Nothing is "live", "current" or "as of today".** Five vintages spanning fourteen years.
10. **Confidence is a category, never a percentage.** Output C is LOW; B is MEDIUM.
11. **The hybrid pressure indicator is not implemented** and is not part of the product.
12. **Don't call the drill-down "nationwide".** Occupation detail is 3 states, 138 districts.

## 6. What the demo can claim, safely

Observed NCS vacancy evidence by state and sector, with named source documents · an estimated national
occupation composition with per-row confidence · a reproducible district and district×occupation *allocation
signal* with its derivation stated on the face of every ranking · PLFS context, correctly fenced · full
coverage and data-quality disclosure · **16 unavailable capabilities published with reasons and the objective
gates that would unlock them** · exports that carry their own caveats · an accessible, bilingual interface ·
and `make reproduce` from immutable raw snapshots to the dashboard.

The strongest honest claim: **this system refuses to state what its evidence cannot support, and it shows you
exactly which dataset would change that.**

---

## 7. Implementation Gate

Step 7.5 changed **no analytical value, formula, table or migration**. The six fixes touched only
`api/static/app.js`, `api/static/styles.css`, `api/static/i18n/en.json`, `api/routers/demand.py`,
`api/routers/exports.py`, `api/routers/coverage.py` and `tests/test_api.py`.

**A later step may** implement the within-state choropleth (with its table always present), extend Hindi
coverage with reviewed translations, and add permitted chart types. **It may not** introduce a gap, forecast,
supply quantity, composite score or the hybrid indicator, or weaken any guardrail audited here.
