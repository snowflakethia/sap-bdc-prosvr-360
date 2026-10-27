# ACOCO_ADVISOR regression (2026-10-28 07:34)

Agent `ACOCO_DB.AGENT.ACOCO_ADVISOR`, model `claude-sonnet-4-5`, 20 prompts (PRD 10): **20/20 PASS**.
Figures checked against `plan/measured_anchors.md` (story project P-0615, FS bench 1.4 %, FS roll-offs 36).

| # | Story | Prompt | Expected tool | Tools used | Routing | Figures | Phrases | Seconds | Result |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PMD-0 | Give me my FY26 ProServe360 scorecard against FY25. | portfolio | portfolio, system_execute_sql, system_execute_sql | ok | ok | ok | 46.6 | **PASS** |
| 2 | PMD-1 | Which of my FS projects drag margin the most in FY26? | project_delivery | project_delivery, system_execute_sql, system_execute_sql, project_commentary, project_commentary | ok | ok | ok | 59.7 | **PASS** |
| 3 | PMD-2 | What are the CPI and SPI of project P-0615 and its forecast margin? | project_delivery | project_delivery, system_execute_sql | ok | ok | ok | 27.2 | **PASS** |
| 4 | PMD-3 | What was my FS time mix by level in FY26 against the level targets? | workforce|portfolio | workforce, system_execute_sql, system_execute_sql, server_skill, data_to_chart | ok | ok | ok | 79.8 | **PASS** |
| 5 | PMD-4 | How many FS people roll off before 30 December 2026, and how many are below the pipeline's AI-skill level? | workforce | workforce, system_execute_sql, system_execute_sql | ok | ok | ok | 36.2 | **PASS** |
| 6 | PMD-5 | Who in FS has the highest attrition risk and what drives it? | workforce | workforce, system_execute_sql, system_execute_sql | ok | ok | ok | 43.2 | **PASS** |
| 7 | PMD-6 | Does pursuit intensity improve our win-rate? Compare above- and below-median intensity bids within size class. | pipeline_presales | pipeline_presales, system_execute_sql, system_execute_sql, system_execute_sql | ok | ok | ok | 63.0 | **PASS** |
| 8 | PMD-7 | Do People+Agents projects earn a better margin than People-only projects in FS in FY26? | project_delivery|ai_adoption | project_delivery, system_execute_sql, system_execute_sql | ok | ok | ok | 38.0 | **PASS** |
| 9 | PMD-8 | Why is project P-0615 behind schedule? | project_commentary | project_delivery, project_commentary, system_execute_sql, system_execute_sql, system_execute_sql | ok | ok | ok | 58.6 | **PASS** |
| 10 | PMD-9 | Which reusable assets did project P-0615 miss, and how many hours could they have saved? | project_delivery|asset_library | project_delivery, system_execute_sql | ok | ok | ok | 30.8 | **PASS** |
| 11 | PMD-10 | What is our win-rate when the pursuit team's skill fit is at least 0.8 versus below 0.5? | pipeline_presales | pipeline_presales, system_execute_sql, system_execute_sql, server_skill, data_to_chart | ok | ok | ok | 51.2 | **PASS** |
| 12 | PMD-11 | If the bid that best fits my roll-off people slips 30 days, who stays on the bench and what does it cost? | pipeline_presales|workforce | pipeline_presales, workforce, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, server_skill, data_to_chart | ok | ok | ok | 134.6 | **PASS** |
| 13 | PMD-12 | Does the agentic-AI curriculum pay back in later productivity? | ai_adoption | ai_adoption, system_execute_sql | ok | ok | ok | 35.5 | **PASS** |
| 14 | WHY-1 | Why are my red FS projects late? | project_commentary | project_delivery, system_execute_sql, project_commentary, project_commentary, project_commentary, system_execute_sql, system_execute_sql, system_execute_sql, project_commentary | ok | ok | ok | 84.4 | **PASS** |
| 15 | WHY-2 | Why did FS margin change between FY25 and FY26? | portfolio|project_delivery | portfolio, system_execute_sql, system_execute_sql, system_execute_sql | ok | ok | ok | 62.2 | **PASS** |
| 16 | WHY-3 | What do the project managers say is the main problem on P-0615? | project_commentary | project_commentary | ok | ok | ok | 20.7 | **PASS** |
| 17 | R1 | Which people rolling off in FS best match my open bids? | pipeline_presales | pipeline_presales, system_execute_sql, system_execute_sql, system_execute_sql, system_execute_sql, server_skill, data_to_chart | ok | ok | ok | 97.1 | **PASS** |
| 18 | R2 | Which FS consultants are in the top attrition-risk decile? | workforce | workforce, system_execute_sql, system_execute_sql | ok | ok | ok | 41.3 | **PASS** |
| 19 | R12 | Recommend assets for a data migration bid. | asset_library|project_delivery | asset_library, asset_library | ok | ok | ok | 32.5 | **PASS** |
| 20 | R13 | Does AI make my skilled-but-inactive consultants more productive? | ai_adoption | ai_adoption, system_execute_sql | ok | ok | ok | 35.4 | **PASS** |

## Latency

| p50 | p90 | max |
|---|---|---|
| 46.6 s | 84.4 s | 134.6 s |

## Answers

### 1. PMD-0 - Give me my FY26 ProServe360 scorecard against FY25.

> 
> 
> 
> 
> FS grew revenue 5% to $70.3M but margin fell 0.7 points to 34.3%; the biggest flag is attrition, which jumped from 8.9% to 13.1%.
> 
> **Operational Excellence:** Delivery ticked down from 72.0% to 71.3%, and margin % compressed from 35.0% to 34.3% despite absolute margin rising $0.7M. Admin (1.4%) and bench (1.4%) remain excellent—both well below ceilings.
> 
> **Value Creation:** Revenue climbed 5% with lower headcount (-0.8%), and bid share rose from 15.9% to 16.4%, signaling stronger pre-sales investment.
> 
> **People Development:** Attrition surged 4.2 points to 13.1%, the most material risk. Learning held steady at 9.5%, meeting the 10% target band.
> 
> **Sources:** Portfolio semantic model (DT_PORTFOLIO_MONTH, ENT_MD_GROUP, DT_FISCAL_MONTH).

### 2. PMD-1 - Which of my FS projects drag margin the most in FY26?

> Your two biggest margin drags in FY26 are **P-0615** (Atlas Bank Data Migration) losing **$408,098** at -5.4% margin, and **P-0533** (Crown Insurance PMO) losing **$117,307** at -78.9% margin.
> 
> 
> 
> **P-0615** (Atlas Bank) is the clear outlier: this large fixed-price Data Migration project started FY26 already in trouble and stayed RED through July. The PM notes show under-estimated data volumes in the migration scripting work package, earned value trending below 0.8, and exhausted contingency. The problem was flagged as early as January.
> 
> **P-0533** (Crown Insurance) shows -78.9% margin but smaller absolute loss; it's an AGENT_LED PMO project—early commentary shows it GREEN through November 2025, so the loss likely emerged in the back half of FY26.
> 
> **Operational Excellence impact**: Both are large fixed-price projects where scope creep (P-0615) or agent delivery model risk (P-0533) eroded margin. The Data Migration under-estimation drove $408K in cost overrun without corresponding revenue recovery.
> 
> **Sources**: project_delivery (DT_PROJECT_MONTH_FINANCIALS), project_commentary (CSS_PROJECT_COMMENTARY).

### 3. PMD-2 - What are the CPI and SPI of project P-0615 and its forecast margin?

> 
> 
> Project P-0615 has a **CPI of 0.70, SPI of 0.96, and a forecast margin of -16.9%**, indicating the project is 30% over budget and running a bit behind schedule with a projected loss.
> 
> 
> 
> **Operational Excellence context:**
> - **CPI 0.70**: For every dollar spent, only $0.70 of earned value was delivered—the project is significantly over budget
> - **SPI 0.96**: Slightly behind schedule (4% under planned progress)
> - **Forecast margin -16.9%**: The project is expected to finish at a loss of nearly 17% of contract value after accounting for liquidated damages exposure
> 
> **Sources:** project_delivery (DT_PROJECT_HEALTH)

### 4. PMD-3 - What was my FS time mix by level in FY26 against the level targets?

> Your FY26 Financial Services time mix tracked well against level targets overall, with strong delivery performance and controlled Admin/Bench levels.
> 
> 
> 
> **Key Performance by Pillar:**
> 
> **Operational Excellence (Delivery):** All levels met or exceeded targets. Senior Managers delivered 52.5% vs 45% target (+7.5 pp), demonstrating strong billability even with high bid responsibilities. Analysts (76.1%), Consultants (71.6%), and Managers (63.4%) all on or slightly above target.
> 
> **Value Creation (Bid):** Well-managed across all levels. Principal bid time at 51.6% vs 50% target is excellent. Consultant bid time elevated at 16.9% vs 14% target (+2.9 pp), which is acceptable if win-rate justifies the investment. Managers and Senior Managers on target at 25.6% and 38.4%.
> 
> **People Development (Learning):** Below target at Consultant (9.1% vs 10%), Manager (8.8% vs 10%), and Senior Manager (7.1% vs 10%) levels. This -1 to -3 pp shortfall may limit capability building for mid-career talent. Principals met the 10% target exactly; Analysts nearly on target at 9.9%.
> 
> **Admin & Bench:** Excellent control. Admin well below the 3% ceiling across all levels (1.0-1.8%). Bench at healthy transition levels (0.8-1.5%), well within the 2% target.
> 
> 
> 
> **Trade-offs:** Higher delivery at Senior Manager level (Operational Excellence +7.5 pp) came partly at the expense of Learning (People Development -2.9 pp). Consider whether Q4 pushed learning aside for client commitments.
> 
> **Sources:** workforce sem

### 5. PMD-4 - How many FS people roll off before 30 December 2026, and how many are below the pipeline's AI-skill level?

> 36 FS people roll off before 30 December 2026, and 32 of them (89%) are below the pipeline's required AI-skill level.
> 
> 
> 
> This is a significant bench-to-pipeline mismatch: nearly 9 in 10 people rolling off lack the AI proficiency that open bids require. You may want to check the bench-to-pipeline match tool (pipeline_presales model) to see which specific opportunities these 32 could support, or explore upskilling options for them before they roll off.
> 
> **Source:** Workforce Performance (DT_ROLL_OFF).

### 6. PMD-5 - Who in FS has the highest attrition risk and what drives it?

> 
> 
> Twenty-eight FS people are in the highest attrition-risk decile, led by Felix Fischer (Analyst, 68.6 %) and Lucas Mehta (Consultant, 68.6 %). All share the same top model drivers: tenure, productivity, and compensation ratio.
> 
> 
> 
> **People Development Context:**  
> The model flags these individuals as requiring retention conversations. The common drivers—tenure, productivity, and compa-ratio—suggest systematic patterns: people with shorter tenure, lower productivity, or pay below market are more likely to consider leaving. The model is indicative (hold-out AUC 0.90 overall, 0.57 within the simulated pool) and should prompt manager check-ins, not predictions about any one person. Focus retention efforts on addressing pay equity, productivity support, and early-tenure engagement.
> 
> **Sources:** Workforce Performance (attrition_risk table).

### 7. PMD-6 - Does pursuit intensity improve our win-rate? Compare above- and below-median intensity bids within size class.

> 
> 
> Yes, pursuit intensity consistently improves win-rate across every size class, with the strongest effect on X-Small bids (+41.9 pp) and gains of 4.9 to 19.7 percentage points elsewhere. However, above-median intensity also raises pursuit cost per won USD in every segment—a Value Creation trade-off between winning more and spending more to win.
> 
> 
> 
> **Key findings:**
> 
> • **X-Small bids** see the biggest lift: 61.1% win-rate (above median) vs 19.2% (below), a 41.9 pp improvement  
> • **Small bids** (largest volume): 53.0% vs 33.3%, +19.7 pp  
> • **Large bids**: 54.5% vs 37.0%, +17.5 pp  
> • **Efficiency penalty**: pursuit cost per won USD ranges from 1.9× higher (Large) to 2.4× higher (XX-Small) when intensity is above median
> 
> **Value Creation perspective:** Higher intensity drives more wins but lowers ROI on pursuit spend. The optimal strategy depends on pipeline scarcity—if you need bookings, invest above median; if pipeline is healthy, stay disciplined on cost per win.
> 
> **Sources:** pipeline_presales (DT_OPPORTUNITY_FACT, ENT_OPPORTUNITY, ENT_CUSTOMER, ENT_MD_GROUP).

### 8. PMD-7 - Do People+Agents projects earn a better margin than People-only projects in FS in FY26?

> 
> 
> Yes, People+Agents projects earned significantly better margin: 40.7% versus 26.3% for People-only projects in FS in FY26.
> 
> 
> 
> **Operational Excellence (Margin):** HUMAN_AGENT delivery improved margin by 14.4 percentage points on similar revenue scale ($27,525k vs $30,144k), generating $11,193k margin across 17 projects versus $7,920k across 13 People-only projects.
> 
> **Value Creation:** The agent model treats AI as a costed resource at compute rates rather than human bill rates, directly improving project profitability while maintaining delivery quality.
> 
> **Sources:** project_delivery semantic model (DT_PROJECT_MONTH_FINANCIALS, ENT_PROJECT).

### 9. PMD-8 - Why is project P-0615 behind schedule?

> 
> 
> P-0615 is severely behind schedule with a 25-week forecast slip, a cost performance index of 0.70 (30% over budget), and -16.9% forecast margin with $1,464,168 in liquidated-damages exposure.
> 
> 
> 
> **Root causes:**
> 
> 1. **Client delays** – Late client data delivery repeatedly delayed the migration scripting work package (WP02), which is on the critical path
> 2. **Staffing gap at Consultant level** – Inability to staff the right level forced use of more expensive resources or less productive alternatives, driving the 0.70 CPI
> 3. **Earned value consistently below 80% of plan** – Work is being completed slower than planned
> 4. **Contingency exhausted** – No buffer remains to absorb further issues
> 
> 
> 
> The team of 323 has 201 Analysts (58% of delivery hours), which should control costs, but the Consultant-level staffing gap forced suboptimal pyramid adjustments. This is a large fixed-price Data Migration project, so cost overruns hit margin directly.
> 
> **Pillar impact:** Operational Excellence (poor CPI/SPI) drives negative Value Creation (forecast margin -16.9%). The staffing gap suggests a People Development constraint.
> 
> **Sources:** project_delivery (DT_PROJECT_HEALTH, DT_PROJECT_TEAM), project_commentary (CSS_PROJECT_COMMENTARY)

### 10. PMD-9 - Which reusable assets did project P-0615 miss, and how many hours could they have saved?

> 
> 
> Project P-0615 missed three reusable assets that could have saved an estimated **1,920 hours** in total.
> 
> 
> 
> All three are Data Migration proposals, with the largest opportunity (960 hours) from AS-0099. These are **estimated** savings based on catalogued effort benchmarks—the actual impact would depend on how well each asset's approach matched P-0615's specific requirements.
> 
> **Pillar:** Operational Excellence—asset reuse directly reduces delivery hours, improving productivity and margin.
> 
> **Source:** project_delivery (asset_match and asset tables)

### 11. PMD-10 - What is our win-rate when the pursuit team's skill fit is at least 0.8 versus below 0.5?

> When pursuit teams have strong skill fit (≥ 0.8), FS wins 53.5% of bids; below 0.5, just 10.3%.
> 
> 
> 
> HIGH fit delivers a **43.2 percentage-point advantage** over LOW. This is Value Creation in action: matching skilled people to the pursuit sharply raises conversion.
> 
> 
> 
> **Practical implication:** Every bid below 0.5 skill fit is nearly four-times more likely to fail than a high-fit pursuit; investing in MEDIUM-band staffing still yields 44% win-rate.
> 
> **Sources:** pipeline_presales (semantic view SV_PIPELINE_PRESALES).

### 12. PMD-11 - If the bid that best fits my roll-off people slips 30 days, who stays on the bench and what does it cost?

> 
> 
> The best-fit bid for your roll-off people is **OPP-01990**, a Large Data Migration opportunity worth $8.7M with 9 people matched to it. If that bid slips 30 days, those **9 people stay on the bench at a cost of $120,000** (5 Analysts, 3 Consultants, 1 Senior Manager).
> 
> 
> 
> 
> 
> **Pillar framing:**
> - **Value Creation**: OPP-01990 has the highest roll-off team match (9 people, 0.77 avg fit score, 69% skill coverage). None meet the bid's AI-skill level. If it slips, you lose a month of pipeline conversion momentum on your largest matched opportunity.
> - **People Development**: The 9-person cohort rolls off between 2 Oct and 11 Dec. Felix Novak goes idle first (2 Oct); the two Dec roll-offs (Priya Singh, Samuel Larsen) have the shortest exposure. Emma Kim (Senior Manager, CEO) drives 25% of the total bench cost.
> - **Operational Excellence**: $120,000 unplanned bench cost breaks down as $45k (Analysts) + $45k (Consultants) + $30k (Senior Manager). Every week of further slip adds another $28k.
> 
> **Sources:** pipeline_presales (bench_match, opportunity), workforce (person, scorecard).

### 13. PMD-12 - Does the agentic-AI curriculum pay back in later productivity?

> 
> 
> Yes, the agentic-AI curriculum is associated with measurable productivity gains. For FS, people who completed the curriculum show a **3.7%** productivity uplift (90% CI: 3.0–4.4%), and that result is statistically significant. Firm-wide the association is even stronger at **4.9%** (CI: 4.6–5.1%).
> 
> 
> 
> **People Development insight**: The payback metric compares productivity *after* a learning episode to *before*, controlling for matched peers who did not complete the training. Both FS and firm-wide results show a positive, significant association—the curriculum correlates with faster delivery, not just skill acquisition. The 90% confidence intervals exclude zero, meaning the effect is reliable within the tested population.
> 
> **Sources**: Learning payback test (ai_adoption / REASONING.LEARNING_PAYBACK_TEST).

### 14. WHY-1 - Why are my red FS projects late?

> 
> 
> Your sole RED FS project is **P-0615** (Large Data Migration, Fixed Price), which is 25 weeks behind schedule with a -16.9% forecast margin and $1.46M liquidated-damages exposure.
> 
> 
> 
> **Why it's late** (Operational Excellence issues):
> 
> The project commentary reveals three recurring problems on the critical-path migration scripting work package (WP02):
> 
> 1. **Under-estimated data volumes** – The team underestimated the complexity and scale of the data to be migrated, forcing rework.
> 
> 2. **Staffing gap at Consultant level** – The project has struggled to fill mid-level positions needed for the scripting work, slowing delivery.
> 
> 3. **Late client data delivery** – The client has repeatedly delayed providing source data, blocking the migration team.
> 
> The project has been earning **below 0.8 of planned value** (SPI 0.96) with contingency exhausted. The CPI of 0.70 means you're only getting 70 cents of earned value for every dollar spent – the combination of schedule slip, scope underestimation, and staffing gaps is burning budget faster than the team can deliver.
> 
> **Sources:** project_delivery (DT_PROJECT_HEALTH), project_commentary (CSS_PROJECT_COMMENTARY)

### 15. WHY-2 - Why did FS margin change between FY25 and FY26?

> 
> 
> FS margin % fell from 35.0% to 34.3% (down 0.7 points) despite revenue growing $3.3M to $70.3M. Costs rose $2.6M (faster than revenue), driven by a shift in time mix away from billable work.
> 
> 
> 
> 
> 
> **By Pillar:**
> 
> **Operational Excellence (Delivery):** Delivery utilization dropped from 72.0% to 71.3% (down 0.7pp). With virtually identical headcount (335 vs 338), the group delivered only 1,905 more hours despite 9,066 more available hours. This lower billability reduced operational efficiency.
> 
> **Value Creation (Pipeline):** Bid intensity rose from 15.9% to 16.4% (up 0.5pp), adding 4,705 hours to pursuit activities. This is a trade-off – higher pursuit investment today may drive future wins, but it immediately reduces margin by pulling capacity from billable delivery.
> 
> **People Development:** Admin overhead increased from 1.2% to 1.4% (up 0.2pp, still within the <5% target). Learning remained steady at 9.5%, and bench held at a healthy 1.4%.
> 
> **Bottom line:** The margin compression stems from **Operational Excellence** (lower delivery %) offsetting revenue growth, compounded by **Value Creation** pursuit investment. The shift of ~5,000 hours from delivery to bid/admin cost roughly $400k in lost margin contribution at typical bill rates.
> 
> **Sources:** portfolio (DT_PORTFOLIO_MONTH), fiscal_month (DT_FISCAL_MONTH).

### 16. WHY-3 - What do the project managers say is the main problem on P-0615?

> The project managers report two recurring issues on P-0615: **under-estimated data volumes** and **late client data delivery**. Both problems have pushed the migration scripting work package (WP02) behind plan, driving earned value below 0.8 and exhausting contingency. The project has been RED since month 4, with WP02 consistently identified as the critical path.
> 
> **Sources:** project_commentary (Cortex Search)

### 17. R1 - Which people rolling off in FS best match my open bids?

> You have **35 people rolling off** in FS over the next 90 days matched to open bids. The best matches are **Grace Ahmed** (Consultant, match 0.89, 100% skill coverage, meets AI level) for AI Engineering opportunities, **Emma Kim** (Senior Manager, 0.89, 100%) and **Priya Singh** (Analyst, 0.90, 100%) for Data Migration.
> 
> 
> 
> 
> 
> **Key patterns:**
> - **11 people meet AI-level requirements** for their best match (blue dots in chart), concentrated in AI Engineering, Cloud Platform, and one AI Engineering Large bid.
> - **Strongest overall matches** (≥0.85 score, 100% coverage): Grace Ahmed, Emma Kim, and Priya Singh are deployment-ready for their top bids.
> - **Coverage gaps** exist at 25-50%: Lucas Singh (0.55, 25%), Mateo Ito (0.56, 25%), and Ruth Ito (0.64, 50%) need skill development or are better suited for stretch assignments.
> - **Work type distribution**: Data Migration (10 people), AI Engineering (6), Analytics (6), Testing (6), others smaller.
> 
> The bench-to-pipeline match uses a 0.6 × semantic similarity + 0.4 × exact skill-coverage formula; scores ≥0.75 with 75%+ coverage typically indicate strong pursuit-team additions.
> 
> **Sources:** pipeline_presales (VW_BENCH_TO_PIPELINE_MATCH).

### 18. R2 - Which FS consultants are in the top attrition-risk decile?

> Six FS Consultants are in the top attrition-risk decile, listed by modelled risk probability (68.6 % down to 3.7 %). These are conversation prompts, not predictions about any individual; the model's hold-out accuracy is strong firm-wide (AUC 0.90) but weaker within the simulated pool (AUC 0.57).
> 
> 
> 
> The global top drivers are tenure, productivity index, and compa-ratio. All six share this pattern, suggesting newer or lower-performing consultants with compensation misalignment warrant retention conversations.
> 
> **Source:** Workforce semantic view (DT_ATTRITION_RISK, ENT_PERSON)

### 19. R12 - Recommend assets for a data migration bid.

> 
> 
> I'll search our asset library for data migration accelerators and templates.For a data migration bid, I recommend the following assets from our library:
> 
> **Core Data Migration Assets:**
> - **AS-0123**: Data Migration Data Model 123
> - **AS-0031**: Data Migration Data Model 31
> - **AS-0015**: Data Migration Data Model 15
> - **AS-0057**: Data Migration Data Model 57
> - **AS-0140**: Data Migration Test Pack 140
> 
> **Testing & Quality Assurance:**
> - **AS-0097**: Testing Data Model 97
> - **AS-0116**: Testing Data Model 116
> - **AS-0146**: Analytics Test Pack 146
> 
> These assets cover the essential skills for data migration: SAP S/4 migration, data engineering, SQL, test automation, quality engineering, and data validation. The data models provide reusable structures for migration work, while the test packs accelerate validation and quality assurance.
> 
> Using these assets can reduce pursuit intensity and improve your team's skill coverage score for the bid—key factors in Value Creation. If you'd like, I can also check which assets were missed on similar past projects to estimate potential hours saved.
> 
> **Source:** Asset Library (Cortex Search)

### 20. R13 - Does AI make my skilled-but-inactive consultants more productive?

> 
> 
> No significant effect. Among your 37 skilled-but-inactive consultants in FY26, the data show an association with +2.6% productivity, but the 90% confidence interval ranges from –0.5% to +5.8%, crossing zero—not statistically significant.
> 
> 
> 
> **Sources:** ai_adoption semantic model (REASONING.AI_PRODUCTIVITY_TEST). This is an observational association within level × work type strata, not a causal claim, and the "skilled-but-inactive" band includes consultants with AI skill ≥ 3 who had no AI tool use in the quarter.
