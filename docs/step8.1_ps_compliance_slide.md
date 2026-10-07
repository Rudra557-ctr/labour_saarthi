# PS Compliance — One Slide

**PS 26246 · ten stated requirements · nothing hidden.**

| # | Requirement | Status | What we implemented | Evidence / blocker | Future unlock |
|---|---|---|---|---|---|
**R1** | Aggregate & normalise fragmented demand signals | **IMPLEMENTED** | 26 sources under a licence gate · 15 acquired immutably (35 files) · conformed to NCO-2015, LGD, NIC-2008 · 40 tables, 82,358 rows | 14/14 reconciliations exact | permitted aggregator API |
**R2** | Cross-reference demand vs training capacity by sector/trade/district | **DATA_BLOCKED** | Both sides published **side by side, never subtracted** — 350 state training rows + PMKK infrastructure | No district/state × trade or × occupation supply exists. PMKVY district resource `ACCESS_PENDING`; NCVT MIS `UNAVAILABLE` | **G-2 · G-3** |
**R3** | **Forecast demand–supply gaps** at sector + district granularity | **NOT_SUPPORTED_YET** | Gap & forecast routes return explicit `UNAVAILABLE` + reason + gate | Gap: supply is a joint distribution; we hold margins + a 21.8% fragment from another scheme. Forecast: **one** dated observation | **G-1** (gap) · **G-4** (forecast) |
**R4** | Rank trades/geographies by oversupply/undersupply severity | **PARTIALLY_IMPLEMENTED** | District, district × occupation and state rankings on **relative allocation signals**, each with its caveat | *Severity* presupposes a gap. Within a state, output B's order **is** the Udyam order (0/36 differ) | **G-1** · **G-6** |
**R5** | Dashboard, national → state → district drill-down | **IMPLEMENTED** | 8 pages · full drill-down · `state` required at the protocol level · offline-capable | No map component (designed, not built) — tables are the only representation | map in a later step |
**R6** | Documented methodology | **IMPLEMENTED** | 40 docs incl. 15 ADRs · in-product Methodology page rendering **stored** methodology strings · machine-readable contract | — | — |
**R7** | Early-warning flags (saturation / acute shortage) | **EXPERIMENTAL** *(not implemented)* | Hybrid quadrant fully designed; declared `EXPERIMENTAL_ONLY`, `implemented: false`, absent from API/dashboard/exports | 207 flags under PMKVY 2.0 vs **0** under PMKVY 1.0; cross-scheme rank corr. **+0.005** | **G-5 · G-6 · G-7 · G-8** |
**R8** | API / export layer | **IMPLEMENTED** | FastAPI · 30 routes (20 production, 10 blocked) · OpenAPI · 11 outputs as CSV + JSON with caveats in the file header | — | — |
**R9** | Multilingual + accessible | **PARTIALLY_IMPLEMENTED** | Full i18n architecture · EN complete (106 keys) · HI 21 keys with English fallback, **0 raw keys leaked** · 20/20 accessibility checks | Hindi 20% — official occupational terms are **not** machine-translated | reviewed translations |
**R10** | Cover at least a few pilot sectors & States | **IMPLEMENTED** | National observed demand (37 states, 22 sectors) · 785 districts for output B · **3 states / 138 districts** for output C — UP 71, MH 35, TN 32 | Census B-24 acquired for 3 states | **G-6** → up to 785 districts, **no formula change** |

---

### Summary

> **6 IMPLEMENTED · 4 PARTIALLY_IMPLEMENTED · 3 DATA_BLOCKED · 2 NOT_SUPPORTED_YET · 1 EXPERIMENTAL**
> *(a requirement may carry more than one status across its parts)*
>
> **The three requirements that depend on a demand–supply gap are blocked by evidence, not by engineering.**
> One dataset — state × trade training outcomes with complete marginals — unblocks R2, R3 and R4 together.

**Speaker note:** don't read the table. Say: *"Six implemented, four partial, and the three that need a gap
are blocked by evidence. R3 is the one everyone will look at — it is `NOT_SUPPORTED_YET`, and I'd rather tell
you that than mark it green."*
