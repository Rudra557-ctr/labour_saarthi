# Step 5.2 — Official Occupation-Linkage Resolution

Date: 2026-10-04 · **Evidence resolution only.** No supply calculated or estimated, no district supply, no
occupation supply, no gap, no forecast, no shortage/surplus score, no early warning, no recommendations, no
API/frontend/LLM. No synthetic data. **No fuzzy matching, no embeddings, no LLM semantic similarity, no
guessed NCO codes.** Nothing bypassed: no CAPTCHA, no authentication, no CSRF circumvention, no URL
brute-forcing, no private endpoints.

---

## Verdict

> ### `TRADE_NCO_MAPPING_STATUS = PARTIALLY_RESOLVED`
> **The mapping mechanism is RESOLVED and official. The coverage is not.**

The chain hypothesised in Step 5.1 — Trade → QP → NCO — turned out to be **unnecessary**. DGT publishes the
NCO-2015 codes **directly on each CTS trade curriculum**.

---

## 1. Audit of existing evidence

`dim_training_trade`: 155 rows, keyed `trade_id` = `(section, serial)` — unique; `trade_name` is **not**
unique ("Desktop Publishing Operator" appears twice). The trades carry **no qualification, QP or trade code**
— only name, NSQF level, entry qualification, duration, revision year. So nothing in the Step 5.0 register
could connect to a qualification. `map_qualification_to_nco` held 1 OFFICIAL row from Step 5.1. Existing
mapping infrastructure was reused, not duplicated.

## 2. The official link found

**DGT CTS curricula contain a `GENERAL INFORMATION` table with exactly the identifiers needed:**

```
Name of the Trade   ELECTRICIAN
Trade Code          DGT/1001
NCO - 2015          7411.0100, 7412.0200
Reference NOS       PSS/N2001, PSS/N0108, PSS/N6001, ...
```

and a narrative block repeating the codes **with their NCO titles**:

```
Reference NCO-2015:
  (i)  7411.0100 – Electrician General
  (ii) 7412.0200 – Electrical Fitter
```

This is an **identifier relationship published by DGT itself**, not a name resemblance.

### Validation against the NCO spine

| Trade | Trade Code | NCO code | Title as DGT printed it | Title in `occupation_master` | Match |
|---|---|---|---|---|---|
| Fitter | DGT/1002 | 7233.0100 | Fitter, General | Fitter, General | ✅ |
| Fitter | DGT/1002 | 7233.0200 | Fitter, Bench | Fitter, Bench | ✅ |
| Electrician | DGT/1001 | 7411.0100 | Electrician General | Electrician, **General** | ❌ comma only |
| Electrician | DGT/1001 | 7412.0200 | Electrical Fitter | Electrical Fitter | ✅ |

All four codes **resolve** in `occupation_master` at OCCUPATION level. 3 of 4 titles match exactly; the
fourth differs **only by a comma**. That mismatch is **reported as False rather than smoothed away** — the
comparison was not loosened to look clean, and a test pins `title_matches_master.sum() == 3`. The **code**
is the mapping; the title is corroboration.

## 3. Multi-NCO ambiguity preserved

Both trades map to **two** NCO occupations. Both codes are kept as separate rows, status
`OFFICIAL_MULTI_NCO`, with `nco_codes_for_trade` recording the full published set. **Neither is arbitrarily
chosen.**

## 4. How a curriculum is linked to a register row

The curriculum declares its own `Name of the Trade`; that is matched to `dim_training_trade.trade_name` by
**exact equality after case-folding and whitespace normalisation, within the same scheme (CTS)**. Both
documents are official publications of the same CTS trade list, so this is exact matching on a canonical
name — recorded as `link_method='EXACT_TRADE_NAME_WITHIN_CTS_SCHEME'`. The Trade Code recovered from the
curriculum is stored as corroboration **and supplies the identifier the MSDE annexure never published**.

If a name does not match exactly and uniquely, **no `trade_id` is asserted**.

## 5. Why this is not name matching — proven three ways

1. **Every mapped row cites a DGT curriculum field and file** as its evidence; mappings can only come from a
   file present in the raw snapshot (asserted by test).
2. **9 trades contain "fitter" or "electric"** (Marine Fitter, Electrician Power Distribution, Aeronautical
   Structure and Equipment Fitter, Solar Technician (Electrical), …). If resemblance drove the mapping, far
   more than 2 would be mapped.
3. **7 unmapped trade names are EXACT case-insensitive matches for NCO occupation titles** — `Welder`,
   `Machinist`, `Electroplater`, `Radiology Technician`, `Tourist Guide`, `Desktop Publishing Operator` (×2)
   — **and every one remains `MAPPING_UNKNOWN` with no NCO code.** The name coincidence bought nothing.
   This is the regression test the brief asked for, and it passes on real data.

## 6. Enumeration — the remaining obstacle

| Route | Result |
|---|---|
| `dgt.gov.in/CTS` | HTTP 200 but **lists no curriculum PDFs** |
| `bharatskills.gov.in/Home/CTS` (DGT's official content portal) | 181 KB, **client-rendered**; no curriculum links in HTML; its `/robots.txt` returns an HTML page, not a policy |
| NQR `filter-search` (from Step 5.1) | **HTTP 500** on every parameter combination, including with the page's own CSRF token |
| NQR `sitemap.xml` | **404** — no sanctioned enumeration |
| URL construction per trade | **Not attempted** — that is brute-forcing |

So the 153 remaining trades are **`MAPPING_UNKNOWN`**, explicitly **not** `MAPPING_DOES_NOT_EXIST`: DGT
demonstrably publishes these codes, we simply cannot list the documents. Every such row states that reason.

## 7. Mapping status — reconciles exactly to 155

| Mapping status | Number of trades |
|---|---:|
| OFFICIAL_EXACT | 0 |
| **OFFICIAL_MULTI_NCO** | **2** |
| OFFICIAL_VIA_QUALIFICATION | 0 |
| PARTIAL_CHAIN | 0 |
| **MAPPING_UNKNOWN** | **153** |
| UNMAPPED_NO_QUALIFICATION_LINK | 0 |
| UNMAPPED_NO_NCO_LINK | 0 |
| **TOTAL** | **155** |

Granularity achieved: **`NCO_OCCUPATION`** (full 8-digit) for the 2 mapped trades. `UNMAPPED` for 153.

## 8. The three questions, answered explicitly

**Q1 — Do we now have a defensible official mapping from the 155 DGT CTS trades to NCO-2015?**
**Partially.** The *mechanism* is official, verified and reproducible — DGT prints the NCO-2015 codes on each
CTS curriculum. But only **2 of 155** curricula could be acquired, because no official index of curricula
exists. So: mapping method resolved, coverage 1.3%.

**Q2 — At what granularity?**
**Full `NCO_OCCUPATION` level (8-digit, e.g. 7233.0100)** — the finest the taxonomy offers, with multi-NCO
ambiguity preserved. Nothing was downgraded to division or sector, and nothing was upgraded from a broader
code.

**Q3 — Even so, do we now have occupation-level SUPPLY observations?**
**No. `MAPPING ≠ SUPPLY DATA.`** This is the critical distinction:

| | Status |
|---|---|
| **A. Occupation taxonomy linkage** | **PARTIALLY RESOLVED** — official method proven, 2/155 covered |
| **B. Occupation-level supply observations** | **NOT AVAILABLE — unchanged** |

`fact_training_outcome` is `state × scheme × measure`. It has **no trade dimension at all**, so there is
nothing to join the mapping onto. Even a complete 155/155 mapping would not produce occupation-level supply.
A test asserts the outcome table still carries no occupation column.

## 9. Implication for Step 6

**Outcome B of the three the brief lists — and only partially:** the occupation taxonomy route is now
official and demonstrated, but **occupation-level supply remains unavailable**, because the supply
*measurements* have no trade dimension.

Therefore, unchanged from Step 5.1: **demand and supply still share no occupation grain**, and a
demand–supply gap must not be computed. The binding constraint was never the taxonomy — it is that MSDE
publishes training outcomes by state and scheme, not by trade.

**Two things would change that, in order of leverage:**

1. **Trade-level training outcome data** (state × trade × measure). Without this, the mapping has nothing to
   attach to. This is the real blocker.
2. An **official index of DGT CTS curricula**, or an NQR bulk export, to take the mapping from 2/155 toward
   155/155.

A PROJECT mapping using the NCVET handbook methodology was **not** started: §12 of the brief reserves that
for a separate step, and the official route is now proven viable, which is a better argument for pursuing
enumeration than for curating by hand.

## 10. Files and tables

**New:** `src/lmis/conform/dgt_curriculum.py`, `db/migrations/006_trade_nco.sql`,
`tests/test_occupation_linkage.py`, `docs/decisions/ADR-0008-dgt-trade-nco-linkage.md`, this document.
**Modified:** `config/sources.yaml` (+`DGT_CTS_CURRICULUM`, 26 sources), `src/lmis/cli.py`,
`src/lmis/warehouse/load.py`, README.

| Table | Rows |
|---|---|
| `map_trade_to_nco` | **4** (2 trades × 2 NCO codes) |
| `dim_trade_mapping_status` | **155** (reconciles exactly) |

Raw: 2 curriculum PDFs under `data/raw/DGT_CTS_CURRICULUM/2026-10-04/` with checksummed manifest.
**`dim_training_trade` untouched** — 155 rows, all still `UNMAPPED_NO_OFFICIAL_MAPPING`, auditable.

## 11. Remaining evidence gaps

| Gap | Status |
|---|---|
| DGT CTS curricula for 153 trades | **MAPPING_UNKNOWN** — no official index |
| Trade-level training outcomes | **UNAVAILABLE** — the real blocker for Step 6 |
| NQR bulk qualification export | **UNAVAILABLE** — search endpoint 500s, no sitemap |
| District-level training data | **STILL_UNRESOLVED** (Step 5.1) |
| Sanctioned seat capacity | **UNAVAILABLE** |
| data.gov.in API key | **ACCESS_PENDING** |
