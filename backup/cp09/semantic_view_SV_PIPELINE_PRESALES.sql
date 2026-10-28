create or replace semantic view SV_PIPELINE_PRESALES
	tables (
		OPPORTUNITY as ACOCO_L2.ONTOLOGY.ENT_OPPORTUNITY primary key (OPPORTUNITY_ID) comment='Shared ontology entity OPPORTUNITY (ACOCO_L2.ONTOLOGY.ENT_OPPORTUNITY)',
		CUSTOMER as ACOCO_L2.ONTOLOGY.ENT_CUSTOMER primary key (CUSTOMER_ID) comment='Shared ontology entity CUSTOMER (ACOCO_L2.ONTOLOGY.ENT_CUSTOMER)',
		MD_GROUP as ACOCO_L2.ONTOLOGY.ENT_MD_GROUP primary key (MD_GROUP_ID) comment='Shared ontology entity MD_GROUP (ACOCO_L2.ONTOLOGY.ENT_MD_GROUP)',
		FISCAL_MONTH as ACOCO_L2.CORE.DT_FISCAL_MONTH primary key (MONTH_START) comment='Shared ontology entity FISCAL_MONTH (ACOCO_L2.CORE.DT_FISCAL_MONTH)',
		PERSON as ACOCO_L2.ONTOLOGY.ENT_PERSON primary key (PERSON_ID) comment='Shared ontology entity PERSON (ACOCO_L2.ONTOLOGY.ENT_PERSON)',
		SKILL as ACOCO_L2.ONTOLOGY.ENT_SKILL primary key (SKILL_ID) comment='Shared ontology entity SKILL (ACOCO_L2.ONTOLOGY.ENT_SKILL)',
		PROJECT as ACOCO_L2.ONTOLOGY.ENT_PROJECT primary key (PROJECT_ID) comment='Shared ontology entity PROJECT (ACOCO_L2.ONTOLOGY.ENT_PROJECT)',
		BID as ACOCO_L2.PIPELINE_PRESALES.DT_OPPORTUNITY_FACT primary key (OPPORTUNITY_ID) comment='Fact PIPELINE_PRESALES.DT_OPPORTUNITY_FACT',
		PURSUIT_TEAM as ACOCO_L2.PIPELINE_PRESALES.DT_PURSUIT_TEAM comment='Fact PIPELINE_PRESALES.DT_PURSUIT_TEAM',
		BENCH_MATCH as ACOCO_L2.REASONING.VW_BENCH_TO_PIPELINE_MATCH comment='Fact REASONING.VW_BENCH_TO_PIPELINE_MATCH',
		BID_SKILL as ACOCO_L2.ONTOLOGY.REL_OPPORTUNITY_SKILL comment='Fact ONTOLOGY.REL_OPPORTUNITY_SKILL'
	)
	relationships (
		CUSTOMER_TO_MD_GROUP as CUSTOMER(MD_GROUP_ID) references MD_GROUP(MD_GROUP_ID),
		BID_TO_CUSTOMER as BID(CUSTOMER_ID) references CUSTOMER(CUSTOMER_ID),
		BID_TO_OPPORTUNITY as BID(OPPORTUNITY_ID) references OPPORTUNITY(OPPORTUNITY_ID),
		BID_TO_PROJECT as BID(PROJECT_ID) references PROJECT(PROJECT_ID),
		PURSUIT_TEAM_TO_OPPORTUNITY as PURSUIT_TEAM(OPPORTUNITY_ID) references OPPORTUNITY(OPPORTUNITY_ID),
		PURSUIT_TEAM_TO_PERSON as PURSUIT_TEAM(PERSON_ID) references PERSON(PERSON_ID),
		BENCH_MATCH_TO_OPPORTUNITY as BENCH_MATCH(OPPORTUNITY_ID) references OPPORTUNITY(OPPORTUNITY_ID),
		BENCH_MATCH_TO_PERSON as BENCH_MATCH(PERSON_ID) references PERSON(PERSON_ID),
		BID_SKILL_TO_OPPORTUNITY as BID_SKILL(OPPORTUNITY_ID) references OPPORTUNITY(OPPORTUNITY_ID),
		BID_SKILL_TO_SKILL as BID_SKILL(SKILL_ID) references SKILL(SKILL_ID)
	)
	facts (
		BID.OPPORTUNITY_KEY as OPPORTUNITY_ID comment='Bid',
		BID.IS_WON as IS_WON comment='Won',
		BID.IS_CLOSED as IS_CLOSED comment='Decided',
		BID.IS_OPEN as IS_OPEN_AS_OF comment='Open at the as-of date',
		BID.ESTIMATED_VALUE as ESTIMATED_VALUE comment='Estimated value USD',
		BID.PURSUIT_COST as PURSUIT_COST comment='Pursuit cost USD',
		BID.SKILL_FIT as SKILL_FIT comment='Team skill fit 0-1',
		BID.PURSUIT_INTENSITY as PURSUIT_INTENSITY comment='Pursuit cost / estimated value',
		PURSUIT_TEAM.BID_HOURS as BID_HOURS comment='Bid hours booked',
		BENCH_MATCH.MATCH_PERSON_KEY as PERSON_ID comment='Roll-off person',
		BENCH_MATCH.MATCH_SCORE as MATCH_SCORE comment='Match score 0-1',
		BENCH_MATCH.SKILL_COVERAGE as SKILL_COVERAGE comment='Share of required skills the person holds at >= 3'
	)
	dimensions (
		OPPORTUNITY.OPPORTUNITY_ID as OPPORTUNITY_ID with synonyms=('bid','deal','pursuit') comment='CRM opportunity (bid)',
		OPPORTUNITY.OPPORTUNITY_SIZE as SIZE_CLASS comment='Opportunity size class',
		OPPORTUNITY.OPPORTUNITY_WORK_TYPE as WORK_TYPE comment='Type of work bid for',
		OPPORTUNITY.OPPORTUNITY_STATUS as STATUS_AS_OF with synonyms=('outcome','stage') comment='OPEN / WON / LOST at the as-of date',
		OPPORTUNITY.REQUIRED_AI_SKILL_LEVEL as REQUIRED_AI_SKILL_LEVEL comment='AI-skill level (1-5) the bid requires',
		CUSTOMER.CUSTOMER_ID as CUSTOMER_ID comment='Customer account id',
		CUSTOMER.CUSTOMER_NAME as CUSTOMER_NAME with synonyms=('client','account') comment='Customer account name',
		MD_GROUP.MD_GROUP_ID as MD_GROUP_ID with synonyms=('group code') comment='MD group code (FS, CMT, HPS, PRD, RES, XAI)',
		MD_GROUP.MD_GROUP as MD_GROUP_NAME with synonyms=('group','industry group','practice') comment='MD group name, e.g. Financial Services',
		MD_GROUP.MANAGING_DIRECTOR as MANAGING_DIRECTOR_NAME with synonyms=('MD name','partner') comment='Managing Director of the group',
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
		SKILL.SKILL_ID as SKILL_ID comment='Skill code',
		SKILL.SKILL_NAME as SKILL_NAME with synonyms=('skill','capability') comment='Skill name',
		SKILL.SKILL_FAMILY as SKILL_FAMILY with synonyms=('skill category') comment='AGENTIC_AI, TECHNICAL or INDUSTRY',
		PROJECT.PROJECT_ID as PROJECT_ID with synonyms=('project','engagement') comment='Customer project (S/4 project / WBS)',
		PROJECT.SIZE_CLASS as SIZE_CLASS with synonyms=('size') comment='Project size class (XX-Small .. Large)',
		PROJECT.WORK_TYPE as WORK_TYPE with synonyms=('service line') comment='Type of work (Data Migration, AI Engineering, ...)',
		PROJECT.CONTRACT_TYPE as CONTRACT_TYPE with synonyms=('pricing') comment='FIXED_PRICE or TIME_AND_MATERIALS',
		PROJECT.DELIVERY_MODEL as DELIVERY_MODEL with synonyms=('AI delivery model') comment='HUMAN, HUMAN_AGENT (people + agents) or AGENT_LED',
		PROJECT.PROJECT_STATUS as STATUS_AS_OF with synonyms=('status') comment='ACTIVE / CLOSED / NOT_STARTED at the as-of date',
		PROJECT.IS_STORY_PROJECT as IS_STORY_PROJECT comment='The seeded at-risk FS fixed-price project',
		BID.DECISION_FISCAL_YEAR as DECISION_FISCAL_YEAR comment='Fiscal year the bid was decided (or created if open)',
		BID.SKILL_FIT_BAND as SKILL_FIT_BAND with synonyms=('fit band') comment='HIGH (>= 0.8) / MEDIUM / LOW (< 0.5)',
		BID.IS_ABOVE_MEDIAN_INTENSITY as IS_ABOVE_MEDIAN_INTENSITY comment='Pursuit intensity above the size-class median',
		PURSUIT_TEAM.TEAM_ROLE as TEAM_ROLE comment='LEAD or MEMBER',
		BENCH_MATCH.MATCH_RANK as RANK_FOR_PERSON comment='1 = best open bid for the person',
		BENCH_MATCH.MEETS_AI_LEVEL as MEETS_AI_LEVEL comment='Person''s AI-skill level meets the bid''s requirement',
		BENCH_MATCH.ROLL_OFF_DATE as ROLL_OFF_DATE comment='Date the person rolls off'
	)
	metrics (
		BID.WIN_RATE_PCT as 100 * SUM(IFF(is_won, 1, 0)) / NULLIF(SUM(IFF(is_closed, 1, 0)), 0) with synonyms=('hit rate','conversion') comment='Won / (won + lost) bids',
		BID.TOTAL_PURSUIT_COST as SUM(pursuit_cost) with synonyms=('bid cost','presales cost') comment='Pre-sales people cost booked to the bid''s internal order (USD)',
		BID.PURSUIT_COST_PER_WON_USD as SUM(IFF(is_closed, pursuit_cost, 0)) / NULLIF(SUM(IFF(is_won, estimated_value, 0)), 0) comment='Pursuit cost of closed bids per USD won',
		BID.AVG_SKILL_FIT as AVG(skill_fit) with synonyms=('team fit') comment='Share of required skills held at >= 3 by the pursuit team',
		BID.WON_VALUE as SUM(IFF(is_won, estimated_value, 0)) with synonyms=('bookings') comment='Value of won bids (USD)',
		BID.OPEN_PIPELINE_VALUE as SUM(IFF(is_open, estimated_value, 0)) with synonyms=('pipeline') comment='Value of open bids at the as-of date (USD)',
		BID.BID_COUNT as COUNT(opportunity_key) with synonyms=('opportunities') comment='Number of bids',
		PURSUIT_TEAM.PURSUIT_TEAM_BID_HOURS as SUM(bid_hours) comment='Bid hours booked by the team member',
		BENCH_MATCH.AVG_MATCH_SCORE as AVG(match_score) with synonyms=('fit score') comment='R1: 0.6 x semantic skill similarity + 0.4 x exact skill coverage between a roll-off person and an open bid',
		BENCH_MATCH.MATCHED_PEOPLE as COUNT(DISTINCT match_person_key) comment='Roll-off people with at least one matching open bid'
	)
	comment='Value Creation pillar: bids, win-rate, pursuit cost and intensity, pursuit-team skill fit, required skills, and which bids became projects.'
	ai_sql_generation 'Fiscal years run October to September (FY26 = Oct 2025 - Sep 2026); the as-of date is 1 Oct 2026, so FY26 is the last closed year. Percentages are 0-100. Filter MD groups by md_group name (e.g. ''Financial Services'').'
	ai_verified_queries (
		VQ_1 AS ( 
QUESTION 'What is the win-rate by pursuit-team skill fit band?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION true
SQL 'SELECT SKILL_FIT_BAND, COUNT(*) AS BIDS, ROUND(100 * AVG(IFF(IS_WON, 1, 0)), 1) AS WIN_RATE_PCT
FROM ACOCO_L2.PIPELINE_PRESALES.DT_OPPORTUNITY_FACT WHERE IS_CLOSED GROUP BY SKILL_FIT_BAND ORDER BY SKILL_FIT_BAND'),
		VQ_2 AS ( 
QUESTION 'What is the open pipeline value by MD group?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION false
SQL 'SELECT g.MD_GROUP_NAME, ROUND(SUM(o.ESTIMATED_VALUE), 0) AS OPEN_PIPELINE_VALUE
FROM ACOCO_L2.PIPELINE_PRESALES.DT_OPPORTUNITY_FACT o
JOIN ACOCO_L2.ONTOLOGY.ENT_CUSTOMER c ON c.CUSTOMER_ID = o.CUSTOMER_ID
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = c.MD_GROUP_ID
WHERE o.IS_OPEN_AS_OF GROUP BY g.MD_GROUP_NAME ORDER BY OPEN_PIPELINE_VALUE DESC')
	)
	with extension (CA='{"tables":[{"name":"opportunity","dimensions":[{"name":"opportunity_id"},{"name":"opportunity_size"},{"name":"opportunity_work_type"},{"name":"opportunity_status"},{"name":"required_ai_skill_level"}]},{"name":"customer","dimensions":[{"name":"customer_id"},{"name":"customer_name"}]},{"name":"md_group","dimensions":[{"name":"md_group_id"},{"name":"md_group"},{"name":"managing_director"}]},{"name":"fiscal_month","dimensions":[{"name":"fiscal_year"},{"name":"fiscal_period"},{"name":"fiscal_quarter"},{"name":"month_label"}],"time_dimensions":[{"name":"month_start"}]},{"name":"person","dimensions":[{"name":"person_id"},{"name":"person_name"},{"name":"person_level"},{"name":"bill_code"},{"name":"is_active"},{"name":"is_managing_director"},{"name":"person_source"}]},{"name":"skill","dimensions":[{"name":"skill_id"},{"name":"skill_name"},{"name":"skill_family"}]},{"name":"project","dimensions":[{"name":"project_id"},{"name":"size_class"},{"name":"work_type"},{"name":"contract_type"},{"name":"delivery_model"},{"name":"project_status"},{"name":"is_story_project"}]},{"name":"bid","dimensions":[{"name":"decision_fiscal_year"},{"name":"skill_fit_band"},{"name":"is_above_median_intensity"}],"facts":[{"name":"opportunity_key"},{"name":"is_won"},{"name":"is_closed"},{"name":"is_open"},{"name":"estimated_value"},{"name":"pursuit_cost"},{"name":"skill_fit"},{"name":"pursuit_intensity"}],"metrics":[{"name":"win_rate_pct"},{"name":"total_pursuit_cost"},{"name":"pursuit_cost_per_won_usd"},{"name":"avg_skill_fit"},{"name":"won_value"},{"name":"open_pipeline_value"},{"name":"bid_count"}]},{"name":"pursuit_team","dimensions":[{"name":"team_role"}],"facts":[{"name":"bid_hours"}],"metrics":[{"name":"pursuit_team_bid_hours"}]},{"name":"bench_match","dimensions":[{"name":"match_rank"},{"name":"meets_ai_level"}],"facts":[{"name":"match_person_key"},{"name":"match_score"},{"name":"skill_coverage"}],"metrics":[{"name":"avg_match_score"},{"name":"matched_people"}],"time_dimensions":[{"name":"roll_off_date"}]},{"name":"bid_skill"}],"relationships":[{"name":"bid_to_opportunity","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"bid_to_customer","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"bid_to_project","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"pursuit_team_to_opportunity","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"pursuit_team_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"bench_match_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"bench_match_to_opportunity","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"bid_skill_to_opportunity","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"bid_skill_to_skill","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"customer_to_md_group","relationship_type":"many_to_one","join_type":"left_outer"}]}');;
