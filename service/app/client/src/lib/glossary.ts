/**
 * Hover definitions for the (i) markers on KPI tiles and panel titles.
 * what = plain-language meaning; calc = how the figure is derived; note = caveat or reading guide.
 */
export interface Term { title: string; what: string; calc?: string; note?: string }

export const GLOSSARY: Record<string, Term> = {
  // --- Financial ---------------------------------------------------------
  revenue: {
    title: 'Revenue',
    what: 'Billed services revenue recognised in the fiscal year (Oct-Sep).',
    calc: 'Sum of monthly project revenue for the selected scope.',
  },
  revenue_firm: {
    title: 'Revenue and margin (firm)',
    what: 'Total services revenue across all business groups, with the share kept as margin.',
    calc: 'Revenue = sum of monthly project revenue.\nMargin % = (revenue - delivery cost) / revenue.',
  },
  margin: {
    title: 'Margin',
    what: 'Share of revenue left after delivery cost.',
    calc: 'Margin % = sum(revenue - cost) / sum(revenue)\nDelta = change in percentage points vs the prior year.',
    note: 'Computed from sums, so large projects weigh more than small ones.',
  },
  rev_margin_trend: {
    title: 'Revenue and margin trend',
    what: 'Monthly revenue (area) and margin % (line) over the last 60 months.',
    calc: 'Margin % per month = monthly margin / monthly revenue (SV_PORTFOLIO_360).',
  },
  book_to_bill: {
    title: 'Book-to-bill',
    what: 'New business won relative to revenue billed.',
    calc: 'Won contract value / revenue, same fiscal year.',
    note: 'Above 1.0 the backlog is growing; below 1.0 it is being consumed.',
  },
  won_value: {
    title: 'Won value',
    what: 'Total contract value of bids won in the fiscal year.',
    calc: 'Sum of estimated value of opportunities closed as won.',
  },

  // --- Delivery ----------------------------------------------------------
  on_time: {
    title: 'On-time (active)',
    what: 'Share of active projects forecast to finish on or before their planned end date.',
    calc: 'Active projects with forecast slip <= 0 weeks / all active projects.',
    note: 'A point-in-time view as of the last closed month, not a fiscal-year figure.',
  },
  reuse_rate: {
    title: 'Asset reuse rate',
    what: 'Share of projects that used at least one asset from the library.',
    calc: 'Projects that reused an asset / all projects ending in the fiscal year.',
    note: 'Shown per business group; not aggregated firm-wide.',
  },
  contract_value: {
    title: 'Contract value',
    what: 'Total value of the signed contract.',
    note: 'Fixed-price contracts carry delivery risk; time-and-materials bill hours as worked.',
  },
  cpi: {
    title: 'CPI - Cost Performance Index',
    what: 'Value delivered per dollar spent.',
    calc: 'CPI = earned value / actual cost (to date).',
    note: 'Below 1.0 the project is over budget. 0.70 means each $1 spent delivers $0.70 of planned work.',
  },
  spi: {
    title: 'SPI - Schedule Performance Index',
    what: 'Work delivered versus work planned by now.',
    calc: 'SPI = earned value / planned value (to date).',
    note: 'Below 1.0 the project is behind schedule.',
  },
  cpi_spi: {
    title: 'CPI / SPI',
    what: 'Cost and schedule efficiency of the project to date.',
    calc: 'CPI = earned value / actual cost\nSPI = earned value / planned value',
    note: 'Both should be at or above 1.0.',
  },
  eac: {
    title: 'Estimate at completion (EAC)',
    what: 'Expected total cost by the end of the project at current efficiency.',
    calc: 'EAC = sold cost / CPI.',
  },
  forecast_margin: {
    title: 'Forecast margin',
    what: 'Margin the project is expected to finish with.',
    calc: '(contract value - EAC) / contract value.',
    note: 'Negative means the project is forecast to lose money.',
  },
  ld_exposure: {
    title: 'LD exposure',
    what: 'Liquidated damages payable if the forecast delay holds (fixed-price only).',
    calc: 'Contract value x LD rate per week x forecast slip (weeks).',
  },
  plan_vs_actual: {
    title: 'Plan vs actual',
    what: 'Cumulative planned value, earned value and actual cost by month.',
    note: 'Earned below planned = behind schedule; actual above earned = over budget.',
  },
  pyramid: {
    title: 'Sold vs actual pyramid',
    what: 'Share of hours by level as sold versus as delivered.',
    note: 'A shift toward senior levels raises cost per hour and erodes margin.',
  },
  work_packages: {
    title: 'Work packages',
    what: 'Plan, forecast slip and productivity per work package.',
    calc: 'Productivity = earned hours / delivery hours.',
    note: 'Slip on the critical path delays the whole project.',
  },
  why_notes: {
    title: 'Why? - PM status notes',
    what: 'Project manager commentary most relevant to the current issues.',
    calc: 'Cortex Search ranks status notes by semantic similarity to the question.',
  },
  assets_fit: {
    title: 'Assets that fit',
    what: 'Library assets that match the work in each work package.',
    calc: 'Embedding similarity between asset and work-package descriptions; top matches shown.',
    note: 'Hours saved are estimates.',
  },
  revenue_by_size: {
    title: 'Revenue by size class',
    what: 'Revenue and margin split by project size (S / M / L / XL).',
    calc: 'From SV_PROJECT_DELIVERY, per fiscal year.',
  },
  pareto: {
    title: 'Revenue Pareto',
    what: 'How concentrated revenue is across projects.',
    calc: 'Projects ranked by revenue; the line shows cumulative share of total.',
    note: 'A steep curve means a few projects carry the year.',
  },
  fp_watch: {
    title: 'Fixed-price watch list',
    what: 'Active fixed-price projects forecast below 10 % margin.',
    calc: 'Forecast margin = (contract value - EAC) / contract value < 10 %.',
  },

  // --- Pipeline ----------------------------------------------------------
  win_rate: {
    title: 'Win-rate',
    what: 'Share of decided bids that were won.',
    calc: 'Won / (won + lost), by decision date in the fiscal year.',
    note: 'Open bids and withdrawn bids are excluded.',
  },
  pursuit_cost: {
    title: 'Pursuit cost per won USD',
    what: 'What it costs to win one dollar of new business.',
    calc: 'Pursuit cost of all decided bids (won and lost) / won value.',
    note: 'Lower is better. $0.127 = 12.7 cents of bid effort per $1 won.',
  },
  win_by_intensity: {
    title: 'Win-rate by pursuit intensity',
    what: 'Does spending more on a bid raise the chance of winning?',
    calc: 'Intensity = pursuit cost / bid value. Bids split above vs below the median within each size class.',
  },
  win_by_fit: {
    title: 'Win-rate by team skill fit',
    what: 'Does a better-matched pursuit team win more often?',
    calc: 'Skill fit = share of the bid\'s required skills held at proficiency 3+ by the team.',
    note: 'Bands: LOW < MEDIUM < HIGH.',
  },
  open_pipeline: {
    title: 'Open pipeline',
    what: 'Value of bids not yet decided, by size class.',
    calc: 'From SV_PIPELINE_PRESALES as of the as-of date.',
  },
  bookings: {
    title: 'Bookings and pursuit cost',
    what: 'Won value against revenue, and the cost of winning it.',
    calc: 'Book-to-bill = won value / revenue\nPursuit cost per won USD = pursuit cost / won value',
  },
  open_bids: {
    title: 'Open bids',
    what: 'Live opportunities with their team fit and best-matched available people.',
    calc: 'People matched by embedding similarity of skills to bid requirements.',
  },

  // --- People & time -----------------------------------------------------
  headcount: {
    title: 'People (end of year)',
    what: 'Headcount at the close of the fiscal year.',
    calc: 'Closing headcount in the last month of the fiscal year (September).',
  },
  people_firm: {
    title: 'People',
    what: 'Firm headcount, and the share who left by choice during the year.',
    calc: 'Headcount = closing headcount in September.\nVoluntary attrition = voluntary leavers / average monthly headcount.',
  },
  attrition: {
    title: 'Voluntary attrition',
    what: 'Share of people who chose to leave during the year.',
    calc: 'Voluntary leavers in the year / average monthly headcount.',
    note: 'Excludes involuntary exits.',
  },
  delivery_share: {
    title: 'Delivery share',
    what: 'Share of available time spent on billable client delivery.',
    calc: 'Delivery hours / available hours.',
    note: 'Shares of Delivery, Bid, Learning, Admin and Bench sum to 100 %.',
  },
  admin_share: {
    title: 'Admin share',
    what: 'Share of available time spent on internal administration.',
    calc: 'Admin hours / available hours.',
    note: 'Target: below 5 %.',
  },
  bench_cost: {
    title: 'Bench cost',
    what: 'Cost of paid time not booked to any activity.',
    calc: 'Bench hours x cost rate, where bench hours = available - booked hours.',
    note: 'Lower is better. ~2 % bench is a structural allowance for transitions.',
  },
  time_mix: {
    title: 'Time mix vs target',
    what: 'How each level spends available hours across Delivery, Bid, Learning, Admin and Bench.',
    calc: 'Hours per category / available hours, weighted by available hours. Second bar = target mix for the level.',
  },
  mix_trend: {
    title: 'Five-way mix over time',
    what: 'Trend of the five time categories as a share of available hours.',
    calc: 'Category hours / available hours, per fiscal year.',
  },
  excess_bench: {
    title: 'Excess bench cost',
    what: 'Bench cost above the ~2 % structural allowance.',
    calc: '(bench hours - 2 % of available hours) x cost rate, floored at zero.',
  },
  bench_admin: {
    title: 'Bench and admin share',
    what: 'Monthly bench and admin as a share of available hours.',
    note: 'Reference lines: admin ceiling 5 %, bench allowance 2 %.',
  },
  roll_off: {
    title: 'Rolling off in 90 days',
    what: 'People whose current assignment ends within 90 days.',
    note: 'Red = AI skill below what the open pipeline needs. Redeploy or reskill before they reach the bench.',
  },
  headcount_attrition: {
    title: 'Headcount and attrition',
    what: 'End-of-year headcount (bars) and voluntary attrition (line).',
    calc: 'Attrition = voluntary leavers / average monthly headcount.',
  },
  demand_forecast: {
    title: 'Demand forecast by skill',
    what: 'Expected delivery hours needed per skill family.',
    calc: 'Pipeline hours weighted by win probability, projected with SNOWFLAKE.ML.FORECAST. Dashed = forecast.',
  },
  skills_supply: {
    title: 'Skills supply',
    what: 'Active people holding each skill family.',
    calc: 'Count of people with proficiency 3 or more (scale 1-5).',
  },
  curriculum: {
    title: 'AI curriculum',
    what: 'Learning items available to close the AI skills gap.',
  },
  attrition_risk: {
    title: 'Attrition risk',
    what: 'People ranked by modelled likelihood of leaving next year.',
    calc: 'SNOWFLAKE.ML.CLASSIFICATION on tenure, compa-ratio, performance, time mix, productivity and AI skill.',
    note: 'Weak separation (AUC ~0.57): use as a ranking for conversations, not a prediction.',
  },
  attrition_decile: {
    title: 'Attrition risk by decile',
    what: 'Active people grouped into ten bands by modelled risk score.',
    calc: 'Decile 10 = highest 10 % of SNOWFLAKE.ML.CLASSIFICATION scores.',
  },

  // --- AI ----------------------------------------------------------------
  ai_uplift: {
    title: 'AI productivity uplift',
    what: 'How much more productive AI-active people are than their peers.',
    calc: 'Productivity = earned hours / delivery hours.\nUplift = AI-active vs the rest, compared within the same level and work type.\nAI-active = AI skill 3+ and AI tools used on 50 %+ of working days.',
    note: '90 % CI from bootstrap resampling. Significant = the interval excludes zero.',
  },
  ai_inactive: {
    title: 'AI-skilled but inactive',
    what: 'People trained in AI (skill 3+) who did not use AI tools in the quarter.',
    note: 'The cheapest uplift to unlock: the skill is already paid for.',
  },
  learning_payback: {
    title: 'Learning payback',
    what: 'Productivity gain after completing a curriculum, beyond what peers gained.',
    calc: '(learner after - before) - (comparison after - before), 6-month windows.\nComparison = same-level people who did not take the course.',
    note: '90 % CI from bootstrap resampling.',
  },
  uplift_by_level: {
    title: 'Uplift by level',
    what: 'AI productivity uplift estimated separately for each level.',
    note: 'Point = estimate; band = 90 % CI; red line = no effect.',
  },
  adoption: {
    title: 'Adoption S-curve',
    what: 'Share of delivery people who are AI-active, over time.',
    calc: 'AI-active people / delivery people, per quarter.',
  },
  ai_cost: {
    title: 'AI cost',
    what: 'Spend on AI assistants and agents charged to projects, by vendor.',
  },
  delivery_model: {
    title: 'Delivery model',
    what: 'Margin and CPI by delivery model, for projects active in the latest year.',
    calc: 'Margin % = margin / revenue; CPI = earned value / actual cost.',
  },

  // --- Assets ------------------------------------------------------------
  harvest_reuse: {
    title: 'Harvest and reuse',
    what: 'How well the firm captures and re-applies its delivery IP.',
    calc: 'Harvest rate = closed projects that contributed an asset / closed projects.\nReuse rate = projects that used an asset / all projects.',
  },
  cpi_reuse: {
    title: 'CPI with vs without reuse',
    what: 'Whether reusing an asset improves cost performance.',
    calc: 'Median CPI of projects that reused an asset vs those that did not.',
  },
  top_reused: {
    title: 'Top reused assets',
    what: 'Most-used library assets and the delivery hours they saved.',
    note: 'Hours saved are estimates.',
  },
  reuse_contract: {
    title: 'Reuse by contract type',
    what: 'Reuse rate and missed reuse by fixed-price vs time-and-materials.',
    calc: 'Missed reuse = hours the best-matching unused asset would have saved.',
  },
  asset_search: {
    title: 'Search the library',
    what: 'Semantic search across asset titles, descriptions and skill tags.',
    calc: 'Cortex Search service CSS_ASSET_LIBRARY.',
  },

  // --- Reasoning ---------------------------------------------------------
  bench_match: {
    title: 'Bench-to-pipeline match',
    what: 'Available people best suited to each open bid.',
    calc: 'Cosine similarity of skill embeddings (AI_EMBED), weighted by skill coverage and AI level.',
  },
  margin_leak: {
    title: 'Margin-leak detector',
    what: 'Projects forecast to finish at a loss.',
    calc: 'Forecast margin = (contract value - EAC) / contract value < 0.',
  },

  // --- Platform ----------------------------------------------------------
  groups_table: {
    title: 'Business groups',
    what: 'The six industry-aligned groups, each led by a Partner MD.',
    calc: 'Ratios computed from sums within each group (ACOCO_L2.SERVING.VW_SCORECARD_FY).',
  },
  business_groups: {
    title: 'Business groups',
    what: 'Industry-aligned operating units, each led by one Partner MD.',
  },
  ontology: {
    title: 'Ontology graph',
    what: 'Business entities and how they relate.',
    note: 'Node size = row count. Click an entity to trace its lineage.',
  },
  entity_lineage: {
    title: 'Entity lineage',
    what: 'Where an entity comes from: source tables (L0), conformed views (L1), modelled tables (L2).',
  },
  lineage_sankey: {
    title: 'Medallion lineage',
    what: 'Data flow from source systems through L1 views to L2 schemas.',
    note: 'Band width is log-scaled row count.',
  },
  cld_tables: {
    title: 'CLD tables read',
    what: 'SAP BDC tables shared to Snowflake (catalog-linked databases) read at L0.',
    note: 'Read-only: nothing is written back to the CLDs.',
  },
  sim_tables: {
    title: 'Simulated tables',
    what: 'Demo tables that fill data not available from SAP BDC.',
  },
  cld_rows: {
    title: 'Rows from BDC CLDs',
    what: 'Rows read from SAP BDC catalog-linked databases.',
  },
  l1_l2: {
    title: 'L1 views / L2 tables',
    what: 'Conformed source views (L1) and modelled business tables (L2).',
  },
  gates: {
    title: 'Gates passing',
    what: 'Checkpoints whose latest automated gate passed.',
    calc: 'Latest run per checkpoint from QUALITY.Q_CHECK_RESULTS.',
  },
  checks: {
    title: 'Checks passing',
    what: 'Individual data-quality checks passing in the latest run.',
  },
  key_nulls: {
    title: 'Keys with nulls',
    what: 'Conformed key columns containing null values.',
    note: 'Target: zero.',
  },
  freshness: {
    title: 'Freshness',
    what: 'Date range covered by each key fact table, by source.',
  },
  completeness: {
    title: 'Completeness',
    what: 'Null rate of conformed keys per L1 object.',
    calc: 'Null keys / total rows.',
  },
  fee_boundary: {
    title: 'Fee boundary',
    what: 'The app reads only governed SERVING, SEMANTIC and ONTOLOGY objects, never raw source tables.',
  },
};
