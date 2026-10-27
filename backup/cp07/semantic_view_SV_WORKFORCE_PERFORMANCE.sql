create or replace semantic view SV_WORKFORCE_PERFORMANCE
	tables (
		PERSON as ACOCO_L2.ONTOLOGY.ENT_PERSON primary key (PERSON_ID) comment='Shared ontology entity PERSON (ACOCO_L2.ONTOLOGY.ENT_PERSON)',
		MD_GROUP as ACOCO_L2.ONTOLOGY.ENT_MD_GROUP primary key (MD_GROUP_ID) comment='Shared ontology entity MD_GROUP (ACOCO_L2.ONTOLOGY.ENT_MD_GROUP)',
		LEVEL as ACOCO_L2.ONTOLOGY.ENT_LEVEL primary key (LEVEL) comment='Shared ontology entity LEVEL (ACOCO_L2.ONTOLOGY.ENT_LEVEL)',
		FISCAL_MONTH as ACOCO_L2.CORE.DT_FISCAL_MONTH primary key (MONTH_START) comment='Shared ontology entity FISCAL_MONTH (ACOCO_L2.CORE.DT_FISCAL_MONTH)',
		SKILL as ACOCO_L2.ONTOLOGY.ENT_SKILL primary key (SKILL_ID) comment='Shared ontology entity SKILL (ACOCO_L2.ONTOLOGY.ENT_SKILL)',
		TIME_CATEGORY as ACOCO_L2.ONTOLOGY.ENT_TIME_CATEGORY primary key (TIME_CATEGORY) comment='Shared ontology entity TIME_CATEGORY (ACOCO_L2.ONTOLOGY.ENT_TIME_CATEGORY)',
		SCORECARD as ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_SCORECARD primary key (PERSON_MONTH_ID) comment='Fact WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_SCORECARD',
		TIME_BOOKING as ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_TIME primary key (PERSON_MONTH_TIME_ID) comment='Fact WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_TIME',
		HEADCOUNT as ACOCO_L2.WORKFORCE_PERFORMANCE.DT_HEADCOUNT_MONTH comment='Fact WORKFORCE_PERFORMANCE.DT_HEADCOUNT_MONTH',
		ROLL_OFF as ACOCO_L2.WORKFORCE_PERFORMANCE.DT_ROLL_OFF primary key (PERSON_ID) comment='Fact WORKFORCE_PERFORMANCE.DT_ROLL_OFF',
		PERSON_SKILL as ACOCO_L2.ONTOLOGY.REL_PERSON_SKILL comment='Fact ONTOLOGY.REL_PERSON_SKILL'
	)
	relationships (
		PERSON_TO_LEVEL as PERSON(LEVEL) references LEVEL(LEVEL),
		PERSON_TO_MD_GROUP as PERSON(MD_GROUP_ID) references MD_GROUP(MD_GROUP_ID),
		SCORECARD_TO_FISCAL_MONTH as SCORECARD(MONTH_START) references FISCAL_MONTH(MONTH_START),
		SCORECARD_TO_PERSON as SCORECARD(PERSON_ID) references PERSON(PERSON_ID),
		TIME_BOOKING_TO_FISCAL_MONTH as TIME_BOOKING(MONTH_START) references FISCAL_MONTH(MONTH_START),
		TIME_BOOKING_TO_PERSON as TIME_BOOKING(PERSON_ID) references PERSON(PERSON_ID),
		TIME_BOOKING_TO_TIME_CATEGORY as TIME_BOOKING(TIME_CATEGORY) references TIME_CATEGORY(TIME_CATEGORY),
		HEADCOUNT_TO_FISCAL_MONTH as HEADCOUNT(MONTH_START) references FISCAL_MONTH(MONTH_START),
		HEADCOUNT_TO_MD_GROUP as HEADCOUNT(MD_GROUP_ID) references MD_GROUP(MD_GROUP_ID),
		ROLL_OFF_TO_PERSON as ROLL_OFF(PERSON_ID) references PERSON(PERSON_ID),
		PERSON_SKILL_TO_PERSON as PERSON_SKILL(PERSON_ID) references PERSON(PERSON_ID),
		PERSON_SKILL_TO_SKILL as PERSON_SKILL(SKILL_ID) references SKILL(SKILL_ID)
	)
	facts (
		SCORECARD.AVAILABLE_HOURS as AVAILABLE_HOURS comment='Available hours',
		SCORECARD.DELIVERY_HOURS as DELIVERY_HOURS comment='Delivery hours',
		SCORECARD.BID_HOURS as BID_HOURS comment='Bid hours',
		SCORECARD.LEARNING_HOURS as LEARNING_HOURS comment='Learning hours',
		SCORECARD.ADMIN_HOURS as ADMIN_HOURS comment='Admin hours',
		SCORECARD.BENCH_HOURS as BENCH_HOURS comment='Bench hours',
		SCORECARD.BENCH_COST as BENCH_COST comment='Bench cost USD',
		SCORECARD.EARNED_HOURS as EARNED_HOURS comment='Earned hours',
		TIME_BOOKING.HOURS as HOURS comment='Hours in the time category',
		TIME_BOOKING.AVAILABLE_HOURS as AVAILABLE_HOURS comment='Person-month available hours',
		TIME_BOOKING.TARGET_PCT as TARGET_PCT comment='Level target % for the category',
		HEADCOUNT.CLOSING_HEADCOUNT as CLOSING_HEADCOUNT comment='Month-end headcount',
		HEADCOUNT.VOLUNTARY_LEAVERS as VOLUNTARY_LEAVERS comment='Voluntary leavers',
		HEADCOUNT.HIRES as HIRES comment='Hires',
		ROLL_OFF.ROLL_OFF_PERSON_KEY as PERSON_ID comment='Person rolling off',
		ROLL_OFF.BELOW_PIPELINE_AI_LEVEL as BELOW_PIPELINE_AI_LEVEL comment='Below pipeline AI level',
		PERSON_SKILL.PROFICIENCY as PROFICIENCY comment='Latest proficiency 1-5'
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
		LEVEL.LEVEL as LEVEL with synonyms=('grade') comment='Career level',
		LEVEL.LEVEL_SORT as LEVEL_SORT comment='1 = Analyst .. 5 = Principal',
		LEVEL.ACTIVITY_TYPE as ACTIVITY_TYPE comment='S/4 activity type that prices the level (ML-100 .. ML-105)',
		FISCAL_MONTH.FISCAL_YEAR as FISCAL_YEAR with synonyms=('FY','year') comment='ACoCo fiscal year (Oct-Sep, V9); FY26 = Oct 2025 - Sep 2026',
		FISCAL_MONTH.FISCAL_PERIOD as FISCAL_PERIOD with synonyms=('period') comment='Fiscal period 1-12 (1 = October)',
		FISCAL_MONTH.FISCAL_QUARTER as FISCAL_QUARTER with synonyms=('quarter') comment='Fiscal quarter 1-4 (1 = Oct-Dec)',
		FISCAL_MONTH.MONTH_LABEL as MONTH_LABEL with synonyms=('month') comment='Calendar month label, e.g. SEP 2026',
		FISCAL_MONTH.MONTH_START as MONTH_START comment='First day of the fiscal month (join key)',
		SKILL.SKILL_ID as SKILL_ID comment='Skill code',
		SKILL.SKILL_NAME as SKILL_NAME with synonyms=('skill','capability') comment='Skill name',
		SKILL.SKILL_FAMILY as SKILL_FAMILY with synonyms=('skill category') comment='AGENTIC_AI, TECHNICAL or INDUSTRY',
		TIME_CATEGORY.TIME_CATEGORY as TIME_CATEGORY with synonyms=('use of time','category') comment='DELIVERY, BID, LEARNING, ADMIN or BENCH',
		TIME_CATEGORY.TIME_CATEGORY_OBJECTIVE as OBJECTIVE comment='What the category is judged on',
		ROLL_OFF.ROLL_OFF_DATE as ROLL_OFF_DATE comment='Last assignment end date'
	)
	metrics (
		SCORECARD.DELIVERY_PCT as 100 * SUM(delivery_hours) / NULLIF(SUM(available_hours), 0) with synonyms=('billability','utilisation of delivery') comment='Billability: Delivery hours as % of available hours (Employee Availability)',
		SCORECARD.BID_PCT as 100 * SUM(bid_hours) / NULLIF(SUM(available_hours), 0) with synonyms=('presales share') comment='Bid (pre-sales) hours as % of available hours',
		SCORECARD.LEARNING_PCT as 100 * SUM(learning_hours) / NULLIF(SUM(available_hours), 0) comment='Learning hours as % of available hours',
		SCORECARD.ADMIN_PCT as 100 * SUM(admin_hours) / NULLIF(SUM(available_hours), 0) comment='Admin hours as % of available hours (ceiling 5 %)',
		SCORECARD.BENCH_PCT as 100 * SUM(bench_hours) / NULLIF(SUM(available_hours), 0) with synonyms=('idle time','unutilised') comment='Bench = available minus booked hours, % of available (target ~2 %, < 3 %)',
		SCORECARD.AVAILABLE_HOURS_TOTAL as SUM(available_hours) with synonyms=('capacity') comment='Available hours (planned work hours minus absence)',
		SCORECARD.TOTAL_BENCH_COST as SUM(bench_cost) comment='Bench hours x level cost rate (USD)',
		SCORECARD.TOTAL_PRODUCTIVITY_INDEX as SUM(earned_hours) / NULLIF(SUM(delivery_hours), 0) with synonyms=('productivity') comment='Earned hours / actual delivery hours (> 1 = faster than plan)',
		TIME_BOOKING.CATEGORY_SHARE_PCT as 100 * SUM(hours) / NULLIF(SUM(available_hours), 0) with synonyms=('time mix') comment='Hours of the time category as % of available hours',
		HEADCOUNT.HEADCOUNT_CLOSING as SUM(closing_headcount) with synonyms=('headcount','FTE') comment='Headcount at month end (sum over a single month only)',
		HEADCOUNT.TOTAL_VOLUNTARY_LEAVERS as SUM(voluntary_leavers) with synonyms=('attrition count','quits') comment='Voluntary leavers',
		HEADCOUNT.TOTAL_HIRES as SUM(hires) comment='Hires',
		ROLL_OFF.ROLL_OFF_PEOPLE as COUNT(roll_off_person_key) with synonyms=('roll-offs') comment='People whose last assignment ends in the 90 days after the as-of date',
		ROLL_OFF.ROLL_OFF_BELOW_AI_LEVEL as SUM(IFF(below_pipeline_ai_level, 1, 0)) comment='Roll-offs below the pipeline''s required AI-skill level',
		PERSON_SKILL.AVG_PROFICIENCY as AVG(proficiency) comment='Average skill proficiency (1-5)'
	)
	comment='People pillar: five-way time mix (Delivery, Bid, Learning, Admin, Bench) vs level targets, productivity, headcount, attrition, roll-off and skills. Use for billability, bench, time mix, headcount and roll-off questions.'
	ai_sql_generation 'Fiscal years run October to September (FY26 = Oct 2025 - Sep 2026); the as-of date is 1 Oct 2026, so FY26 is the last closed year. Percentages are 0-100. Filter MD groups by md_group name (e.g. ''Financial Services'').'
	ai_verified_queries (
		VQ_1 AS ( 
QUESTION 'What was the FY26 time mix by level for Financial Services?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION true
SQL 'SELECT p.LEVEL, ROUND(100 * SUM(s.DELIVERY_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS DELIVERY_PCT, ROUND(100 * SUM(s.BID_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS BID_PCT, ROUND(100 * SUM(s.LEARNING_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS LEARNING_PCT, ROUND(100 * SUM(s.ADMIN_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS ADMIN_PCT, ROUND(100 * SUM(s.BENCH_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS BENCH_PCT FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_SCORECARD s JOIN ACOCO_L2.ONTOLOGY.ENT_PERSON p ON p.PERSON_ID = s.PERSON_ID JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = p.MD_GROUP_ID JOIN ACOCO_L2.CORE.DT_FISCAL_MONTH f ON f.MONTH_START = s.MONTH_START WHERE g.MD_GROUP_NAME = ''Financial Services'' AND f.FISCAL_YEAR = 2026 GROUP BY p.LEVEL, p.LEVEL_SORT ORDER BY p.LEVEL_SORT'),
		VQ_2 AS ( 
QUESTION 'How many Financial Services people roll off in the next 90 days and how many are below the pipeline AI-skill level?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION false
SQL 'SELECT COUNT(*) AS ROLL_OFF_PEOPLE, SUM(IFF(r.BELOW_PIPELINE_AI_LEVEL, 1, 0)) AS BELOW_AI_LEVEL
FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_ROLL_OFF r
JOIN ACOCO_L2.ONTOLOGY.ENT_PERSON p ON p.PERSON_ID = r.PERSON_ID
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = p.MD_GROUP_ID
WHERE g.MD_GROUP_NAME = ''Financial Services''')
	)
	with extension (CA='{"tables":[{"name":"person","dimensions":[{"name":"person_id"},{"name":"person_name"},{"name":"person_level"},{"name":"bill_code"},{"name":"is_active"},{"name":"is_managing_director"},{"name":"person_source"}]},{"name":"md_group","dimensions":[{"name":"md_group_id"},{"name":"md_group"},{"name":"managing_director"}]},{"name":"level","dimensions":[{"name":"level"},{"name":"level_sort"},{"name":"activity_type"}]},{"name":"fiscal_month","dimensions":[{"name":"fiscal_year"},{"name":"fiscal_period"},{"name":"fiscal_quarter"},{"name":"month_label"}],"time_dimensions":[{"name":"month_start"}]},{"name":"skill","dimensions":[{"name":"skill_id"},{"name":"skill_name"},{"name":"skill_family"}]},{"name":"time_category","dimensions":[{"name":"time_category"},{"name":"time_category_objective"}]},{"name":"scorecard","facts":[{"name":"available_hours"},{"name":"delivery_hours"},{"name":"bid_hours"},{"name":"learning_hours"},{"name":"admin_hours"},{"name":"bench_hours"},{"name":"bench_cost"},{"name":"earned_hours"}],"metrics":[{"name":"delivery_pct"},{"name":"bid_pct"},{"name":"learning_pct"},{"name":"admin_pct"},{"name":"bench_pct"},{"name":"available_hours_total"},{"name":"total_bench_cost"},{"name":"total_productivity_index"}]},{"name":"time_booking","facts":[{"name":"hours"},{"name":"available_hours"},{"name":"target_pct"}],"metrics":[{"name":"category_share_pct"}]},{"name":"headcount","facts":[{"name":"closing_headcount"},{"name":"voluntary_leavers"},{"name":"hires"}],"metrics":[{"name":"headcount_closing"},{"name":"total_voluntary_leavers"},{"name":"total_hires"}]},{"name":"roll_off","facts":[{"name":"roll_off_person_key"},{"name":"below_pipeline_ai_level"}],"metrics":[{"name":"roll_off_people"},{"name":"roll_off_below_ai_level"}],"time_dimensions":[{"name":"roll_off_date"}]},{"name":"person_skill","facts":[{"name":"proficiency"}],"metrics":[{"name":"avg_proficiency"}]}],"relationships":[{"name":"scorecard_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"scorecard_to_fiscal_month","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"time_booking_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"time_booking_to_fiscal_month","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"time_booking_to_time_category","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"headcount_to_md_group","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"headcount_to_fiscal_month","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"roll_off_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"person_skill_to_person","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"person_skill_to_skill","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"person_to_md_group","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"person_to_level","relationship_type":"many_to_one","join_type":"left_outer"}]}');;
