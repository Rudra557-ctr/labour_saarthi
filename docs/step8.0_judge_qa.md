# Judge Q&A — LMIS (PS 26246)

**38 questions across 15 categories.** Every number was verified against the repository on 2026-10-06. Where
an answer is "we can't", it says so and then says what we did instead.

**The one-sentence version, if you only remember one thing:**
> *We standardised fragmented official labour-market evidence into a reproducible, provenance-aware platform,
> and we established — rigorously — that the demand–supply gap the problem statement asks for is not
> identifiable from the evidence that exists. We publish that finding, and the exact dataset that would
> change it.*

---

## 1 · Problem understanding

**Q1. What problem are you actually solving?**
Skilling targets are set with labour-market data scattered across NCS, Udyam, PLFS, Census and scheme MIS.
Nothing combines demand with training capacity at district × trade resolution, so mismatch is discovered
after placement outcomes are reported — too late to change a target. We solve the **reconciliation** problem:
making heterogeneous official sources comparable on shared NCO-2015, LGD and period dimensions without
fabricating the comparison. That is the prerequisite for everything else the PS asks for.

**Q2. Why is this problem hard?**
Three reconciliations, each failing differently. **Semantic**: a portal says "CNC Operator", an ITI says
"Machinist (Grinder)", NCO-2015 says `7223.xxxx`. **Granularity**: demand arrives at district level but
non-representatively; survey truth arrives at state level and *is* representative. **Temporal**: the decision
is made before outcomes are observed. Combining them naively manufactures precision that does not exist.

**Q3. Isn't this just a dashboard?**
The dashboard is the delivery mechanism; the reconciliation is the product. 40 warehouse tables, 3,982
conformed NCO occupations, a 3,447-row official concordance, 14 of 14 reconciliations matching source
published totals, and a publication contract that refuses to serve an overstated claim. The dashboard is
maybe 15% of the work.

---

## 2 · Data sources

**Q4. Which sources, and are they official?**
All official Government of India. **26 registered** under a licence gate — nothing can be acquired unless
registered. **15 acquired** as immutable sha256-checksummed snapshots: 35 files, 50.5 MB. **Six feed
production**: NCS (Parliament answers), Udyam MSME, Census 2011 B-24, LGD, PLFS bulletin, MSDE Annual Report
2023-24. Plus ILOSTAT, DGE's NAT table, DGT CTS curricula and NCVET NQR for taxonomy and mapping.

**Q5. Why not scrape Naukri or Indeed?**
Three reasons, in order. **Terms of service** — scraping them would disqualify a government-facing tool.
**Postings are not vacancies** — re-posted, duplicated across platforms, and structurally biased toward
white-collar urban roles while most blue-collar hiring never appears online. **It would not fix our actual
blocker**, which is supply-side, not demand-side. We'd still have no state × trade supply.

**Q6. Why is your data old? November 2024?**
2024-11-15 is the as-on date of the **most recent NCS figures published in Parliament answers** — it is the
frontier of what is officially available, not a stale choice. The dashboard shows that date on every relevant
figure and never says "current" or "live". If NCS published monthly machine-readable district data, our
ingestion layer would take it unchanged.

**Q7. Did you bypass any access control to get this data?**
No, and that constraint shaped the project. No CAPTCHA bypass, no authentication bypass, no robots violation,
no fabricated API keys, no unofficial mirrors. Two concrete cases: `censusindia.gov.in` serves an **incomplete
TLS chain**, and we completed it legitimately from the certificate's own AIA URL with verification **left
enabled**; `microdata.gov.in` presents a **self-signed** certificate and we **refused it**. The PMKVY district
dataset needs a registered data.gov.in API key we don't hold, so it is recorded as `ACCESS_PENDING` rather
than worked around.

---

## 3 · Data quality

**Q8. How do you know your extractions are correct?**
**14 of 14 reconciliation checks match each source's own published totals exactly**, plus Pandera contracts
and 479 tests. Concretely, three bugs we caught this way: Census B-24 double-counted by **1,612,514** workers
because a division total and its sub-division detail share one table (fixed with a `row_type` classifier);
MSDE trade serials restart per section, so keying on serial alone silently dropped **70 of 155** trades; and
three NCS Parliament answers report the *same* as-on date and figures — three documents describing **one**
observation, so we deduplicated rather than summed.

**Q9. What happens to missing values?**
Missing stays missing, with a **reason**. `NO_DATA` ≠ `NOT_ACQUIRED` ≠ `ACCESS_PENDING` ≠ `MAPPING_UNKNOWN` ≠
`NOT_IDENTIFIABLE`. **No row in the system carries a signal of zero** — verified by test. A district without a
Census prior has no occupation rows at all, so a zero cannot be rendered even by accident. Five training cells
the source printed as `-` are stored NULL with `value_status = NO_DATA`, never zero — a state that didn't
report placement is not a state with no placement.

**Q10. How do you handle conflicting figures between sources?**
One designated authoritative source per measure, recorded in the registry; conflicts are logged, never
averaged. We hit this with ITI seat capacity — parliamentary answers differ markedly between years — which is
one reason that measure never entered a production output.

---

## 4 · Standardisation

**Q11. How do you map "Welder" on a portal to an ITI trade?**
We don't, and that is deliberate. **Fuzzy matching, embeddings, LLM inference and name resemblance are
prohibited project-wide.** Every mapping carries `authority`, `method` and `confidence`, and OFFICIAL is
structurally separated from PROJECT. Our one official trade → NCO link came from DGT's **own** CTS curriculum
PDFs, which carry a `Trade Code` and an `NCO - 2015` field — that yielded **2 trades**: Electrician (DGT/1001)
and Fitter (DGT/1002). The other **153 remain `MAPPING_UNKNOWN`**. We could have matched all 155 by name in an
afternoon; the result would have been invented.

**Q12. Census is NCO-2004 and your spine is NCO-2015. How is that valid?**
Through the **official** DGE concordance — 3,447 rows, `authority = OFFICIAL`. And we **measure** rather than
assume division purity: division 2 is 0.998, division 3 is 0.789, division 8 is 0.805. Division X maps to
NULL, never to a guess. Where purity is low, that weakness flows into the weakest-link confidence.

**Q13. How do you handle district boundary changes?**
LGD is the geography spine — 821 rows, 36 states and 785 districts. `location_master` was deliberately left
**empty** until a validated LGD download existed. Census codes of `'000'` became NULL rather than a fabricated
code, and **125 post-2011 districts correctly have no Census code at all** — which is why their occupation
detail is permanently unavailable rather than merely unacquired.

**Q14. Your NCS sectors — are those occupations?**
No, and proving that was an important early result. NCS publishes against 22 "sectors" which we established
are **NIC-2008 industry sections**. An industry is not an occupation, so **no NCS-sector → NCO crosswalk can
exist as a function.** Any pipeline that equates them has fabricated its occupation axis. That finding is why
we went looking for a real industry → occupation bridge.

---

## 5 · Demand estimation

**Q15. How did you get an occupation axis if NCS has none?**
We found the bridge in **ILOSTAT's `EMP_TEMP_ECO_OCU_NB_A` series for India** — whose own source is PLFS —
giving an official `P(NCO division | NIC section)`. That is output A: observed industry totals × an official
conditional structure. It is labelled ESTIMATED, joined at NIC section only, with **no geographic allocation**.

**Q16. Why call it "demand" if it's estimated?**
We don't call it demand. The published labels are **"District Relative Demand Allocation Signal"** and
**"District × Occupation Relative Demand Allocation Signal"**. The unit is `relative_signal_unitless`. The
stored interpretation is `RELATIVE_RANKING_SIGNAL_NOT_A_VACANCY_COUNT`. A terminology lint fails the build if
anyone writes "district demand ranking", "highest-demand districts" or "vacancy count by district" — in code,
in labels, or in translation files.

**Q17. Isn't your district ranking just enterprise density?**
**Within a state, yes — and we print that above the table.** We measured it: in **0 of 36 states** does the
within-state ordering differ from ranking districts by Udyam enterprise share. The NCS demand component only
varies *between* states. The caveat is stored as a column on every row, and the publication contract refuses
to build a response if it is missing. We also measured the variance decomposition of the district × occupation
signal: **district effect 61.2%, occupation effect 30.7%, genuinely district-specific occupational information
8.1%.** We publish that too.

**Q18. Then what in your product actually adds information?**
Districts compared **within one state and one NCO division**. That ordering differs from enterprise share
alone, and from occupation share alone, in **27 of 27** groups we tested — it is the one place the two
structures combine. It is the main panel of the occupation view for exactly that reason. Still estimated,
still LOW confidence, never an observed ranking.

**Q19. What happens to the 58.13%?**
Nothing — deliberately. **20,507,320 of 35,275,833 published NCS vacancies are PAN-India or multiple-state**
and are not attributable to any state. They stay on a NATIONAL row, are disclosed on every relevant screen,
and **allocating them is a `PROHIBITED` capability** with its own blocked API route. If we distributed them,
every district figure would be inflated by an invented geography. The district signal therefore rests on
**41.87%** of the published total, stated wherever it appears.

**Q20. Why is Census 2011 acceptable in a 2024 analysis?**
It is the most recent Indian census occupational structure that exists — 2021 was not conducted. We use it as
a **structural prior only**, never as a demand measure (`not_a_demand_measure = TRUE` on every row), and the
14-year gap is disclosed on the face of the product: *"Census occupation structure is 2011; the demand
baseline is 2024-11-15."* It is also the single largest reason output C is **LOW** confidence.

---

## 6 · Supply

**Q21. Where is your supply side?**
Published, but only at the grain it exists: **state × scheme × measure** — 350 rows, five distinct measures
(enrolled → trained → assessed → certified → placed), OBSERVED, reconciling exactly — plus PMKK
infrastructure, plus national × Top-N trade outcomes. What does **not** exist in any accessible official
source is district × trade, state × trade, state × occupation or district × occupation supply. Our 17-row
`supply_evidence_matrix` records every source tried and why each failed.

**Q22. Why don't you call training outcomes "supply"?**
Because they aren't. They have **no occupation dimension** — 153 of 155 trades are unmapped to NCO — so they
cannot tell you supply *of what*. "Supply" is a reserved word in our publication contract: it may not appear
in any published label, API field or export column. We say "candidate counts within a named scheme and
period", which is what the source published.

**Q23. Can't you just distribute state training totals to districts by population?**
That is allocation, not evidence — and it would manufacture precisely the variation the output claims to
measure. Our gate G-2 names it as **explicitly insufficient**: "any state total distributed by population,
enterprise share, district count or centre count." It would also be unfalsifiable, since no district cell
exists to check it against.

**Q24. What about the Top-N trade data you do have?**
It is a **subset**, flagged `is_top_n_subset = TRUE` on every row, and may not become a distribution. The
numbers are why: the Top-10 PMKVY 4.0 job roles cover **514,619 of 2,361,798** enrolments — **21.8%**. The
other 78% sit in job roles the source does not name. You cannot rake a distribution from a fifth of the mass.

---

## 7 · ML / AI

**Q25. Where is the AI? The PS says "AI-Enabled".**
I'll be direct: **there is no machine-learning model in production, and no ML library is installed.** No
scikit-learn, LightGBM, XGBoost, PyTorch, TensorFlow or statsforecast; no model code in the repository. We
will not invent a model to match a title.

What the system does is data engineering and statistical reasoning: source acquisition under a licence gate,
PDF and HTML extraction, taxonomy and geography conformance, contract validation, deterministic signal
construction, weakest-link confidence, and a publication contract enforced in code.

**The reason is substantive, not an excuse.** Every ML capability this PS implies is blocked by the same
missing evidence, not by modelling. Forecasting needs **≥2 dated demand observations**; we have one. A
learned gap model needs a target variable; the target is not identifiable. An early-warning classifier needs
labels; no ground-truth shortage label exists. Training a model on data of this shape would produce
confident output with no validity — the exact failure the rest of this submission avoids.

**Q26. So what would the ML be, when the data arrives?**
Specified, not hand-waved. Forecasting: mandatory naive baselines first, then classical per-series models
where history permits, then a pooled global gradient-boosted model across districts — many short series is
exactly the regime where pooling wins — with **rolling-origin backtesting** and MASE, interval coverage and
top-N rank overlap. Deep learning is rejected on evidence: insufficient history, no interpretability, nothing
a planner can defend. All of it waits on gate G-4.

**Q27. Why not use an LLM to infer the missing government data?**
Because an LLM cannot observe a `state × trade` cell that nobody measured. It would produce fluent, plausible
numbers with no provenance — and the error would be invisible, which is worse than the gap. Our contract
prohibits LLM-generated mappings and values outright.

**Q28. Is there any legitimate place for an LLM here?**
Yes, one: a **grounded query interface** over the analytical database — fixed parameterised queries,
read-only, answers grounded in returned rows with their provenance and confidence attached. Free-form
text-to-SQL is rejected: hallucination risk is unacceptable in a government planning tool. It is designed,
not built, and it would add no new analytical claim.

**Q29. How do you prevent hallucination generally?**
Structurally, not by prompting. No model generates a value anywhere in the pipeline. Every number traces to a
named source document. Evidence status is **read from the data**, never declared in config — we have a test
that forges a lying config and proves the API still reports ESTIMATED. And the application **refuses to
start** if any output claims a shortage it cannot measure.

---

## 8 · Forecasting

**Q30. Why no forecasting? That's in the title.**
One dated demand observation. `flow_available = FALSE` on every demand row with the reason stored: *"the
measure is a cumulative stock and all acquired snapshots share one as-on date; differencing requires two
different dated snapshots."* A single point cannot support a trend, and inventing one would be the clearest
possible case of fabrication.

**Q31. You have PMKVY 1.0 and 2.0 — isn't that a time series?**
No, and we tested it. They are **different schemes** with different designs, and their state orderings are
unrelated: cross-scheme rank correlation is **+0.034** for certification rate and **+0.005** for placement
rate. Treating them as a series would attribute scheme redesign to labour-market change. We excluded it
permanently, not provisionally.

**Q32. What exactly unlocks forecasting?**
Gate **G-4**: at least two defensible dated observations of the same demand measure, same basis, same
geography, same source; the measure must be a flow or two differenceable stocks; no scheme or definition
change between them; and rolling-origin backtesting against naive baselines before anything is published.
Practically: **a second dated NCS snapshot.** That is all.

---

## 9 · Architecture

**Q33. Why separate fact tables instead of one merged table?**
Because a survey estimate, an administrative registration count and a decennial census stock are different
*kinds* of fact. Merging them makes an invalid comparison expressible in SQL — and therefore inevitable.
Keeping them apart means any cross-source claim must be written deliberately, in the open, in the derived
layer. `geo_level`, `occupation_level` and `period_grain` are on every fact, so an unsupported join is
visible.

**Q34. Is it reproducible?**
`make reproduce` — verify every raw snapshot against its recorded sha256, rebuild staging, dimensions, facts,
analytical layer, demand products, supply products, run validation, load the warehouse, emit the publication
contract, run the terminology lint, profile, and run 479 tests. Raw storage is immutable: a fetch never
overwrites an existing snapshot. Results survive a source going offline mid-competition.

**Q35. Why DuckDB rather than Postgres or Spark?**
No data volume justifies Spark — 82,358 rows. DuckDB needs no server, reads Parquet directly, and makes
grain-safe joins expressible and reviewable as plain SQL, which matters when the correctness of a join *is*
the methodology. The serving layer is stateless and read-only.

---

## 10 · API and dashboard

**Q36. Why do your blocked endpoints return 200 instead of 404?**
Because a 404 reads as *"none found"* and an empty array reads as *"zero"* — when the truth is *"not
computable"*. All ten blocked routes return **HTTP 200 with `data: null`**, a reason code, and a blocking
gate. That distinction is the whole point of the publication contract.

**Q37. What stops a developer from accidentally overstating a claim later?**
Four independent layers. The contract refuses to **load** if a mode is weakened. The app refuses to **start**
if a label or translation string fails the terminology lint or any output claims a shortage. Every **response**
carries its evidence envelope. Every **export** carries it as a file header. Plus `is_measured_shortage` is
`false` by database constraint and regression test. We also ran hostile-input QA and found and fixed a
reflected XSS in our own frontend.

---

## 11 · Security

**Q38. Did you do any security review?**
Yes — Step 7.5. Findings: **one reflected XSS in our own dashboard**, where `esc()` escaped `& < > "` but not
the single quote, and an inline handler interpolated a URL-hash argument into a JS string. We found it by
executing the real frontend against the live API with a hostile hash, and closed it in three layers: validate
the route argument, escape the delimiter, remove the interpolation. Also verified: no secrets, no debug flag,
no CORS exposure, parameterised SQL only, no stack traces across 12 hostile inputs, path traversal refused,
and the warehouse connection is opened **read-only** so no route can write.

---

## 12 · Scalability

**Q39. Does this scale to all of India?**
On the dimension that matters — evidence, not rows. Adding a source means registering it in the licence gate,
writing one conformer to the existing masters, and adding a contract. Nothing downstream changes shape.
Concretely: **Census B-24 for the remaining 33 states would take output C from 138 districts toward 785 with
no formula change** — the estimator already handles the full grid and reports per-district status. 82,358 rows
query in milliseconds and would take two orders more.

---

## 13 · Innovation

**Q40. What is genuinely novel here?**
Not the FastAPI or the dashboard. Four things. **Identification-aware analytics** — the system distinguishes
*"we lack this data"* from *"this quantity is not identifiable from evidence of this shape"*, and treats the
second as a mathematical result. **A publication contract enforced in code** that makes evidence, confidence,
coverage and prohibited interpretations part of the response contract, with startup refusal on breach. **A
terminology lint over the published surface**, translation files included, with negation detection so the
product can still say "this is *not* a vacancy count". And **caveats stored as data** — outputs B and C carry
their own derivation caveats as columns, so the UI cannot drift from the data.

**Q41. Isn't "we couldn't do it" a weak submission?**
The submission isn't "we couldn't". It is: we built the full platform the engine requires, and we produced a
**reproducible proof** of which quantity is unidentifiable and why, plus the exact dataset that resolves it.
A planner can act on that — they can request one dataset. They cannot act safely on a fabricated gap table,
and they would not know it was fabricated.

---

## 14 · Limitations

**Q42. Can the system tell MSDE which trade to train more?**
**No.** That requires occupation-level supply, which does not exist at any geographic grain. The system can
tell MSDE which district × occupation combinations show a higher relative demand allocation signal within a
state, at LOW confidence over 138 districts — and it can tell them precisely which dataset would let it answer
the trade question properly.

**Q43. How reliable are your estimates, really?**
Output B is MEDIUM, output C is **LOW** — and LOW by construction, not by tuning. Confidence is weakest-link:
the *worst* of source quality, allocation depth, occupation mapping, temporal compatibility, geography
coverage and missingness, never an average, because averaging lets a strong term mask a fatal one. Output C
rests on a 2011 structural prior, so nothing can lift it above LOW except better data.

**Q44. What's the weakest part of your own work?**
Output C. It covers 138 of 785 districts, rests on a 14-year-old occupational structure, and within a district
its ordering is simply the Census ordering. We print all three facts above the table. The second weakest is
that we have no map — designed, not built.

**Q45. Your hybrid pressure indicator — doesn't that measure shortage?**
No, and it is **not implemented**. It is designed and declared `EXPERIMENTAL_ONLY`, absent from the API,
dashboard, exports and OpenAPI. We didn't build it because we tested it: identical rules yield **207 flags
under PMKVY 2.0 and 0 under PMKVY 1.0**. An output whose existence depends on an undecidable choice between
two source schemes is not a production indicator. Even promoted, it would carry
`is_measured_shortage = FALSE` and could never name *which* trade is short, because its training axis has no
occupation dimension.

**Q46. Why didn't you use synthetic data to demonstrate the full pipeline?**
We considered it and rejected it for production. A synthetic gap would look exactly like a real one; the error
would be invisible, systematically wrong in one direction, and it informs seat sanctioning — real money. If we
had used any, our own rules would require it to be generated by committed seeded code, flagged at row level,
visibly marked in every UI surface and export, and documented as a limitation. We used none.

---

## 15 · Future roadmap

**Q47. What exactly do you need to produce a real gap?**
In order of decisiveness: **(1) state × trade — ideally district × trade — training outcomes with complete
trade marginals.** That is gate G-1 condition six: one observed interior cell of `SUPPLY[geography × trade]`.
The other five conditions (same time grain, geography, occupation grain, unit, population definition) are
harmonisation problems that better data solves. Condition six is the identification barrier, and **more of
the same marginals never passes it.** Then **(2)** the remaining 153 official trade → NCO mappings, **(3)**
Census B-24 for the other 33 states, **(4)** a second dated NCS snapshot for any forecast, **(5)** NCO-coded
NCS vacancies.

**Q48. How long would that take once the data exists?**
The conformance layer, estimator scaffolding, confidence framework, contract and serving layer already exist.
A new source is a registry entry, one conformer and a contract. The work would be acquisition and validation,
not architecture — which is precisely why we spent this project building the platform rather than a number.

**Q49. What would you say to MSDE if you had one minute?**
*"Publish state-by-trade training outcomes with complete trade marginals, and this platform computes the
demand–supply gap you asked for — with provenance, confidence and coverage attached, and no formula change.
Until then, here is honest demand intelligence, and here is exactly what is missing."*
