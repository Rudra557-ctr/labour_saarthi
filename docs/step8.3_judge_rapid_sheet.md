# Judge Q&A — Rapid Sheet

**One glance, one answer.** 1–3 sentences each. Full versions in `docs/step8.1_final_judge_answers.md`.
Print single-sided; keep it face-down beside the laptop.

---

## A · Problem

**What problem are you solving?**
Skilling targets are set from six official sources that cannot be joined. We solve the reconciliation — making heterogeneous official evidence comparable without fabricating the comparison.

**Isn't this just a dashboard?**
The dashboard is the delivery; the reconciliation is the product. 40 tables, 3,982 conformed occupations, 14 of 14 reconciliations exact against each source's own totals.

---

## B · Data

**Which sources, and are they official?**
All Government of India. 26 registered under a licence gate, 15 acquired as checksummed snapshots, 6 feed production: NCS, Udyam, Census 2011 B-24, LGD, PLFS, MSDE Annual Report.

**Why is your data old — November 2024?**
2024-11-15 is the as-on date of the most recent NCS figures published in Parliament. It's the frontier of what's official, not a stale choice.

**Why not scrape Naukri or Indeed?**
Terms of service, and postings aren't vacancies — duplicated and urban-biased. It also wouldn't fix our blocker, which is supply-side.

**Did you bypass any access control?**
No. We completed one incomplete TLS chain legitimately from the certificate's own AIA URL with verification left on, and **refused** a site presenting a self-signed certificate.

**How do you know extractions are correct?**
14 of 14 reconciliations match each source's own published totals exactly. One early parser double-counted Census by 1,612,514 workers — a row-type classifier fixed it.

---

## C · AI / ML

**Where is the AI?**
I'll be direct: **no machine-learning model is in production and no ML library is installed.** We won't invent one to match a title.

**Why no ML?**
Every ML capability this PS implies is blocked by the same missing evidence. Forecasting needs two dated observations; we have one. A learned gap model needs a target; the target isn't identifiable.

**Why not use an LLM to infer the missing data?**
An LLM can't observe a state-by-trade cell nobody measured. It would produce fluent numbers with no provenance — and the error would be invisible.

**Any legitimate place for an LLM?**
One: a grounded query interface over fixed parameterised queries, read-only, answers grounded in returned rows. Designed, not built. Free-form text-to-SQL is rejected.

**How do you prevent hallucination?**
Structurally. No model generates any value. Evidence status is read from the data, never declared — we have a test that forges a lying config and proves the API still says ESTIMATED.

---

## D · Methodology

**How do you map "Welder" to an ITI trade?**
We don't. Fuzzy, semantic, embedding and LLM mapping are prohibited project-wide. Our 2 official trade→NCO links came from DGT's own curriculum PDFs; **153 of 155 remain MAPPING_UNKNOWN**.

**Census is NCO-2004, your spine is NCO-2015. Valid?**
Through the **official** 3,447-row concordance. And we measure division purity rather than assume it — division 2 is 0.998, division 3 is 0.789.

**Why is Census 2011 acceptable in 2024?**
It's the most recent Indian census occupational structure — 2021 wasn't conducted. We use it as a structural prior only, and the 14-year gap is printed on the district page.

**What exactly is estimated vs observed?**
Observed: NCS state and industry demand. Estimated: the occupation composition and the two allocation signals. And the distinction is read from each table's own column, never declared in config.

---

## E · Gap / forecasting

**Where is the demand–supply gap?**
We don't publish one. Supply by state and trade is a **joint distribution**; we hold row totals plus 21.8% of column totals from a *different scheme*. Margins never determine an interior.

**If you can't calculate the gap, how does this solve the PS?**
It doesn't fully — gap forecasting is `NOT_SUPPORTED_YET` and our requirement mapping says so. What we deliver is the platform plus a reproducible proof of *why*, and the dataset that resolves it.

**Why no forecasting?**
One dated demand observation. A single point can't support a trend, and PMKVY 1.0→2.0 isn't a time series — different schemes, state orderings unrelated at +0.005.

**What would unlock the gap?**
**State-by-trade training outcomes with complete marginals** — one observed interior cell of SUPPLY[geography × trade]. That's gate G-1. More of the same margins never passes it.

**Why not synthetic data?**
A synthetic gap looks exactly like a real one. The error would be invisible, directionally wrong, and it informs seat sanctioning — real money. We used none.

---

## F · Product / engineering

**Why separate fact tables?**
A survey estimate, an administrative count and a census stock are different kinds of fact. Merging them makes an invalid comparison expressible in SQL — and therefore inevitable.

**Is it reproducible?**
`make reproduce` — verify every snapshot against its sha256, rebuild everything, run 479 tests. Raw storage is immutable; a fetch never overwrites.

**Why DuckDB not Spark?**
82,358 rows. DuckDB needs no server and makes grain-safe joins reviewable as plain SQL — which matters when the correctness of a join *is* the methodology.

**Why do blocked endpoints return 200, not 404?**
A 404 reads as "none found"; an empty array reads as "zero". The truth is "not computable" — so we return 200 with `data: null`, a reason code and a gate.

**What stops a developer overstating a claim later?**
Four layers: the contract won't load if a mode is weakened, the app won't start if a label fails the lint, every response carries its envelope, every export carries it as a file header.

**Any security review?**
Yes — we found and fixed a reflected XSS in our own dashboard, closed in three layers. No secrets, no CORS exposure, parameterised SQL, warehouse opened read-only.

---

## G · Innovation

**What's genuinely novel?**
Identification-aware analytics — distinguishing "we lack this data" from "this isn't identifiable from evidence of this shape", and treating the second as a mathematical result.

**Anything else?**
A publication contract enforced in code with startup refusal; evidence status read from the data not declared; caveats stored as columns; a terminology lint covering translation files.

**Isn't "we couldn't do it" a weak submission?**
The submission isn't "we couldn't" — it's a reproducible proof of which quantity is unidentifiable, plus the exact dataset that resolves it. A planner can act on that.

---

## H · Scalability

**Does this scale to all of India?**
On the dimension that matters — evidence, not rows. Census B-24 for the remaining 33 states takes output C from **138 toward 785 districts with no formula change**.

**What if better data arrives?**
The conformance layer, estimator, confidence framework and contract already exist. It's acquisition and validation, not architecture — which is why we built the platform rather than a number.

**What about district boundary changes?**
LGD is effective-dated, and 125 post-2011 districts correctly have **no** Census code — which is why their occupation detail is permanently unavailable rather than merely unacquired.

---

## I · Limitations

**Can you tell MSDE which trade to train more?**
**No.** That needs occupation-level supply, which doesn't exist at any geographic grain. We can say which district × occupation shows a higher relative signal within a state, at LOW confidence.

**How reliable are the estimates?**
We don't claim reliable — we claim **labelled**. Output B is MEDIUM, C is LOW by construction. Confidence is weakest-link: the worst dimension, never an average.

**Isn't your district ranking just enterprise density?**
**Within a state, yes — and we print that above the table.** Zero of thirty-six states differ. The demand component only varies between states.

**What's the weakest part?**
Output C. 138 of 785 districts, a 14-year-old structure, and within a district its ordering is just the Census ordering. We print all three facts above the table.

**What about the hybrid indicator?**
Designed, `EXPERIMENTAL_ONLY`, not implemented, absent from the product. Its flag set collapses from 207 to 0 depending on which training scheme you read.

**What happens to the 58% PAN-India vacancies?**
Nothing, deliberately. 20,507,320 belong to no state; allocating them is a `PROHIBITED` capability. The district signal rests on the remaining 41.87%.

---

## If you don't know

> *"I don't want to guess at that — it's in the repository and I'd rather be exact than approximate."*

**Never improvise a number.**
