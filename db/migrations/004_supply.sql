-- LMIS supply-side foundation (Step 5.0)
--
-- OBSERVED official training data. No supply estimation, no gap, no forecast.
--
-- The five supply concepts are stored in LONG format - one row per measure, each
-- carrying its own `measure` label and `measure_definition`. A wide table invites
-- treating `trained` as `certified`; long format forces the measure to be named
-- wherever it is used.
--
-- GRAIN WARNING: these sources are STATE-level. District-level training data is
-- not published in them and remains unavailable.

CREATE TABLE IF NOT EXISTS fact_training_outcome (
    source_annexure        VARCHAR NOT NULL,
    annexure_title         VARCHAR NOT NULL,
    scheme                 VARCHAR NOT NULL,   -- PMKVY_1.0 | PMKVY_2.0_CSSM_STT
    scheme_period          VARCHAR,
    as_on_date             VARCHAR,            -- NULL where the source states none
    state_name_as_source   VARCHAR NOT NULL,   -- retained verbatim
    state_lgd_code         VARCHAR,            -- NULL when unresolved
    geo_level              VARCHAR NOT NULL,   -- STATE
    geography_status       VARCHAR NOT NULL,   -- MATCHED | UNMATCHED
    measure                VARCHAR NOT NULL,   -- ENROLLED|TRAINED|ASSESSED|CERTIFIED|PLACED
    measure_definition     VARCHAR NOT NULL,   -- so the concept travels with the number
    value_as_published     VARCHAR,            -- raw string, e.g. '1,36,635' or '-'
    value                  DOUBLE,             -- NULL where the source publishes '-'
    unit                   VARCHAR NOT NULL,   -- candidates
    value_status           VARCHAR NOT NULL,   -- AVAILABLE | NO_DATA
    observed_or_estimated  VARCHAR NOT NULL,   -- OBSERVED
    source_id              VARCHAR NOT NULL,
    snapshot_file          VARCHAR NOT NULL,
    ingested_at            VARCHAR NOT NULL,
    PRIMARY KEY (source_annexure, state_name_as_source, measure)
);

-- Training INFRASTRUCTURE (PMKK centres). A different concept from outcomes:
-- a centre is not a candidate.
CREATE TABLE IF NOT EXISTS fact_training_infrastructure (
    as_on_date             VARCHAR NOT NULL,
    source_annexure        VARCHAR NOT NULL,
    annexure_title         VARCHAR NOT NULL,
    state_name_as_source   VARCHAR NOT NULL,
    state_lgd_code         VARCHAR,
    geo_level              VARCHAR NOT NULL,
    geography_status       VARCHAR NOT NULL,
    metric                 VARCHAR NOT NULL,   -- DISTRICTS_IN_STATE | DISTRICTS_WITH_PMKK
                                               -- | PMKK_ALLOCATED | PMKK_ESTABLISHED
    metric_definition      VARCHAR NOT NULL,
    value_as_published     VARCHAR,
    value                  DOUBLE,
    unit                   VARCHAR NOT NULL,
    value_status           VARCHAR NOT NULL,
    observed_or_estimated  VARCHAR NOT NULL,
    source_id              VARCHAR NOT NULL,
    snapshot_file          VARCHAR NOT NULL,
    ingested_at            VARCHAR NOT NULL,
    PRIMARY KEY (source_annexure, state_name_as_source, metric)
);

-- Official NSQF-compliant trade reference (DGT Craftsmen Training Scheme).
-- NO NCO CODE IS PUBLISHED, so nco_2015_code stays NULL and the status says why.
-- A trade -> NCO mapping is NOT invented anywhere in this project.
CREATE TABLE IF NOT EXISTS dim_training_trade (
    trade_id               VARCHAR NOT NULL PRIMARY KEY,
    trade_section_index    INTEGER NOT NULL,   -- serials restart per section
    trade_serial           INTEGER NOT NULL,
    trade_name             VARCHAR NOT NULL,
    entry_qualification    VARCHAR,
    nsqf_level             VARCHAR,
    duration               VARCHAR,
    revision_year          VARCHAR,
    scheme                 VARCHAR NOT NULL,
    trade_scheme_source    VARCHAR NOT NULL,
    nco_2015_code          VARCHAR,            -- always NULL at Step 5.0
    nco_mapping_status     VARCHAR NOT NULL,   -- UNMAPPED_NO_OFFICIAL_MAPPING
    nco_mapping_authority  VARCHAR,
    nco_mapping_confidence DOUBLE,
    source_annexure        VARCHAR NOT NULL,
    annexure_title         VARCHAR NOT NULL,
    observed_or_estimated  VARCHAR NOT NULL,
    source_id              VARCHAR NOT NULL,
    snapshot_file          VARCHAR NOT NULL,
    ingested_at            VARCHAR NOT NULL
);

-- Reconciliation of extracted sums against the totals the source itself prints.
CREATE TABLE IF NOT EXISTS fact_training_reconciliation (
    source_annexure   VARCHAR NOT NULL,
    measure           VARCHAR NOT NULL,
    extracted_sum     DOUBLE,
    published_total   DOUBLE,            -- NULL where the source prints no total
    difference        DOUBLE,            -- 0 means the extraction is faithful
    source_id         VARCHAR NOT NULL,
    ingested_at       VARCHAR NOT NULL,
    PRIMARY KEY (source_annexure, measure)
);

-- Supply coverage accounting, using the project's existing status vocabulary.
CREATE TABLE IF NOT EXISTS supply_coverage_summary (
    metric    VARCHAR NOT NULL PRIMARY KEY,
    value     DOUBLE,
    unit      VARCHAR NOT NULL,
    status    VARCHAR,     -- AVAILABLE|NO_DATA|NOT_ACQUIRED|ACCESS_PENDING|UNMAPPED|NOT_APPLICABLE
    note      VARCHAR,
    built_at  VARCHAR NOT NULL
);
