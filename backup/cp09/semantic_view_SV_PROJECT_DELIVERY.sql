create or replace semantic view SV_PROJECT_DELIVERY
	tables (
		PROJECT as ACOCO_L2.ONTOLOGY.ENT_PROJECT primary key (PROJECT_ID) comment='Shared ontology entity PROJECT (ACOCO_L2.ONTOLOGY.ENT_PROJECT)',
		CUSTOMER as ACOCO_L2.ONTOLOGY.ENT_CUSTOMER primary key (CUSTOMER_ID) comment='Shared ontology entity CUSTOMER (ACOCO_L2.ONTOLOGY.ENT_CUSTOMER)',
		MD_GROUP as ACOCO_L2.ONTOLOGY.ENT_MD_GROUP primary key (MD_GROUP_ID) comment='Shared ontology entity MD_GROUP (ACOCO_L2.ONTOLOGY.ENT_MD_GROUP)',
		WORK_PACKAGE as ACOCO_L2.ONTOLOGY.ENT_WORK_PACKAGE primary key (WBS_ID) comment='Shared ontology entity WORK_PACKAGE (ACOCO_L2.ONTOLOGY.ENT_WORK_PACKAGE)',
		FISCAL_MONTH as ACOCO_L2.CORE.DT_FISCAL_MONTH primary key (MONTH_START) comment='Shared ontology entity FISCAL_MONTH (ACOCO_L2.CORE.DT_FISCAL_MONTH)',
		PERSON as ACOCO_L2.ONTOLOGY.ENT_PERSON primary key (PERSON_ID) comment='Shared ontology entity PERSON (ACOCO_L2.ONTOLOGY.ENT_PERSON)',
		ASSET as ACOCO_L2.ONTOLOGY.ENT_ASSET primary key (ASSET_ID) comment='Shared ontology entity ASSET (ACOCO_L2.ONTOLOGY.ENT_ASSET)',
		SKILL as ACOCO_L2.ONTOLOGY.ENT_SKILL primary key (SKILL_ID) comment='Shared ontology entity SKILL (ACOCO_L2.ONTOLOGY.ENT_SKILL)',
		SOURCE_PROJECT as ACOCO_L2.ONTOLOGY.ENT_PROJECT primary key (PROJECT_ID) comment='Shared ontology entity PROJECT (ACOCO_L2.ONTOLOGY.ENT_PROJECT) in the role source_project',
		PROJECT_MONTH as ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_MONTH_FINANCIALS comment='Fact PROJECT_DELIVERY.DT_PROJECT_MONTH_FINANCIALS',
		PROJECT_HEALTH as ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_HEALTH primary key (PROJECT_ID) comment='Fact PROJECT_DELIVERY.DT_PROJECT_HEALTH',
		PROJECT_TEAM as ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_TEAM comment='Fact PROJECT_DELIVERY.DT_PROJECT_TEAM',
		ASSET_USE as ACOCO_L2.ONTOLOGY.REL_ASSET_USE primary key (ASSET_USE_ID) comment='Fact ONTOLOGY.REL_ASSET_USE',
		ASSET_MATCH as ACOCO_L2.REASONING.VW_ASSET_MATCH comment='Fact REASONING.VW_ASSET_MATCH',
		WP_SKILL as ACOCO_L2.ONTOLOGY.REL_WP_SKILL comment='Fact ONTOLOGY.REL_WP_SKILL',
		ASSET_SKILL as ACOCO_L2.ONTOLOGY.REL_ASSET_SKILL comment='Fact ONTOLOGY.REL_ASSET_SKILL'
	)
	relationships (
		PROJECT_TO_CUSTOMER as PROJECT(CUSTOMER_ID) references CUSTOMER(CUSTOMER_ID),
		PROJECT_TO_MD_GROUP as PROJECT(MD_GROUP_ID) references MD_GROUP(MD_GROUP_ID),
		WORK_PACKAGE_TO_PROJECT as WORK_PACKAGE(PROJECT_ID) references PROJECT(PROJECT_ID),
		ASSET_TO_SOURCE_PROJECT as ASSET(SOURCE_PROJECT_ID) references SOURCE_PROJECT(PROJECT_ID),
		PROJECT_MONTH_TO_FISCAL_MONTH as PROJECT_MONTH(MONTH_START) references FISCAL_MONTH(MONTH_START),
		PROJECT_MONTH_TO_WORK_PACKAGE as PROJECT_MONTH(WBS_ID) references WORK_PACKAGE(WBS_ID),
		PROJECT_HEALTH_TO_PROJECT as PROJECT_HEALTH(PROJECT_ID) references PROJECT(PROJECT_ID),
		PROJECT_TEAM_TO_PERSON as PROJECT_TEAM(PERSON_ID) references PERSON(PERSON_ID),
		PROJECT_TEAM_TO_PROJECT as PROJECT_TEAM(PROJECT_ID) references PROJECT(PROJECT_ID),
		ASSET_USE_TO_ASSET as ASSET_USE(ASSET_ID) references ASSET(ASSET_ID),
		ASSET_USE_TO_PROJECT as ASSET_USE(PROJECT_ID) references PROJECT(PROJECT_ID),
		ASSET_MATCH_TO_ASSET as ASSET_MATCH(ASSET_ID) references ASSET(ASSET_ID),
		ASSET_MATCH_TO_WORK_PACKAGE as ASSET_MATCH(WBS_ID) references WORK_PACKAGE(WBS_ID),
		WP_SKILL_TO_SKILL as WP_SKILL(SKILL_ID) references SKILL(SKILL_ID),
		WP_SKILL_TO_WORK_PACKAGE as WP_SKILL(WBS_ID) references WORK_PACKAGE(WBS_ID),
		ASSET_SKILL_TO_ASSET as ASSET_SKILL(ASSET_ID) references ASSET(ASSET_ID),
		ASSET_SKILL_TO_SKILL as ASSET_SKILL(SKILL_ID) references SKILL(SKILL_ID)
	)
	facts (
		PROJECT_MONTH.REVENUE as REVENUE comment='Revenue USD',
		PROJECT_MONTH.TOTAL_COST as TOTAL_COST comment='Total cost USD',
		PROJECT_MONTH.MARGIN as MARGIN comment='Margin USD',
		PROJECT_MONTH.AGENT_COST as AGENT_COST comment='AI-agent cost USD',
		PROJECT_MONTH.AGENT_HOURS as AGENT_HOURS comment='AI-agent hours',
		PROJECT_MONTH.DELIVERY_HOURS as DELIVERY_HOURS comment='Delivery hours',
		PROJECT_MONTH.EARNED_HOURS as EARNED_HOURS comment='Earned hours',
		PROJECT_HEALTH.PROJECT_KEY as PROJECT_ID comment='Project',
		PROJECT_HEALTH.EARNED_VALUE_TD as EARNED_VALUE_TD comment='Earned value to date',
		PROJECT_HEALTH.ACTUAL_COST_TD as ACTUAL_COST_TD comment='Actual cost to date',
		PROJECT_HEALTH.PLANNED_VALUE_TD as PLANNED_VALUE_TD comment='Planned value to date',
		PROJECT_HEALTH.CONTRACT_VALUE as CONTRACT_VALUE comment='Contract value',
		PROJECT_HEALTH.EAC as EAC comment='Estimate at completion',
		PROJECT_HEALTH.LD_EXPOSURE as LD_EXPOSURE comment='LD exposure',
		PROJECT_HEALTH.REUSED_ASSET as REUSED_ASSET comment='Reused >= 1 asset',
		PROJECT_HEALTH.FORECAST_SLIP_WEEKS as FORECAST_SLIP_WEEKS comment='Forecast slip in weeks',
		PROJECT_TEAM.DELIVERY_HOURS as DELIVERY_HOURS comment='Delivery hours on the project',
		ASSET_USE.HOURS_SAVED_ESTIMATED as HOURS_SAVED_ESTIMATED comment='ESTIMATED hours saved',
		ASSET_USE.USES as 1 comment='One recorded use',
		ASSET_MATCH.SIMILARITY as SIMILARITY comment='Semantic similarity of the work package need and the asset',
		ASSET_MATCH.EFFORT_SAVING_HOURS as EFFORT_SAVING_HOURS comment='Catalogued effort saving (ESTIMATED)',
		WP_SKILL.REQUIRED_PROFICIENCY as REQUIRED_PROFICIENCY comment='Required proficiency'
	)
	dimensions (
		PROJECT.PROJECT_ID as PROJECT_ID with synonyms=('project','engagement') comment='Customer project (S/4 project / WBS)',
		PROJECT.SIZE_CLASS as SIZE_CLASS with synonyms=('size') comment='Project size class (XX-Small .. Large)',
		PROJECT.WORK_TYPE as WORK_TYPE with synonyms=('service line') comment='Type of work (Data Migration, AI Engineering, ...)',
		PROJECT.CONTRACT_TYPE as CONTRACT_TYPE with synonyms=('pricing') comment='FIXED_PRICE or TIME_AND_MATERIALS',
		PROJECT.DELIVERY_MODEL as DELIVERY_MODEL with synonyms=('AI delivery model') comment='HUMAN, HUMAN_AGENT (people + agents) or AGENT_LED',
		PROJECT.PROJECT_STATUS as STATUS_AS_OF with synonyms=('status') comment='ACTIVE / CLOSED / NOT_STARTED at the as-of date',
		PROJECT.IS_STORY_PROJECT as IS_STORY_PROJECT comment='The seeded at-risk FS fixed-price project',
		CUSTOMER.CUSTOMER_ID as CUSTOMER_ID comment='Customer account id',
		CUSTOMER.CUSTOMER_NAME as CUSTOMER_NAME with synonyms=('client','account') comment='Customer account name',
		MD_GROUP.MD_GROUP_ID as MD_GROUP_ID with synonyms=('group code') comment='MD group code (FS, CMT, HPS, PRD, RES, XAI)',
		MD_GROUP.MD_GROUP as MD_GROUP_NAME with synonyms=('group','industry group','practice') comment='MD group name, e.g. Financial Services',
		MD_GROUP.MANAGING_DIRECTOR as MANAGING_DIRECTOR_NAME with synonyms=('MD name','partner') comment='Managing Director of the group',
		WORK_PACKAGE.WBS_ID as WBS_ID with synonyms=('work package','WBS') comment='Work package (WBS element)',
		WORK_PACKAGE.IS_CRITICAL_PATH as IS_CRITICAL_PATH comment='On the project''s critical path',
		FISCAL_MONTH.FISCAL_YEAR as FISCAL_YEAR with synonyms=('FY','year') comment='ACoCo fiscal year (Oct-Sep, V9); FY26 = Oct 2025 - Sep 2026',
		FISCAL_MONTH.FISCAL_PERIOD as FISCAL_PERIOD with synonyms=('period') comment='Fiscal period 1-12 (1 = October)',
		FISCAL_MONTH.FISCAL_QUARTER as FISCAL_QUARTER with synonyms=('quarter') comment='Fiscal quarter 1-4 (1 = Oct-Dec)',
		FISCAL_MONTH.MONTH_LABEL as MONTH_LABEL with synonyms=('month') comment='Calendar month label, e.g. SEP 2026',
		FISCAL_MONTH.MONTH_START as MONTH_START comment='First day of the fiscal month (join key)',
		PERSON.PERSON_ID as PERSON_ID with synonyms=('employee id','user id') comment='People Intelligence userId',
		PERSON.PERSON_NAME as DISPLAY_NAME with synonyms=('name','employee','consultant') comment='Person''s display name',
		PERSON.PERSON_LEVEL as LEVEL with synonyms=('level','grade','rank') comment='Career level at the as-of date (Analyst .. Principal)',
		PERSON.BILL_CODE as BILL_CODE with synonyms=('billing code') comment='Bill code 30-79 within the level band (higher = more senior, more bid time)',
		PERSON.IS_ACTIVE as IS_ACTIVE_AS_OF with synonyms=('active','current employee') comment='Employed on the as-of date (1 Oct 2026)',
		PERSON.IS_MANAGING_DIRECTOR as IS_MANAGING_DIRECTOR with synonyms=('MD') comment='Holds the Managing Director role for a group',
		PERSON.PERSON_SOURCE as SOURCE_SYSTEM comment='BDC_CLD = real People Intelligence person; SIMULATED = simulated pool',
		ASSET.ASSET_ID as ASSET_ID comment='Reusable delivery asset',
		ASSET.ASSET_TITLE as ASSET_TITLE with synonyms=('accelerator','template') comment='Asset title',
		ASSET.ASSET_TYPE as ASSET_TYPE comment='Accelerator, code template, test pack ...',
		ASSET.ASSET_WORK_TYPE as WORK_TYPE comment='Work type the asset serves',
		SKILL.SKILL_ID as SKILL_ID comment='Skill code',
		SKILL.SKILL_NAME as SKILL_NAME with synonyms=('skill','capability') comment='Skill name',
		SKILL.SKILL_FAMILY as SKILL_FAMILY with synonyms=('skill category') comment='AGENTIC_AI, TECHNICAL or INDUSTRY',
		SOURCE_PROJECT.SOURCE_PROJECT_PROJECT_ID as PROJECT_ID comment='Customer project (S/4 project / WBS)',
		SOURCE_PROJECT.SOURCE_PROJECT_SIZE_CLASS as SIZE_CLASS comment='Project size class (XX-Small .. Large)',
		SOURCE_PROJECT.SOURCE_PROJECT_WORK_TYPE as WORK_TYPE comment='Type of work (Data Migration, AI Engineering, ...)',
		SOURCE_PROJECT.SOURCE_PROJECT_CONTRACT_TYPE as CONTRACT_TYPE comment='FIXED_PRICE or TIME_AND_MATERIALS',
		SOURCE_PROJECT.SOURCE_PROJECT_DELIVERY_MODEL as DELIVERY_MODEL comment='HUMAN, HUMAN_AGENT (people + agents) or AGENT_LED',
		SOURCE_PROJECT.SOURCE_PROJECT_PROJECT_STATUS as STATUS_AS_OF comment='ACTIVE / CLOSED / NOT_STARTED at the as-of date',
		SOURCE_PROJECT.SOURCE_PROJECT_IS_STORY_PROJECT as IS_STORY_PROJECT comment='The seeded at-risk FS fixed-price project',
		ASSET_MATCH.REUSE_STATUS as REUSE_STATUS comment='REUSED or MISSED',
		ASSET_MATCH.SAME_WORK_TYPE as SAME_WORK_TYPE comment='Asset built for the same work type'
	)
	metrics (
		PROJECT_MONTH.TOTAL_REVENUE as SUM(revenue) with synonyms=('sales','fees') comment='Recognised revenue (USD, S/4 journal GL 0041000000)',
		PROJECT_MONTH.TOTAL_TOTAL_COST as SUM(total_cost) with synonyms=('cost') comment='People + AI-agent + 35 % overhead cost (USD)',
		PROJECT_MONTH.TOTAL_MARGIN as SUM(margin) with synonyms=('profit') comment='Revenue minus total cost (USD)',
		PROJECT_MONTH.MARGIN_PCT as 100 * SUM(margin) / NULLIF(SUM(revenue), 0) with synonyms=('profit margin') comment='Margin as % of revenue',
		PROJECT_MONTH.TOTAL_AGENT_COST as SUM(agent_cost) with synonyms=('AI cost') comment='AI-agent cost charged to projects (S/4 AGT_* allocations, USD)',
		PROJECT_MONTH.TOTAL_AGENT_HOURS as SUM(agent_hours) comment='AI-agent hours charged to projects',
		PROJECT_MONTH.PRODUCTIVITY_INDEX as SUM(earned_hours) / NULLIF(SUM(delivery_hours), 0) with synonyms=('productivity') comment='Earned hours / actual delivery hours (> 1 = faster than plan)',
		PROJECT_HEALTH.TOTAL_CPI as SUM(earned_value_td) / NULLIF(SUM(actual_cost_td), 0) with synonyms=('cost performance') comment='Cost performance index = earned value / actual cost (< 1 = over budget)',
		PROJECT_HEALTH.TOTAL_SPI as SUM(earned_value_td) / NULLIF(SUM(planned_value_td), 0) with synonyms=('schedule performance') comment='Schedule performance index = earned value / planned value (< 1 = late)',
		PROJECT_HEALTH.TOTAL_FORECAST_MARGIN_PCT as 100 * (SUM(contract_value) - SUM(eac) - SUM(ld_exposure)) / NULLIF(SUM(contract_value), 0) with synonyms=('forecast profitability') comment='(Contract - EAC - LD exposure) / contract',
		PROJECT_HEALTH.TOTAL_LD_EXPOSURE as SUM(ld_exposure) with synonyms=('penalties') comment='Liquidated damages exposure on late fixed-price projects (USD)',
		PROJECT_HEALTH.TOTAL_EAC as SUM(eac) comment='Estimate at completion = sold cost / CPI (USD)',
		PROJECT_HEALTH.PROJECT_COUNT as COUNT(DISTINCT project_key) with synonyms=('projects') comment='Number of projects',
		PROJECT_HEALTH.ASSET_REUSE_RATE_PCT as 100 * AVG(IFF(reused_asset, 1, 0)) with synonyms=('reuse rate') comment='Projects with >= 1 recorded asset use / projects',
		PROJECT_TEAM.TEAM_DELIVERY_HOURS as SUM(delivery_hours) comment='Delivery hours booked by the person on the project',
		ASSET_USE.TOTAL_HOURS_SAVED_ESTIMATED as SUM(hours_saved_estimated) comment='ESTIMATED hours saved by asset reuse (catalogued saving per use)',
		ASSET_USE.ASSET_USES as SUM(uses) comment='Recorded asset uses',
		ASSET_MATCH.MISSED_REUSE_HOURS as SUM(IFF(reuse_status = 'MISSED', effort_saving_hours, 0)) comment='ESTIMATED hours a matching asset would have saved but was not reused'
	)
	comment='Operational Excellence pillar: project P&L, earned value (CPI, SPI, EAC), liquidated-damages exposure, forecast margin, teams, asset reuse and the skills work packages need.'
	ai_sql_generation 'Fiscal years run October to September (FY26 = Oct 2025 - Sep 2026); the as-of date is 1 Oct 2026, so FY26 is the last closed year. Percentages are 0-100. Filter MD groups by md_group name (e.g. ''Financial Services'').'
	ai_verified_queries (
		VQ_1 AS ( 
QUESTION 'Which active Financial Services projects have a negative forecast margin?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION true
SQL 'SELECT h.PROJECT_ID, h.SIZE_CLASS, h.CONTRACT_TYPE, ROUND(h.CPI, 2) AS CPI, ROUND(h.SPI, 2) AS SPI, ROUND(100 * h.FORECAST_MARGIN_PCT, 1) AS FORECAST_MARGIN_PCT, ROUND(h.LD_EXPOSURE, 0) AS LD_EXPOSURE FROM ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_HEALTH h JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = h.MD_GROUP_ID WHERE g.MD_GROUP_NAME = ''Financial Services'' AND h.STATUS_AS_OF = ''ACTIVE'' AND h.FORECAST_MARGIN_PCT < 0 ORDER BY h.FORECAST_MARGIN_PCT'),
		VQ_2 AS ( 
QUESTION 'What was FY26 margin % by delivery model?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION false
SQL 'SELECT p.DELIVERY_MODEL, ROUND(100 * SUM(m.MARGIN) / SUM(m.REVENUE), 1) AS MARGIN_PCT
FROM ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_MONTH_FINANCIALS m
JOIN ACOCO_L2.ONTOLOGY.ENT_WORK_PACKAGE w ON w.WBS_ID = m.WBS_ID
JOIN ACOCO_L2.ONTOLOGY.ENT_PROJECT p ON p.PROJECT_ID = w.PROJECT_ID
JOIN ACOCO_L2.CORE.DT_FISCAL_MONTH f ON f.MONTH_START = m.MONTH_START
WHERE f.FISCAL_YEAR = 2026 GROUP BY p.DELIVERY_MODEL ORDER BY MARGIN_PCT DESC')
	)
	with extension (CA='{"tables":[{"name":"project","dimensions":[{"name":"project_id"},{"name":"size_class"},{"name":"work_type"},{"name":"contract_type"},{"name":"delivery_model"},{"name":"project_status"},{"name":"is_story_project"}]},{"name":"customer","dimensions":[{"name":"customer_id"},{"name":"customer_name"}]},{"name":"md_group","dimensions":[{"name":"md_group_id"},{"name":"md_group"},{"name":"managing_director"}]},{"name":"work_package","dimensions":[{"name":"wbs_id"},{"name":"is_critical_path"}]},{"name":"fiscal_month","dimensions":[{"name":"fiscal_year"},{"name":"fiscal_period"},{"name":"fiscal_quarter"},{"name":"month_label"}],"time_dimensions":[{"name":"month_start"}]},{"name":"person","dimensions":[{"name":"person_id"},{"name":"person_name"},{"name":"person_level"},{"name":"bill_code"},{"name":"is_active"},{"name":"is_managing_director"},{"name":"person_source"}]},{"name":"asset","dimensions":[{"name":"asset_id"},{"name":"asset_title"},{"name":"asset_type"},{"name":"asset_work_type"}]},{"name":"skill","dimensions":[{"name":"skill_id"},{"name":"skill_name"},{"name":"skill_family"}]},{"name":"source_project","dimensions":[{"name":"source_project_project_id"},{"name":"source_project_size_class"},{"name":"source_project_work_type"},{"name":"source_project_contract_type"},{"name":"source_project_delivery_model"},{"name":"source_project_project_status"},{"name":"source_project_is_story_project"}]},{"name":"project_month","facts":[{"name":"revenue"},{"name":"total_cost"},{"name":"margin"},{"name":"agent_cost"},{"name":"agent_hours"},{"name":"delivery_hours"},{"name":"earned_hours"}],"metrics":[{"name":"total_revenue"},{"name":"total_total_cost"},{"name":"total_margin"},{"name":"margin_pct"},{"name":"total_agent_cost"},{"name":"total_agent_hours"},{"name":"productivity_index"}]},{"name":"project_health","facts":[{"name":"project_key"},{"name":"earned_value_td"},{"name":"actual_cost_td"},{"name":"planned_value_td"},{"name":"contract_value"},{"name":"eac"},{"name":"ld_exposure"},{"name":"reused_asset"},{"name":"forecast_slip_weeks"}],"metrics":[{"name":"total_cpi"},{"name":"total_spi"},{"name":"total_forecast_margin_pct"},{"name":"total_ld_exposure"},{"name":"total_eac"},{"name":"project_count"},{"name":"asset_reuse_rate_pct"}]},{"name":"project_team","facts":[{"name":"delivery_hours"}],"metrics":[{"name":"team_delivery_hours"}]},{"name":"asset_use","facts":[{"name":"hours_saved_estimated"},{"name":"uses"}],"metrics":[{"name":"total_hours_saved_estimated"},{"name":"asset_uses"}]},{"name":"asset_match","dimensions":[{"name":"reuse_status"},{"name":"same_work_type"}],"facts":[{"name":"similarity"},{"name":"effort_saving_hours"}],"metrics":[{"name":"missed_reuse_hours"}]},{"name":"wp_skill","facts":[{"name":"required_proficiency"}]},{"name":"asset_skill"}],"relationships":[{"name":"project_month_to_work_package","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"project_month_to_fiscal_month","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"project_health_to_project","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"project_team_to_project","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"project_team_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"asset_use_to_asset","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"asset_use_to_project","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"asset_match_to_work_package","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"asset_match_to_asset","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"wp_skill_to_work_package","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"wp_skill_to_skill","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"asset_skill_to_asset","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"asset_skill_to_skill","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"project_to_customer","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"project_to_md_group","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"work_package_to_project","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"asset_to_source_project","relationship_type":"many_to_one","join_type":"left_outer"}]}');;
