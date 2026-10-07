-- LMIS trade -> NCO-2015 occupation linkage (Step 5.2)
--
-- Evidence only. No supply estimation, no district supply, no occupation supply,
-- no gap, no forecast.
--
-- dim_training_trade is NOT modified: its 155 rows stay exactly as Step 5.0 wrote
-- them, so they remain auditable and the original UNMAPPED records are preserved.
-- The authoritative per-trade status now lives in dim_trade_mapping_status, and a
-- test asserts the Step 5.0 table was left untouched.

-- One row per (trade, NCO code). MULTI-NCO is represented as multiple rows, never
-- collapsed to a single arbitrarily chosen code.
CREATE TABLE IF NOT EXISTS map_trade_to_nco (
    mapping_id                    VARCHAR NOT NULL PRIMARY KEY,
    dgt_trade_code                VARCHAR NOT NULL,   -- e.g. DGT/1002, from the curriculum
    dgt_trade_name_as_curriculum  VARCHAR,            -- the curriculum's own trade name
    trade_id                      VARCHAR,            -- dim_training_trade key; NULL if not uniquely matched
    trade_name_as_register        VARCHAR,            -- the MSDE annexure's trade name
    nco_2015_code                 VARCHAR NOT NULL,
    nco_2015_title_as_curriculum  VARCHAR,            -- title as DGT printed it
    nco_2015_title_in_master      VARCHAR,            -- title in occupation_master
    nco_mapping_level             VARCHAR NOT NULL,   -- NCO_OCCUPATION (full 8 digits)
    is_multi_nco                  BOOLEAN NOT NULL,
    nco_codes_for_trade           VARCHAR,            -- all codes for this trade, as published
    reference_nos_codes           VARCHAR,            -- NOS codes the curriculum also cites
    mapping_status                VARCHAR NOT NULL,   -- OFFICIAL_EXACT | OFFICIAL_MULTI_NCO
    mapping_authority             VARCHAR NOT NULL,   -- OFFICIAL
    mapping_method                VARCHAR NOT NULL,
    mapping_confidence            DOUBLE,
    -- How the curriculum was linked to a register row. EXACT name equality within
    -- the CTS scheme; never similarity matching.
    link_method                   VARCHAR NOT NULL,
    evidence_field                VARCHAR NOT NULL,
    evidence_reference            VARCHAR NOT NULL,
    nco_code_resolves_in_master   BOOLEAN,
    title_matches_master          BOOLEAN,            -- informational; the CODE is the mapping
    source_id                     VARCHAR NOT NULL,
    snapshot_file                 VARCHAR NOT NULL,
    ingested_at                   VARCHAR NOT NULL
);

-- Explicit status for every one of the 155 trades. Totals reconcile to 155.
CREATE TABLE IF NOT EXISTS dim_trade_mapping_status (
    trade_id             VARCHAR NOT NULL PRIMARY KEY,
    trade_name           VARCHAR NOT NULL,
    nsqf_level           VARCHAR,
    dgt_trade_code       VARCHAR,          -- NULL where the curriculum was not acquired
    nco_codes_for_trade  VARCHAR,          -- NULL where unmapped
    mapping_status       VARCHAR NOT NULL, -- OFFICIAL_EXACT | OFFICIAL_MULTI_NCO
                                           -- | OFFICIAL_VIA_QUALIFICATION | PARTIAL_CHAIN
                                           -- | MAPPING_UNKNOWN
                                           -- | UNMAPPED_NO_QUALIFICATION_LINK
                                           -- | UNMAPPED_NO_NCO_LINK
    mapping_level        VARCHAR NOT NULL, -- NCO_OCCUPATION | UNMAPPED
    status_reason        VARCHAR NOT NULL  -- why, in words
);
