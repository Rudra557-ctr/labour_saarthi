-- LMIS warehouse schema (DuckDB)
-- Step 2.0 real data foundation.
--
-- Design rules enforced by this schema, from Step 0:
--   * One table per source-concept at its NATIVE grain. No merged mega-table.
--   * Every fact records geo_level / period_grain / unit explicitly, so no query
--     can silently combine incompatible rows.
--   * observed_or_estimated is NOT NULL on every fact. Step 2.0 loads OBSERVED
--     rows only; the column exists so estimation can never arrive unlabelled.
--   * Missing stays missing: measure columns are nullable and are never defaulted
--     to zero.
--   * Provenance is a first-class table, not a comment.

-- ============================== DIMENSIONS ==============================

CREATE TABLE IF NOT EXISTS location_master (
    lgd_code                  VARCHAR NOT NULL,
    level                     VARCHAR NOT NULL,   -- STATE | DISTRICT
    parent_lgd_code           VARCHAR,
    name_en                   VARCHAR NOT NULL,
    name_local                VARCHAR,
    state_lgd_code            VARCHAR,
    census_2011_code          VARCHAR,            -- NULL = district post-dates Census 2011
    valid_from                VARCHAR,            -- source's own last_updated; snapshot age is visible
    valid_to                  VARCHAR,
    is_current                BOOLEAN,
    stable_district_group_id  VARCHAR,
    source_id                 VARCHAR NOT NULL,
    ingested_at               VARCHAR NOT NULL,
    PRIMARY KEY (level, lgd_code)
);

CREATE TABLE IF NOT EXISTS occupation_master (
    nco_version          VARCHAR NOT NULL,
    nco_code             VARCHAR NOT NULL,
    level                VARCHAR NOT NULL,   -- DIVISION | SUB_DIVISION | GROUP | FAMILY | OCCUPATION
    parent_nco_code      VARCHAR,
    title_en             VARCHAR,
    title_variant_count  INTEGER,
    qp_nos_indicated     BOOLEAN,            -- NCO digits 7-8 != 00; NULL for hierarchy nodes
    nco_2004_code        VARCHAR,
    source_id            VARCHAR NOT NULL,
    ingested_at          VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS sector_master (
    sector_id         VARCHAR NOT NULL PRIMARY KEY,
    portal_sector_id  INTEGER,
    sector_name_en    VARCHAR NOT NULL,
    ssc_name          VARCHAR,
    ssc_code          VARCHAR,
    source_id         VARCHAR NOT NULL,
    valid_from        VARCHAR,
    valid_to          VARCHAR
);

CREATE TABLE IF NOT EXISTS nic_section_master (
    nic_version       VARCHAR NOT NULL,
    section_code      VARCHAR NOT NULL,   -- A..U
    section_title_en  VARCHAR NOT NULL,
    source_id         VARCHAR NOT NULL,
    ingested_at       VARCHAR NOT NULL,
    PRIMARY KEY (nic_version, section_code)
);

CREATE TABLE IF NOT EXISTS dim_period (
    period_id         VARCHAR NOT NULL PRIMARY KEY,
    period_start      VARCHAR NOT NULL,
    period_end        VARCHAR NOT NULL,
    period_grain      VARCHAR NOT NULL,
    calendar_year     INTEGER NOT NULL,
    calendar_month    INTEGER NOT NULL,
    calendar_quarter  INTEGER NOT NULL,
    fiscal_year       VARCHAR NOT NULL,
    fiscal_quarter    INTEGER NOT NULL,
    academic_year     VARCHAR NOT NULL,
    label_en          VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS location_alias (
    alias_id          VARCHAR, alias_text VARCHAR, normalised_alias VARCHAR,
    lgd_code          VARCHAR, match_method VARCHAR, confidence DOUBLE,
    source_id         VARCHAR, reviewed_by VARCHAR, reviewed_at VARCHAR
);

CREATE TABLE IF NOT EXISTS location_change_event (
    event_id          VARCHAR, event_type VARCHAR, parent_lgd_code VARCHAR,
    child_lgd_code    VARCHAR, effective_date VARCHAR,
    notification_reference VARCHAR, source_id VARCHAR, notes VARCHAR
);

-- ============================== MAPPINGS ==============================
-- authority separates OFFICIAL crosswalks from PROJECT mappings. Never merged
-- without it, and PROJECT rows always carry a confidence.

CREATE TABLE IF NOT EXISTS map_nco2004_to_nco2015 (
    nco_2015_code       VARCHAR NOT NULL,
    nco_2004_code       VARCHAR,            -- NULL where the source leaves it blank
    occupational_title  VARCHAR,
    authority           VARCHAR NOT NULL,   -- OFFICIAL
    method              VARCHAR NOT NULL,
    confidence          DOUBLE NOT NULL,
    source_id           VARCHAR NOT NULL,
    ingested_at         VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS map_ncs_sector_to_nic_section (
    ncs_sector_name   VARCHAR NOT NULL PRIMARY KEY,
    nic_version       VARCHAR,
    section_code      VARCHAR,            -- NULL for unmappable residual categories
    authority         VARCHAR NOT NULL,   -- PROJECT
    method            VARCHAR NOT NULL,
    confidence        DOUBLE,
    rationale         VARCHAR,
    reviewed_at       VARCHAR
);

-- ============================== PROVENANCE ==============================

CREATE TABLE IF NOT EXISTS source_master (
    source_id            VARCHAR NOT NULL PRIMARY KEY,
    source_name          VARCHAR NOT NULL,
    publisher_org        VARCHAR NOT NULL,
    landing_url          VARCHAR,
    role                 VARCHAR NOT NULL,
    access_method        VARCHAR NOT NULL,
    licence              VARCHAR,
    licence_verified     BOOLEAN,
    geo_level_available  VARCHAR,
    occ_coding_scheme    VARCHAR,
    period_grain         VARCHAR,
    update_cadence       VARCHAR,
    is_authoritative     BOOLEAN,
    verification_status  VARCHAR NOT NULL,
    notes                VARCHAR
);

CREATE TABLE IF NOT EXISTS source_snapshot (
    snapshot_id          VARCHAR NOT NULL PRIMARY KEY,
    source_id            VARCHAR NOT NULL,
    retrieved_at         VARCHAR NOT NULL,
    retrieved_date       VARCHAR NOT NULL,
    file_name            VARCHAR NOT NULL,
    file_url             VARCHAR,
    sha256               VARCHAR NOT NULL,
    size_bytes           BIGINT NOT NULL,
    http_status          INTEGER,
    publication_vintage  VARCHAR,            -- NULL unless the SOURCE states it
    retrieved_by         VARCHAR,
    notes                VARCHAR
);

CREATE TABLE IF NOT EXISTS fact_data_quality (
    run_id       VARCHAR NOT NULL,
    table_name   VARCHAR NOT NULL,
    check_name   VARCHAR NOT NULL,
    status       VARCHAR NOT NULL,   -- PASS | FAIL
    observed     VARCHAR,
    expected     VARCHAR,
    severity     VARCHAR,
    checked_at   VARCHAR NOT NULL
);

-- ============================== FACTS ==============================
-- NCS publishes state-wise and sector-wise as SEPARATE MARGINAL tables. They are
-- modelled as two tables precisely because a joint state x sector cross-tab does
-- not exist and must not be implied.

CREATE TABLE IF NOT EXISTS fact_vacancy_official_by_state (
    snapshot_date         VARCHAR NOT NULL,   -- the "as on" date the source states
    lgd_code              VARCHAR,            -- NULL for the PAN-India residual
    geo_level             VARCHAR NOT NULL,   -- STATE | NATIONAL
    state_name_as_source  VARCHAR NOT NULL,
    vacancies_cumulative  BIGINT,
    unit                  VARCHAR NOT NULL,   -- count
    measure_basis         VARCHAR NOT NULL,   -- CUMULATIVE_SINCE_INCEPTION
    is_pan_india_residual BOOLEAN NOT NULL,
    observed_or_estimated VARCHAR NOT NULL,
    source_id             VARCHAR NOT NULL,
    snapshot_file         VARCHAR NOT NULL,
    ingested_at           VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_vacancy_official_by_sector (
    snapshot_date          VARCHAR NOT NULL,
    ncs_sector_name        VARCHAR NOT NULL,
    nic_section_code       VARCHAR,           -- via map_ncs_sector_to_nic_section; NULL if unmappable
    vacancies_cumulative   DOUBLE,
    unit                   VARCHAR NOT NULL,  -- lakh (as published)
    measure_basis          VARCHAR NOT NULL,
    observed_or_estimated  VARCHAR NOT NULL,
    source_id              VARCHAR NOT NULL,
    snapshot_file          VARCHAR NOT NULL,
    ingested_at            VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_establishment_district (
    snapshot_date          VARCHAR NOT NULL,
    lgd_code               VARCHAR NOT NULL,
    geo_level              VARCHAR NOT NULL,   -- DISTRICT
    district_name_as_source VARCHAR,
    enterprise_category    VARCHAR NOT NULL,   -- TOTAL | SERVICES
    size_class             VARCHAR NOT NULL,   -- MICRO | SMALL | MEDIUM | TOTAL
    enterprise_count       BIGINT,             -- NULL where source says 'NA'
    unit                   VARCHAR NOT NULL,   -- count
    measure_basis          VARCHAR NOT NULL,   -- CUMULATIVE_REGISTRATIONS
    observed_or_estimated  VARCHAR NOT NULL,
    source_id              VARCHAR NOT NULL,
    snapshot_file          VARCHAR NOT NULL,
    ingested_at            VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_labour_force_estimate (
    period_id              VARCHAR NOT NULL,
    geo_level              VARCHAR NOT NULL,   -- NATIONAL only: PLFS monthly is all-India
    lgd_code               VARCHAR,            -- NULL at NATIONAL level, by design
    area                   VARCHAR NOT NULL,   -- RURAL | URBAN | RURAL_URBAN
    sex                    VARCHAR NOT NULL,   -- MALE | FEMALE | PERSON
    age_group              VARCHAR NOT NULL,
    indicator              VARCHAR NOT NULL,   -- LFPR | WPR | UR
    approach               VARCHAR NOT NULL,   -- CWS
    value_percent          DOUBLE,
    std_error              DOUBLE,             -- not published in the monthly bulletin
    unit                   VARCHAR NOT NULL,   -- percent
    observed_or_estimated  VARCHAR NOT NULL,   -- OBSERVED_SURVEY_ESTIMATE
    source_id              VARCHAR NOT NULL,
    snapshot_file          VARCHAR NOT NULL,
    ingested_at            VARCHAR NOT NULL
);
