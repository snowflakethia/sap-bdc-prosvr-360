# ACOCO_ADVISOR regression (2026-10-28 13:46)

Agent `ACOCO_DB.AGENT.ACOCO_ADVISOR`, model `claude-sonnet-4-5`, 20 prompts (PRD 10): **20/20 PASS**.
Figures checked against `plan/measured_anchors.md` (story project P-0615, FS bench 1.4 %, FS roll-offs 36).

| # | Story | Prompt | Expected tool | Tools used | Routing | Figures | Phrases | Seconds | Result |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PMD-0 | Give me my FY26 ProServe360 scorecard against FY25. | portfolio | portfolio, system_execute_sql, system_execute_sql | ok | ok | ok | 45.9 | **PASS** |
| 2 | PMD-1 | Which of my FS projects drag margin the most in FY26? | project_delivery | project_delivery, system_execute_sql, system_execute_sql, system_execute_sql, server_skill, data_to_chart | ok | ok | ok | 74.4 | **PASS** |
| 3 | PMD-2 | What are the CPI and SPI of project P-0615 and its forecast margin? | project_delivery | project_delivery, system_execute_sql, system_execute_sql | ok | ok | ok | 36.7 | **PASS** |
| 4 | PMD-3 | What was my FS time mix by level in FY26 against the level targets? | workforce|portfolio | workforce, system_execute_sql, system_execute_sql, system_execute_sql | ok | ok | ok | 61.3 | **PASS** |
| 5 | PMD-4 | How many FS people roll off before 30 December 2026, and how many are below the pipeline's AI-skill level? | workforce | workforce, system_execute_sql, system_execute_sql | ok | ok | ok | 35.2 | **PASS** |
| 6 | PMD-5 | Who in FS has the highest attrition risk and what drives it? | workforce | workforce, system_execute_sql, system_execute_sql | ok | ok | ok | 38.9 | **PASS** |
| 7 | PMD-6 | Does pursuit intensity improve our win-rate? Compare above- and below-median intensity bids within size class. | pipeline_presales | pipeline_presales, system_execute_sql, system_execute_sql, system_execute_sql | ok | ok | ok | 54.3 | **PASS** |
| 8 | PMD-7 | Do People+Agents projects earn a better margin than People-only projects in FS in FY26? | project_delivery|ai_adoption | project_delivery, system_execute_sql, system_execute_sql | ok | ok | ok | 36.0 | **PASS** |
| 9 | PMD-8 | Why is project P-0615 behind schedule? | project_commentary | project_delivery, project_commentary, system_execute_sql, system_execute_sql | ok | ok | ok | 42.2 | **PASS** |
| 10 | PMD-9 | Which reusable assets did project P-0615 miss, and how many hours could they have saved? | project_delivery|asset_library | project_delivery, system_execute_sql, system_execute_sql, system_execute_sql | ok | ok | ok | 43.0 | **PASS** |
| 11 | PMD-10 | What is our win-rate when the pursuit team's skill fit is at least 0.8 versus below 0.5? | pipeline_presales | pipeline_presales, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, server_skill, data_to_chart | ok | ok | ok | 74.4 | **PASS** |
| 12 | PMD-11 | If the bid that best fits my roll-off people slips 30 days, who stays on the bench and what does it cost? | pipeline_presales|workforce | workforce, pipeline_presales, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, read_tabular | ok | ok | ok | 153.7 | **PASS** |
| 13 | PMD-12 | Does the agentic-AI curriculum pay back in later productivity? | ai_adoption | ai_adoption, system_execute_sql, system_execute_sql | ok | ok | ok | 44.7 | **PASS** |
| 14 | WHY-1 | Why are my red FS projects late? | project_commentary | project_delivery, project_commentary, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql | ok | ok | ok | 86.2 | **PASS** |
| 15 | WHY-2 | Why did FS margin change between FY25 and FY26? | portfolio|project_delivery | portfolio, system_execute_sql, system_execute_sql | ok | ok | ok | 46.0 | **PASS** |
| 16 | WHY-3 | What do the project managers say is the main problem on P-0615? | project_commentary | project_commentary | ok | ok | ok | 20.1 | **PASS** |
| 17 | R1 | Which people rolling off in FS best match my open bids? | pipeline_presales | pipeline_presales, system_execute_sql, system_execute_sql, workforce, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql | ok | ok | ok | 177.8 | **PASS** |
| 18 | R2 | Which FS consultants are in the top attrition-risk decile? | workforce | workforce, system_execute_sql, system_execute_sql, system_execute_sql | ok | ok | ok | 45.1 | **PASS** |
| 19 | R12 | Recommend assets for a data migration bid. | asset_library|project_delivery | asset_library | ok | ok | ok | 22.0 | **PASS** |
| 20 | R13 | Does AI make my skilled-but-inactive consultants more productive? | ai_adoption | ai_adoption, system_execute_sql, system_execute_sql | ok | ok | ok | 42.5 | **PASS** |

## Latency

| p50 | p90 | max |
|---|---|---|
| 45.1 s | 86.2 s | 177.8 s |

## Answers

### 1. PMD-0 - Give me my FY26 ProServe360 scorecard against FY25.

> Your Financial Services group grew revenue to $70.3M in FY26 (from $67.0M in FY25), though margin compressed to 34.3% (from 35.0%) and attrition jumped to 13.1% (from 8.9%).
> 
> 
> 
> **Pillar Assessment:**
> 
> • **Operational Excellence (Delivery):** Delivery fell to 71.3% (from 72.0%), below the blended target of ~72% given your level mix. Admin (1.4%) and Bench (1.4%) remain healthy.
> 
> • **Value Creation (Bid):** Bid rose to 16.4% (from 15.9%), stronger than most levels' targets—indicates disciplined pursuit activity. Revenue growth of $3.3M (5.0% YoY) without headcount expansion (335 vs 338 avg) suggests productivity gains.
> 
> • **People Development:** Attrition increased by 4.2 percentage points to 13.1%, signaling retention pressure. Learning held steady at 9.5%, in line with the 10% target.
> 
> **Trade-offs:** The margin drop (–0.7 pp) alongside attrition spike may reflect higher replacement hiring costs or mix shift toward junior staff. Bench staying at 1.4% despite attrition means resourcing remains tight.
> 
> **Source:** Portfolio (semantic view: SV_PORTFOLIO_360).

### 2. PMD-1 - Which of my FS projects drag margin the most in FY26?

> 
> 
> **P-0615 is your biggest margin drag**, forecast to lose 16.9 % on an $8.4M contract—costing FS roughly $1.4M in liquidated damages and wiping out profit entirely. All other active projects are forecast positive (31.7–48.6 %).
> 
> 
> 
> 
> 
> **Operational Excellence view:** P-0615 is severely over budget with a Cost Performance Index of 0.70 (earning only $0.70 for every dollar spent) and running slightly behind schedule (SPI 0.96). This Large, Fixed Price engagement has burned through cost reserves and triggered LD penalties. The next-lowest project (P-0703, X-Small Fixed Price) is still forecast at +31.7 %, so P-0615 stands alone as the portfolio outlier.
> 
> **Sources:** project_delivery semantic model (DT_PROJECT_HEALTH, DT_PROJECT_MONTH_FINANCIALS, ENT_PROJECT).

### 3. PMD-2 - What are the CPI and SPI of project P-0615 and its forecast margin?

> 
> 
> Project P-0615 has a CPI of 0.70, SPI of 0.96, and forecast margin of -16.9%.
> 
> 
> 
> **Operational Excellence Assessment:**
> - **Cost Performance (CPI 0.70)**: The project is significantly over budget, delivering only $0.70 of earned value for every $1.00 spent—a 30% cost overrun.
> - **Schedule Performance (SPI 0.96)**: Running slightly behind schedule at 96% of planned progress.
> - **Forecast Margin (-16.9%)**: The project is forecast to lose nearly 17% on the contract value after accounting for estimate-at-completion and any liquidated damages exposure.
> 
> This project requires immediate corrective action to control costs and protect margin.
> 
> **Sources:** project_delivery semantic model (DT_PROJECT_HEALTH)

### 4. PMD-3 - What was my FS time mix by level in FY26 against the level targets?

> 
> 
> Your Financial Services group delivered stronger billability than targeted in FY26, with Senior Managers and Managers notably above their Delivery goals (+7.5 and +3.4 points), but Learning time fell short across all levels by 1–3 points.
> 
> 
> 
> **People Development observations:**
> - **Delivery** outperformed across the board (Analysts +1.1, Consultants +0.6, Managers +3.4, Senior Managers +7.5, Principals +0.3), indicating strong client demand and good utilization.
> - **Bid** time met or exceeded targets at most levels (Consultants +2.9, Managers +0.6, Principals +1.6), though Senior Managers came in 1.6 points under the 40% target — manageable given their Delivery overperformance.
> - **Learning** consistently missed targets by 0.1–2.9 points; Senior Managers had the largest shortfall at −2.9, which compounds the risk when they're already working above Delivery target.
> - **Admin** stayed safely below the 3% ceiling (1.0–1.8%), and **Bench** remained in the healthy 2% transition zone (0.8–1.5%) at all levels.
> 
> **Trade-off**: Higher Delivery and Bid crowded out Learning time. While this boosted short-term Operational Excellence (billability, revenue), it may undermine medium-term People Development (skill refresh, certifications) and reduce the readiness for next-generation work.
> 
> **Sources:** Workforce semantic model (DT_PERSON_MONTH_SCORECARD, fiscal_year = 2026, md_group = 'Financial Services').

### 5. PMD-4 - How many FS people roll off before 30 December 2026, and how many are below the pipeline's AI-skill level?

> 36 people roll off before 30 December 2026, and 32 of them are below the pipeline's AI-skill level.
> 
> 
> 
> **People Development pillar:** With 89% (32 out of 36) of the roll-offs lacking the AI skills now required by your open pipeline, you have a significant upskilling or backfill challenge before year-end. Cross-reference the **bench-to-pipeline match** tool (`pipeline_presales`) to see who among your current bench meets the AI-skill bar and can transition quickly.
> 
> **Sources:** Workforce semantic model (DT_ROLL_OFF, ENT_PERSON).

### 6. PMD-5 - Who in FS has the highest attrition risk and what drives it?

> Felix Fischer and Lucas Mehta top your FS attrition risk at 68.6 %, both in decile 1. Across your highest-risk group all drivers converge: tenure months, productivity index and compa-ratio.
> 
> 
> 
> **People Development insight:** The model flags 20 people in decile 1 (highest risk) within FS. Felix and Lucas – an Analyst and Consultant – each carry 68.6 % risk; Isabel Dubois (Analyst, 58.9 %) and Wei Nguyen (Manager, 44.3 %) follow. Every single person shares the same three global drivers: **tenure months, productivity index and compensation ratio**. That cluster tells you short tenure combined with either under- or over-performance and pay misalignment creates flight risk; have retention conversations that address all three levers—career progression, workload balance and reward equity.
> 
> **Honesty rules:** The attrition model is indicative (hold-out AUC 0.90 overall, 0.57 within the simulated pool); treat these lists as a prompt for conversations, not predictions about any individual. Some of these rows include simulated data.
> 
> **Sources:** Workforce (DT_ATTRITION_RISK, ENT_PERSON, ENT_MD_GROUP).

### 7. PMD-6 - Does pursuit intensity improve our win-rate? Compare above- and below-median intensity bids within size class.

> 
> 
> Yes, pursuit intensity consistently improves win-rate across every size class in FS. Above-median intensity bids win at 52.8% versus 33.6% for below-median efforts – an uplift of **+19 percentage points**. The effect is strongest in X-Small deals (+42 points) and weakest in XX-Small (+5 points).
> 
> 
> 
> **Value Creation trade-off**: Spending above the size-class median on pursuit (0.050–0.482 vs. 0.017–0.165 intensity) delivers materially higher conversion in Large through X-Small deals. The Small segment shows the best balance – a 19.7-point lift with 0.233 average intensity. XX-Small bids return minimal lift despite the highest absolute intensity (0.482), suggesting over-investment in tiny deals.
> 
> **Sources:** pipeline_presales (bid table with pursuit intensity, win outcomes, and size class from opportunity entity).

### 8. PMD-7 - Do People+Agents projects earn a better margin than People-only projects in FS in FY26?

> 
> 
> 
> 
> **Yes** — People+Agent projects (HUMAN_AGENT) earned a **40.7% margin** in FY26, compared to **26.3%** for people-only (HUMAN) projects. That's a **14.4 percentage point** advantage.
> 
> Across 17 People+Agent engagements you delivered $27.5M in revenue and $11.2M margin, versus 13 people-only projects earning $30.1M revenue but only $7.9M margin. The hybrid delivery model shows a clear **Operational Excellence** win: more efficient execution with AI agents as a costed resource driving higher profitability.
> 
> **Sources:** project_delivery semantic model (DT_PROJECT_MONTH_FINANCIALS, ENT_PROJECT).

### 9. PMD-8 - Why is project P-0615 behind schedule?

> 
> 
> P-0615 is behind schedule and over budget because of late client data delivery and under-estimated data volumes on the critical-path migration scripting work package (WP02), with contingency exhausted. The project shows a CPI of 0.70 (30% over budget) and a forecast margin of -16.9%, with $1.46M in liquidated damages exposure.
> 
> 
> 
> **Root Causes** (from project manager status notes):
> - **Late client data delivery** — repeatedly delayed the critical-path migration scripting work package
> - **Under-estimated data volumes** — required more scripting work than planned
> - **Earned value trending below 0.8 of plan** — work completion is materially behind schedule
> - **Contingency exhausted** — no buffer remains to absorb further delays
> 
> The project's status escalated from AMBER in December 2025 to RED by March 2026 and has remained RED through July 2026. With 25 weeks of forecast slip and substantial liquidated damages exposure, this Large fixed-price Data Migration project poses significant risk to FS Operational Excellence metrics.
> 
> **Sources:** project_delivery (DT_PROJECT_HEALTH), project_commentary (CSS_PROJECT_COMMENTARY)

### 10. PMD-9 - Which reusable assets did project P-0615 miss, and how many hours could they have saved?

> 
> 
> Project P-0615 missed **3 reusable assets** across 4 work packages, which could have saved an estimated **1,920 hours**.
> 
> 
> 
> All three missed assets are Data Migration proposals that matched work packages with a 0.78 similarity score:
> 
> - **AS-0099** "Data Migration Proposal 99" matched all 4 work packages (240 hours ESTIMATED savings each)
> - **AS-0010** "Data Migration Proposal 10" matched all 4 work packages (160 hours ESTIMATED savings each)
> - **AS-0050** "Data Migration Proposal 50" matched all 4 work packages (80 hours ESTIMATED savings each)
> 
> **Operational Excellence note:** These ESTIMATED hours represent the catalogued effort savings if the matched assets had been reused. The similarity scores (0.78) indicate the semantic match strength between the asset capabilities and the work package requirements.
> 
> **Sources:** project_delivery semantic model (REASONING.VW_ASSET_MATCH, ONTOLOGY.ENT_ASSET, ONTOLOGY.ENT_WORK_PACKAGE)

### 11. PMD-10 - What is our win-rate when the pursuit team's skill fit is at least 0.8 versus below 0.5?

> With high skill fit (≥ 0.8), FS wins 53.5% of closed bids; with low fit (< 0.5), we win only 10.3% – a 5× difference.
> 
> 
> 
> 
> 
> **Value Creation Impact**: When our pursuit team's skill coverage meets or exceeds 80% of the bid's requirements, we win more than half the deals. Below 50% coverage, the win rate collapses – we're fielding teams that don't match the work, and clients notice. Of our 78 low-fit bids, 70 were lost. Every percentage point of skill fit matters at the margin, but crossing the 0.8 threshold delivers the clearest boost.
> 
> **Sources**: Semantic View pipeline_presales (DT_OPPORTUNITY_FACT via bid table).

### 12. PMD-11 - If the bid that best fits my roll-off people slips 30 days, who stays on the bench and what does it cost?

> 
> 
> **If OPP-01990 (Large Data Migration) slips 30 days, all 9 matched people stay on the bench at a cost of $84,300.**
> 
> OPP-01990 is your best-fit bid—it matches 9 roll-off people (the most of any open bid) with an average match score of 0.77. If it slips 30 days, everyone rolling off between Oct 2 and Dec 11 waits for it to start.
> 
> | Person | Level | Roll-Off Date | Match Score | Skill Coverage | 30-Day Bench Cost |
> |--------|-------|---------------|-------------|----------------|-------------------|
> | Felix Novak | Consultant | Oct 2 | 0.78 | 75% | $10,538 |
> | Isabel Owusu | Analyst | Nov 6 | 0.79 | 75% | $6,323 |
> | Leila Johnson | Analyst | Nov 6 | 0.69 | 50% | $6,323 |
> | Elena Mehta | Consultant | Nov 13 | 0.78 | 75% | $10,538 |
> | Emma Kim | Senior Manager | Nov 13 | 0.89 | 100% | $21,075 |
> | Ivan Moreau | Analyst | Nov 13 | 0.69 | 50% | $6,323 |
> | Leila Garcia | Consultant | Nov 20 | 0.68 | 50% | $10,538 |
> | Priya Singh | Analyst | Dec 11 | 0.90 | 100% | $6,323 |
> | Samuel Larsen | Analyst | Dec 11 | 0.70 | 50% | $6,323 |
> | **Total** | **5 Analysts, 3 Consultants, 1 Sr Mgr** | | **Avg 0.77** | | **$84,300** |
> 
> **Value Creation impact:** The bid delay directly increases pursuit cost-per-won-USD (an extra $84k before any revenue). If the slip causes you to lose the $2M+ Large deal, the cost is far higher.
> 
> **People Development note:** None of these 9 meet the bid's AI-skill level requirement, so even when it starts, there's a delivery-model risk.
> 
> **Sources:** Bench-to-pipel

### 13. PMD-12 - Does the agentic-AI curriculum pay back in later productivity?

> 
> 
> Yes, the agentic-AI curriculum shows a significant positive payback: people who completed it are 3.7% more productive afterward (90% CI: 3.0–4.4%). In contrast, the CORE curriculum shows a negative 4.2% association.
> 
> 
> 
> **People Development pillar:** The agentic-AI learning investment pays back through measurably higher productivity. The matched-comparison design controls for level and work type; the positive association is statistically significant at 90% confidence. The CORE curriculum's negative result may reflect time away from delivery without compensating skill gains, or selection effects if it was assigned to underperformers.
> 
> **Sources:** ai_adoption (REASONING.LEARNING_PAYBACK_TEST). These are indicative associations from a matched-comparison design (hold-out performance), not causal guarantees for individuals.

### 14. WHY-1 - Why are my red FS projects late?

> 
> 
> Your one red FS project, **P-0615** (Large Data Migration, fixed-price, $8.4M), is late primarily due to **cost overruns** (CPI 0.70) rather than schedule slippage (SPI 0.96). The critical-path migration scripting work package has been behind plan for months, driven by three recurring problems: a **staffing gap at Consultant level**, **late client data delivery**, and **under-estimated data volumes**. Contingency is exhausted and earned value has trended below 0.8 of plan.
> 
> 
> 
> **Pillar Impact:**
> - **Operational Excellence**: CPI 0.70 means every earned dollar cost $1.43; forecast to slip 25 weeks
> - **Value Creation**: -16.9% forecast margin (loss-making) with $1,464,168 in liquidated-damages exposure  
> - **People Development**: Consultant-level staffing gap on the critical path undermines delivery capacity
> 
> **Sources:** Project Commentary (search), Project Delivery (DT_PROJECT_HEALTH).

### 15. WHY-2 - Why did FS margin change between FY25 and FY26?

> 
> 
> FS margin fell 0.7 points from 35.0% to 34.3% because **costs grew faster than revenue**: total cost rose 6.0% vs. revenue up 5.0%, squeezing the margin despite $703K more profit in absolute terms.
> 
> 
> 
> **Key drivers** (Operational Excellence):
> 1. **Cost growth outpaced revenue** – the 1-point difference (6% vs 5%) eroded margin rate
> 2. **Delivery utilization slipped 0.7 points** (72.0% → 71.3%) – less billable time relative to available hours, though bench stayed constant at 1.4%
> 3. **Bench cost edged up $10K** despite flat bench percentage, reflecting higher average labor rates
> 
> While FS delivered more absolute margin (+$703K), the revenue expansion did not fully absorb the higher cost base – likely a mix of wage inflation, overhead growth, or lower realization rates on projects.
> 
> **Sources:** portfolio (DT_PORTFOLIO_MONTH, DT_FISCAL_MONTH)

### 16. WHY-3 - What do the project managers say is the main problem on P-0615?

> The main problem on P-0615 is **under-estimated data volumes** in the migration scripting work package (WP02). This has been the consistent issue reported by project managers since month 2, causing the critical path work package to fall behind plan.
> 
> The project has also experienced compounding issues including late client data delivery and a staffing gap at the Consultant level. Across all monthly reports, earned value has been trending below 0.8 of plan with contingency exhausted, maintaining a RED status on this fixed-price FS engagement.
> 
> **Sources:** Project Commentary search service

### 17. R1 - Which people rolling off in FS best match my open bids?

> Perfect! I now have the bench-to-pipeline match data for FS. The best matches are Priya Singh (Analyst, rolling off Dec 11) with 90% match score and 100% skill coverage for three Data Migration bids, and Grace Ahmed (Consultant, rolling off Nov 6) with 89% match scores and 100% skill coverage for AI Engineering bids. Let me create a clear answer with a table.
> 
> 
> 
> Your best bench-to-pipeline matches are **Priya Singh** (Analyst, 0.90 fit, 100% skill coverage, rolling off Dec 11) for Data Migration work and **Grace Ahmed** (Consultant, 0.89 fit, meets AI level for two bids, rolling off Nov 6) for AI Engineering opportunities.
> 
> The table shows the top 30 matches ranked by match score (0-1, combining semantic skill similarity and exact skill coverage). Key findings:
> 
> - **Highest fits (0.89-0.90)**: Priya Singh, Grace Ahmed, and Emma Kim (Senior Manager) cover Data Migration and AI Engineering bids with 100% skill coverage
> - **Grace Ahmed and GM6** (same person, Consultant) meet the required AI-skill level for smaller AI Engineering bids (X-Small, XX-Small)
> - **Strong 0.79-0.80 matches**: Nine analysts (Diego Smith, Isabel Ahmed, Ivan Okafor, etc.) rolling off Oct-Dec match Analytics, Testing, and Data Migration work at 75% skill coverage
> - **Match rank** shows each person's priority order — rank 1 is their best-fit bid
> 
> The "meets_ai_level" flag shows whether the person's AI-skill proficiency meets the bid's requirement; most matches don't meet it yet, so consider targeted AI upsk

### 18. R2 - Which FS consultants are in the top attrition-risk decile?

> Six FS consultants are in the top attrition-risk decile: Lucas Mehta shows the highest modelled risk at 68.6%, followed by Kenji Singh at 37.8%.
> 
> 
> 
> All six share the same top drivers: tenure, productivity index, and compensation ratio. These are associations from the indicative attrition model (hold-out AUC 0.90 overall, 0.57 within the simulated pool) and should prompt conversations rather than serve as predictions about any individual.
> 
> **Sources:** workforce (attrition_risk, person tables)

### 19. R12 - Recommend assets for a data migration bid.

> For a data migration bid, I recommend five delivery assets from our library that will accelerate your pursuit and delivery:
> 
> **Data Models (4 assets)**
> - Data Migration Data Model 123 (AS-0123)
> - Data Migration Data Model 57 (AS-0057)
> - Data Migration Data Model 31 (AS-0031)
> - Data Migration Data Model 15 (AS-0015)
> 
> **Test Pack (1 asset)**
> - Data Migration Test Pack 140 (AS-0140)
> 
> All five assets cover SAP S/4 migration, data engineering, and SQL skills. These accelerators will help you demonstrate proven methodologies in your bid and reduce delivery risk by reusing tested data models and quality-assurance frameworks.
> 
> **Source:** Asset Library

### 20. R13 - Does AI make my skilled-but-inactive consultants more productive?

> No. AI-skilled but inactive consultants showed no significant effect on productivity in FY26. The 37 people with AI skill ≥ 3 who didn't use tools had a point estimate of +2.6% (90% CI: –0.5% to +5.8%), which crosses zero.
> 
> 
> 
> **People Development pillar:** By contrast, the 146 AI-active consultants (skill ≥ 3 plus use on ≥ 50% of working days) showed a significant +11.9% association (CI: +9.8% to +13.8%). Having the skill but not using the tools yielded no measurable productivity benefit—the association appeared only when people actively used AI.
> 
> **Source:** AI productivity test (REASONING.AI_PRODUCTIVITY_TEST, stratified within level × work type, 90% bootstrap confidence intervals).
