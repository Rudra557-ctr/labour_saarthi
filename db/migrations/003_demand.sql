-- LMIS demand estimation layer (Step 4.0)
--
-- These are the FIRST tables in the project containing ESTIMATED values.
-- Every row therefore carries:
--   observed_or_estimated   ESTIMATED | UNAVAILABLE  (never OBSERVED: the inputs
--                           are observed, the products are not)
--   the seven confidence dimensions + overall_confidence (weakest-link)
--   methodology             the formula, in words
--   source_ids              every source that contributed
--   flow_available = false  with its reason
--
-- Outputs A and C are separate tables on purpose. A must never be used as a
-- factor in C: that would apply two occupational structures to one quantity and
-- double-count the occupational signal.

-- A. National occupation demand composition.
-- Grain: baseline_period x nic_section_code x nco_2015_division
CREATE TABLE IF NOT EXISTS demand_national_occupation_composition (
    baseline_period                VARCHAR NOT NULL,
    nic_section_code               VARCHAR NOT NULL,
    ncs_sector_name                VARCHAR NOT NULL,
    nco_2015_division              VARCHAR NOT NULL,
    vacancies_cumulative           DOUBLE,          -- OBSERVED input (lakh)
    occupation_conditional_share   DOUBLE,          -- P(occupation | industry), ILO/PLFS
    estimated_occupation_demand    DOUBLE,          -- the product
    occupation_total_all_sections  DOUBLE,          -- summed across sections
    occupation_share_of_total      DOUBLE,          -- the composition itself
    bridge_cells_in_section        BIGINT,
    bridge_year                    VARCHAR NOT NULL,
    unit                           VARCHAR NOT NULL,
    measure_basis                  VARCHAR NOT NULL,
    geo_level                      VARCHAR NOT NULL,  -- NATIONAL only
    industry_level                 VARCHAR NOT NULL,
    occupation_level               VARCHAR NOT NULL,
    is_heterogeneous_or_residual   BOOLEAN,
    industry_mapping_confidence    DOUBLE,
    source_confidence              VARCHAR NOT NULL,
    mapping_confidence             DOUBLE,
    temporal_confidence            VARCHAR NOT NULL,
    geography_coverage             VARCHAR NOT NULL,
    occupation_coverage            VARCHAR NOT NULL,
    statistical_support            VARCHAR NOT NULL,
    transformation_depth           INTEGER NOT NULL,
    overall_confidence             VARCHAR NOT NULL,
    observed_or_estimated          VARCHAR NOT NULL,
    methodology                    VARCHAR NOT NULL,
    source_ids                     VARCHAR NOT NULL,
    flow_available                 BOOLEAN NOT NULL,
    flow_unavailable_reason        VARCHAR,
    built_at                       VARCHAR NOT NULL,
    PRIMARY KEY (baseline_period, nic_section_code, nco_2015_division)
);

-- B. District relative demand signal. NO occupation dimension by design.
-- Grain: baseline_period x lgd_code
CREATE TABLE IF NOT EXISTS demand_district_relative_signal (
    baseline_period                VARCHAR NOT NULL,
    lgd_code                       VARCHAR NOT NULL,
    district_name_lgd              VARCHAR,
    state_lgd_code                 VARCHAR,
    state_name_lgd                 VARCHAR,
    census_2011_code               VARCHAR,
    observed_state_vacancies       DOUBLE,          -- OBSERVED input
    ncs_source_rows                BIGINT,
    ncs_state_names                VARCHAR,
    district_enterprise_count      BIGINT,          -- SUPPORTING input
    enterprise_share_within_state  DOUBLE,          -- SUPPORTING input
    relative_demand_signal         DOUBLE,          -- ESTIMATED: not a vacancy count
    signal_share_of_national       DOUBLE,
    rank_within_state              BIGINT,
    rank_national                  BIGINT,
    unit                           VARCHAR NOT NULL,
    geo_level                      VARCHAR NOT NULL,
    occupation_level               VARCHAR NOT NULL,  -- NONE
    pan_india_residual_excluded    BOOLEAN NOT NULL,
    udyam_snapshot_date            VARCHAR,
    udyam_source_vintage           VARCHAR,
    source_confidence              VARCHAR NOT NULL,
    mapping_confidence             DOUBLE,
    temporal_confidence            VARCHAR NOT NULL,
    geography_coverage             VARCHAR NOT NULL,
    occupation_coverage            VARCHAR NOT NULL,
    statistical_support            VARCHAR NOT NULL,
    transformation_depth           INTEGER NOT NULL,
    overall_confidence             VARCHAR NOT NULL,
    observed_or_estimated          VARCHAR NOT NULL,
    methodology                    VARCHAR NOT NULL,
    within_state_ranking_caveat    VARCHAR NOT NULL,
    source_ids                     VARCHAR NOT NULL,
    flow_available                 BOOLEAN NOT NULL,
    flow_unavailable_reason        VARCHAR,
    built_at                       VARCHAR NOT NULL,
    PRIMARY KEY (baseline_period, lgd_code)
);

-- C. District x occupation relative demand signal.
-- Grain: baseline_period x lgd_code x nco_2015_division
--        (nco_2015_division is NULL on the one row that states why a district
--         has no prior, so every district is represented explicitly)
CREATE TABLE IF NOT EXISTS demand_district_occupation_signal (
    baseline_period                        VARCHAR NOT NULL,
    lgd_code                               VARCHAR NOT NULL,
    district_name_lgd                      VARCHAR,
    state_lgd_code                         VARCHAR,
    state_name_lgd                         VARCHAR,
    census_2011_code                       VARCHAR,
    census_district_code                   VARCHAR,
    nco_2004_division                      VARCHAR,
    nco_2015_division                      VARCHAR,
    nco_name                               VARCHAR,
    relative_demand_signal                 DOUBLE,   -- output B, the input here
    occupation_share_of_district           DOUBLE,   -- Census 2011 share
    district_occupation_signal             DOUBLE,   -- ESTIMATED: ranking signal only
    unclassified_share_not_allocated       DOUBLE,   -- Census 'X' share, retained not redistributed
    main_workers                           BIGINT,
    district_total_main_workers            BIGINT,
    rank_within_district                   BIGINT,
    rank_within_occupation_across_districts BIGINT,
    occupation_prior_status                VARCHAR NOT NULL,
    unit                                   VARCHAR NOT NULL,
    geo_level                              VARCHAR NOT NULL,
    occupation_level                       VARCHAR NOT NULL,
    interpretation                         VARCHAR NOT NULL,
    source_confidence                      VARCHAR NOT NULL,
    mapping_confidence                     DOUBLE,
    division_map_confidence                DOUBLE,
    temporal_confidence                    VARCHAR NOT NULL,
    geography_coverage                     VARCHAR NOT NULL,
    occupation_coverage                    VARCHAR NOT NULL,
    statistical_support                    VARCHAR NOT NULL,
    transformation_depth                   INTEGER NOT NULL,
    overall_confidence                     VARCHAR NOT NULL,
    observed_or_estimated                  VARCHAR NOT NULL,
    methodology                            VARCHAR NOT NULL,
    within_district_ranking_caveat         VARCHAR NOT NULL,
    source_ids                             VARCHAR NOT NULL,
    flow_available                         BOOLEAN NOT NULL,
    flow_unavailable_reason                VARCHAR,
    built_at                               VARCHAR NOT NULL
);

-- Coverage accounting, including the PAN-India residual, so the share of the
-- measure that is geographically attributable is always visible.
CREATE TABLE IF NOT EXISTS demand_coverage_summary (
    baseline_period  VARCHAR NOT NULL,
    metric           VARCHAR NOT NULL,
    value            DOUBLE,
    unit             VARCHAR NOT NULL,
    note             VARCHAR,
    built_at         VARCHAR NOT NULL,
    PRIMARY KEY (baseline_period, metric)
);
