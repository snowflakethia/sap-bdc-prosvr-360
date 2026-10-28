create or replace semantic view SV_PORTFOLIO_360
	tables (
		MD_GROUP as ACOCO_L2.ONTOLOGY.ENT_MD_GROUP primary key (MD_GROUP_ID) comment='Shared ontology entity MD_GROUP (ACOCO_L2.ONTOLOGY.ENT_MD_GROUP)',
		FISCAL_MONTH as ACOCO_L2.CORE.DT_FISCAL_MONTH primary key (MONTH_START) comment='Shared ontology entity FISCAL_MONTH (ACOCO_L2.CORE.DT_FISCAL_MONTH)',
		LEVEL as ACOCO_L2.ONTOLOGY.ENT_LEVEL primary key (LEVEL) comment='Shared ontology entity LEVEL (ACOCO_L2.ONTOLOGY.ENT_LEVEL)',
		TIME_CATEGORY as ACOCO_L2.ONTOLOGY.ENT_TIME_CATEGORY primary key (TIME_CATEGORY) comment='Shared ontology entity TIME_CATEGORY (ACOCO_L2.ONTOLOGY.ENT_TIME_CATEGORY)',
		PORTFOLIO_MONTH as ACOCO_L2.PORTFOLIO_360.DT_PORTFOLIO_MONTH comment='Fact PORTFOLIO_360.DT_PORTFOLIO_MONTH',
		CAPACITY_MIX as ACOCO_L2.PORTFOLIO_360.DT_CAPACITY_MIX_LONG comment='Fact PORTFOLIO_360.DT_CAPACITY_MIX_LONG',
		RISK_ITEM as ACOCO_L2.PORTFOLIO_360.DT_RISK_REGISTER primary key (RISK_ID) comment='Fact PORTFOLIO_360.DT_RISK_REGISTER'
	)
	relationships (
		PORTFOLIO_MONTH_TO_FISCAL_MONTH as PORTFOLIO_MONTH(MONTH_START) references FISCAL_MONTH(MONTH_START),
		PORTFOLIO_MONTH_TO_MD_GROUP as PORTFOLIO_MONTH(MD_GROUP_ID) references MD_GROUP(MD_GROUP_ID),
		CAPACITY_MIX_TO_FISCAL_MONTH as CAPACITY_MIX(MONTH_START) references FISCAL_MONTH(MONTH_START),
		CAPACITY_MIX_TO_LEVEL as CAPACITY_MIX(LEVEL) references LEVEL(LEVEL),
		CAPACITY_MIX_TO_MD_GROUP as CAPACITY_MIX(MD_GROUP_ID) references MD_GROUP(MD_GROUP_ID),
		CAPACITY_MIX_TO_TIME_CATEGORY as CAPACITY_MIX(TIME_CATEGORY) references TIME_CATEGORY(TIME_CATEGORY),
		RISK_ITEM_TO_MD_GROUP as RISK_ITEM(MD_GROUP_ID) references MD_GROUP(MD_GROUP_ID)
	)
	facts (
		PORTFOLIO_MONTH.REVENUE as REVENUE comment='Revenue USD',
		PORTFOLIO_MONTH.TOTAL_COST as TOTAL_COST comment='Total cost USD',
		PORTFOLIO_MONTH.MARGIN as MARGIN comment='Margin USD',
		PORTFOLIO_MONTH.AVAILABLE_HOURS as AVAILABLE_HOURS comment='Available hours',
		PORTFOLIO_MONTH.DELIVERY_HOURS as DELIVERY_HOURS comment='Delivery hours',
		PORTFOLIO_MONTH.BID_HOURS as BID_HOURS comment='Bid hours',
		PORTFOLIO_MONTH.LEARNING_HOURS as LEARNING_HOURS comment='Learning hours',
		PORTFOLIO_MONTH.ADMIN_HOURS as ADMIN_HOURS comment='Admin hours',
		PORTFOLIO_MONTH.BENCH_HOURS as BENCH_HOURS comment='Bench hours',
		PORTFOLIO_MONTH.BENCH_COST as BENCH_COST comment='Bench cost USD',
		PORTFOLIO_MONTH.CLOSING_HEADCOUNT as CLOSING_HEADCOUNT comment='Month-end headcount',
		PORTFOLIO_MONTH.VOLUNTARY_LEAVERS as VOLUNTARY_LEAVERS comment='Voluntary leavers',
		PORTFOLIO_MONTH.MONTH_KEY as MONTH_START comment='Month of the row (counts months for averages)',
		CAPACITY_MIX.HOURS as HOURS comment='Hours in the category',
		CAPACITY_MIX.AVAILABLE_HOURS as AVAILABLE_HOURS comment='Available hours',
		CAPACITY_MIX.TARGET_PCT as TARGET_PCT comment='Level target %',
		RISK_ITEM.RISK_KEY as RISK_ID comment='Risk item',
		RISK_ITEM.USD_AT_STAKE as USD_AT_STAKE comment='USD at stake'
	)
	dimensions (
		MD_GROUP.MD_GROUP_ID as MD_GROUP_ID with synonyms=('group code') comment='MD group code (FS, CMT, HPS, PRD, RES, XAI)',
		MD_GROUP.MD_GROUP as MD_GROUP_NAME with synonyms=('group','industry group','practice') comment='MD group name, e.g. Financial Services',
		MD_GROUP.MANAGING_DIRECTOR as MANAGING_DIRECTOR_NAME with synonyms=('MD name','partner') comment='Managing Director of the group',
		FISCAL_MONTH.FISCAL_YEAR as FISCAL_YEAR with synonyms=('FY','year') comment='ACoCo fiscal year (Oct-Sep, V9); FY26 = Oct 2025 - Sep 2026',
		FISCAL_MONTH.FISCAL_PERIOD as FISCAL_PERIOD with synonyms=('period') comment='Fiscal period 1-12 (1 = October)',
		FISCAL_MONTH.FISCAL_QUARTER as FISCAL_QUARTER with synonyms=('quarter') comment='Fiscal quarter 1-4 (1 = Oct-Dec)',
		FISCAL_MONTH.MONTH_LABEL as MONTH_LABEL with synonyms=('month') comment='Calendar month label, e.g. SEP 2026',
		FISCAL_MONTH.MONTH_START as MONTH_START comment='First day of the fiscal month (join key)',
		LEVEL.LEVEL as LEVEL with synonyms=('grade') comment='Career level',
		LEVEL.LEVEL_SORT as LEVEL_SORT comment='1 = Analyst .. 5 = Principal',
		LEVEL.ACTIVITY_TYPE as ACTIVITY_TYPE comment='S/4 activity type that prices the level (ML-100 .. ML-105)',
		TIME_CATEGORY.TIME_CATEGORY as TIME_CATEGORY with synonyms=('use of time','category') comment='DELIVERY, BID, LEARNING, ADMIN or BENCH',
		TIME_CATEGORY.TIME_CATEGORY_OBJECTIVE as OBJECTIVE comment='What the category is judged on',
		RISK_ITEM.PILLAR as PILLAR comment='OPERATIONAL / PEOPLE / VALUE',
		RISK_ITEM.RISK_TYPE as RISK_TYPE comment='Risk type',
		RISK_ITEM.RISK_OBJECT_ID as OBJECT_ID comment='Project / person / opportunity the risk is about',
		RISK_ITEM.RISK_DETAIL as DETAIL comment='Short explanation'
	)
	metrics (
		PORTFOLIO_MONTH.TOTAL_REVENUE as SUM(revenue) with synonyms=('sales','fees') comment='Recognised revenue (USD, S/4 journal GL 0041000000)',
		PORTFOLIO_MONTH.TOTAL_TOTAL_COST as SUM(total_cost) with synonyms=('cost') comment='People + AI-agent + 35 % overhead cost (USD)',
		PORTFOLIO_MONTH.TOTAL_MARGIN as SUM(margin) with synonyms=('profit') comment='Revenue minus total cost (USD)',
		PORTFOLIO_MONTH.MARGIN_PCT as 100 * SUM(margin) / NULLIF(SUM(revenue), 0) with synonyms=('profit margin') comment='Margin as % of revenue',
		PORTFOLIO_MONTH.DELIVERY_PCT as 100 * SUM(delivery_hours) / NULLIF(SUM(available_hours), 0) with synonyms=('billability','utilisation of delivery') comment='Billability: Delivery hours as % of available hours (Employee Availability)',
		PORTFOLIO_MONTH.BID_PCT as 100 * SUM(bid_hours) / NULLIF(SUM(available_hours), 0) with synonyms=('presales share') comment='Bid (pre-sales) hours as % of available hours',
		PORTFOLIO_MONTH.LEARNING_PCT as 100 * SUM(learning_hours) / NULLIF(SUM(available_hours), 0) comment='Learning hours as % of available hours',
		PORTFOLIO_MONTH.ADMIN_PCT as 100 * SUM(admin_hours) / NULLIF(SUM(available_hours), 0) comment='Admin hours as % of available hours (ceiling 5 %)',
		PORTFOLIO_MONTH.BENCH_PCT as 100 * SUM(bench_hours) / NULLIF(SUM(available_hours), 0) with synonyms=('idle time','unutilised') comment='Bench = available minus booked hours, % of available (target ~2 %, < 3 %)',
		PORTFOLIO_MONTH.TOTAL_BENCH_COST as SUM(bench_cost) comment='Bench hours x level cost rate (USD)',
		PORTFOLIO_MONTH.VOLUNTARY_ATTRITION_PCT as 100 * SUM(voluntary_leavers) / NULLIF(SUM(closing_headcount) / COUNT(DISTINCT month_key), 0) with synonyms=('attrition rate','turnover') comment='Voluntary leavers / average monthly headcount (annual when over one fiscal year; correct for any group or firm-wide)',
		CAPACITY_MIX.CATEGORY_SHARE_PCT as 100 * SUM(hours) / NULLIF(SUM(available_hours), 0) with synonyms=('time mix') comment='Hours of the time category as % of available hours',
		RISK_ITEM.RISK_USD_AT_STAKE as SUM(usd_at_stake) comment='Money at stake on cross-pillar risk items (USD)',
		RISK_ITEM.RISK_ITEMS as COUNT(risk_key) comment='Number of risk items'
	)
	comment='ProServe360 overlay for the Managing Director: group P&L, capacity mix by time category vs target, headcount and attrition, win-rate and the cross-pillar risk register.'
	ai_sql_generation 'Fiscal years run October to September (FY26 = Oct 2025 - Sep 2026); the as-of date is 1 Oct 2026, so FY26 is the last closed year. Percentages are 0-100. Filter MD groups by md_group name (e.g. ''Financial Services'').'
	ai_verified_queries (
		VQ_1 AS ( 
QUESTION 'What were FY26 revenue, margin % and bench % for Financial Services?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION true
SQL 'SELECT ROUND(SUM(p.REVENUE), 0) AS REVENUE, ROUND(100 * SUM(p.MARGIN) / SUM(p.REVENUE), 1) AS MARGIN_PCT,
ROUND(100 * SUM(p.BENCH_HOURS) / SUM(p.AVAILABLE_HOURS), 1) AS BENCH_PCT FROM ACOCO_L2.PORTFOLIO_360.DT_PORTFOLIO_MONTH p JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = p.MD_GROUP_ID WHERE g.MD_GROUP_NAME = ''Financial Services'' AND p.FISCAL_YEAR = 2026'),
		VQ_2 AS ( 
QUESTION 'What are the top 5 risks for Financial Services by USD at stake?' 
VERIFIED_AT 1793059200
VERIFIED_BY 'ACoCo build (CP-07)'
ONBOARDING_QUESTION false
SQL 'SELECT r.PILLAR, r.RISK_TYPE, r.OBJECT_ID, r.DETAIL, ROUND(r.USD_AT_STAKE, 0) AS USD_AT_STAKE
FROM ACOCO_L2.PORTFOLIO_360.DT_RISK_REGISTER r
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = r.MD_GROUP_ID
WHERE g.MD_GROUP_NAME = ''Financial Services'' ORDER BY r.USD_AT_STAKE DESC LIMIT 5')
	)
	with extension (CA='{"tables":[{"name":"md_group","dimensions":[{"name":"md_group_id"},{"name":"md_group"},{"name":"managing_director"}]},{"name":"fiscal_month","dimensions":[{"name":"fiscal_year"},{"name":"fiscal_period"},{"name":"fiscal_quarter"},{"name":"month_label"}],"time_dimensions":[{"name":"month_start"}]},{"name":"level","dimensions":[{"name":"level"},{"name":"level_sort"},{"name":"activity_type"}]},{"name":"time_category","dimensions":[{"name":"time_category"},{"name":"time_category_objective"}]},{"name":"portfolio_month","facts":[{"name":"revenue"},{"name":"total_cost"},{"name":"margin"},{"name":"available_hours"},{"name":"delivery_hours"},{"name":"bid_hours"},{"name":"learning_hours"},{"name":"admin_hours"},{"name":"bench_hours"},{"name":"bench_cost"},{"name":"closing_headcount"},{"name":"voluntary_leavers"},{"name":"month_key"}],"metrics":[{"name":"total_revenue"},{"name":"total_total_cost"},{"name":"total_margin"},{"name":"margin_pct"},{"name":"delivery_pct"},{"name":"bid_pct"},{"name":"learning_pct"},{"name":"admin_pct"},{"name":"bench_pct"},{"name":"total_bench_cost"},{"name":"voluntary_attrition_pct"}]},{"name":"capacity_mix","facts":[{"name":"hours"},{"name":"available_hours"},{"name":"target_pct"}],"metrics":[{"name":"category_share_pct"}]},{"name":"risk_item","dimensions":[{"name":"pillar"},{"name":"risk_type"},{"name":"risk_object_id"},{"name":"risk_detail"}],"facts":[{"name":"risk_key"},{"name":"usd_at_stake"}],"metrics":[{"name":"risk_usd_at_stake"},{"name":"risk_items"}]}],"relationships":[{"name":"portfolio_month_to_md_group","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"portfolio_month_to_fiscal_month","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"capacity_mix_to_md_group","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"capacity_mix_to_level","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"capacity_mix_to_fiscal_month","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"capacity_mix_to_time_category","relationship_type":"many_to_one","join_type":"left_outer"},{"name":"risk_item_to_md_group","relationship_type":"many_to_one","join_type":"left_outer"}]}');;
