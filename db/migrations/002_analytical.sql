-- LMIS analytical layer (Step 3.0)
--
-- These are DERIVED tables. Each carries:
--   observation_status  OBSERVED | SUPPORTING   (never ESTIMATED at this stage)
--   source_vintage      what the SOURCE says its data is as-of
--   *_level columns     the geography / occupation / industry level actually valid
--   transformation      how the row was produced
-- so any number can be explained without reading code.

CREATE TABLE IF NOT EXISTS analytical_state_demand (
    snapshot_date                VARCHAR NOT NULL,
    state_name_as_source         VARCHAR NOT NULL,
    lgd_code                     VARCHAR,          -- NULL for the PAN-India residual
    geo_level                    VARCHAR NOT NULL, -- STATE | NATIONAL
    vacancies_cumulative         BIGINT,
    unit                         VARCHAR NOT NULL,
    measure_basis                VARCHAR NOT NULL,
    is_pan_india_residual        BOOLEAN NOT NULL,
    share_of_published_total     DOUBLE,
    share_of_state_attributable  DOUBLE,           -- NULL for the residual row
    n_source_documents           INTEGER NOT NULL,
    source_documents             VARCHAR NOT NULL,
    flow_available               BOOLEAN NOT NULL,
    flow_unavailable_reason      VARCHAR,
    occupation_level             VARCHAR NOT NULL, -- NONE: NCS carries no occupation
    industry_level               VARCHAR NOT NULL,
    observation_status           VARCHAR NOT NULL,
    source_vintage               VARCHAR NOT NULL,
    transformation               VARCHAR NOT NULL,
    source_id                    VARCHAR NOT NULL,
    PRIMARY KEY (snapshot_date, state_name_as_source)
);

CREATE TABLE IF NOT EXISTS analytical_demand_by_industry (
    snapshot_date                 VARCHAR NOT NULL,
    ncs_sector_name               VARCHAR NOT NULL,
    nic_section_code              VARCHAR,          -- NULL where deliberately unmapped
    vacancies_cumulative          DOUBLE,
    unit                          VARCHAR NOT NULL, -- lakh, as published
    measure_basis                 VARCHAR NOT NULL,
    share_of_published_total      DOUBLE,
    mapping_authority             VARCHAR,
    mapping_method                VARCHAR,
    mapping_confidence            DOUBLE,
    is_heterogeneous_or_residual  BOOLEAN NOT NULL,
    n_source_documents            INTEGER NOT NULL,
    source_documents              VARCHAR NOT NULL,
    geo_level                     VARCHAR NOT NULL,
    industry_level                VARCHAR NOT NULL,
    occupation_level              VARCHAR NOT NULL, -- NONE: industry is not occupation
    observation_status            VARCHAR NOT NULL,
    source_vintage                VARCHAR NOT NULL,
    transformation                VARCHAR NOT NULL,
    source_id                     VARCHAR NOT NULL,
    PRIMARY KEY (snapshot_date, ncs_sector_name)
);

CREATE TABLE IF NOT EXISTS analytical_district_structure (
    snapshot_date                  VARCHAR NOT NULL,
    lgd_code                       VARCHAR NOT NULL,
    enterprise_category            VARCHAR NOT NULL, -- TOTAL | SERVICES
    district_name_lgd              VARCHAR,
    state_lgd_code                 VARCHAR,
    census_2011_code               VARCHAR,
    micro                          BIGINT,
    small                          BIGINT,
    medium                         BIGINT,           -- NULL where source says 'NA'
    total                          BIGINT,
    enterprise_share_of_national   DOUBLE,
    enterprise_share_within_state  DOUBLE,
    micro_share_of_district        DOUBLE,
    small_share_of_district        DOUBLE,
    medium_share_of_district       DOUBLE,
    unit                           VARCHAR NOT NULL,
    measure_basis                  VARCHAR NOT NULL,
    geo_level                      VARCHAR NOT NULL,
    occupation_level               VARCHAR NOT NULL,
    not_a_demand_measure           BOOLEAN NOT NULL,
    observation_status             VARCHAR NOT NULL, -- SUPPORTING
    source_vintage                 VARCHAR NOT NULL,
    transformation                 VARCHAR NOT NULL,
    source_id                      VARCHAR NOT NULL,
    snapshot_file                  VARCHAR NOT NULL,
    PRIMARY KEY (snapshot_date, lgd_code, enterprise_category)
);

CREATE TABLE IF NOT EXISTS analytical_district_occupation_structure (
    census_year                   INTEGER NOT NULL,
    census_state_code             VARCHAR NOT NULL,
    census_district_code          VARCHAR NOT NULL,
    area_name                     VARCHAR,
    nco_2004_division             VARCHAR NOT NULL,
    nco_2015_division             VARCHAR,          -- via derived crosswalk; NULL for 'X'
    division_map_authority        VARCHAR,
    division_map_confidence       DOUBLE,
    nco_name                      VARCHAR,
    row_type                      VARCHAR NOT NULL,
    area                          VARCHAR NOT NULL,
    sex                           VARCHAR NOT NULL,
    main_workers                  BIGINT,
    district_total_main_workers   BIGINT,
    occupation_share_of_district  DOUBLE,
    geo_level                     VARCHAR NOT NULL,
    occupation_scheme             VARCHAR NOT NULL,
    occupation_level              VARCHAR NOT NULL,
    universe                      VARCHAR NOT NULL,
    is_historical                 BOOLEAN NOT NULL,
    not_a_demand_measure          BOOLEAN NOT NULL,
    observation_status            VARCHAR NOT NULL, -- SUPPORTING
    source_vintage                VARCHAR NOT NULL,
    transformation                VARCHAR NOT NULL,
    source_id                     VARCHAR NOT NULL,
    snapshot_file                 VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS analytical_labour_market_context (
    period_id                 VARCHAR NOT NULL,
    geo_level                 VARCHAR NOT NULL,
    area                      VARCHAR NOT NULL,
    sex                       VARCHAR NOT NULL,
    age_group                 VARCHAR NOT NULL,
    indicator                 VARCHAR NOT NULL,
    approach                  VARCHAR NOT NULL,
    value_percent             DOUBLE,
    std_error                 DOUBLE,
    unit                      VARCHAR NOT NULL,
    statistical_basis         VARCHAR NOT NULL,
    valid_geo_level           VARCHAR NOT NULL,
    district_estimates_valid  BOOLEAN NOT NULL,
    not_a_demand_measure      BOOLEAN NOT NULL,
    observation_status        VARCHAR NOT NULL,
    source_vintage            VARCHAR NOT NULL,
    transformation            VARCHAR NOT NULL,
    source_id                 VARCHAR NOT NULL,
    snapshot_file             VARCHAR NOT NULL,
    PRIMARY KEY (period_id, area, sex, age_group, indicator)
);

-- Derived crosswalk with MEASURED purity, not an assumed identity.
CREATE TABLE IF NOT EXISTS map_nco2004_division_to_nco2015_division (
    nco_2004_division      VARCHAR NOT NULL PRIMARY KEY,
    nco_2015_division      VARCHAR,
    confidence             DOUBLE,          -- share of concorded codes in the modal division
    n_concorded_codes      INTEGER NOT NULL,
    n_in_modal_division    INTEGER NOT NULL,
    alternative_divisions  VARCHAR,
    authority              VARCHAR NOT NULL,
    method                 VARCHAR NOT NULL
);

-- Source fact table for Census B-24 at its native grain.
CREATE TABLE IF NOT EXISTS fact_census_occupation_workers (
    census_year            INTEGER NOT NULL,
    census_state_code      VARCHAR NOT NULL,
    census_district_code   VARCHAR,
    area_name              VARCHAR,
    nco_2004_division      VARCHAR NOT NULL,
    nco_2004_sub_division  VARCHAR NOT NULL,
    nco_name               VARCHAR,
    row_type               VARCHAR NOT NULL,
    area                   VARCHAR NOT NULL,
    sex                    VARCHAR NOT NULL,
    main_workers           BIGINT,
    geo_level              VARCHAR NOT NULL,
    occupation_scheme      VARCHAR NOT NULL,
    occupation_level       VARCHAR NOT NULL,
    universe               VARCHAR NOT NULL,
    observed_or_estimated  VARCHAR NOT NULL,
    source_id              VARCHAR NOT NULL,
    snapshot_file          VARCHAR NOT NULL,
    ingested_at            VARCHAR NOT NULL
);

-- One row per analytical table: the catalog a dashboard reads to explain itself.
CREATE TABLE IF NOT EXISTS analytical_dataset_catalog (
    analytical_table    VARCHAR NOT NULL PRIMARY KEY,
    grain               VARCHAR NOT NULL,
    source_tables       VARCHAR NOT NULL,
    source_ids          VARCHAR NOT NULL,
    source_vintage      VARCHAR NOT NULL,
    geo_level           VARCHAR NOT NULL,
    occupation_level    VARCHAR NOT NULL,
    industry_level      VARCHAR NOT NULL,
    observation_status  VARCHAR NOT NULL,
    transformations     VARCHAR NOT NULL,
    row_count           BIGINT NOT NULL,
    coverage_note       VARCHAR,
    limitations         VARCHAR,
    built_at            VARCHAR NOT NULL
);

-- Added in Step 3.1 (evidence resolution). SOURCE fact at native grain.
-- This is the evidence that makes an industry->occupation bridge possible; the
-- bridge itself is specified in docs/step3_1_estimation_methodology.md and is
-- deliberately NOT built here.
CREATE TABLE IF NOT EXISTS fact_ilo_employment_eco_occ (
    ref_area              VARCHAR NOT NULL,
    year                  VARCHAR NOT NULL,
    nic_2008_section      VARCHAR NOT NULL,   -- from ISIC-Rev.4 section
    isco_08_major_group   VARCHAR NOT NULL,
    nco_2015_division     VARCHAR NOT NULL,   -- == ISCO-08 major group (one-to-one)
    employment_thousands  DOUBLE,             -- NULL where ILO suppresses/omits the cell
    unit                  VARCHAR NOT NULL,
    measure_basis         VARCHAR NOT NULL,
    geo_level             VARCHAR NOT NULL,   -- NATIONAL: there is no state dimension
    industry_level         VARCHAR NOT NULL,
    occupation_level      VARCHAR NOT NULL,
    survey_source_code    VARCHAR,
    survey_source_label   VARCHAR,            -- 'LFS - Periodic Labour Force Survey'
    obs_status            VARCHAR,
    observed_or_estimated VARCHAR NOT NULL,
    source_id             VARCHAR NOT NULL,
    snapshot_file         VARCHAR NOT NULL,
    ingested_at           VARCHAR NOT NULL,
    PRIMARY KEY (ref_area, year, nic_2008_section, isco_08_major_group)
);
