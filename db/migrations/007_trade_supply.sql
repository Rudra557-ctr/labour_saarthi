-- LMIS trade/job-role level supply quantities (Step 5.3)
--
-- Evidence only. No supply estimation, no allocation to states/districts/trades,
-- no gap, no forecast.
--
-- GRAIN: NATIONAL x entity x measure. There is NO state or district dimension in
-- these tables and none is manufactured. is_top_n_subset is TRUE on every row:
-- these are published "Top N" lists, so the rows do NOT sum to the population and
-- no share or denominator may be derived from them.

CREATE TABLE IF NOT EXISTS fact_training_trade_outcome (
    source_table                VARCHAR NOT NULL,   -- TABLE_5_54 | TABLE_5_10 | TABLE_5_9
    source_table_title          VARCHAR NOT NULL,
    scheme                      VARCHAR NOT NULL,   -- NAPS_APPRENTICESHIP | PMKVY_4.0
    period_label                VARCHAR NOT NULL,
    geo_level                   VARCHAR NOT NULL,   -- NATIONAL only
    occupation_entity_type      VARCHAR NOT NULL,   -- TRADE | JOB_ROLE | SECTOR
    entity_name_as_source       VARCHAR NOT NULL,   -- retained verbatim
    entity_type_as_source       VARCHAR,            -- e.g. Designated / Optional Trade
    published_rank              INTEGER NOT NULL,   -- the rank the source printed
    measure                     VARCHAR NOT NULL,   -- APPRENTICES_ENGAGED|ENROLLED|TRAINED_ORIENTED
    measure_definition          VARCHAR NOT NULL,   -- the concept travels with the number
    value_as_published          VARCHAR,
    value                       DOUBLE,
    unit                        VARCHAR NOT NULL,
    value_status                VARCHAR NOT NULL,   -- AVAILABLE | NO_DATA
    -- TRUE everywhere: a top-N subset, never a population.
    is_top_n_subset             BOOLEAN NOT NULL,
    published_grand_total       DOUBLE,             -- subtotal of the displayed rows where printed
    -- NCO is CONNECTED through the existing official maps, never newly mapped.
    nco_link_status             VARCHAR NOT NULL,   -- OFFICIAL_VIA_MAP_TRADE_TO_NCO
                                                    -- | OFFICIAL_VIA_MAP_QUALIFICATION_TO_NCO
                                                    -- | NO_EXISTING_OFFICIAL_MAP
    nco_codes_via_existing_map  VARCHAR,
    nco_link_method             VARCHAR,            -- EXACT_NAME_AGAINST_EXISTING_OFFICIAL_MAP
    observed_or_estimated       VARCHAR NOT NULL,   -- OBSERVED
    source_id                   VARCHAR NOT NULL,
    snapshot_file               VARCHAR NOT NULL,
    ingested_at                 VARCHAR NOT NULL,
    PRIMARY KEY (source_table, entity_name_as_source, measure)
);

-- Reconciliation. A non-zero shortfall is EXPECTED for a top-N list and is not an
-- extraction error; where the source prints a total of the displayed rows it must
-- match exactly.
CREATE TABLE IF NOT EXISTS fact_trade_supply_reconciliation (
    source_table           VARCHAR NOT NULL,
    measure                VARCHAR NOT NULL,
    top_n_extracted_sum    DOUBLE,
    published_grand_total  DOUBLE,
    top_n_shortfall        DOUBLE,
    note                   VARCHAR NOT NULL,
    source_id              VARCHAR NOT NULL,
    ingested_at            VARCHAR NOT NULL,
    PRIMARY KEY (source_table, measure)
);
