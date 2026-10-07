# Future Roadmap — One Slide

**No dates. No promised capability without the evidence that makes it defensible.** Every source named below
was already investigated in this project; none is invented here.

---

## Slide title

### One dataset unlocks the gap

```
┌──────────────────────────────────────────────────────────────────────────┐
│  NOW                                                                     │
│  Evidence-qualified demand intelligence                                  │
│  • Observed NCS demand: state · industry                                 │
│  • Estimated: national occupation composition                            │
│  • Estimated: District (785) and District × Occupation (138) allocation  │
│    signals, with provenance, confidence and coverage on every value      │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   DATA UNLOCK  · G-1    │   state × trade training
                    │                         │   outcomes, COMPLETE
                    │  one OBSERVED interior  │   trade marginals
                    │  cell of SUPPLY[geo ×   │   (not a Top-N subset)
                    │  trade]                 │   + official trade→NCO
                    └────────────┬────────────┘     coverage  · G-3
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  NEXT  ·  NUMERIC DEMAND–SUPPLY GAP                                      │
│  Publishable only where demand and supply share the same time grain,     │
│  geography, occupation grain, unit and population definition             │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   DATA UNLOCK  · G-4    │   a SECOND dated NCS
                    │  ≥2 dated observations  │   observation of the same
                    │  of the same measure    │   measure and basis
                    └────────────┬────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  NEXT  ·  TEMPORAL FORECASTING                                           │
│  Naive baselines first, then classical, then a pooled global model.      │
│  Rolling-origin backtesting before anything is published                 │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ UNLOCK · G-5 G-6 G-7 G-8│   occupation dimension on
                    │                         │   the training axis +
                    │ G-7 is NON-NEGOTIABLE   │   scheme-independent or
                    └────────────┬────────────┘   stable evidence + coverage
                                 ▼                + stability demonstration
┌──────────────────────────────────────────────────────────────────────────┐
│  NEXT  ·  VALIDATED EARLY-WARNING SYSTEM                                 │
│  Still `is_measured_shortage = FALSE`. A prioritisation instrument,      │
│  never a shortage measure                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## The evidence each transition actually requires

| Transition | Required evidence | Current blocker |
|---|---|---|
**→ Numeric gap** | **G-1:** one observed interior cell of `SUPPLY[geography × trade]`, plus matching time grain, geography, occupation grain, unit and population definition. **G-3:** complete trade marginals + sufficient official trade → NCO coverage | Only **national × Top-N** exists (35 rows). 78% of PMKVY 4.0 enrolment is in unnamed job roles, so even raking is unavailable. **2 of 155** trades officially NCO-mapped |
**→ Forecasting** | **G-4:** ≥2 defensible dated observations of the same demand measure, same basis, same geography, same source; a flow or two differenceable stocks; no scheme or definition change between them; rolling-origin backtesting against naive baselines | **One** NCS as-on date (2024-11-15). `flow_available = FALSE` on every demand row. PMKVY 1.0 → 2.0 is **permanently excluded** — different schemes, state orderings unrelated (**+0.005**) |
**→ Early warning** | **G-7** occupation dimension on the training axis *(non-negotiable — without it a flag can never name what is short)* · **G-5** scheme-independent or stable training evidence · **G-6** coverage above 138/785 districts and 3/36 states · **G-8** a pre-registered stability demonstration | Flag set collapses **207 → 0** on scheme substitution. Training axis has exactly **3** distinct values for 1,242 cells |
**→ Wider demand coverage** *(parallel, no gate)* | **Census 2011 B-24 for the remaining 33 states** — same source, already parsed; a pure acquisition task | Acquisition only. **Would take output C from 138 → up to 785 districts with no formula change** |

---

## Named sources, with their actual status

| Source | Status | Would unlock |
|---|---|---|
data.gov.in — PMKVY district outcomes | **`ACCESS_PENDING`** *(needs a registered API key)* | district × trade supply (G-2) |
NCVT MIS (`ncvtmis.gov.in`) | `UNAVAILABLE` | ITI district × trade capacity |
NQR bulk filter-search | `UNAVAILABLE` | qualification → NCO at scale (G-3) |
`apprenticeshipindia.gov.in` (NAPS portal) | `UNAVAILABLE` | state × trade apprenticeship outcomes (G-1) |
Remaining DGT CTS curriculum PDFs | acquirable, per-trade | the other 153 official trade → NCO mappings |
Census 2011 B-24, other 33 states | acquirable, same parser | 138 → up to 785 districts |
A second dated NCS publication | awaiting publication | any forecast (G-4) |

---

**Speaker note:** *"Nine objective gates, published inside the product itself. The decisive one is G-1
condition six — one observed interior cell of supply by geography and trade. The other five conditions are
harmonisation problems that better data solves. Condition six is why this is an identification failure:
more of the same marginals never passes it. And note the bottom row — Census B-24 for thirty-three more
states is pure acquisition. The architecture already handles the full grid."*

**Explicitly not promised:** any date, any timeline, any capability without its gate, and any source not
already investigated above.
