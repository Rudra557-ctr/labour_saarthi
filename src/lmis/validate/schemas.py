"""Pandera contracts for the standardized tables.

These are the rules from Step 0 turned into enforced checks. The ones that matter
most are the negative checks: `observed_or_estimated` must be present on every
fact so estimation can never arrive unlabelled, measures must be nullable so
missing stays missing, and units must be explicit so incompatible rows cannot be
summed by accident.
"""
from __future__ import annotations

import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

OBSERVED_VALUES = ["OBSERVED", "OBSERVED_SURVEY_ESTIMATE"]

location_master_schema = DataFrameSchema(
    {
        "lgd_code": Column(str, nullable=False),
        "level": Column(str, Check.isin(["STATE", "DISTRICT"]), nullable=False),
        "parent_lgd_code": Column(str, nullable=True),
        "name_en": Column(str, nullable=False),
        # NULL means the district post-dates Census 2011. The literal '000' must
        # never survive into the warehouse.
        "census_2011_code": Column(str, nullable=True, checks=Check(lambda s: ~s.isin(["000", "0"]))),
        "valid_from": Column(str, nullable=False),
        "is_current": Column(bool, nullable=False),
        "source_id": Column(str, nullable=False),
    },
    strict=False,
    name="location_master",
)

occupation_master_schema = DataFrameSchema(
    {
        "nco_version": Column(str, Check.eq("2015")),
        "nco_code": Column(str, nullable=False),
        "level": Column(
            str,
            Check.isin(["DIVISION", "SUB_DIVISION", "GROUP", "FAMILY", "OCCUPATION"]),
        ),
        "title_en": Column(str, nullable=True),
        "source_id": Column(str, nullable=False),
    },
    strict=False,
    name="occupation_master",
)

vacancy_by_state_schema = DataFrameSchema(
    {
        "snapshot_date": Column(str, nullable=False),
        "lgd_code": Column(str, nullable=True),
        "geo_level": Column(str, Check.isin(["STATE", "NATIONAL"])),
        "state_name_as_source": Column(str, nullable=False),
        "vacancies_cumulative": Column("Int64", Check.ge(0), nullable=True),
        "unit": Column(str, Check.eq("count")),
        "measure_basis": Column(str, Check.eq("CUMULATIVE_SINCE_INCEPTION")),
        "is_pan_india_residual": Column(bool, nullable=False),
        "observed_or_estimated": Column(str, Check.isin(OBSERVED_VALUES)),
    },
    strict=False,
    name="fact_vacancy_official_by_state",
)

vacancy_by_sector_schema = DataFrameSchema(
    {
        "snapshot_date": Column(str, nullable=False),
        "ncs_sector_name": Column(str, nullable=False),
        "nic_section_code": Column(str, nullable=True),
        "vacancies_cumulative": Column(float, Check.ge(0), nullable=True),
        # Published in lakh. Recorded as published; never silently converted.
        "unit": Column(str, Check.eq("lakh")),
        "measure_basis": Column(str, Check.eq("CUMULATIVE_SINCE_INCEPTION")),
        "observed_or_estimated": Column(str, Check.isin(OBSERVED_VALUES)),
    },
    strict=False,
    name="fact_vacancy_official_by_sector",
)

establishment_district_schema = DataFrameSchema(
    {
        "snapshot_date": Column(str, nullable=False),
        "lgd_code": Column(str, nullable=False),
        "geo_level": Column(str, Check.eq("DISTRICT")),
        "enterprise_category": Column(str, Check.isin(["TOTAL", "SERVICES"])),
        "size_class": Column(str, Check.isin(["MICRO", "SMALL", "MEDIUM", "TOTAL"])),
        # Nullable on purpose: the source writes 'NA' and that is real missingness.
        "enterprise_count": Column("Int64", Check.ge(0), nullable=True),
        "unit": Column(str, Check.eq("count")),
        "measure_basis": Column(str, Check.eq("CUMULATIVE_REGISTRATIONS")),
        "observed_or_estimated": Column(str, Check.isin(OBSERVED_VALUES)),
    },
    strict=False,
    name="fact_establishment_district",
)

labour_force_estimate_schema = DataFrameSchema(
    {
        "period_id": Column(str, nullable=False),
        # PLFS monthly is all-India only. A STATE/DISTRICT row here would be a
        # statistically invalid claim, so the schema forbids it.
        "geo_level": Column(str, Check.eq("NATIONAL")),
        "lgd_code": Column(str, nullable=True),
        "area": Column(str, Check.isin(["RURAL", "URBAN", "RURAL_URBAN"])),
        "sex": Column(str, Check.isin(["MALE", "FEMALE", "PERSON"])),
        "indicator": Column(str, Check.isin(["LFPR", "WPR", "UR"])),
        "approach": Column(str, Check.eq("CWS")),
        "value_percent": Column(float, Check.in_range(0, 100), nullable=True),
        "unit": Column(str, Check.eq("percent")),
        "observed_or_estimated": Column(str, Check.eq("OBSERVED_SURVEY_ESTIMATE")),
    },
    strict=False,
    name="fact_labour_force_estimate",
)

# ----------------------------- analytical layer ----------------------------- #
# ESTIMATED is deliberately NOT an allowed value yet: the analytical layer must
# not contain estimates. Demand estimation is a separate, reviewed step.
ANALYTICAL_STATUS = ["OBSERVED", "SUPPORTING"]

analytical_state_demand_schema = DataFrameSchema(
    {
        "snapshot_date": Column(str, nullable=False),
        "state_name_as_source": Column(str, nullable=False),
        "lgd_code": Column(str, nullable=True),
        "geo_level": Column(str, Check.isin(["STATE", "NATIONAL"])),
        "vacancies_cumulative": Column("Int64", Check.ge(0), nullable=True),
        "share_of_published_total": Column(float, Check.in_range(0, 1), nullable=True),
        "n_source_documents": Column(int, Check.ge(1)),
        "flow_available": Column(bool, Check.eq(False)),
        "occupation_level": Column(str, Check.eq("NONE")),
        "observation_status": Column(str, Check.isin(ANALYTICAL_STATUS)),
        "source_vintage": Column(str, nullable=False),
        "transformation": Column(str, nullable=False),
    },
    strict=False,
    name="analytical_state_demand",
    unique=["snapshot_date", "state_name_as_source"],
)

analytical_district_structure_schema = DataFrameSchema(
    {
        "lgd_code": Column(str, nullable=False),
        "enterprise_category": Column(str, Check.isin(["TOTAL", "SERVICES"])),
        "total": Column("Int64", Check.ge(0), nullable=True),
        "medium": Column("Int64", Check.ge(0), nullable=True),
        "enterprise_share_within_state": Column(float, Check.in_range(0, 1), nullable=True),
        "not_a_demand_measure": Column(bool, Check.eq(True)),
        "observation_status": Column(str, Check.eq("SUPPORTING")),
        "source_vintage": Column(str, nullable=False),
    },
    strict=False,
    name="analytical_district_structure",
    unique=["snapshot_date", "lgd_code", "enterprise_category"],
)

analytical_district_occupation_structure_schema = DataFrameSchema(
    {
        "census_year": Column(int, Check.eq(2011)),
        "census_district_code": Column(str, nullable=False),
        "nco_2004_division": Column(str, nullable=False),
        "nco_2015_division": Column(str, nullable=True),
        "row_type": Column(str, Check.isin(["DIVISION_TOTAL", "UNCLASSIFIED"])),
        "main_workers": Column("Int64", Check.ge(0), nullable=True),
        "occupation_share_of_district": Column(float, Check.in_range(0, 1), nullable=True),
        "is_historical": Column(bool, Check.eq(True)),
        "not_a_demand_measure": Column(bool, Check.eq(True)),
        "occupation_scheme": Column(str, Check.eq("NCO_2004")),
        "observation_status": Column(str, Check.eq("SUPPORTING")),
    },
    strict=False,
    name="analytical_district_occupation_structure",
)

analytical_labour_market_context_schema = DataFrameSchema(
    {
        "geo_level": Column(str, Check.eq("NATIONAL")),
        "valid_geo_level": Column(str, Check.eq("NATIONAL")),
        "district_estimates_valid": Column(bool, Check.eq(False)),
        "not_a_demand_measure": Column(bool, Check.eq(True)),
        "observation_status": Column(str, Check.isin(ANALYTICAL_STATUS)),
    },
    strict=False,
    name="analytical_labour_market_context",
    unique=["period_id", "area", "sex", "age_group", "indicator"],
)

analytical_demand_by_industry_schema = DataFrameSchema(
    {
        "ncs_sector_name": Column(str, nullable=False),
        "nic_section_code": Column(str, nullable=True),
        "vacancies_cumulative": Column(float, Check.ge(0), nullable=True),
        "unit": Column(str, Check.eq("lakh")),
        "occupation_level": Column(str, Check.eq("NONE")),
        "industry_level": Column(str, Check.eq("NIC_SECTION")),
        "is_heterogeneous_or_residual": Column(bool, nullable=False),
        "observation_status": Column(str, Check.isin(ANALYTICAL_STATUS)),
    },
    strict=False,
    name="analytical_demand_by_industry",
    unique=["snapshot_date", "ncs_sector_name"],
)

# ------------------------------- supply layer -------------------------------- #
SUPPLY_MEASURES = ["ENROLLED", "TRAINED", "ASSESSED", "CERTIFIED", "PLACED"]

training_outcome_schema = DataFrameSchema(
    {
        "source_annexure": Column(str, nullable=False),
        "scheme": Column(str, nullable=False),
        "state_name_as_source": Column(str, nullable=False),
        "state_lgd_code": Column(str, nullable=True),
        "geo_level": Column(str, Check.eq("STATE")),
        "geography_status": Column(str, Check.isin(["MATCHED", "UNMATCHED"])),
        # The five concepts must stay distinct and fully enumerated.
        "measure": Column(str, Check.isin(SUPPLY_MEASURES)),
        "measure_definition": Column(str, nullable=False),
        # Nullable on purpose: the source prints '-' and that is NOT zero.
        "value": Column(float, Check.ge(0), nullable=True),
        "unit": Column(str, Check.eq("candidates")),
        "value_status": Column(str, Check.isin(["AVAILABLE", "NO_DATA"])),
        "observed_or_estimated": Column(str, Check.eq("OBSERVED")),
        "source_id": Column(str, nullable=False),
    },
    strict=False,
    name="fact_training_outcome",
    unique=["source_annexure", "state_name_as_source", "measure"],
)

training_infrastructure_schema = DataFrameSchema(
    {
        "as_on_date": Column(str, nullable=False),
        "state_name_as_source": Column(str, nullable=False),
        "geography_status": Column(str, Check.isin(["MATCHED", "UNMATCHED"])),
        "metric": Column(
            str,
            Check.isin(["DISTRICTS_IN_STATE", "DISTRICTS_WITH_PMKK",
                        "PMKK_ALLOCATED", "PMKK_ESTABLISHED"]),
        ),
        "value": Column(float, Check.ge(0), nullable=True),
        "unit": Column(str, Check.eq("count")),
        "observed_or_estimated": Column(str, Check.eq("OBSERVED")),
    },
    strict=False,
    name="fact_training_infrastructure",
    unique=["source_annexure", "state_name_as_source", "metric"],
)

training_trade_schema = DataFrameSchema(
    {
        "trade_id": Column(str, nullable=False),
        "trade_section_index": Column(int, Check.in_range(1, 3)),
        "trade_serial": Column(int, Check.ge(1)),
        "trade_name": Column(str, nullable=False),
        # No NCO code is published, so this must stay entirely NULL.
        "nco_2015_code": Column(str, nullable=True),
        "nco_mapping_status": Column(str, Check.eq("UNMAPPED_NO_OFFICIAL_MAPPING")),
        "observed_or_estimated": Column(str, Check.eq("OBSERVED")),
    },
    strict=False,
    name="dim_training_trade",
    unique=["trade_id"],
)

SCHEMAS: dict[str, DataFrameSchema] = {
    "location_master": location_master_schema,
    "occupation_master": occupation_master_schema,
    "fact_vacancy_official_by_state": vacancy_by_state_schema,
    "fact_vacancy_official_by_sector": vacancy_by_sector_schema,
    "fact_establishment_district": establishment_district_schema,
    "fact_labour_force_estimate": labour_force_estimate_schema,
    "analytical_state_demand": analytical_state_demand_schema,
    "analytical_demand_by_industry": analytical_demand_by_industry_schema,
    "analytical_district_structure": analytical_district_structure_schema,
    "analytical_district_occupation_structure": analytical_district_occupation_structure_schema,
    "analytical_labour_market_context": analytical_labour_market_context_schema,
    "fact_training_outcome": training_outcome_schema,
    "fact_training_infrastructure": training_infrastructure_schema,
    "dim_training_trade": training_trade_schema,
}


def validate(table: str, df):
    """Validate and return the frame. Raises pandera.errors.SchemaError on breach."""
    schema = SCHEMAS.get(table)
    return df if schema is None else schema.validate(df, lazy=False)
