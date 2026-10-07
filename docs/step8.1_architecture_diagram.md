# Architecture Diagram Specification — Slide 4

One diagram, one job: **show that unsupported values are blocked rather than invented.**

Vertical flow down the centre. **Master dimensions on the left rail** (they are consulted, not passed
through). **Evidence gates on the right rail** (what each layer stamps onto a value). **The no-fabrication
boundary as a hard red stop** — the only red in the diagram, so the eye goes there.

---

## 1 · The diagram

```
   MASTER / REFERENCE                  PIPELINE                      EVIDENCE GATE
   ════════════════════     ═══════════════════════════════     ═════════════════════

                            ┌─────────────────────────────┐
                            │  OFFICIAL SOURCES    (26)   │
                            │  NCS · Udyam · Census B-24  │
                            │  LGD · PLFS · MSDE AR       │
                            └──────────────┬──────────────┘
   ┌───────────────┐                       │  ▲ LICENCE GATE
   │ source /      │◀──────────────────────┤    nothing acquired
   │ provenance    │                       │    unless registered
   │ registry (26) │         ┌─────────────▼──────────────┐
   └───────────────┘         │  RAW SNAPSHOTS             │
                             │  sha256 · retrieved_at     │      ┌──────────────┐
                             │  IMMUTABLE — never         │─────▶│  PROVENANCE  │
                             │  overwritten  (35 files)   │      │  attached    │
                             └─────────────┬──────────────┘      └──────────────┘
                                           │
                             ┌─────────────▼──────────────┐
                             │  STANDARDISATION           │
                             │  PDF · HTML · XLSX · DBF   │
                             │  NULL ≠ 0 ≠ '-' ≠ 'NA'     │
                             └─────────────┬──────────────┘
   ┌───────────────┐                       │
   │ LGD / location│──────────┐            │
   │ 821           │          │            │
   ├───────────────┤          │  ┌─────────▼──────────────┐
   │ NCO-2015      │──────────┼─▶│  NORMALISATION         │
   │ 3,982         │          │  │  geography · occupation│
   ├───────────────┤          │  │  sector · period       │
   │ NIC / NCS     │──────────┤  │                        │
   │ sector 21/22  │          │  │  every mapping carries │
   ├───────────────┤          │  │  authority + method    │
   │ dim_period    │──────────┘  │  + confidence          │
   │ 132           │             └─────────┬──────────────┘
   └───────────────┘                       │
                             ┌─────────────▼──────────────┐      ┌──────────────┐
                             │  VALIDATION & DATA QUALITY │─────▶│  CONTRACTS   │
                             │  Pandera contracts         │      │  ENFORCED    │
                             │  reconcile to each source's│      │  14/14 exact │
                             │  OWN published totals      │      └──────────────┘
                             └─────────────┬──────────────┘
                                           │
                             ┌─────────────▼──────────────┐      ┌──────────────┐
                             │  STANDARDISED FACTS        │      │ ■ OBSERVED   │
                             │  one table per source-     │─────▶│ □ SUPPORTING │
                             │  concept, NATIVE grain     │      └──────────────┘
                             │  (never merged)            │
                             └─────────────┬──────────────┘
                                           │
                             ┌─────────────▼──────────────┐      ┌──────────────┐
                             │  ANALYTICAL DATASET        │      │ ■ OBSERVED   │
                             │  grain-safe views          │─────▶│ □ SUPPORTING │
                             └─────────────┬──────────────┘      └──────────────┘
                                           │
                             ┌─────────────▼──────────────┐      ┌──────────────┐
                             │  DEMAND INTELLIGENCE       │      │ ◪ ESTIMATED  │
                             │  A national composition    │─────▶│   weakest-   │
                             │  B district allocation     │      │   link conf. │
                             │  C district × occupation   │      │   MEDIUM/LOW │
                             └─────────────┬──────────────┘      └──────────────┘

╔══════════════════════════════════════════════════════════════════════════════════╗
║  ⛔  NO-FABRICATION BOUNDARY                                                      ║
║                                                                                  ║
║   SUPPLY[geography × trade]  →  row marginals held                               ║
║                              →  column marginals  21.8% ONLY, different scheme   ║
║                              →  marginals NEVER determine an interior            ║
║                                                                                  ║
║   ╭──────────────────────────╮        ╭──────────────────────────────────╮        ║
║   │  numeric demand–supply   │        │  ⬚ UNAVAILABLE                   │        ║
║   │  gap                     │━━━━━▶ │  reason_code: NOT_IDENTIFIABLE    │        ║
║   │  shortage · forecast     │ BLOCKED│  blocking_gate: G-1 … G-9        │        ║
║   │  occupation-level supply │        │  data: null   (HTTP 200)          │        ║
║   ╰──────────────────────────╯        ╰──────────────────────────────────╯        ║
║                                                                                  ║
║        NOT estimated.  NOT zero.  NOT 404.  NOT omitted.                         ║
╚══════════════════════════════════════════════════════════════════════════════════╝
                                           │
                             ┌─────────────▼──────────────┐
                             │  PUBLICATION CONTRACT      │
                             │  tier · evidence status    │      ┌──────────────┐
                             │  (READ FROM THE DATA) ·    │─────▶│ is_measured_ │
                             │  confidence · coverage ·   │      │ shortage =   │
                             │  vintage · limitations     │      │ FALSE        │
                             │  + terminology lint        │      │ (every row)  │
                             └─────────────┬──────────────┘      └──────────────┘
                                           │   app REFUSES TO START on breach
                             ┌─────────────▼──────────────┐
                             │  FastAPI  ·  30 routes     │
                             │  20 production · 10 blocked│
                             └─────────────┬──────────────┘
                     ┌─────────────────────┼─────────────────────┐
                     ▼                     ▼                     ▼
            ┌────────────────┐   ┌──────────────────┐   ┌────────────────┐
            │  DASHBOARD     │   │  CSV / JSON      │   │  OpenAPI       │
            │  8 pages       │   │  EXPORT  (11)    │   │  /docs         │
            │  EN / HI       │   │  caveats in the  │   │                │
            │  WCAG 2.1 AA   │   │  file header     │   │                │
            └────────────────┘   └──────────────────┘   └────────────────┘
```

---

## 2 · Drawing notes

**Three vertical bands.** Left rail = master dimensions, drawn as a stack of small boxes with arrows pointing
*into* the Normalisation layer — they are consulted, not pipeline stages. Centre = the flow. Right rail =
evidence gates, each showing what that layer *stamps onto* a value.

**The boundary is the point of the slide.** Draw it as a full-width band with a heavy border, the only red in
the diagram. Inside it: the blocked capabilities on the left, the `UNAVAILABLE` state on the right, and the
"NOT estimated. NOT zero. NOT 404. NOT omitted." line as the band's closing statement. If an audience member
remembers one thing from the diagram, it should be this band.

**Evidence tiers always as shape + text** — `■ OBSERVED` · `◪ ESTIMATED` · `□ SUPPORTING` · `⬚ UNAVAILABLE`.
Never colour alone; this mirrors the product's own accessibility rule, which is a point worth making if asked.

**Two annotations earn their space:** `LICENCE GATE` on the arrow out of sources, and
`app REFUSES TO START on breach` on the arrow out of the publication contract.

**Numbers to keep on the diagram** (all verified): 26 sources · 35 raw files · 821 LGD · 3,982 NCO · 21 NIC
sections · 132 periods · 14/14 reconciliations · 21.8% column fragment · 30 routes (20 + 10) · 8 pages ·
11 exports.

**Leave off:** row counts per fact table, the staging sub-steps, DuckDB/Parquet internals, and anything
needing a second look. If it needs explaining, it belongs in the speaker notes.

---

## 3 · Simplified variant (if the full diagram will not read from the back of the room)

```
  26 OFFICIAL SOURCES  ──licence gate──▶  IMMUTABLE RAW (sha256)
            │
            ▼
  STANDARDISE  ──▶  CONFORM to NCO-2015 · LGD · NIC · period  ──▶  VALIDATE (14/14 exact)
            │
            ▼
  FACTS (native grain, never merged)  ──▶  ANALYTICAL  ──▶  DEMAND INTELLIGENCE
            │                                                 ■ OBSERVED  ◪ ESTIMATED  □ SUPPORTING
            ▼
  ⛔ NO-FABRICATION BOUNDARY
     no compatible supply evidence  ⇒  ⬚ UNAVAILABLE + reason + gate
     NOT estimated · NOT zero · NOT 404
            │
            ▼
  PUBLICATION CONTRACT  ──▶  FastAPI (30)  ──▶  DASHBOARD · EXPORT · OpenAPI
```

Use this if the slide is projected small. It keeps the boundary and the four tiers, which are the only
non-negotiable elements.
