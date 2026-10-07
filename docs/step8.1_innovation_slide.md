# Innovation — One Slide

**Five defensible claims.** Each is checkable in the repository, and none of them is "we used a framework".

---

## Slide title

### Identification-aware analytics

> *The hard part of this problem is not model selection. It is making heterogeneous official evidence
> comparable without fabricating the comparison — and proving what cannot yet be computed.*

---

## 1 · We distinguish "missing" from "not identifiable"

Most systems have one bucket for anything absent. We have two, and the difference is the project's central
contribution.

- **`NOT_ACQUIRED`** — the source exists; we haven't got it. A paperwork problem.
- **`NOT_IDENTIFIABLE`** — the quantity cannot be determined from evidence of this *shape*. More of the same
  data never fixes it.

`SUPPLY[state, trade]` is a **joint distribution**. We hold row marginals plus a **21.8%** column fragment
(514,619 of 2,361,798) **from a different scheme**. Marginals never determine an interior.

**Why it matters:** this is the difference between a backlog item and a mathematical result. Treating the
second as the first is how fabricated numbers enter policy tools.

---

## 2 · A publication contract enforced in code

Evidence status, confidence, coverage, provenance, vintage and **prohibited interpretations** are part of the
response contract — not documentation.

- `config/publication_contract.yaml` + `src/lmis/publish/`
- **The application refuses to start** if any output breaches it
- `is_measured_shortage = false` on every response — database constraint, contract validator, startup check
  and regression test
- Four independent enforcement layers: contract load · app start · every response · every export header

---

## 3 · Evidence status is read from the data, never declared

A derived output **cannot** be relabelled `OBSERVED` by editing a config file. The envelope reads each
table's own `observation_status` / `observed_or_estimated` column; the contract declares only *which column
to read*.

**A test forges a config that lies and proves the API still reports `ESTIMATED`.**
*(That test exists because an earlier step's own summary made exactly this mistake. We made it structurally
impossible rather than promising to be careful.)*

---

## 4 · Caveats stored as data, and self-criticism we published

We measured our own signals and printed the weakness on the face of the product:

- **Within a state, output B's district ordering *is* the Udyam enterprise-share ordering** — **0 of 36**
  states differ
- **Within a district, output C's occupation ordering *is* the Census-2011 occupation-share ordering** —
  **0 of 138** districts differ
- Variance decomposition: district **61.2%**, occupation **30.7%**, genuinely district-specific occupational
  information **8.1%**

Both caveats are stored as **columns on every row**, and the contract **refuses to build a response without
them** — so the interface cannot drift from the data. The occupation view then promotes the one comparison
that restates neither input: districts within a state × NCO division, which differs from both inputs in
**27 of 27** groups.

---

## 5 · A terminology lint over the published surface

Reserved words, forbidden ranking phrasings and corroboration framings **fail the build** — in code, in UI
labels, in **translation files**, and in export headers.

- With **negation detection**, so the product can still say *"this is **not** a vacancy count"*
- And dash normalisation, so a rule written with a hyphen catches a label written with an en-dash

**Found in our own QA:** a reflected XSS where `esc()` escaped `& < > "` but not the single quote. Closed in
three layers, with a static test asserting no inline handler interpolates anything but a compile-time
constant.

---

## Also: reproducible, end to end

`make reproduce` — verify every raw snapshot against its recorded **sha256**, rebuild staging, dimensions,
facts, analytical layer and demand products, validate, load, emit the contract, lint, profile, and run
**479 tests**. Raw storage is immutable: a fetch never overwrites a snapshot, so results survive a source
going offline mid-competition.

---

## What we explicitly do **not** claim as innovation

- ✗ FastAPI, DuckDB or the dashboard — ordinary, correct engineering choices
- ✗ "AI-powered" anything — **there is no ML model in production and no ML library installed**
- ✗ Generic LLM usage — prohibited project-wide for mappings and values
- ✗ Forecasting — `NOT_SUPPORTED_YET`
- ✗ A gap, shortage or severity score — not identifiable

**Speaker note:** *"The honest innovation here is the discipline, and it's measurable. We found that our own
district ranking was really an enterprise-density ranking, and instead of hiding that we printed it above the
table and built a contract that won't let anyone remove it."*
