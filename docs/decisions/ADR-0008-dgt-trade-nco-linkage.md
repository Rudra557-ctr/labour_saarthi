# ADR-0008 — The official trade → NCO-2015 link is the DGT CTS curriculum, not a QP chain

- **Status:** Accepted
- **Date:** 2026-10-04 (Step 5.2)
- **Relates to:** ADR-0007 (supply evidence grain), Step 5.1

## Context

Step 5.1 proved that NQR Q-Files carry an official `Aligned to NCO/ISCO Code/s` field, and hypothesised the
chain **DGT CTS Trade → Qualification/QP → NCO-2015**. The missing link was trade → qualification, and NQR's
search endpoint returns HTTP 500 so Q-Files cannot be enumerated.

## Decision

**Adopt a shorter, stronger official chain that makes the QP intermediate unnecessary:**

```
DGT CTS curriculum "GENERAL INFORMATION" table
    -> Trade Code        (e.g. DGT/1002)
    -> NCO - 2015        (e.g. 7233.0100, 7233.0200)
    -> occupation_master (titles verified)
```

DGT publishes the NCO-2015 codes **on the trade curriculum itself**. No qualification or QP identifier is
required, so the Step 5.1 chain is superseded rather than completed.

## Evidence

Verified by extraction from two acquired curricula, then validated against the NCO spine:

| Trade | Trade Code | NCO-2015 codes (as published) | Resolve in master? |
|---|---|---|---|
| Fitter | `DGT/1002` | `7233.0100` Fitter, General · `7233.0200` Fitter, Bench | **Yes, titles match** |
| Electrician | `DGT/1001` | `7411.0100` Electrician General · `7412.0200` Electrical Fitter | **Yes** (one title differs only by a comma) |

Both are **multi-NCO**, and both codes are retained per trade. The curricula additionally cite
`Reference NOS` codes (e.g. `PSS/N2001`), stored as corroborating evidence.

## Consequences

- `map_trade_to_nco` holds **4 rows / 2 trades**, `authority='OFFICIAL'`, level `NCO_OCCUPATION`.
- **Granularity is the full 8-digit NCO occupation** — the finest the taxonomy offers. Not downgraded.
- **153 of 155 trades are `MAPPING_UNKNOWN`, not unmapped-because-nonexistent.** DGT demonstrably publishes
  the codes; no official index of curricula exists, so they cannot be enumerated. The distinction is
  recorded per row.
- `dim_training_trade` is **not modified** — its 155 rows and their UNMAPPED records stay exactly as Step 5.0
  wrote them, and a test enforces that. The authoritative status lives in `dim_trade_mapping_status`.
- **This changes ADR-0007 on taxonomy only.** It does **not** change the supply grain: training outcomes
  still carry no trade dimension, so `state × NCO supply` remains unsupported.
