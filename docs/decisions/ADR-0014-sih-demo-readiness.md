# ADR-0014 — SIH demo readiness: the system is cleared to demonstrate

- **Status:** Proposed (QA record; awaiting review)
- **Date:** 2026-10-06
- **Records the audit of:** ADR-0011 (publication policy), ADR-0012 (information architecture),
  ADR-0013 (SUPPORTING tier and allocation-signal terminology), and the Step 7.4 implementation
- **Supersedes:** nothing. No guardrail was weakened and no contract term changed.
- **Report:** `docs/step7.5_sih_demo_readiness.md`

## Context

Steps 7.1 to 7.4 built a publication contract, enforced it in code, designed a product around it and
implemented that product. What had not been established was whether **the running system can be driven into
making a stronger claim than its evidence supports** — by a user clicking through it, by a URL someone types,
by an export opened in a spreadsheet, or by a demo operator reading a label aloud.

Step 7.5 audited the whole chain — warehouse → publication contract → API → frontend → export → user
interpretation — by executing the real application rather than reading it: the live API was exercised over
every route, and `app.js` was run in a DOM harness against that API so every page, deep link and hostile
input produced real rendered output to inspect.

## What was validated

- **20 readiness items**, all PASS (§1 of the report).
- **30 API routes**: 20 production and 10 blocked. Every blocked route returns **HTTP 200 with `data: null`**,
  a reason code and a gate — never 404, never `[]`, never 0.
- **8 frontend pages** plus 6 deep links, rendered and inspected; **0 runtime errors, 0 suspect output**
  after fixes.
- **A 16-step canonical demo journey**, every step confirmed against the running app.
- **22 exports** (11 outputs × CSV + JSON), each carrying the 13 mandatory metadata keys.
- **14 precise terminology rules** over 18 user-facing surfaces.
- **20 accessibility checks**, including that a caveat precedes in DOM order the table it qualifies.
- **Both language catalogues** linted; 83 keys fall back to English with **0 raw keys leaked**.
- **12 hostile or malformed inputs**: no SQL injection, no traceback, no path traversal, no path leakage.
- **15 routes profiled**: median ≈ 14 ms, slowest 67 ms.
- **Full data regression**: 40 tables, 7 migrations, 82,358 rows, 14 row counts and 7 measure sums — all
  unchanged.

## Defects found

Six, all fixed within the bug-fix policy. **None required a methodology change, a data change, or a
weakened guardrail.**

| # | Defect | Severity |
|---|---|---|
1 | **Reflected XSS.** `esc()` did not escape `'`, and an inline `onchange` handler interpolated a `location.hash` argument into a JS string literal. `#occupation/x');alert(document.domain);//` executed. | **demo-critical** |
2 | **District rank rendered "25 / 0."** The detail envelope lacked `districts_in_state`, behind a ternary inert in both branches; `count('')` → 0. | correctness |
3 | **An available output with no matching rows rendered an unexplained empty table**, blurring *no match* into *unavailable*. Four `Math.max(...)` calls also returned `-Infinity` on an empty set. | correctness |
4 | **An export mixed a relative signal with a coarser-grain observed count** (`observed_state_vacancies` = a *state* total on a district row) under one declared unit. Nothing renamed; metadata incomplete. | metadata |
5 | **The coverage page displayed a training-evidence domain as "supply"** — a reserved word that may not name a training measure. | terminology |
6 | **Interactive targets were 38 px**, below the 44 px WCAG 2.1 AA minimum. | accessibility |

The XSS is the finding that mattered. Escaping only `& < > "` is a common and plausible-looking mistake, and
the vulnerable sink — one inline handler out of two — was not visible from reading the page's output; it took
executing the page with a hostile hash to surface it. It is now closed in three independent layers
(validate the argument, escape the delimiter, remove the interpolation), with a static test asserting that no
inline handler interpolates anything but a compile-time constant.

## Decisions

1. **The system is SIH-demo-ready.** All 20 readiness items pass, the 16-step journey runs end to end on the
   live application, and no demo-critical defect remains open.

2. **The six fixes stand as made.** Each was confined to the API serialisation or frontend layer. No
   analytical module, formula, value, table or migration was touched.

3. **Two reported terminology "failures" are retained as correct behaviour.** The methodology page publishes
   the prohibited corroboration labels and the prohibited vintage phrasings — the guardrail made visible. A
   keyword sweep cannot distinguish a prohibition from a claim; both were read in rendered text and confirmed
   as negations. Removing them would hide the rules from the reader, which is the opposite of the intent.

4. **Legitimate observed-vacancy terminology is retained.** Every remaining `vacanc` occurrence belongs to
   genuinely OBSERVED evidence — `analytical_demand_by_industry`, `observed_state_vacancies`, the
   `lakh_vacancy_equivalent` unit, or a prohibition list. Step 7.1 permits this explicitly, and none of it
   labels a relative signal.

5. **The missing map is recorded as a PARTIAL, not a defect.** Step 7.3 specified a within-state choropleth;
   Step 7.4 built tables only. This makes no false claim and blocks nothing: tables are the *only*
   representation, so no value is reachable only through a map — which is precisely what the accessibility
   fallback requires. It is deferred, not waived.

6. **Twelve claims are prohibited during the demo**, listed in §5 of the report, chief among them: no gap, no
   forecast, no total labour demand, outputs B and C are allocation signals rather than demand or vacancy
   rankings, training outcomes are not supply, and PLFS is national context.

## Consequences

**Positive.** The contract is now enforced at four independent layers — contract load, application startup,
HTTP response, and export header — and the application **refuses to start** if a label, translation string or
envelope breaches it. 19 new regression tests pin every defect found, so none can return silently. The demo
operator has an explicit list of what may and may not be said. The reusable DOM harness means the frontend is
genuinely testable without a browser.

**Negative, and accepted.**

- **The honest labels are long.** "District × Occupation Relative Demand Allocation Signal" with two caveats
  above its table is not a crisp demo visual. It is accurate, and every shorter phrasing asserts something
  the output does not contain.
- **The product looks modest next to the problem statement.** Its headline capability is a relative ranking
  at LOW confidence over 17.6% of districts, and the most striking page is the one listing what cannot be
  computed. An audience expecting a gap dashboard will not find one.
- **No map**, which is the most expected visual in a government dashboard.
- Hindi is partial, and will read as unfinished to a Hindi-speaking reviewer — the alternative was fabricating
  official occupational terminology.
- The audit relies on a DOM harness rather than a real browser, so CSS rendering, actual focus order and real
  screen-reader output are verified structurally rather than observationally. A manual pass with a screen
  reader before the demo would close that gap.

**Reversal condition.** Superseded only by a new ADR. A fix that requires changing methodology or analytical
data is out of scope for QA by construction and must be raised as its own step.

## Implementation Gate

**A later step may** implement the within-state choropleth (with its ranked table always present), extend
Hindi with reviewed translations, add permitted chart types, and run a manual screen-reader pass.

**It may not** introduce a numeric gap, a forecast, a supply quantity, a composite score or the hybrid
indicator; change an analytical formula or value; add a table or migration; or weaken any guardrail audited
here.

## Verification

479 tests passing (460 → 479). `make reproduce` complete. 40 tables, 7 migrations, 82,358 rows — unchanged.
All analytical row counts and measure sums identical. No numeric gap, no forecast, no synthetic data, no
composite score, no unsupported supply, no residual allocation. `is_measured_shortage = false` on every
response, enforced at startup. Hybrid remains `EXPERIMENTAL_ONLY`, `implemented: false`, absent from the API
surface, exports and OpenAPI.
