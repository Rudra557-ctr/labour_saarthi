-- LMIS supply evidence resolution (Step 5.1)
--
-- Evidence only. No supply estimation, no district allocation, no gap, no forecast.

-- OFFICIAL qualification -> NCO-2015 mapping, read out of the NQR Q-File's own
-- field 14. One row per Q-File that STATES a code; a Q-File without a code yields
-- no row. No fuzzy matching, embeddings or model-generated codes are involved.
--
-- NOTE: these are NQR QUALIFICATIONS, not the 155 DGT Craftsmen Training Scheme
-- trades. `applies_to_dgt_cts_trade` is False for every row, and
-- dim_training_trade stays UNMAPPED.
CREATE TABLE IF NOT EXISTS map_qualification_to_nco (
    mapping_id                    VARCHAR NOT NULL PRIMARY KEY,
    qualification_name            VARCHAR,
    qualification_code            VARCHAR,      -- awarding-body code from the published filename
    qfile_version                 VARCHAR,
    nsqf_level                    VARCHAR,
    nco_2015_code                 VARCHAR NOT NULL,
    nco_2015_title                VARCHAR,      -- resolved from occupation_master
    nco_mapping_level             VARCHAR NOT NULL,  -- OCCUPATION (full 8 digits)
    mapping_authority             VARCHAR NOT NULL,  -- OFFICIAL
    mapping_method                VARCHAR NOT NULL,
    mapping_confidence            DOUBLE,
    evidence_field                VARCHAR NOT NULL,  -- the exact Q-File field cited
    evidence_reference            VARCHAR NOT NULL,  -- the exact file
    -- Independent corroboration, stored so the mapping can be audited:
    title_matches_nco_title       BOOLEAN,
    nco_code_resolves_in_master   BOOLEAN,
    qp_nos_indicated_by_nco_code  BOOLEAN,
    applies_to_dgt_cts_trade      BOOLEAN NOT NULL,
    source_id                     VARCHAR NOT NULL,
    snapshot_file                 VARCHAR NOT NULL,
    ingested_at                   VARCHAR NOT NULL
);

-- The Step 5.1 evidence matrix, stored as DATA so the decisions are queryable
-- rather than only narrated in prose. Every REJECTED / UNAVAILABLE /
-- ACCESS_PENDING row carries a concrete reason.
CREATE TABLE IF NOT EXISTS supply_evidence_matrix (
    blocker               VARCHAR NOT NULL,   -- A_DISTRICT_SUPPLY | B_TRADE_NCO
    source                VARCHAR NOT NULL,
    resource              VARCHAR NOT NULL,
    official_publisher    VARCHAR NOT NULL,
    url                   VARCHAR,
    access_status         VARCHAR NOT NULL,
    access_date           VARCHAR NOT NULL,
    vintage               VARCHAR,
    grain                 VARCHAR,
    district_available    BOOLEAN,
    trade_available       BOOLEAN,
    occupation_available  BOOLEAN,
    measure_available     BOOLEAN,
    nco_mapping_available BOOLEAN,
    decision              VARCHAR NOT NULL,   -- ACQUIRED|PARTIALLY_ACQUIRED|ACCESS_PENDING
                                              -- |UNAVAILABLE|REJECTED|ACQUIRED_METADATA_ONLY
    reason                VARCHAR NOT NULL,
    built_at              VARCHAR NOT NULL,
    PRIMARY KEY (blocker, source, resource)
);
