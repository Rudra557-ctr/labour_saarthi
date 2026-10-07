# Hard Judge Questions

**15 questions a technically strong judge could ask, aimed at genuine weaknesses.** Each has the strongest
*honest* answer, the evidence behind it, and what must not be said.

**The posture that works:** concede the point first where it is true, then show the measurement. A judge
who sees you volunteer a weakness stops hunting for one.

---

### 1. "Your district demand is just Udyam enterprise share. Why is that useful?"

**Answer.** "Within a state, you're exactly right — we measured it: in **zero of thirty-six states** does the
within-state ordering differ from ranking districts by enterprise share. We print that above the table
rather than hide it. It's useful in two narrower ways. **Across** states the NCS demand component does vary,
so the national comparison carries real signal. And at district × occupation level, comparing districts
*within one state and one division* combines two structures — it differs from enterprise share alone **and**
from occupation share alone in 27 of 27 groups we tested. That's the one comparison that restates neither
input, and it's the main panel of the occupation view for that reason."

**Evidence.** `within_state_ranking_caveat`; variance decomposition district 61.2% / occupation 30.7% /
interaction 8.1%.

**Don't say.** "It's still useful demand data." Don't defend the within-state ranking as demand.

---

### 2. "Why should we trust Census 2011 in a 2024 analysis?"

**Answer.** "You shouldn't trust it as current — and we don't present it as current. It's the most recent
Indian census occupational structure that exists; 2021 wasn't conducted. We use it as a **structural prior
only**, never as a demand measure — every row carries `not_a_demand_measure = TRUE` — and the district page
literally prints *'Census occupation structure is 2011; the demand baseline is 2024-11-15.'* It's also the
single largest reason output C is LOW confidence, and weakest-link means nothing can lift it above LOW
except better data."

**Evidence.** `analytical_district_occupation_structure`; all 1,889 rows LOW.

**Don't say.** "Occupational structure doesn't change much." That's an assumption we haven't tested.

---

### 3. "Where exactly is the AI?"

**Answer.** "There isn't one in production, and I'd rather say that than invent it. No scikit-learn,
LightGBM, XGBoost, PyTorch or TensorFlow is installed; no model code exists. The reason is substantive:
every ML capability this problem statement implies is blocked by the same missing evidence. Forecasting
needs two dated observations and we have one. A learned gap model needs a target variable and the target
isn't identifiable. An early-warning classifier needs labels and no ground-truth shortage label exists.
Training on data of this shape would give confident output with no validity."

**Evidence.** `pyproject.toml`; no model code in `src/` or `api/`.

**Don't say.** "Our data pipeline is AI." Don't call deterministic arithmetic machine learning.

---

### 4. "Why didn't you use ML anyway? Even a baseline would show capability."

**Answer.** "A baseline forecast on a single observation isn't a baseline, it's a constant. The honest
version is specified and waiting on data: mandatory naive baselines first, then classical per-series models,
then a pooled global gradient-boosted model across districts — many short series is exactly where pooling
wins — with rolling-origin backtesting and MASE, interval coverage and top-N rank overlap. Deep learning is
rejected on evidence: insufficient history and nothing a planner can defend. All of it waits on gate G-4."

**Don't say.** "We ran out of time." The blocker is evidence, not effort.

---

### 5. "Why didn't you use job portals? Everyone else does."

**Answer.** "Three reasons, and the third is the one that matters. Terms of service — it disqualifies a
government-facing tool. Postings aren't vacancies: re-posted, duplicated across platforms, structurally
biased toward white-collar urban roles while most blue-collar hiring never appears online. And it wouldn't
fix our actual blocker, which is **supply-side**. We'd have richer demand and still no state-by-trade
supply, so still no gap."

**Don't say.** Disparage teams who did.

---

### 6. "Why is 58% of your vacancy data unusable?"

**Answer.** "It isn't unusable — it's unattributable, and that's a different thing. NCS books 20,507,320 of
35,275,833 vacancies to 'Multiple States/PAN India'. They're real, published and counted in our national
view. What we can't do is assign them to a state or district, because the source doesn't. If we distributed
them by population or enterprise share, every district number would be inflated by an invented geography —
so allocating them is a `PROHIBITED` capability with its own blocked route. The district signal rests on the
remaining 41.87%, and we state that wherever a district figure appears."

**Don't say.** "It's a data quality problem." It's a publication-grain property of the source.

---

### 7. "Why don't you have district-wise supply? Surely MSDE publishes it."

**Answer.** "We looked, and recorded every attempt in a 17-row evidence matrix. The data.gov.in PMKVY
district resource is `ACCESS_PENDING` — it needs a registered API key we don't hold. NCVT MIS, the NQR bulk
search and the apprenticeship portal are all `UNAVAILABLE`. What is published is state × scheme, and
national × **Top-N** trade. We won't convert a Top-N subset into a distribution, and we won't allocate state
totals to districts — that's manufacturing the variation the output claims to measure."

**Evidence.** `supply_evidence_matrix`; `district_level_training_data = 0, NOT_ACQUIRED`.

**Don't say.** "It doesn't exist." We haven't proved that; we've proved we couldn't acquire it.

---

### 8. "Why call this demand intelligence if it's partly estimated?"

**Answer.** "Because it's labelled estimated wherever it is. Two of our products are OBSERVED — NCS state
and industry demand. Three are ESTIMATED, and they're named *allocation signals*, not demand rankings, with
unit `relative_signal_unitless`. The distinction isn't a label we typed: evidence status is **read from each
table's own column**, never declared in config. We have a test that forges a config claiming a derived
output is observed and proves the API still reports estimated."

**Don't say.** "It's basically demand." The whole product exists to not say that.

---

### 9. "What prevents an incorrect ranking from reaching a planner?"

**Answer.** "Three things, and none is discipline. The ranking carries its own caveat as a **column on every
row**, and the publication contract refuses to build a response if it's missing — so the UI can't drift from
the data. Confidence is weakest-link, so output C is LOW and can't be tuned up. And the terminology lint
fails the build if anyone writes 'demand ranking' or 'highest-demand districts', including inside
translation files. What it doesn't prevent is a planner reading the ranking as more than it is — which is
why the caveat is above the table rather than in a footnote."

**Don't say.** "Our estimates are accurate."

---

### 10. "How would you validate these estimates? Against what?"

**Answer.** "Honestly — we can't, and we don't claim to. There's no ground-truth district × occupation
vacancy count anywhere, so predictive validation is impossible. What we can demonstrate is **correctness of
construction**: 14 of 14 reconciliations match each source's own published totals exactly, 479 tests pin the
behaviour, and `make reproduce` rebuilds everything from checksummed bytes. The appropriate framework here
is methodological validation plus sensitivity analysis, not accuracy — and claiming accuracy without a label
would be the exact failure we built this to avoid."

**Don't say.** "We validated against PLFS." PLFS is national and not a demand measure.

---

### 11. "What happens when a district changes boundaries?"

**Answer.** "LGD is the spine and it's effective-dated. The concrete case is already in the product: **125
post-2011 districts have no Census 2011 code at all**, so their occupation detail is permanently
unavailable — reported as `NO_CENSUS_2011_CODE`, which we deliberately distinguish from the 522 districts
where we simply haven't acquired the table. Different problems, different reasons on screen. Census codes of
'000' became NULL rather than a fabricated code."

**Weakness to concede if pressed.** "Our `location_change_event` table is empty, so a time series spanning a
split isn't yet safe — but we have no time series, so nothing currently depends on it."

---

### 12. "How would the system behave if we gave you new data tomorrow?"

**Answer.** "It depends which data, and the system already says so. Census B-24 for the other 33 states is
pure acquisition — register the source, run the existing parser, and output C goes from 138 toward 785
districts **with no formula change**; the estimator already handles the full grid and reports per-district
status. State-by-trade outcomes would be a new conformer plus a Pandera contract, and then gate G-1 is
evaluated on evidence rather than opinion. Promotion is gated: each gate requires recorded evidence and an
ADR, and no gate may be weakened to admit an output."

---

### 13. "What is genuinely novel here? Everyone has a FastAPI dashboard."

**Answer.** "You're right that the dashboard isn't. Four things I'd defend. **Identification-aware
analytics** — the system distinguishes 'we lack this data' from 'this quantity isn't identifiable from
evidence of this shape', and treats the second as a mathematical result. **A publication contract enforced
in code** — the app refuses to start on a breach. **Evidence status read from the data, never declared.**
And **caveats stored as data**, so the interface can't overstate the number it's displaying. The one I'd
defend hardest is that we measured our own signal's weakness and printed it above the table."

**Don't say.** "Our architecture is novel." It's careful, not novel.

---

### 14. "How does this actually become the forecasting engine that was asked for?"

**Answer.** "Two gates, in order. **G-1** for the gap: one observed interior cell of supply by geography and
trade, with complete trade marginals. **G-4** for forecasting: a second dated NCS observation of the same
measure and basis, then rolling-origin backtesting against naive baselines before anything is published.
The conformance layer, estimator scaffolding, confidence framework, contract and serving layer already
exist — so the work would be acquisition and validation, not architecture. That's precisely why we spent
this project building the platform rather than a number."

**Don't say.** Any timeline. We have promised no dates.

---

### 15. "If the government handed you the missing dataset tomorrow, how long?"

**Answer.** "I won't give you a date, because the honest answer depends on the dataset's shape, not our
speed. What I can tell you is what wouldn't change: no analytical formula, no schema redesign, no new
architecture. A new source is a registry entry, one conformer to the existing masters, and a Pandera
contract. Then gate G-1's six conditions get evaluated against the data — same time grain, geography,
occupation grain, unit and population definition, plus one observed interior cell. If they pass, the gap is
computable at the grain the evidence supports, and it's published with provenance, confidence and coverage
like everything else. If they only partly pass, we publish at the grain that does pass and say so."

**Don't say.** "Two weeks." Any estimate invents certainty we don't have.

---

## The three hardest moments, and the posture for each

| Moment | Posture |
|---|---|
**"Where's the AI?"** | Direct, unapologetic, immediate. *"There isn't one in production, and here's why that's a finding rather than a gap."* Hesitation reads as evasion. |
**"Your ranking is enterprise density."** | **Agree first.** *"Within a state, exactly right — we measured it and print it above the table."* Then show where it does add information. |
**"So you didn't solve the problem."** | Concede the scope, redirect to the deliverable. *"Not fully — gap forecasting is NOT_SUPPORTED_YET and our requirement mapping says so. What we deliver is the platform, the proof of why, and the one dataset that resolves it. I'd rather hand MSDE a costed data request than a number that restates an assumption."* |
