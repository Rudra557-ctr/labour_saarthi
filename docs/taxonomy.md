# Taxonomy

## NCO-2015 is the occupation spine

Verified structure (NCVET, *Report on Mapping of Qualifications with NCO Codes*, 22 Aug 2023, Annexure IX s.3):

```
            8 digits, decimal after the first four:   D D D D . O O Q Q
digit 1 ........................................ Division     (ISCO-08 Major Group)
digits 1-2 ..................................... Sub-Division (Sub-Major Group)
digits 1-3 ..................................... Group        (Minor Group)
digits 1-4 ..................................... Family       (Unit Group)   <-- canonical analytic unit
digits 5-6 ..................................... occupation within the Family
digits 7-8 ..................................... QP/NOS availability: 00 = none, 01-99 = exists
```

Aligned one-to-one with ISCO-08 (ISCO plus two digits). Example: `8153.0111` = Sewing Machine Operator.

**Why the 4-digit Family is the canonical analytic unit (D-01):** the official handbook itself permits
assigning a family-level code when no exact occupation matches — *"a code till first four digits that is
upto family level can be assigned"*. Mapping free-text job titles to 8-digit occupations would assert
distinctions the source text does not support.

## As built

| Table | Rows | Source | Authority |
|---|---|---|---|
| `occupation_master` | 3,982 | `dge.gov.in/nat` (official HTML table) | OFFICIAL |
| └ DIVISION | 9 | derived from digit 1 (Division 0 absent) | OFFICIAL |
| └ SUB_DIVISION | 40 | derived from digits 1–2 | OFFICIAL |
| └ GROUP | 123 | derived from digits 1–3 | OFFICIAL |
| └ FAMILY | 373 | derived from digits 1–4 | OFFICIAL |
| └ OCCUPATION | 3,437 | published 8-digit codes | OFFICIAL |
| `map_nco2004_to_nco2015` | 3,447 | same table's NCO-2004 column | OFFICIAL |
| `sector_master` | 59 | NQR sector listing | OFFICIAL |

Hierarchy **codes** are derived from documented digit positions; hierarchy **titles** come from the
source's own Division/Sub-Division/Group/Family columns. Nothing is invented: a node exists only because
at least one official row implies it.

## OFFICIAL mapping vs PROJECT mapping

Every mapping row carries `authority`, and the two kinds never share a table without it.

| | OFFICIAL | PROJECT |
|---|---|---|
| Source | published GoI crosswalk, or a code field inside an official record | our rules and review |
| `confidence` | 1.0 with citation | 0–1 by method |
| Built so far | `map_nco2004_to_nco2015` (NCO-2004↔2015) | none yet |

### Qualification → occupation is OFFICIAL, and here is why

The NCO code is **a field on the qualification itself** — *"all Qualifications are required to be mapped to
an NCO code. The NCO is also reflected in the Qualification File Template"*. So
`map_qualification_to_occupation` is populated by extracting that field from Q-File / NQR records, with
`authority='OFFICIAL'`. No project mapping is needed for this edge.

**Confidence is not uniform, and we have official evidence of that.** Annexure VII of the same report
audits 45 awarding bodies for unassigned and wrongly-mapped NCO codes
([CSV](../mappings/official/ncvet_nco_mapping_quality_by_awarding_body.csv)). Those rates are the basis for
per-awarding-body confidence — a documented prior rather than an invented one. Example contrast: DGT
reports 463 qualifications with 0 unassigned and 0 wrongly mapped; ESSCI reports 88 with 54 unassigned
and 20 wrongly mapped.

### Still to build (not in Step 1)

- `map_title_to_occupation` — job title → NCO family, PROJECT authority, via the Step 0 cascade
  (normalise → alias → rules → similarity shortlist → human review), with unmapped retained and counted.
- `map_trade_to_occupation` — DGT/ITI trade → NCO.
- `map_eshram_occupation_to_nco` — e-Shram's ~400 occupations → NCO. Likely **structural**: e-Shram's
  occupation capture is documented as NCO-2015-based with 30 sectors / 190 families / ~400 occupations.
- `bridge_occupation_sector` — weighted many-to-many. **Blocked**: no official weighting basis verified.

## Sector is a dimension, not a parent of occupation

An SSC sector spans occupations across NCO divisions, and one occupation may be served by qualifications
from more than one sector. Forcing sector into the occupation hierarchy would double-count or drop rows,
so the relationship belongs in a weighted bridge table.

`sector_master` holds exactly **59** sectors, matching NCVET's documented count — an independent check that
the extraction is complete. A test asserts this count so that drift forces re-verification.
