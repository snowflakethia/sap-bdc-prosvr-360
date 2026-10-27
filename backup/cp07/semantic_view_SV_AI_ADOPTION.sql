create or replace semantic view SV_AI_ADOPTION
	tables (
		PERSON as ACOCO_L2.ONTOLOGY.ENT_PERSON primary key (PERSON_ID) comment='Shared ontology entity PERSON (ACOCO_L2.ONTOLOGY.ENT_PERSON)',
		MD_GROUP as ACOCO_L2.ONTOLOGY.ENT_MD_GROUP primary key (MD_GROUP_ID) comment='Shared ontology entity MD_GROUP (ACOCO_L2.ONTOLOGY.ENT_MD_GROUP)',
		AI_TOOL as ACOCO_L2.ONTOLOGY.ENT_AI_TOOL primary key (AI_TOOL_ID) comment='Shared ontology entity AI_TOOL (ACOCO_L2.ONTOLOGY.ENT_AI_TOOL)',
		PROJECT as ACOCO_L2.ONTOLOGY.ENT_PROJECT primary key (PROJECT_ID) comment='Shared ontology entity PROJECT (ACOCO_L2.ONTOLOGY.ENT_PROJECT)',
		LEARNING_ITEM as ACOCO_L2.ONTOLOGY.ENT_LEARNING_ITEM primary key (LEARNING_ITEM_ID) comment='Shared ontology entity LEARNING_ITEM (ACOCO_L2.ONTOLOGY.ENT_LEARNING_ITEM)',
		SKILL as ACOCO_L2.ONTOLOGY.ENT_SKILL primary key (SKILL_ID) comment='Shared ontology entity SKILL (ACOCO_L2.ONTOLOGY.ENT_SKILL)',
		FISCAL_MONTH as ACOCO_L2.CORE.DT_FISCAL_MONTH primary key (MONTH_START) comment='Shared ontology entity FISCAL_MONTH (ACOCO_L2.CORE.DT_FISCAL_MONTH)',
		AI_USAGE as ACOCO_L2.AI_ADOPTION.DT_AI_USAGE_DAILY comment='Fact AI_ADOPTION.DT_AI_USAGE_DAILY',
		AGENT_ON_PROJECT as ACOCO_L2.AI_ADOPTION.DT_AI_AGENT_PROJECT_MONTH primary key (AGENT_PROJECT_MONTH_ID) comment='Fact AI_ADOPTION.DT_AI_AGENT_PROJECT_MONTH',
		AI_PRODUCTIVITY as ACOCO_L2.AI_ADOPTION.DT_AI_PRODUCTIVITY comment='Fact AI_ADOPTION.DT_AI_PRODUCTIVITY',
		LEARNING_EPISODE as ACOCO_L2.AI_ADOPTION.DT_LEARNING_PAYBACK comment='Fact AI_ADOPTION.DT_LEARNING_PAYBACK'
	)
	relationships (
		PERSON_TO_MD_GROUP as PERSON(MD_GROUP_ID) references MD_GROUP(MD_GROUP_ID),
		LEARNING_ITEM_TO_SKILL as LEARNING_ITEM(TARGET_SKILL_ID) references SKILL(SKILL_ID),
		AI_USAGE_TO_AI_TOOL as AI_USAGE(AI_TOOL_ID) references AI_TOOL(AI_TOOL_ID),
		AI_USAGE_TO_PERSON as AI_USAGE(PERSON_ID) references PERSON(PERSON_ID),
		AGENT_ON_PROJECT_TO_AI_TOOL as AGENT_ON_PROJECT(AI_TOOL_ID) references AI_TOOL(AI_TOOL_ID),
		AGENT_ON_PROJECT_TO_FISCAL_MONTH as AGENT_ON_PROJECT(MONTH_START) references FISCAL_MONTH(MONTH_START),
		AGENT_ON_PROJECT_TO_PROJECT as AGENT_ON_PROJECT(PROJECT_ID) references PROJECT(PROJECT_ID),
		AI_PRODUCTIVITY_TO_FISCAL_MONTH as AI_PRODUCTIVITY(QUARTER_START) references FISCAL_MONTH(MONTH_START),
		AI_PRODUCTIVITY_TO_PERSON as AI_PRODUCTIVITY(PERSON_ID) references PERSON(PERSON_ID),
		LEARNING_EPISODE_TO_FISCAL_MONTH as LEARNING_EPISODE(COMPLETION_MONTH) references FISCAL_MONTH(MONTH_START),
		LEARNING_EPISODE_TO_LEARNING_ITEM as LEARNING_EPISODE(LEARNING_ITEM_ID) references LEARNING_ITEM(LEARNING_ITEM_ID),
		LEARNING_EPISODE_TO_PERSON as LEARNING_EPISODE(PERSON_ID) references PERSON(PERSON_ID)
	)
	facts (
		AI_USAGE.COST_USD as COST_USD comment='Spend USD',
		AI_USAGE.SESSIONS as SESSIONS comment='Sessions',
		AGENT_ON_PROJECT.AGENT_COST as AGENT_COST comment='Agent cost USD',
		AGENT_ON_PROJECT.AGENT_HOURS as AGENT_HOURS comment='Agent hours',
		AI_PRODUCTIVITY.PERSON_KEY as PERSON_ID comment='Person',
		AI_PRODUCTIVITY.AI_ACTIVE as AI_ACTIVE comment='AI-active in the quarter',
		AI_PRODUCTIVITY.AI_SKILLED_INACTIVE as AI_SKILLED_INACTIVE comment='AI-skilled but no use',
		AI_PRODUCTIVITY.EARNED_HOURS as EARNED_HOURS comment='Earned hours',
		AI_PRODUCTIVITY.DELIVERY_HOURS as DELIVERY_HOURS comment='Delivery hours',
		LEARNING_EPISODE.PAYBACK as PAYBACK comment='Productivity payback',
		LEARNING_EPISODE.HOURS_SAVED as HOURS_SAVED comment='Hours saved'
	)
	dimensions (
		PERSON.PERSON_ID as PERSON_ID with synonyms=('employee id','user id') comment='People Intelligence userId',
		PERSON.PERSON_NAME as DISPLAY_NAME with synonyms=('name','employee','consultant') comment='Person''s display name',
		PERSON.PERSON_LEVEL as LEVEL with synonyms=('level','grade','rank') comment='Career level at the as-of date (Analyst .. Principal)',
		PERSON.BILL_CODE as BILL_CODE with synonyms=('billing code') comment='Bill code 30-79 within the level band (higher = more senior, more bid time)',
		PERSON.IS_ACTIVE as IS_ACTIVE_AS_OF with synonyms=('active','current employee') comment='Employed on the as-of date (1 Oct 2026)',
		PERSON.IS_MANAGING_DIRECTOR as IS_MANAGING_DIRECTOR with synonyms=('MD') comment='Holds the Managing Director role for a group',
		PERSON.PERSON_SOURCE as SOURCE_SYSTEM comment='BDC_CLD = real People Intelligence person; SIMULATED = simulated pool',
		MD_GROUP.MD_GROUP_ID as MD_GROUP_ID with synonyms=('group code') comment='MD group code (FS, CMT, HPS, PRD, RES, XAI)',
		MD_GROUP.MD_GROUP as MD_GROUP_NAME with synonyms=('group','industry group','practice') comment='MD group name, e.g. Financial Services',
		MD_GROUP.MANAGING_DIRECTOR as MANAGING_DIRECTOR_NAME with synonyms=('MD name','partner') comment='Managing Director of the group',
		AI_TOOL.AI_TOOL_ID as AI_TOOL_ID comment='AI assistant (OPENAI, ANTHROPIC, CORTEX) or S/4 agent activity type (AGT_*)',
		AI_TOOL.AI_TOOL_NAME as AI_TOOL_NAME with synonyms=('AI tool','assistant','agent') comment='AI tool / agent name',
		AI_TOOL.TOOL_KIND as TOOL_KIND comment='ASSISTANT (people use it) or AGENT (charged to projects)',
		PROJECT.PROJECT_ID as PROJECT_ID with synonyms=('project','engagement') comment='Customer project (S/4 project / WBS)',
		PROJECT.SIZE_CLASS as SIZE_CLASS with synonyms=('size') comment='Project size class (XX-Small .. Large)',
		PROJECT.WORK_TYPE as WORK_TYPE with synonyms=('service line') comment='Type of work (Data Migration, AI Engineering, ...)',
		PROJECT.CONTRACT_TYPE as CONTRACT_TYPE with synonyms=('pricing') comment='FIXED_PRICE or TIME_AND_MATERIALS',
		PROJECT.DELIVERY_MODEL as DELIVERY_MODEL with synonyms=('AI delivery model') comment='HUMAN, HUMAN_AGENT (people + agents) or AGENT_LED',
		PROJECT.PROJECT_STATUS as STATUS_AS_OF with synonyms=('status') comment='ACTIVE / CLOSED / NOT_STARTED at the as-of date',
		PROJECT.IS_STORY_PROJECT as IS_STORY_PROJECT comment='The seeded at-risk FS fixed-price project',
		LEARNING_ITEM.LEARNING_ITEM_ID as LEARNING_ITEM_ID with synonyms=('course') comment='Learning item',
		LEARNING_ITEM.LEARNING_ITEM_TITLE as LEARNING_ITEM_TITLE with synonyms=('course name') comment='Learning item title',
		LEARNING_ITEM.CURRICULUM as CURRICULUM with synonyms=('learning path') comment='AGENTIC_AI or CORE curriculum',
		SKILL.SKILL_ID as SKILL_ID comment='Skill code',
		SKILL.SKILL_NAME as SKILL_NAME with synonyms=('skill','capability') comment='Skill name',
		SKILL.SKILL_FAMILY as SKILL_FAMILY with synonyms=('skill category') comment='AGENTIC_AI, TECHNICAL or INDUSTRY',
		FISCAL_MONTH.FISCAL_YEAR as FISCAL_YEAR with synonyms=('FY','year') comment='ACoCo fiscal year (Oct-Sep, V9); FY26 = Oct 2025 - Sep 2026',
		FISCAL_MONTH.FISCAL_PERIOD as FISCAL_PERIOD with synonyms=('period') comment='Fiscal period 1-12 (1 = October)',
		FISCAL_MONTH.FISCAL_QUARTER as FISCAL_QUARTER with synonyms=('quarter') comment='Fiscal quarter 1-4 (1 = Oct-Dec)',
		FISCAL_MONTH.MONTH_LABEL as MONTH_LABEL with synonyms=('month') comment='Calendar month label, e.g. SEP 2026',
		FISCAL_MONTH.MONTH_START as MONTH_START comment='First day of the fiscal month (join key)',
		AI_USAGE.USAGE_DATE as USAGE_DATE comment='Usage date',
		AI_PRODUCTIVITY.PRODUCTIVITY_WORK_TYPE as WORK_TYPE comment='Work type of the delivery'
	)
	metrics (
		AI_USAGE.AI_COST_USD as SUM(cost_usd) with synonyms=('AI spend') comment='AI assistant spend (USD)',
		AI_USAGE.AI_SESSIONS as SUM(sessions) comment='AI assistant sessions',
		AGENT_ON_PROJECT.TOTAL_AGENT_COST as SUM(agent_cost) with synonyms=('AI cost') comment='AI-agent cost charged to projects (S/4 AGT_* allocations, USD)',
		AGENT_ON_PROJECT.TOTAL_AGENT_HOURS as SUM(agent_hours) comment='AI-agent hours charged to projects',
		AI_PRODUCTIVITY.AI_ACTIVE_PEOPLE as COUNT(DISTINCT IFF(ai_active, person_key, NULL)) comment='People AI-active in the quarter (AI-skill >= 3 and use on >= 50 % of working days)',
		AI_PRODUCTIVITY.AI_SKILLED_INACTIVE_PEOPLE as COUNT(DISTINCT IFF(ai_skilled_inactive, person_key, NULL)) comment='People with AI-skill >= 3 and no AI use in the quarter',
		AI_PRODUCTIVITY.PI_AI_ACTIVE as SUM(IFF(ai_active, earned_hours, 0)) / NULLIF(SUM(IFF(ai_active, delivery_hours, 0)), 0) comment='Productivity index of AI-active people (unstratified)',
		AI_PRODUCTIVITY.PI_NOT_AI_ACTIVE as SUM(IFF(NOT ai_active, earned_hours, 0)) / NULLIF(SUM(IFF(NOT ai_active, delivery_hours, 0)), 0) comment='Productivity index of everyone else (unstratified; the stratified test is VW_AI_PRODUCTIVITY_TEST)',
		LEARNING_EPISODE.LEARNING_PAYBACK as AVG(payback) with synonyms=('learning ROI') comment='Productivity change after vs before a learning episode minus the matched comparison change',
		LEARNING_EPISODE.LEARNING_HOURS_SAVED as SUM(hours_saved) comment='Hours saved by learning payback'
	)
	comment='People Development pillar (AI): AI tool use and spend, agent cost on projects, AI-active vs other productivity, and learning payback. The stratified, confidence-tested results are in SERVING.VW_AI_PRODUCTIVITY_TEST.'
	ai_sql_generation 'Fiscal years run October to September (FY26 = Oct 2025 - Sep 2026); the as-of date is 1 Oct 2026, so FY26 is the last closed year. Percentages are 0-100. Filter MD groups by md_group name (e.g. ''Financial Services'').'
	ai_verified_queries (
		VQ_1 AS ( 
QUESTION 'What is FY26 AI assistant spend by tool?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION true
SQL 'SELECT t.AI_TOOL_NAME, ROUND(SUM(u.COST_USD), 0) AS AI_COST_USD
FROM ACOCO_L2.AI_ADOPTION.DT_AI_USAGE_DAILY u JOIN ACOCO_L2.ONTOLOGY.ENT_AI_TOOL t ON t.AI_TOOL_ID = u.AI_TOOL_ID
WHERE u.USAGE_DATE BETWEEN ''2025-10-01'' AND ''2026-09-30'' GROUP BY t.AI_TOOL_NAME ORDER BY AI_COST_USD DESC'),
		VQ_2 AS ( 
QUESTION 'What is the average learning payback by curriculum?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION false
SQL 'SELECT li.CURRICULUM, ROUND(AVG(l.PAYBACK), 4) AS LEARNING_PAYBACK
FROM ACOCO_L2.AI_ADOPTION.DT_LEARNING_PAYBACK l JOIN ACOCO_L2.ONTOLOGY.ENT_LEARNING_ITEM li ON li.LEARNING_ITEM_ID = l.LEARNING_ITEM_ID
GROUP BY li.CURRICULUM ORDER BY li.CURRICULUM')
	)
	with extension (CA='{"tables":[{"name":"person","dimensions":[{"name":"person_id"},{"name":"person_name"},{"name":"person_level"},{"name":"bill_code"},{"name":"is_active"},{"name":"is_managing_director"},{"name":"person_source"}]},{"name":"md_group","dimensions":[{"name":"md_group_id"},{"name":"md_group"},{"name":"managing_director"}]},{"name":"ai_tool","dimensions":[{"name":"ai_tool_id"},{"name":"ai_tool_name"},{"name":"tool_kind"}]},{"name":"project","dimensions":[{"name":"project_id"},{"name":"size_class"},{"name":"work_type"},{"name":"contract_type"},{"name":"delivery_model"},{"name":"project_status"},{"name":"is_story_project"}]},{"name":"learning_item","dimensions":[{"name":"learning_item_id"},{"name":"learning_item_title"},{"name":"curriculum"}]},{"name":"skill","dimensions":[{"name":"skill_id"},{"name":"skill_name"},{"name":"skill_family"}]},{"name":"fiscal_month","dimensions":[{"name":"fiscal_year"},{"name":"fiscal_period"},{"name":"fiscal_quarter"},{"name":"month_label"}],"time_dimensions":[{"name":"month_start"}]},{"name":"ai_usage","facts":[{"name":"cost_usd"},{"name":"sessions"}],"metrics":[{"name":"ai_cost_usd"},{"name":"ai_sessions"}],"time_dimensions":[{"name":"usage_date"}]},{"name":"agent_on_project","facts":[{"name":"agent_cost"},{"name":"agent_hours"}],"metrics":[{"name":"total_agent_cost"},{"name":"total_agent_hours"}]},{"name":"ai_productivity","dimensions":[{"name":"productivity_work_type"}],"facts":[{"name":"person_key"},{"name":"ai_active"},{"name":"ai_skilled_inactive"},{"name":"earned_hours"},{"name":"delivery_hours"}],"metrics":[{"name":"ai_active_people"},{"name":"ai_skilled_inactive_people"},{"name":"pi_ai_active"},{"name":"pi_not_ai_active"}]},{"name":"learning_episode","facts":[{"name":"payback"},{"name":"hours_saved"}],"metrics":[{"name":"learning_payback"},{"name":"learning_hours_saved"}]}],"relationships":[{"name":"ai_usage_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"ai_usage_to_ai_tool","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"agent_on_project_to_project","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"agent_on_project_to_ai_tool","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"agent_on_project_to_fiscal_month","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"ai_productivity_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"ai_productivity_to_fiscal_month","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"learning_episode_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"learning_episode_to_learning_item","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"learning_episode_to_fiscal_month","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"person_to_md_group","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"learning_item_to_skill","relationship_type":"many_to_one","join_type":"left_outer"}]}');;
