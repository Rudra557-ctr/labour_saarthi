# Source Verification Report — Step 1

Date: 2026-10-02 · All findings below were obtained by direct acquisition or by
probing the live source. Nothing here is inferred from secondary commentary.

Probe raw output: [`probe_results.json`](probe_results.json)

---

## 1. Official NCO ↔ qualification / QP mapping — **RESOLVED**

**Question:** does a published official crosswalk from NSQF qualifications (QPs) to NCO codes exist?

**Answer: there is no per-qualification crosswalk table, because one is not needed — the NCO code is a field on the qualification itself.**

Acquired and extracted: NCVET, *Report on Mapping of Qualifications with NCO Codes*, **22 August 2023**, 58 pages
(`data/raw/NCVET_NCO_MAPPING_REPORT/2026-10-02/`, sha256 in manifest).

Verbatim from Annexure IX (User Handbook):

> "As a standard practice of NSQF alignment, all Qualifications are required to be mapped to an NCO code. The NCO is also reflected in the Qualification File Template…"

**Implication for the architecture:** `map_qualification_to_occupation` is populated with
`authority='OFFICIAL'` by **extracting the NCO code from each qualification's Q-File / NQR record**,
not by building a project mapping. Step 0 risk **R-02 is closed**.

### What the report does contain

| Annexure | Content |
|---|---|
| I | Skill levels and NCO-2015 education requirements |
| II | Committee composition (OM File No. 32001/12/2023/NCVET, 14 Feb 2023) |
| III–VI | Minutes of 4 committee meetings (Feb–Jul 2023) |
| VII | **Mapping-quality audit by awarding body** — extracted to [`../mappings/official/ncvet_nco_mapping_quality_by_awarding_body.csv`](../mappings/official/ncvet_nco_mapping_quality_by_awarding_body.csv) |
| VIII | Sub-group meeting schedule |
| IX | **User Handbook on mapping qualifications to NCO codes** — the official method |

### Annexure VII gives us an official mapping-confidence prior

45 awarding bodies audited, with counts of: total qualifications; job roles **not assigned** NCO codes;
qualifications with no NCO code where one **has been proposed**; qualifications whose NCO codes are
**wrongly mapped**. This is a documented, citable basis for setting `confidence` by awarding body
rather than inventing one.

> **Data-quality finding (source defect):** the report's own TOTAL row reads
> **2157 / 256 / 236 / 156**, but the 45 body rows we extracted sum to
> **2354 / 349 / 325 / 210**. Extraction was verified row-by-row (serials 1–45 present, no duplicates
> beyond one genuinely repeated abbreviation "HSSC"), so **the published total does not equal the sum of
> its own rows.** Both figures are recorded; neither is silently preferred. To be raised with NCVET.

---

## 2. NCO-2015 code structure — **RESOLVED**

Verbatim from Annexure IX s.3 — this is now a verified fact, not an assumption:

> "NCO – 2015 is an 8-digit coding structure which was mapped and aligned to ISCO – 08 with an addition of 2 digits."

| Position | Meaning |
|---|---|
| digit 1 | Division (ISCO-08 Major Group) |
| digits 1–2 | Sub-Division (Sub-Major Group) |
| digits 1–3 | Group (Minor Group) |
| digits 1–4 | Family (Unit Group) |
| decimal | separates Families from individual Occupations |
| digits 5–6 | the occupation within the Family |
| digits 7–8 | **QP/NOS availability: `00` = none exists; `01`–`99` = one exists** |

Example given: `8153.0111` = Sewing Machine Operator.

**Two consequences:**

1. The handbook explicitly permits assigning **a four-digit family-level code** when no exact occupation
   matches ("a code till first four digits that is upto family level can be assigned"). This **officially
   sanctions Step 0 decision D-01**, which chose the 4-digit family as the canonical analytic unit.
2. The NCO code itself encodes whether a QP/NOS exists for a job role. This gives the Step 0
   `NO_QUALIFICATION_EXISTS` early-warning flag a structural basis. In our build, 824 of 3,437
   occupations carry a QP/NOS indicator and 2,613 do not.

Also confirmed: when nothing maps, **no code is assigned** and the Standing Committee/MoLE/NCVET must be
notified. Official practice therefore includes an explicit unmapped state — consistent with our rule that
unmapped records are retained and counted.

---

## 3. A structured official NCO source — **NEW, better than planned**

Annexure IX Note 1 names a MoLE search engine. Following it led to **<https://dge.gov.in/nat>**: a
paginated HTML table with columns `S.No. | Occupational Title | NCO 2015 | NCO 2004 | Division |
Sub Division | Group | Family`, pages 0–6, **3,447 rows**.

This replaces PDF extraction as the source for `occupation_master`, and it additionally carries an
**official NCO-2004 ↔ NCO-2015 concordance** (present for 77.9% of rows).

**Data-quality findings:** 11 NCO-2015 codes appear twice (22 rows) — `2132.0700` and `2132.0800` straddle
a pagination boundary, the rest are repeats within page 2, and `8155.0201` has its title duplicated inside
one cell. **Division 0 (Armed Forces) is absent**; only divisions 1–9 appear, consistent with civilian
coverage.

---

## 4. NCS district-level occupation coding — **UNRESOLVED, D-04 still open**

`https://www.ncs.gov.in/_layouts/15/ncsp/ViewStaticReport.aspx` → HTTP 200 but **0 table rows and
0 NCO-format codes** in the served HTML: the report is client-rendered. **No NCO-coded district vacancy
table was obtained.** Decision D-04 (demand-signal acquisition) therefore remains open, and the
granular demand signal is **not** currently available from a verified official source.

## 5. e-Shram occupation × district — **PARTIALLY RESOLVED**

Occupation coding **is** documented as NCO-2015-based (30 broad sector categories, 190 broad occupation
families, ~400 occupations), which makes `map_eshram_occupation_to_nco` structural rather than invented.
But `https://eshram.gov.in/` serves **0 table rows** — the dashboard is client-rendered, and **no joint
occupation × district extract was obtained.**

## 6. DGT / ITI trade × district — **UNRESOLVED**

`dgt.gov.in` returns only 7 table rows (navigation). `www.ncvtmis.gov.in` **connection-timed out**.
No trade × district open dataset located. Long-term training capacity may only be obtainable at a
coarser grain, which must then be labelled.

## 7. data.gov.in programmatic access — **BLOCKED ON AN API KEY**

`api.data.gov.in` was unreachable from this environment and the alternative datastore path returned 404.
Resource pages for the LGD mirrors and the PMKVY district dataset all return an identical ~1.01 MB
**SPA shell with no download links** — data.gov.in is itself a JavaScript application.

**Nothing on data.gov.in can be ingested programmatically without a registered API key.** This is a
decision for the project owner, and it gates several sources at once.

## 8. LGD download behaviour — **BLOCKED (browser session required)**

The bulk download form at `lgdirectory.gov.in/downloadDirectory.do` was submitted with a valid
`OWASP_CSRFTOKEN` harvested from the live page, both as a form field and as a query parameter. Both
attempts returned **"Session Time Out"**. The citizen district report is a **DWR/AJAX** endpoint and
serves 0 table rows. LGD cannot be acquired without browser automation.

Confirmed from the form itself: download options include `allStateofIndia`, `allDistrictofIndia`,
`allSubDistrictofIndia` and per-state variants — so the data we need does exist behind that form.

## 9. PLFS valid geographic granularity — **CONFIRMED**

Acquired the April 2025 monthly bulletin and the sample-design press note. Confirms monthly estimates at
**all-India level only**; **district-level estimates are not valid**. Step 0's treatment of PLFS as
state/national context only requires no change.

## 10. Newer MSDE/PMKVY vintage — **NOT FOUND**

No vintage newer than the 2022-04-21 district-wise dataset was located, and the resource page is not
machine-readable (item 7). The supply-side history therefore remains stale, which is why Step 0 models
training supply as a **policy projection** rather than a time-series forecast.

---

## Summary

| # | Question | Verdict |
|---|---|---|
| 1 | Official NCO ↔ QP mapping | **RESOLVED** — NCO is a field on the qualification; R-02 closed |
| 2 | NCO-2015 code structure | **RESOLVED** — 8-digit `DDDD.OOQQ`, family-level officially permitted |
| 3 | Structured NCO source | **RESOLVED, better than planned** — official HTML table, 3,447 rows |
| 4 | NCS district × occupation | **UNRESOLVED** — client-rendered; D-04 still open |
| 5 | e-Shram occupation × district | **PARTIAL** — coding confirmed NCO-based; joint extract not obtained |
| 6 | DGT/ITI trade × district | **UNRESOLVED** — not located; MIS portal timed out |
| 7 | data.gov.in API per resource | **BLOCKED** — API key required |
| 8 | LGD download/update | **BLOCKED** — browser session required |
| 9 | PLFS valid granularity | **CONFIRMED** — national monthly, state quarterly; not district |
| 10 | Newer PMKVY vintage | **NOT FOUND** |
