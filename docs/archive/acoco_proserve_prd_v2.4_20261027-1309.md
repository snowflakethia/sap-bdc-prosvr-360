# PRD - ACoCo ProServe360: Partner MD Decision Support on SAP BDC + Snowflake (v2.1, SPCS edition)

**Document type:** Product Requirements Document - **master document for the demo**
**Version:** 2.4 - 27 October 2026 (v2.3 + revised time targets: Learning 10 % at every level, group Bid ~15 %; mix measured on the generated data)
**Supersedes:** `docs/references/acoco_prd/acoco_oldref/ACoCo_Agentic_AI_Decision_Support_Demo_PRD.md` v1.1 (Streamlit edition, three personas, four roles)
**Target account:** `SFSEAPAC.SNOWFLAKE_SAP_APJ` (AWS, connector `SNOWFLAKE_APJ`, status `CONNECTED`)
**Demo "today":** **1 October 2026** - data window **1 Oct 2021 to 30 Sep 2026** (five fiscal years, FY22-FY26)

> **SAP is the System of Record. Snowflake is the System of Context and Reasoning.**
> SAP S/4HANA and SAP SuccessFactors (via SAP People Intelligence on SAP Business Data Cloud) own the
> transactions and the people master. Snowflake joins them zero-copy with data SAP does not hold -
> CRM pipeline, AI-agent telemetry, unstructured project commentary - and reasons over the combined
> context with Semantic Views, Cortex Agents, Cortex Search and Snowflake ML. Decisions go back to SAP
> as actions; derived data products go back to BDC.

---

## 0. What changes from v1.1

| # | Area | v1.1 (built) | v2.0 (this document) | Why |
|---|---|---|---|---|
| C1 | Roles | 4 custom roles (`ACOCO_ADMIN`, `ACOCO_REFRESH`, `ACOCO_APP`, `ACOCO_PERSONA`) + row access policy | **`ACCOUNTADMIN` only.** No role is created. No row access policy. | User decision: demo simplicity |
| C2 | Personas | MD, Senior Manager, Individual Consultant (10 stories) | **One persona: Partner MD** (Financial Services group). SM and IC content survives only as drill-downs the MD performs | User decision |
| C3 | People data | Emulated SuccessFactors entities (Workforce Person, Job Information, Skills, Learning...) | **SAP People Intelligence data products** on BDC; four already present on the account as catalog-linked databases | User decision; see section 3 |
| C4 | L0 | Emulated `ACOCO_L0` schemas, synthetic | **Real catalog-linked databases (CLDs)** from connector `SNOWFLAKE_APJ` + a BDC-shaped synthetic gap-fill database for products not yet shared | User decision; see section 4 |
| C5 | Front end | Streamlit in Snowflake `ACOCO_COMMAND_CENTER` | **React + Express container on a Snowpark Container Services compute pool**, modelled on `snowflakethia/sap-bdc-supply-chain-360` | User decision; see section 8 |
| C6 | Time | as-of 31 Aug 2026; 24 months (Sep 2024-Aug 2026); FY Sep-Aug | **as-of 1 Oct 2026; 60 months (Oct 2021-Sep 2026); FY Oct-Sep (FY22-FY26)** | User decision; see section 6 |
| C7 | Fee boundary | Enforced by grants (`ACOCO_APP` has no privilege on L0/L1) | **Enforced by design, evidenced by `ACCESS_HISTORY`** - grants cannot enforce it under a single `ACCOUNTADMIN` role | Consequence of C1; see section 5.6 |
| C8 | Story figures | Measured on the v1.1 dataset (e.g. P-0417 forecast margin -0.6 %) | **All story figures are design targets until re-measured** on the new 60-month dataset | The generator, window and calendar change; no v1.1 figure carries over |
| C9 | Story structure (v2.1) | Flat list of stories | **Business scenario -> three pillars (Operational Excellence, Value Creation, People Development) -> ProServe360 overlay -> one epic each -> stories.** New stories PMD-0 (scorecard), PMD-9 (asset harvest/reuse), PMD-10 (pursuit-team optimisation), PMD-11 (capacity what-if) | User decision; see section 2 |
| C10 | Asset library (v2.1) | Not modelled | **New `ACOCO_SIM.ASSETS` product** (catalogue, harvest, usage) + `CSS_ASSET_LIBRARY` + page P11; SAP holds no asset library | Needed for Operational Excellence; see 4.3, 7, 8.3 |
| C11 | Time model (v2.2) | Utilisation / billability / bench | **Five categories - Delivery, Bid, Learning, Admin, Bench - with targets by level** (2.1). Pillars deliberately unbalanced: Delivery largest; Bid judged on win-rate; Learning on shorter future delivery; Admin < 5 %; Bench ~2 % transition | User decision |
| C12 | AI productivity (v2.2) | AI margin by delivery model | **Explicit test whether AI skill and AI use raise productivity**, within level x work type, with confidence interval (PMD-7, R13); learning payback (PMD-12, R14) | User decision |
| C14 | Medallion (v2.3) | L1 = source-area views; ontology = registry only; `VW_*` inside marts | **L0 = CLDs (+ `ACOCO_SIM`), L1 = nine data domains (views, conformed keys), L2 = data assets** in `CORE`, `ONTOLOGY` (`ENT_*`, `REL_*`, `ONT_*`), five marts, `REASONING`, `SEMANTIC`, `SERVING`, `QUALITY` | User decision; SC360 review (Appendix D); see 5.1, 7 |
| C13 | Context and architecture (v2.2) | One "Demo Context" link | **Four context pages**: Business Overview, Dashboard Overview, Demo Overview, Platform Architecture; five-layer platform view (5.2); **ontology** registry and graph (5.3) | User decision |

Everything not listed - the medallion discipline, single definition of every metric, logic-free front end, the
as-of control view, honesty markers - carries over unchanged.

---

## 1. Executive summary

| Item | Decision |
|---|---|
| Story | ACoCo's revenue is people-hours priced by bill code; its risks are fixed-price overrun, wasted pursuit effort, bench cost and skills mismatch. A **Partner MD** runs her group on three pillars - **Operational Excellence** (deliver on target, harvest and reuse assets), **Value Creation** (put pursuit effort where it wins) and **People Development** (billable, skilled, AI-ready consultants) - under a **ProServe360 overlay** that balances every hour between delivery, bids, learning and bench. One app and one agent answer the questions SAP alone cannot, across five years of history, and the actions go back to SAP. |
| Time model | Every hour is **Delivery, Bid, Learning, Admin or Bench**, with targets by level (2.1). Delivery is the largest share and the focus of lower bill codes; Bid is judged on win-rate; Learning on shorter future delivery; Admin < 5 %; Bench driven to ~2 % (transition only). Whether AI skill raises productivity is tested, not assumed |
| Epics | EPIC-OX, EPIC-VC, **EPIC-PD (the SAP People Intelligence epic)**, EPIC-PS (overlay) - section 2.4 |
| Persona | **Partner MD, Financial Services group** - owns the group's client portfolio (projects, opportunities) and the group's people (home cost centre). Can toggle to firm-wide. |
| Data | **L0** = SAP BDC data products as **catalog-linked databases** (S/4HANA finance/project + SAP People Intelligence workforce) + `ACOCO_SIM` (BDC-shaped synthetic data for products not yet shared) + AI-agent telemetry. **L1** passthrough views. **L2** dynamic tables + 5 Semantic Views. |
| Reasoning | Cortex Agent `ACOCO_ADVISOR` (5 Cortex Analyst tools + 1 Cortex Search tool), Cortex `AI_COMPLETE` for in-page "Ask Cortex" explanations, Snowflake ML for forecasts and risk scores. |
| Front end | **ACoCo Command Center** - React (Vite, Tailwind, Recharts) + Express (Node 20) in one container, served by an SPCS **service** on compute pool `ACOCO_POOL`, public endpoint, sidebar navigation and Ask-Cortex buttons as in Supply Chain 360. |
| Security model | Everything runs as `ACCOUNTADMIN`. The service's identity is the service owner (`ACCOUNTADMIN`). |
| Time | Demo today = **2026-10-01**. Data = 2021-10-01 to 2026-09-30. FY = Oct-Sep. "Current" = last closed month **Sep 2026** = FY26 close. |
| Scale (design) | ~1,000 consultants (with hires and leavers over 5 years: ~1,700 distinct people), ~400 projects, ~800 opportunities, 60 closed fiscal months, six MD groups. |

---

## 2. Business scenario, pillars and epics

### 2.1 The business scenario - how ACoCo makes (and loses) money

**ACoCo Consulting** is a ~1,000-person professional-services firm organised in six industry groups (Financial
Services, Products, Health & Public Service, Communications/Media/Tech, Resources, Cross-Industry AI). Each group is
run by a **Partner MD** who owns two things: a **portfolio of client work** (projects in delivery and deals being
bid) and a **group of people** (the consultants whose home cost centre is in the group).

**ACoCo sells people-hours.** Every consultant carries a **bill code** that sets two numbers - what an hour costs
ACoCo and what it can be billed at:

| Level | Bill code | Cost / day (USD) | Bill rate / day (USD) | Role in the pyramid |
|---|---|---|---|---|
| Analyst | 30-39 | ~300 | 620-800 | Builds |
| Consultant | 40-49 | ~500 | 1,030-1,300 | Builds, leads small teams |
| Manager | 50-59 | ~800 | 1,540-1,900 | Runs a team |
| Senior Manager | 60-69 | ~1,000 | 2,050-2,500 | Owns a Small project or a work package; co-leads bids |
| Principal | 70+ | ~1,300 | 2,560+ | Leads Medium/Large projects and bids; 6 are MDs |

A project's economics are therefore set by three levers:

1. **The pyramid** - the mix of bill codes on the team. A Large team (1 Principal + 3-5 Medium teams) bills
   > USD 92,800/day against ~USD 47,200 direct cost; after the 35 % delivery overhead S/4HANA applies through the
   costing sheet, the sold margin is ~31 %. Putting a Senior Manager where a Manager was planned, or an Analyst
   where a Consultant was sold, moves margin by points.
2. **Hours burned versus hours sold.** More than 60 % of contracts are **fixed price**. Revenue is recognised by
   percentage of completion; every hour over plan is lost margin, and late delivery adds liquidated damages
   (0.5-1.0 % of contract value per week). One Large fixed-price overrun can erase a group's year.
3. **How much is built from scratch.** Teams that reuse a **harvested asset** - an accelerator, data model, code
   template, test pack, AI agent or proposal library from an earlier project - deliver the same scope in fewer
   hours. On fixed price the saved hours are margin; on a bid they are a sharper price.

**The life cycle of an hour.** A deal is **bid** by a pursuit team (Principal, Senior Managers, some Consultants)
booking hours to a pre-sales internal order - cost with no revenue. About half of bids are won. A won deal becomes a
**project** staffed from people rolling off other work; Large projects (~20 % of count, ~80 % of revenue) break into
Small-team **work packages** owned by Senior Managers. At close, the best work should be **harvested** into the asset
library. Consultants who roll off without a next assignment fall to the **bench** - full cost, no revenue - until they
are redeployed to a project or a bid, or put into **learning**.

**Five uses of time - deliberately unbalanced.** Every available hour is booked to exactly one of five categories.
They are not meant to be equal: **Delivery is the business** and takes the largest share, and each other category has
its own objective, which is never "more hours":

| Category | What it is | Objective | Who carries it |
|---|---|---|---|
| **Delivery** | Billable hours on a customer project WBS | **Maximise** - it is the revenue | Mostly the lower bill codes: Analysts and Consultants spend ~70-75 % of their time here |
| **Bid** | Hours on an opportunity's pre-sales internal order | **Raise the win-rate**, not the bid hours. Fewer, better-staffed pursuits beat many thin ones; success = win-rate and pursuit cost per won USD | Everyone contributes (~10 % for Analysts); Senior Managers and Principals carry 40-50 % |
| **Learning** | Training and certification hours | **Shorten future delivery time** - learning pays back when the same scope is later delivered in fewer hours (higher margin on fixed price) | Everyone, ~10 % |
| **Admin** | Internal, non-client work | **Keep below 5 %** | Everyone |
| **Bench** | Available hours with no booking (derived, not booked) | **Drive to almost zero.** A residual ~2 % is structural - people transiting between projects and bids - and is accepted | Nobody by design |

Target time allocation by level (share of available hours; sums to 100 %; revised 27 Oct 2026 - plan D-02-11):

| Level | Delivery (= target billability) | Bid | Learning | Admin | Bench (transition) |
|---|---|---|---|---|---|
| Analyst | **75 %** | 10 % | 10 % | 3 % | 2 % |
| Consultant | **71 %** | 14 % | 10 % | 3 % | 2 % |
| Manager | **60 %** | 25 % | 10 % | 3 % | 2 % |
| Senior Manager | 45 % | **40 %** | 10 % | 3 % | 2 % |
| Principal | 35 % | **50 %** | 10 % | 3 % | 2 % |
| *Group (ACoCo headcount mix)* | *~70 %* | *~15 %* | *~10 %* | *~3 %* | *~2 %* |

The MD's job is to move her group's actual mix towards this target across ~330 people and ~90 concurrent projects
and bids - above all, to convert the remaining bench into delivery and to make the bid hours win.

**Agentic AI changes the arithmetic - if it raises productivity.** AI-skilled consultants using AI tools and AI assets
should deliver the same scope in fewer hours: margin up on fixed price, and capacity freed for more wins and new
AI-led offerings. **That is a hypothesis the MD must test, not assume**: does a higher AI-skill level, and actual use
of AI tools, show up as higher productivity (earned hours / actual hours) at the same level and work type? If it does,
AI learning and AI tools are funded like any asset; if not, the spend is cut. Turning AI into margin needs three
things at once: delivery discipline, a bid machine that wins, and people with the right skills. **They are the three
pillars.**

**Priya Nair, Partner MD Financial Services, on 1 October 2026** (FY26 has just closed; figures are design targets,
section 6.3): her people spend ~65 % of their time in delivery against a ~70 % target, ~15 % bidding and ~10 % learning,
and **~7 % on the bench against ~2 %**; one Large fixed-price banking migration is forecast to lose money; bids with above-median pursuit effort
win far more often than the rest, but pursuit hours are spread thinly across every deal; 30-40 of her people roll off
before 30 December with no next assignment, most below the AI-skill level her pipeline needs; she has funded AI
learning for two years without knowing whether it made anyone faster; and attrition, though
falling, is concentrated in the Managers who hold her largest accounts.

She already has SAP. **S/4HANA** shows her each project's P&L and work breakdown structure. **SAP People
Intelligence** on SuccessFactors shows her headcount, availability and attrition. Neither tells her *which* bench
consultant should go to *which* bid, whether reusing last year's migration accelerator would have saved the
loss-making project, or whether the AI training she paid for is visible in margin. Those answers need SAP's records
**joined with data SAP does not hold** - CRM pursuit data, the asset library, AI-tool telemetry, project commentary -
and reasoned over. That is the demo.

### 2.2 The Partner MD

| Attribute | Value |
|---|---|
| Name and title | **Priya Nair** - Partner, Managing Director, Financial Services (bill code 72) |
| Scope | Group portfolio: projects/opportunities whose client belongs to the FS group; group people: home cost centre in the FS group. Toggle: **Firm-wide**. |
| Horizon | Five fiscal years for trend; FY26 (just closed) for performance; next 90 days (from 2026-10-01) for forward risk |
| Decisions | Where to intervene on margin and delivery risk; which assets to fund and mandate; which bids to pursue and with whom; where bench is forming and how to redeploy; which skills to build or hire; who is at risk of leaving |
| Scoping mechanism | **No row access policy.** The app passes `MD_GROUP_ID` as a filter into every `SEMANTIC_VIEW()` query; the agent receives it in its instructions. This is a demo convenience, not a security boundary, and the presenter says so. |

Senior Manager and consultant views from v1.1 survive only as drill-downs the MD performs (project -> work package ->
person).

### 2.3 Three pillars and the ProServe360 overlay

```
     ProServe360 overlay - one hour, five uses, one P&L - Delivery first
     Delivery ##################################   ~70 %   (maximise)
     Bid      ########                             ~15 %   (raise win-rate)
     Learning #####                                ~10 %   (shorten future delivery)
     Admin    #                                    < 5 %   (minimise)
     Bench    #                                    ~2 %    (transition only)
     +-----------------------+-----------------------+-----------------------+
     | 1 OPERATIONAL         | 2 VALUE CREATION      | 3 PEOPLE DEVELOPMENT  |
     |   EXCELLENCE          |                       |                       |
     | Deliver on time, on   | Put pursuit effort    | Keep consultants      |
     | target; harvest and   | where it wins         | in delivery, skilled, |
     | reuse assets          |                       | AI-productive         |
     +-----------------------+-----------------------+-----------------------+
       projects, WBS, assets   opportunities, bids     people, skills, AI use
```

The pillars are **not balanced by design**. Operational Excellence owns the Delivery hours, which are most of the
firm; Value Creation owns the small Bid share and is judged on win-rate; People Development owns Learning and Bench
and is judged on bench approaching zero and on learning (including AI) showing up as faster delivery.

| | 1 Operational Excellence | 2 Value Creation | 3 People Development | ProServe360 overlay |
|---|---|---|---|---|
| **Goal** | Deliver the portfolio on time and on target - this pillar carries the Delivery hours, the largest share of time; turn delivered work into reusable assets and reuse them | Raise the win-rate per pursuit hour - not the bid hours | Keep consultants in Delivery (bench -> ~2 %, admin < 5 %); build the skills, including AI, that shorten future delivery | Move the actual time mix to the level targets (2.1): Delivery first, Bid for win-rate, Learning for productivity, Admin < 5 %, Bench ~2 % |
| **MD question** | "Which projects decide my year, and am I reusing what we have already built?" | "Am I bidding the right deals with the right people and the right effort?" | "Who is on the bench, who is about to be, and are they skilled - and using AI - for what I am selling next?" | "Where should my next hour of capacity go, and what does it do to margin, bookings and people?" |
| **Key measures** | Revenue, margin, sold vs forecast margin, CPI, SPI, EAC, LD exposure, margin by bill-code mix, on-time %, **asset harvest rate, asset reuse rate, hours saved by reuse** | Pipeline, win-rate, bookings, book-to-bill, **pursuit cost per won USD, win-rate by pursuit intensity and by bid-team skill fit**, asset use in proposals | Utilisation, billability (= Delivery share) vs level target, bench hours and cost vs ~2 %, admin share vs 5 %, roll-off in 90 days, skill index, AI-skill level, AI-curriculum hours, **AI usage, AI productivity uplift, learning payback**, attrition and attrition risk | Time mix (Delivery / Bid / Learning / Admin / Bench) actual vs target by level, group P&L bridge, forward 90-day bench-to-pipeline cover, cross-pillar risk list |
| **SAP holds** | S/4HANA project, WBS, plan, Universal Journal, sales contract, activity-type rates | S/4 pre-sales internal-order cost; sales contract once won | SAP People Intelligence: Core Workforce, Employee Availability, Planned Working Time, Assignment Additional Information (+ Skills, Learning, Performance to be shared) | All of the left |
| **SAP does not hold** | Asset library and asset-use records; PM status commentary; AI-agent telemetry per project | CRM opportunity stages, probabilities, required skills, outcomes; who was on the pursuit team and in what role | AI-tool usage per person (OpenAI, Anthropic, Cortex); pipeline skill demand from CRM; the link between people data and project margin | The joined, five-year history across all of the above |

### 2.4 Epic stories - what SAP data alone cannot answer

One epic per pillar and one for the overlay. Each epic names the cross-system question that neither S/4HANA nor
SAP People Intelligence can answer on its own, the data Snowflake joins, and the reasoning it applies.

#### EPIC-OX - Operational Excellence: "Deliver on target and compound what we build"

> **As** the Partner MD, **I want** to see which projects in my portfolio decide the year, why the at-risk ones are
> slipping, and whether they used the assets we harvested from earlier projects, **so that** I intervene before a
> fixed-price project turns into a loss and make reuse the default way ACoCo delivers.

| Item | Content |
|---|---|
| Why SAP alone cannot answer | S/4HANA has the project P&L, WBS and plan, so it shows *that* a project is over budget. It has no asset library, no record of which asset a team reused or harvested, and no project-status commentary, so it cannot show *why* the project is slipping or *what reuse would have saved*. Five-year EAC history by size class and delivery model needs to be rebuilt from journal lines. |
| SAP data products | `ENTRYVIEWJOURNALENTRY_V1`, `JOURNALENTRYHEADER_V1`, `PROJECT_V1`, `FINANCIALPLANNINGENTRYITEM_V1`, `SALESCONTRACT_V1`, `COSTCENTERACTIVITYTYPE_V1` (bill-code rates), `CUSTOMER_V1`, `PROFITCENTER_V1` |
| Non-SAP context | `ACOCO_SIM.ASSETS` (asset catalogue, harvest and reuse events), PM status commentary, AI-agent telemetry, `ACOCO_SIM` CustomerProject/Timesheet |
| Snowflake reasoning | `SV_PORTFOLIO_360`, `SV_PROJECT_DELIVERY`; Cortex Search over commentary (`CSS_PROJECT_COMMENTARY`) and over the asset library (`CSS_ASSET_LIBRARY`); `AI_CLASSIFY` of slippage root causes; asset-to-work-package matching (R12) |
| Stories | PMD-1, PMD-2, PMD-8, **PMD-9** |
| Done when | The MD goes from the five-year portfolio to the one at-risk project, sees its CPI, SPI, EAC and critical work package, reads the "why" from PM notes, and sees which harvested assets it did not use and the estimated hours they would have saved |
| People Intelligence use | **Light** - Core Workforce `payGrade` gives the bill code of each team member for the pyramid-mix view; no PI analytics |

#### EPIC-VC - Value Creation: "Bid the right deals with the right team and the right effort"

> **As** the Partner MD, **I want** to know which bids are worth more pursuit effort, who should be on each pursuit
> team, and what that effort has returned historically, **so that** I put scarce Principal and Senior Manager hours
> where they raise the win-rate instead of spreading them across every deal.

| Item | Content |
|---|---|
| Why SAP alone cannot answer | S/4HANA records pre-sales cost on internal orders, but the opportunity, its stage, probability, required skills and outcome live in CRM. Without the join, pursuit cost cannot be tied to win or loss, and the pursuit team's skill fit to the deal cannot be measured. |
| SAP data products | `ENTRYVIEWJOURNALENTRY_V1` (pre-sales GL on internal orders), `COSTCENTERACTIVITYTYPE_V1`, `CUSTOMER_V1`, `SALESCONTRACT_V1` (won deals) |
| Non-SAP context | `ACOCO_SIM` Opportunity (CRM shape), InternalOrder, pursuit-team timesheet hours by person and role, assets cited in proposals |
| Snowflake reasoning | `SV_PIPELINE_PRESALES`; win-rate by pursuit intensity within size class; win-rate by bid-team skill fit and by Principal involvement; fixed-price bid advisor over five years of sold-vs-actual margin (R4) |
| Stories | PMD-6, **PMD-10** |
| Done when | The MD sees win-rate by pursuit intensity and by team fit within deal size, the open bids where adding effort or a better-fit person is likely to pay, and the historical overrun to price into a fixed-price bid |
| People Intelligence use | **Medium** - Core Workforce (level, bill code) and Skills give pursuit-team composition and skill fit; PI is a dimension here, not the subject |

#### EPIC-PD - People Development: "Keep every consultant in delivery, skilled and AI-productive" (the People Intelligence epic)

> **As** the Partner MD, **I want** one view of how each of my consultants' time is used - Delivery, Bid,
> Learning, Admin, Bench - against their level's target, with their skills, their AI-skill level, their actual use of
> AI tools and whether that AI skill and use makes them measurably more productive, **so that** I drive bench towards
> zero, keep admin below 5 %, and fund only the learning and AI that shortens delivery.

| Item | Content |
|---|---|
| Why SAP alone cannot answer | SAP People Intelligence answers HR questions well - headcount, availability, attrition, skills - inside SuccessFactors. It does not see where those hours were billed (S/4 timesheets and project margin), what the pipeline will demand (CRM), or whether people actually use AI tools (OpenAI, Anthropic, Cortex telemetry). Utilisation vs billability by bill code, bench cost, skills-vs-pipeline gaps and "AI skill shows up in productivity" are all cross-system joins. |
| **SAP People Intelligence data products** | **Core Workforce Data** (level/bill code via `payGrade`, cost centre -> MD group, manager, tenure, hires, terminations, `moveOutReason`), **Employee Availability** (available hours = utilisation denominator, absence), **Workforce Planned Working Time** (capacity baseline), **Assignment Additional Information** (people-lead / engagement-partner dotted lines); to be shared: **Skills (Talent Intelligence Hub)** incl. the Agentic-AI skill family, **Learning History**, **Performance & Goals**, **Compensation**, **Succession** |
| Other SAP data products | `ENTRYVIEWJOURNALENTRY_V1` (billed hours, bench cost at activity-type rate), `COSTCENTERACTIVITYTYPE_V1` |
| Non-SAP context | AI-tool telemetry per person (OpenAI, Anthropic, Cortex `ACCOUNT_USAGE`); CRM required skills and start dates; `ACOCO_SIM` Timesheet, ResourceAssignment |
| Snowflake reasoning | `SV_WORKFORCE_PERFORMANCE`, `SV_AI_ADOPTION`; **AI productivity test** (productivity index by AI-skill level and AI-usage band, controlled for level and work type, with confidence interval - R13); learning payback (R14); attrition-risk model (R2); skills-demand forecast (R3); bench-to-pipeline matching with `AI_EMBED` (R1) |
| Stories | PMD-3, PMD-4, PMD-5, PMD-7, **PMD-12** |
| Done when | The MD sees the time mix by level against target over five years (bench vs ~2 %, admin vs 5 %), the 90-day roll-off list with each person's skills and AI-skill level against the pipeline's need, whether AI skill and AI use raise productivity (with the size and confidence of the effect), whether learning shortened later delivery, and who is at elevated attrition risk |
| People Intelligence use | **Primary.** This is the epic built on SAP People Intelligence: all four shared PI data products plus the requested Skills, Learning and Performance products. Snowflake adds the S/4, CRM and AI-telemetry context PI does not hold |

#### EPIC-PS - ProServe360 overlay: "Spend each hour where it earns the most"

> **As** the Partner MD, **I want** one view of my group across the three pillars - how time splits between
> Delivery, Bid, Learning, Admin and Bench against the level targets, what each gap costs in margin, bookings and
> people risk, and what happens if I move people between them - **so that** I convert bench into delivery and
> winning bids, and send the resulting action back to SAP.

| Item | Content |
|---|---|
| Why SAP alone cannot answer | The trade-offs span three SAP domains (S/4 project finance, S/4 pre-sales, SuccessFactors people) plus CRM and the asset library. No SAP application holds the joined history or can run a "move these five people from bench to that bid" scenario across them. |
| Data | Everything above, joined at person x month and project/opportunity x month |
| Snowflake reasoning | `SV_PORTFOLIO_360` (overlay metrics) with all five Semantic Views behind the `ACOCO_ADVISOR` agent; redeployment what-if (R7); cross-pillar risk list; actions written back to SAP (staffing request, re-plan, learning assignment) - narrated |
| Stories | **PMD-0**, **PMD-11** |
| Done when | The MD opens one page that shows FY26 against FY25 for each pillar, the time-mix bar (actual vs target) by level, the bench gap in USD, and the top five cross-pillar risks; asks the agent one what-if and gets a figure with its sources |
| People Intelligence use | **Indirect** - consumes EPIC-PD's PI-based measures (capacity, availability, attrition risk) as one of three inputs |

**Which epic uses SAP People Intelligence?** **EPIC-PD (People Development)** is the People Intelligence epic: it
is built on the four PI data products already on the account and the PI products requested in section 3.2. EPIC-VC
uses PI as a dimension (bid-team level and skills), EPIC-OX uses only the bill code from Core Workforce, and the
ProServe360 overlay consumes EPIC-PD's outputs.

### 2.5 User stories (all for the Partner MD)

Format: story -> demo question -> data products -> L2 / Semantic View -> SEC indicator (indicators I1-I12 are
unchanged from v1.1 section 3.1 and reproduced in Appendix C). PMD-1..PMD-8 keep their v2.0 numbers; PMD-0, PMD-9,
PMD-10 and PMD-11 are new in v2.1; PMD-12 is new in v2.2.

**ProServe360 overlay (EPIC-PS)**

**PMD-0 - ProServe360 scorecard.** I need FY26 against FY25 for each pillar on one page - margin and on-time
(Operational Excellence), win-rate and pursuit cost per won USD (Value Creation), Delivery share, bench, admin and
AI productivity uplift (People Development) - and the time mix by level against target, so I see where the gaps sit
before drilling into a pillar.
- *"Give me my group's FY26 ProServe360 scorecard against FY25, and how my people's hours split between Delivery, Bid, Learning, Admin and Bench by level against target - what does the bench gap cost?"*
- All of the below. `SV_PORTFOLIO_360` (overlay metrics), `DT_CAPACITY_MIX_MONTH`, `DT_TIME_TARGET`. SEC: I1, I2, I3, I4.

**PMD-11 - Capacity what-if.** I need to see what moving named roll-off people to a bid or to learning does to bench
cost, the bid's win probability and next quarter's billability, so I decide redeployment with numbers.
- *"If the eight Consultants rolling off P-xxxx in November join the Opp-yyyy pursuit, what happens to Q1 FY27 bench cost and to the bid's skill fit?"*
- `SV_WORKFORCE_PERFORMANCE`, `SV_PIPELINE_PRESALES`, `VW_BENCH_TO_PIPELINE_MATCH`. Reasoning R1, R7. SEC: I4, I8.

**Operational Excellence (EPIC-OX)**

**PMD-1 - Portfolio health and the Pareto tail.** I need revenue, margin, bookings and on-time status for my
portfolio over five years, with Large projects separated, so I intervene on the few projects that decide the year.
- *"Show FY22-FY26 revenue and margin by project size class for my group, and list every live fixed-price project whose forecast margin is below 10 %."*
- EntryViewJournalEntry, JournalEntryHeader, Project, FinancialPlanningEntryItem, CostCenter, ProfitCenter, Customer, SalesContract.
- `SV_PORTFOLIO_360`, `SV_PROJECT_DELIVERY`. SEC: I1, I3, I6.

**PMD-2 - Fixed-price exposure and pyramid drift (drill: project -> work package).** I need CPI, SPI, EAC,
liquidated-damages exposure and margin erosion for one at-risk project and its work packages, and the sold versus
actual bill-code mix, so I re-plan before it turns into a loss.
- *"For my worst fixed-price project, show plan vs actual by month, EAC, SPI, which work package is the critical path, and how the actual level mix differs from what we sold."*
- EntryViewJournalEntry, FinancialPlanningEntryItem, Project (WBS), CostCenterActivityType, Core Workforce (`payGrade`), `ACOCO_SIM` CustomerProject. `SV_PROJECT_DELIVERY`. SEC: I6, I8.
- (Absorbs v1.1 SM-1, SM-2.)

**PMD-8 - "Why?" questions.** I need the delivery narrative behind a number, so I can challenge the project lead.
- *"Why is P-xxxx behind schedule?"* -> Cortex Search over PM status commentary (`CSS_PROJECT_COMMENTARY`), causes classified with `AI_CLASSIFY`.

**PMD-9 - Asset harvest and reuse.** I need the asset library's harvest and reuse record - which closed projects
harvested an asset, which live projects and bids reused one, the hours reuse saved and its effect on CPI and
margin - and the assets an at-risk project could still use, so I fund the assets that pay and make reuse the default.
- *"Which harvested assets did my FY26 projects reuse, what did reuse save in hours and margin, and which assets match the critical work package on my worst fixed-price project?"*
- `ACOCO_SIM.ASSETS` (catalogue, harvest, usage), EntryViewJournalEntry, Project (WBS). `SV_PROJECT_DELIVERY` (asset tables), `CSS_ASSET_LIBRARY`. Reasoning R12. SEC: I3, I10.

**Value Creation (EPIC-VC)**

**PMD-6 - Pursuit payback.** I need win-rate by pursuit intensity, pursuit cost per won USD, bookings and
book-to-bill, so I find the pursuit effort that maximises win-rate - not the bid hours - and stop over-investing in
bids that will not win.
- *"Compare win-rate for above- vs below-median pre-sales investment within deal size, and show FY26 book-to-bill."*
- `ACOCO_SIM` Opportunity, InternalOrder; EntryViewJournalEntry (pre-sales GL). `SV_PIPELINE_PRESALES`. SEC: I2, I8.

**PMD-10 - Pursuit-team optimisation.** I need, for each open bid, the pursuit hours spent by level, the team's skill
fit to the deal's required skills, Principal involvement and the assets cited, against the historical win-rate of
similar bids, so I add or move pursuit effort only where it raises the odds.
- *"Which of my open bids above USD 5 M have below-median skill fit or no Principal, and who on my bench would raise the fit?"*
- `ACOCO_SIM` Opportunity, InternalOrder, Timesheet (pre-sales hours by person); Core Workforce (level); Skills; `ACOCO_SIM.ASSETS`. `SV_PIPELINE_PRESALES` (pursuit-team table), `VW_BENCH_TO_PIPELINE_MATCH`. Reasoning R1, R4. SEC: I2, I9.

**People Development (EPIC-PD - SAP People Intelligence)**

**PMD-3 - Time mix and bench.** I need each level's Delivery, Bid, Learning, Admin and Bench shares against target by
month, bench cost against the ~2 % transition allowance, admin against the 5 % ceiling, and the 90-day roll-off list
from 1 Oct 2026, so I convert bench into delivery before the cost lands.
- *"What is my group's time mix by level against target over the last 12 months, how much did bench above 2 % cost in September, and who rolls off before 30 Dec 2026 without a next assignment?"*
- **People Intelligence:** Core Workforce Data, Employee Availability, Workforce Planned Working Time, Assignment Additional Information; `ACOCO_SIM` Timesheet, ResourceAssignment. `SV_WORKFORCE_PERFORMANCE`. SEC: I4, I8.

**PMD-4 - Skills supply vs demand.** I need the skills profile (incl. the Agentic-AI family) of my people against
the skills my open pipeline requires, so I decide to train, hire or partner.
- *"Which skills does my open pipeline need that my roll-off population lacks, and what AI-curriculum learning would close the gap?"*
- **People Intelligence:** Skills / Talent Intelligence Hub, Learning; `ACOCO_SIM` Opportunity. `SV_WORKFORCE_PERFORMANCE`, `SV_PIPELINE_PRESALES`. SEC: I9, I11.

**PMD-5 - Attrition and retention risk.** I need annualised voluntary attrition by level over five years and the
people currently at elevated risk, so I act on retention before key-account knowledge walks out.
- *"What is voluntary attrition by level FY22-FY26, and which of my Managers and above on Large accounts have an elevated attrition-risk score?"*
- **People Intelligence:** Core Workforce Data (`terminations`, `moveOutReason`, `organizationalTenure`, `payGrade`, `compa` from salary range), Compensation, Performance. `SV_WORKFORCE_PERFORMANCE` + ML score in `DT_ATTRITION_RISK`. SEC: I5.

**PMD-7 - Does AI skill raise productivity?** I need productivity (earned / actual hours) by AI-skill level and by
actual AI-tool use, compared within the same level and work type, with the size and confidence of the effect, and the
skilled-but-inactive list, so I fund AI learning and tools only where they make people faster - and see that
productivity in project CPI and margin.
- *"Within the same level and work type, are consultants with AI-skill level 3+ who actively use AI tools more productive than those who do not - by how much, and how sure are we? Who is skilled but not using AI? Show margin and CPI for People+Agents vs People-only projects FY24-FY26."*
- **People Intelligence:** Skills (Agentic-AI family), Core Workforce (level); EntryViewJournalEntry (`AGT_*` activity allocations), CostCenterActivityType, AI telemetry, Timesheet (`ZZ_AI_ASSISTED`). `SV_AI_ADOPTION` (`DT_AI_PRODUCTIVITY`), `SV_WORKFORCE_PERFORMANCE`. Reasoning R13. SEC: I10, I11, I12.
- **Honesty rule:** the answer is a correlation within strata, not proof of cause; the two AI-enabled projects seeded to under-perform must appear, and the agent says "no significant effect" when the confidence interval spans zero.

**PMD-12 - Learning payback.** I need, for people who completed a learning curriculum (AI and non-AI), their
productivity on comparable work packages before and after, and the hours and margin it saved, so I keep funding
learning that shortens delivery and stop learning that does not.
- *"Did FY25 AI-curriculum learning shorten FY26 delivery for the people who took it, compared with similar people who did not, and what did it save in hours and margin?"*
- **People Intelligence:** Learning History, Skills, Core Workforce; Timesheet, EntryViewJournalEntry. `SV_WORKFORCE_PERFORMANCE`, `SV_AI_ADOPTION`. Reasoning R14. SEC: I11.

### 2.6 Traceability

| Story | Epic | People Intelligence | Non-SAP context | Semantic View(s) | Page | Reasoning |
|---|---|---|---|---|---|---|
| PMD-0 | PS | indirect | all | `SV_PORTFOLIO_360` | P0 | - |
| PMD-11 | PS | Core Workforce, Availability | CRM | `SV_WORKFORCE_PERFORMANCE`, `SV_PIPELINE_PRESALES` | P7, P10 | R1, R7 |
| PMD-1 | OX | - | - | `SV_PORTFOLIO_360`, `SV_PROJECT_DELIVERY` | P1 | - |
| PMD-2 | OX | Core Workforce (`payGrade`) | - | `SV_PROJECT_DELIVERY` | P2 | - |
| PMD-8 | OX | - | PM commentary | Cortex Search | P2, P10 | R9 |
| PMD-9 | OX | - | Asset library | `SV_PROJECT_DELIVERY`, `CSS_ASSET_LIBRARY` | P11 | R12 |
| PMD-6 | VC | - | CRM | `SV_PIPELINE_PRESALES` | P5 | - |
| PMD-10 | VC | Core Workforce, Skills | CRM, asset library | `SV_PIPELINE_PRESALES` | P5 | R1, R4 |
| PMD-3 | PD | **Core Workforce, Availability, Planned Working Time, Assignment Add. Info** | - | `SV_WORKFORCE_PERFORMANCE` | P3 | - |
| PMD-4 | PD | **Skills, Learning** | CRM | `SV_WORKFORCE_PERFORMANCE`, `SV_PIPELINE_PRESALES` | P4 | R3 |
| PMD-5 | PD | **Core Workforce, Compensation, Performance** | - | `SV_WORKFORCE_PERFORMANCE` | P4 | R2 |
| PMD-7 | PD | **Skills, Core Workforce** | AI telemetry | `SV_AI_ADOPTION` | P6 | R6, R13 |
| PMD-12 | PD | **Learning, Skills, Core Workforce** | - | `SV_WORKFORCE_PERFORMANCE`, `SV_AI_ADOPTION` | P6 | R14 |

### 2.7 Business definitions (single definition of every metric)

| Term | Definition in L2 |
|---|---|
| Available hours | Employee Availability `plannedWorkHours - dailyAbsenceHours` |
| Billable hours | Approved timesheet hours on a customer-project WBS with billable `BillableControl` |
| Billability | Billable hours / available hours = **Delivery share**, compared with the level target (2.1) |
| Utilisation | (Delivery + Bid + Learning + Admin hours) / available hours = 1 - Bench share |
| Time mix | Share of available hours in **Delivery, Bid, Learning, Admin, Bench**, by level and month; the five shares sum to 100 % |
| Time-mix gap | Actual minus target share per category (targets in 2.1, table `DT_TIME_TARGET`) |
| Bench hours / cost | Available - booked hours; cost = bench hours x level cost rate (`CostCenterActivityType` planned price / 8). **Excess bench** = bench above the 2 % transition allowance |
| Admin share | Admin hours / available hours; ceiling 5 % |
| Pursuit (pre-sales) cost / intensity | Hours booked to an opportunity's internal order x level cost rate; intensity = pursuit cost / opportunity size |
| Win-rate | Won / (won + lost) opportunities closed in the period |
| Pursuit cost per won USD | Pursuit cost of all closed bids / value of won bids |
| Bid-team skill fit | Share of the opportunity's required skills held at proficiency >= 3 by at least one pursuit-team member |
| Project cost / margin | People cost (activity allocations) + AI-agent cost + 35 % overhead + expenses; margin = revenue - cost |
| Pyramid drift | Actual minus sold share of hours by level on a project or work package; margin effect = drift x (bill rate - cost rate) |
| EAC / CPI / SPI | EAC = sold cost / CPI; CPI = earned value / actual cost; SPI = earned value / planned value to date |
| LD exposure / forecast margin | LD = contract x LD rate per week x weeks late (fixed price); forecast margin = (contract - EAC - LD) / contract |
| Asset harvest rate | Closed projects that registered >= 1 asset / closed projects |
| Asset reuse rate | Projects (or bids) with >= 1 recorded asset use / projects (or bids) started |
| Hours saved by reuse | Sum of the asset's catalogued effort saving for each recorded use, marked **ESTIMATED** |
| Skill index / AI-skill level | Weighted mean TIH proficiency (1-5) over the level's required skills / max proficiency across the Agentic-AI skill family |
| AI usage | Active days, sessions and cost per person from AI-tool telemetry mapped to `userId` |
| Productivity index | Earned hours of completed work packages / actual hours booked |
| AI productivity uplift | Mean productivity index of AI-active people (AI-skill >= 3 and AI usage on >= 50 % of working days in the quarter) minus that of the rest, **within the same level x work type stratum**, weighted by hours; reported with a 90 % bootstrap confidence interval |
| Learning payback | Change in productivity index on comparable work packages in the 6 months after vs before a curriculum completion, minus the same change for a matched non-learner group; hours saved = payback x actual hours |
| Roll-off | Assignment ending within 90 days of the as-of date with no later assignment |
| Voluntary attrition | Voluntary terminations / average headcount, annualised |

---

## 3. SAP People Intelligence - the data products needed

SAP People Intelligence (on SAP Business Data Cloud) packages SuccessFactors data as SAP-managed data products and
ships its own insight apps on top. For ACoCo, Snowflake consumes the **same data products** zero-copy and joins them
with S/4HANA project finance - something People Intelligence alone does not do.

### 3.1 Already shared to `SFSEAPAC.SNOWFLAKE_SAP_APJ` (verified 2026-10-26)

| Data product (CLD) | Tables used | Rows | What it gives ACoCo |
|---|---|---|---|
| **Core Workforce Data** `COREWORKFORCEDATA_V1` | `coreworkforce_standardfields` (93 cols) | 70,738 | Effective-dated job record per person: `userId`, `startDate`/`endDate`, `managerId`, `costCenter`, `department`, `businessUnit`, `jobCode`, `jobTitle`, `payGrade` (-> level/bill code), `fte`, `employmentStatus`, `eventReasonCode`, `moveOutReason`, `terminations`, `externalHires`, `organizationalTenure`, `sop/eop/avgHeadcount`, `annualSalary`, `salaryRange`/`midPoint`. **Headcount, attrition, hierarchy, level** |
| **Employee Availability** `EMPLOYEEAVAILABILITY_V1` | `employeeavailability` | 1,545,495 | Per assignment per day: `plannedWorkHours`, `absenceType`, `dailyAbsenceHours`, `isPublicHoliday`, `isLoa`, `availabilityStatus`. **Available hours = the utilization denominator** |
| **Workforce Planned Working Time** `WORKFORCEPLANNEDWORKINGTIME_V1` | `plannedworkingtime` | 1,545,495 | Planned working time per assignment/day; holiday and non-working-day flags. **Capacity baseline** |
| **Assignment Additional Information** `ASSIGNMENTADDITIONALINFORMATION_V1` | `jobrelationship`, `jobrelationshipdetail`, `jobrelationshipdetailgrid` | ~1,300 each | Matrix / dotted-line relationships (e.g. engagement partner, people lead). **Second reporting line for staffing** |

Measured coverage: Core Workforce `startDate` 2023-01-01 to 2026-07-01, 1,684 distinct users; Employee Availability
`workDate` 2024-07-09 to 2027-01-09, 1,698 assignments. **Neither covers the full Oct 2021-Sep 2026 window** - see
section 4.3.

### 3.2 Recommended additional People Intelligence data products (request from SAP BDC)

Names follow SuccessFactors module naming; **confirm the exact product names and versions in the BDC catalog
before requesting the share** - they could not be verified from this account.

| Priority | Data product (to confirm) | SF module | Needed for | Gap if absent |
|---|---|---|---|---|
| **Must** | Skills / Workforce Skills (Talent Intelligence Hub) | TIH | PMD-4, PMD-7 (AI-skill level, skill index, Agentic-AI skill family) | Simulated in `ACOCO_SIM` |
| **Must** | Learning History / Learning Assignment | SF Learning | PMD-4 (AI-curriculum hours, gap-closing items) | Simulated |
| **Must** | Time Off / Absence | Employee Central Time Off | PMD-3 (absence detail beyond `absenceType`) | Partly covered by Employee Availability |
| Should | Compensation (pay components, merit, bonus) | Compensation | PMD-5 (compa-ratio, pay-vs-market as attrition driver) | Use `annualSalary`/`midPoint` from Core Workforce |
| Should | Performance & Goals (ratings, goal attainment) | PMG | PMD-5 (performance x attrition), level targets | Simulated |
| Should | Succession & Talent Pools | Succession | PMD-5 (key-person risk on Large accounts) | Simulated flag |
| Could | Recruiting (requisitions, applications, time-to-fill) | Recruiting | Hire-vs-redeploy decision in PMD-4 | Out of scope |
| Could | Onboarding | Onboarding | Ramp-up of new hires (productivity curve) | Out of scope |
| Could | Organizational Structure (cost centre, department, legal entity foundation objects) | EC Foundation | Group hierarchy labels | Use S/4 CostCenter/ProfitCenter hierarchies |

Individual pay is used **only** as an aggregated driver in the attrition model; no per-person salary is shown in the app.

### 3.3 S/4HANA data products used (CLDs already on the account)

| CLD | Key tables | Rows | Use |
|---|---|---|---|
| `ENTRYVIEWJOURNALENTRY_V1` | `operationalacctgdocitem` | 13.7 M | Universal Journal: project revenue/cost, pre-sales GL, `AGT_*` agent allocations |
| `JOURNALENTRYHEADER_V1` | `journalentry` | 4.6 M | Reversal exclusion, document type |
| `PROJECT_V1` | `project`, `workbreakdownstructureelement`, `wbselementmilestone` | 778 / 10,663 / 786 | Project + WBS structure, basic/forecast dates, responsible person |
| `FINANCIALPLANNINGENTRYITEM_V1` | `financialplanningentryitem`, `planningcategory` | 4.2 M | Budget/plan by period (BAC, plan curve) |
| `COSTCENTER_V1` | `costcenter`, `costcenterhierarchynode`, texts | 1,625 | MD groups, AI platform cost centres |
| `COSTCENTERACTIVITYTYPE_V1` | `costcenteractivitytype`, texts | 263 | Level rates and `AGT_*` agent activity types |
| `PROFITCENTER_V1` | `profitcenter`, hierarchy | 838 | Group P&L attribution |
| `GENERALLEDGERACCOUNT_V1` | `generalledgeraccount`, hierarchies, semantic tags | 34,829 | Revenue / cost / pre-sales GL classification |
| `CUSTOMER_V1` | `customer`, `customercompanycode`, ... | 3,450 | Clients and industry |
| `SALESCONTRACT_V1` | `salescontract`, `salescontractitem` | 112 / 137 | Contract value, fixed-price vs T&M |
| `FISCALYEAR_V1` | `fiscalcalendardate`, `fiscalperiod` | 153,498 | Fiscal calendar (variant to be chosen for Oct-Sep, see 6.1) |
| `JOURNALENTRYCODES_V1`, `JOURNALENTRYITEMCODES_V1` | code lists | - | Code texts |

Duplicate CLD `SAP_CUSTOMER` holds the same content as `CUSTOMER_V1`; use `CUSTOMER_V1` (the `_V1` naming is the
pattern for this tenant). The supply-chain, mining and maintenance CLDs on the account are **not** used.

---

## 4. L0 design - zero-copy CLDs plus a gap-fill

### 4.1 Connector and CLD creation

The account already has connector `SAP_BDC_CONNECTOR_APJ.PUBLIC.SNOWFLAKE_APJ` (`CONNECTED`, SAP BDC endpoint on
`prod-us10`). **Reuse it; do not create a second connector.** Every CLD listed in 3.1 and 3.3 already exists and is
owned by `ACCOUNTADMIN`. New People Intelligence products (3.2), once shared by the SAP administrator, are added with:

```sql
SELECT SYSTEM$ZEROCOPY_CONNECTOR_LIST_SHARES('SAP_BDC_CONNECTOR_APJ.PUBLIC.SNOWFLAKE_APJ');

CREATE DATABASE IF NOT EXISTS WORKFORCESKILLS_V1
  LINKED_ZEROCOPY_CONNECTOR = (
    CONNECTOR_NAME        = 'SAP_BDC_CONNECTOR_APJ.PUBLIC.SNOWFLAKE_APJ',
    SHARE_NAME            = '<share name returned by LIST_SHARES>',
    SYNC_INTERVAL_SECONDS = 86400 );
```

CLD shape on this account (observed, not assumed): `<PRODUCT>_V1."<product>"."<entity>"` - database upper case,
schema and table **lower case, quoted**; S/4 column names are **CamelCase quoted** (`"WBSElement"`); SuccessFactors
column names are **camelCase quoted** (`"userId"`). Every table carries technical columns (`__OPERATION_TYPE`,
`__TIMESTAMP`, `load_type_<hash>`, `run_id_<hash>`) which L1 drops. `PROJECT_V1."project"."projectstatus"` and
`"wbselementstatus"` are **empty** - project status must come from `ACOCO_SIM`.

### 4.2 Shared-account rule

These CLDs are shared by other demos on the account (Finance 360, Supply Chain 360, Mining 360, Wipro). ACoCo
**reads them only**. No `ALTER`, `DROP` or re-sync of any CLD or of the connector. Drop of a CLD is unrecoverable
(no `UNDROP`).

### 4.3 The data-window gap and how it is closed

The CLD contents are an SAP demo tenant's data, not ACoCo's, and none spans the five-year window. Two layers fill it:

| Need | Source | Treatment |
|---|---|---|
| Master data (cost centres, profit centres, GL, activity types, customers, fiscal calendar) | CLDs | Exposed through L1 domain views (`ORGANISATION`, `SALES`). ACoCo's six MD groups are a **mapping table** (`ACOCO_DB.OPS.MAP_MD_GROUP`) over real cost-centre hierarchy nodes |
| People master and capacity | People Intelligence CLDs | Used as-is for the population they cover; **back-history** Oct 2021-Dec 2022 is generated in `ACOCO_SIM` in the identical column shape, keyed to the same `userId` |
| Transactions Oct 2021-Sep 2026 (journal lines on ACoCo projects, plan, timesheets, assignments, opportunities) | `ACOCO_SIM` | Generated by the seeded generator, keyed to CLD master data (real cost centres, GL accounts, activity types, customers, WBS where possible) |
| Products SAP does not ship for professional services (CustomerProject, Timesheet, ResourceAssignment, Opportunity, InternalOrder, BillableControl) | `ACOCO_SIM` | One schema per product, CDS-shaped, as in v1.1 |
| Products requested but not yet shared (Skills, Learning, Performance, Compensation, Succession) | `ACOCO_SIM` | Same shape as the expected product; swapped for the real CLD when it arrives (L1 regenerated from `INFORMATION_SCHEMA`) |
| AI-agent telemetry | `ACOCO_SIM.TELEMETRY` (OpenAI, Anthropic shapes) + `SNOWFLAKE.ACCOUNT_USAGE` (Cortex) | As v1.1 section 2.4 |
| Asset library (no SAP equivalent) | `ACOCO_SIM.ASSETS`: `ASSET` (id, title, type - accelerator / data model / code template / test pack / AI agent / proposal, skill tags, catalogued effort saving in hours, description text), `ASSET_HARVEST` (asset x source project x date x harvesting person), `ASSET_USAGE` (asset x project/WBS or opportunity x date x hours saved ESTIMATED) | Generated: ~150 assets over five years; harvest rate rising FY22 ~15 % -> FY26 ~40 %; reuse correlated with CPI. In production this is a knowledge-management or Git/SharePoint catalogue, loaded to Snowflake |

**L1 unions CLD and `ACOCO_SIM` rows per business object** where both exist (e.g. `WORKFORCE.WORKFORCE_JOB` =
CLD `coreworkforce_standardfields` UNION ALL `ACOCO_SIM` back-history), carrying a `SOURCE_SYSTEM` column
(`BDC_CLD` / `SIMULATED`). The Data Trust page shows the split. The presenter states plainly which numbers are
real-tenant shape and which are simulated.

> **Open decision OD-1.** Alternative: restrict L0 to the CLDs only and accept a 2023-2026 window for people data.
> Rejected here because the user fixed a five-year window; flag it if the customer prefers "real CLD rows only".

---

## 5. Architecture

### 5.1 Reference architecture - strict three-layer medallion

```
SAP S/4HANA (PCE) + SAP SuccessFactors        SAP Business Data Cloud / SAP People Intelligence
  (System of Record)               ------>     SAP-managed data products (CSN/ORD)
                                                   | zero-copy, connector SNOWFLAKE_APJ
=============================== Snowflake SFSEAPAC.SNOWFLAKE_SAP_APJ (System of Context & Reasoning) ====
L0  SOURCE   *_V1 CLDs (SAP, read-only, zero-copy)  +  ACOCO_SIM (non-SAP sources + BDC-shaped gap-fill,
             read-only after load)  +  SNOWFLAKE.ACCOUNT_USAGE (Cortex telemetry)
             "as delivered" - never modified, never read by a consumer
                 |  views only
L1  DOMAIN   ACOCO_L1.{ORGANISATION, FINANCE, PROJECTS, TIME, SALES, WORKFORCE, TALENT, ASSETS, AI_TELEMETRY}
             one view per business object; business names, types, conformed keys; CLD + SIM union
             with SOURCE_SYSTEM; no cross-domain joins, no aggregation, no "today"
                 |  dynamic tables + views
L2  ASSETS   ACOCO_L2.CORE        calendar, as-of, level targets
             ACOCO_L2.ONTOLOGY    ENT_* conformed entities, REL_* relationships, ONT_* registry
             ACOCO_L2.<marts>     PORTFOLIO_360, PROJECT_DELIVERY, PIPELINE_PRESALES,
                                  WORKFORCE_PERFORMANCE, AI_ADOPTION   (DT_* facts keyed to ENT_*)
             ACOCO_L2.REASONING   ML scores/forecasts, Cortex Search services, match views
             ACOCO_L2.SEMANTIC    5 Semantic Views (logical tables = ENT_* + DT_*)
             ACOCO_L2.SERVING     VW_* app-facing views (the app's only table interface)
             ACOCO_L2.QUALITY     checks, freshness, lineage counts, ACCESS_HISTORY snapshot
        ^ fee boundary: every consumer reads L2 only
Consume  Cortex Agent ACOCO_ADVISOR -> SEMANTIC + REASONING  |  SPCS app -> SERVING + SEMANTIC + ONTOLOGY
Act      -> SAP: staffing request / re-plan / learning assignment (write-back via API, roadmap)
         -> BDC: derived data products published back from L2 (SYSTEM$SAP_PUBLISH_DATA_PRODUCT, roadmap)
```

**Layer contract** - each layer has one job, one reader and one writer:

| | L0 Source | L1 Domain | L2 Assets |
|---|---|---|---|
| **Purpose** | Data as delivered by SAP BDC (and by non-SAP sources) | Trusted business objects, one domain at a time | Cross-domain, consumption-ready assets for the agent and the app |
| **Content** | CLDs `*_V1`; `ACOCO_SIM` schemas; `ACCOUNT_USAGE` | One view per business object (Person job record, WBS element, Opportunity, Timesheet record, Asset...) | Ontology entities and relationships, fact marts, Semantic Views, reasoning objects, serving views, quality evidence |
| **Object type** | As shared / as loaded | **Views only** (zero-copy stays zero-copy) | Dynamic tables, views, Semantic Views, Cortex Search, ML |
| **Allowed logic** | None | Rename to business names, cast types and dates, `UPPER(TRIM())` keys, conform keys to ontology keys, drop technical columns, filter to ACoCo scope, CLD UNION SIM with `SOURCE_SYSTEM`, within-domain lookups (e.g. reversal flag from journal header) | Cross-domain joins, entity conformance, aggregation, business rules and metrics (2.7), as-of logic, ML, search |
| **Not allowed** | Any DDL/DML by ACoCo | Cross-domain joins, aggregation, metrics, `CURRENT_DATE`, as-of logic | Reading L0 directly |
| **Reads from** | - | L0 only | L1 and L2 only |
| **Read by** | L1 only | L2 only | Agent, app, publish-back - **nothing else** |
| **Naming** | `<PRODUCT>_V1."<product>"."<entity>"`, `ACOCO_SIM.<SOURCE>.<ENTITY>` | `ACOCO_L1.<DOMAIN>.<BUSINESS_OBJECT>` | `ENT_*`, `REL_*`, `ONT_*`, `DT_*`, `SV_*`, `CSS_*`, `VW_*`, `Q_*` |
| **Built by** | Connector / generator | `tools/gen_l1.py` from `INFORMATION_SCHEMA` + rename map | SQL in `sql/l2/` + `tools/gen_ontology.py` |

**Order of build inside L2** (each step reads only the steps above it):
`CORE` -> `ONTOLOGY.ENT_*` (from L1 master-data domains) -> marts `DT_*` (facts keyed to `ENT_*`) ->
`ONTOLOGY.REL_*` -> `REASONING` -> `SEMANTIC` -> `ONTOLOGY.ONT_*` registry (generated from `SEMANTIC`) -> `SERVING` -> `QUALITY`.

### 5.2 Platform architecture - the solution in five layers

This is the narrative the **Platform Architecture** page (C4) presents. Each layer answers one question.

| Layer | Question | Snowflake capability | ACoCo objects |
|---|---|---|---|
| **1 Access (L0)** | How does SAP data arrive without copying it? | SAP BDC Connect zero-copy share -> catalog-linked databases | 4 People Intelligence + 13 S/4HANA CLDs via `SNOWFLAKE_APJ`; `ACOCO_SIM` for non-SAP and not-yet-shared products |
| **2 Prepare (L1)** | How do raw data products become trusted business objects? | L1 **data domains** - views only, conformed keys, CLD + SIM union | `ACOCO_L1.{ORGANISATION, FINANCE, PROJECTS, TIME, SALES, WORKFORCE, TALENT, ASSETS, AI_TELEMETRY}` |
| **3 Define (L2)** | What do the business words mean, once? | L2 **data assets**: ontology entities and relationships, fact marts (dynamic tables), 5 Semantic Views over them | `ACOCO_L2.ONTOLOGY`, marts, `ACOCO_L2.SEMANTIC` |
| **4 Reason** | How does the MD ask anything and get a sourced answer? | Cortex Agent (Analyst + Search tools), `AI_COMPLETE`, `AI_EMBED`, Snowflake ML | `ACOCO_ADVISOR`, `CSS_*`, `ACOCO_L2.REASONING` |
| **5 Serve and act** | Where does the MD see it, and how does the decision go back? | Snowpark Container Services app; write-back to SAP; publish-back to BDC | `ACOCO_COMMAND_CENTER` on `ACOCO_POOL`; R1-R14 actions |

Cross-cutting **Trust**: `SOURCE_SYSTEM` on every row, freshness and completeness checks, `ACCESS_HISTORY` fee-boundary
evidence (5.6), lineage (P8).

### 5.3 Ontology - the shared business model behind the five Semantic Views

**Decision: include it, kept lightweight.** The MD's questions cross six sources (S/4 finance, S/4 projects, People
Intelligence, CRM, asset library, AI telemetry) and five Semantic Views. Without one explicit model of the business
objects and how they relate, every Semantic View redefines "person", "project" or "level" slightly differently and
the agent cannot route a cross-pillar question ("which bench people with AI skill 3+ fit the bid that needs the
asset we harvested from P-xxxx?"). The ontology is that model. It is **not** a graph database: it is a small
set of L2 assets in `ACOCO_L2.ONTOLOGY` - conformed entity tables (`ENT_*`) built from the L1 domains, relationship
bridges (`REL_*`) and a registry (`ONT_*`) generated from the Semantic Views - plus one graph on the Platform
Architecture page. The five Semantic Views use the `ENT_*` tables as their shared dimensions (7.2).

**Entities (11) and the system that owns each**

| Entity | System of record | L1 domain (source) | L2 entity | Semantic Views |
|---|---|---|---|---|
| Person | SAP People Intelligence (Core Workforce) | `WORKFORCE.WORKFORCE_JOB` | `ENT_PERSON` | WORKFORCE, AI, PIPELINE, DELIVERY |
| Level / bill code | People Intelligence `payGrade` + S/4 activity type | `ORGANISATION.LEVEL`, `ACTIVITY_TYPE` | `ENT_LEVEL` | all |
| MD group | S/4 cost centre hierarchy | `ORGANISATION.MD_GROUP` | `ENT_MD_GROUP` | all |
| Customer | S/4 Customer | `SALES.CUSTOMER` | `ENT_CUSTOMER` | PORTFOLIO, DELIVERY, PIPELINE |
| Project / work package | S/4 Project (WBS) | `PROJECTS.PROJECT`, `WBS_ELEMENT`, `WORK_PACKAGE` | `ENT_PROJECT`, `ENT_WORK_PACKAGE` | PORTFOLIO, DELIVERY, AI |
| Opportunity | CRM (non-SAP) | `SALES.OPPORTUNITY` | `ENT_OPPORTUNITY` | PIPELINE, PORTFOLIO |
| Asset | Asset library (non-SAP) | `ASSETS.ASSET` | `ENT_ASSET` | DELIVERY, PIPELINE |
| Skill | People Intelligence Skills (TIH) | `TALENT.SKILL` | `ENT_SKILL` | WORKFORCE, PIPELINE, AI |
| Learning item | People Intelligence Learning | `TALENT.LEARNING_ITEM` | `ENT_LEARNING_ITEM` | WORKFORCE, AI |
| AI tool / agent | AI telemetry + S/4 `AGT_*` activity type (non-SAP + SAP) | `AI_TELEMETRY.AI_TOOL`, `ORGANISATION.ACTIVITY_TYPE` | `ENT_AI_TOOL` | AI, DELIVERY |
| Time category | Timesheet attendance type (Delivery, Bid, Learning, Admin, Bench) | `TIME.TIMESHEET_RECORD` | `ENT_TIME_CATEGORY` | WORKFORCE, PORTFOLIO |

**Relationships (examples; 16 in total):** Person *has* Level; Person *belongs to* MD group; Person *holds* Skill
(proficiency); Person *books time to* Time category *on* Project / Opportunity; Person *completes* Learning item;
Learning item *targets* Skill; Person *uses* AI tool; Project *is for* Customer; Opportunity *becomes* Project;
Opportunity *requires* Skill; Project *harvests* Asset; Project / Opportunity *reuses* Asset; Asset *embodies* Skill;
Work package *requires* Skill; Project *consumes* AI agent (`AGT_*`); Customer *belongs to* MD group.

**Objects**

| Object | Content |
|---|---|
| `ACOCO_L2.ONTOLOGY.ENT_*` (12) | Conformed entity dynamic tables, one row per key, from the owning L1 domain |
| `ACOCO_L2.ONTOLOGY.REL_*` (7) | Bridge dynamic tables for many-to-many relationships (person-skill, person-assignment, pursuit team, WP-skill, opportunity-skill, asset-skill, asset use) |
| `ACOCO_L2.ONTOLOGY.ONT_ENTITY` | entity, definition, owning system, SAP data product or non-SAP source, L1 domain object, key, `ENT_*` table, `SOURCE_SYSTEM` share |
| `ACOCO_L2.ONTOLOGY.ONT_RELATIONSHIP` | from-entity, verb, to-entity, cardinality, join keys, Semantic View(s) that implement it |
| `ACOCO_L2.ONTOLOGY.ONT_METRIC` | metric (from 2.7), entity it measures, pillar, Semantic View and metric name |
| `tools/gen_ontology.py` | Generates the three tables from the Semantic View DDL (`DESCRIBE SEMANTIC VIEW`) plus a hand-kept entity file; CI fails if a Semantic View joins two entities with no registered relationship |

**Where it is used**

1. **Dashboard** - the Platform Architecture page (C4) draws the entity graph, coloured by owning system (SAP
   S/4HANA, SAP People Intelligence, non-SAP). Clicking an entity shows its source data product, L2 object, Semantic
   Views and metrics by pillar. This makes "SAP is the record; Snowflake adds context" visible on one screen.
2. **Agent** - `ACOCO_ADVISOR` instructions include the entity -> Semantic View map from `ONT_RELATIONSHIP`, so a
   cross-pillar question is split across the right Analyst tools.
3. **Build discipline** - one definition of each entity and metric across all five Semantic Views (2.7).

### 5.4 Object inventory (all owned by `ACCOUNTADMIN`)

| Kind | Name | Notes |
|---|---|---|
| Databases | L0: CLDs `*_V1` + `ACOCO_SIM`; L1: `ACOCO_L1` (9 domain schemas); L2: `ACOCO_L2` (`CORE`, `ONTOLOGY`, 5 marts, `REASONING`, `SEMANTIC`, `SERVING`, `QUALITY`); control plane: `ACOCO_DB` (`OPS` config and maps, `AGENT`, `APP`) | `ACOCO_L0` of v1.1 is **retired** - L0 is the CLDs plus `ACOCO_SIM` |
| Warehouses | `WH_ACOCO_BUILD` (Medium, auto-suspend 60 s, timeout 3600 s), `WH_ACOCO_APP` (X-Small, auto-suspend 60 s, timeout 300 s) | Exact names; never prefix-matched |
| Compute pool | `ACOCO_POOL` - `INSTANCE_FAMILY = CPU_X64_XS`, `MIN_NODES = 1`, `MAX_NODES = 1`, `AUTO_SUSPEND_SECS = 3600`, `AUTO_RESUME = TRUE` | Resume and warm the service before a demo |
| Image repository | `ACOCO_DB.APP.IMAGES` | Image `acoco_command_center:<tag>` |
| Service | `ACOCO_DB.APP.ACOCO_COMMAND_CENTER` | Spec in 8.5; `QUERY_WAREHOUSE = WH_ACOCO_APP` |
| Agent | `ACOCO_DB.AGENT.ACOCO_ADVISOR` | 7 tools |
| Cortex Search | `ACOCO_L2.REASONING.CSS_PROJECT_COMMENTARY`, `ACOCO_L2.REASONING.CSS_ASSET_LIBRARY` | PM status notes; asset library |
| Semantic Views | `ACOCO_L2.SEMANTIC`: `SV_PORTFOLIO_360`, `SV_PROJECT_DELIVERY`, `SV_WORKFORCE_PERFORMANCE`, `SV_PIPELINE_PRESALES`, `SV_AI_ADOPTION` | Names frozen (mirrored in agent tools) |
| Ontology | `ACOCO_L2.ONTOLOGY`: 12 `ENT_*`, 7 `REL_*`, `ONT_ENTITY`, `ONT_RELATIONSHIP`, `ONT_METRIC` | Entities from L1; registry generated from SV DDL (5.3, 7.2) |
| ML | `ACOCO_L2.REASONING`: `DT_ATTRITION_RISK`, `FC_DEMAND_BY_SKILL` (forecast), model registry entries | New schema in v2 |
| Serving | `ACOCO_L2.SERVING`: `VW_*` | The app's only table interface |
| Roles | **none created** | Everything as `ACCOUNTADMIN` |
| Row access policies | **none** | Group scoping is a query filter |

### 5.5 Layer rules

- The layer contract in 5.1 is the rule set; L1 domains and L2 assets are specified in section 7.
- L0 is never modified and never read except by L1 views. L1 is never read except by L2.
- "Today" lives only in `ACOCO_L2.CORE.VW_AS_OF` = `COALESCE(override, CURRENT_DATE())`, override **2026-10-01**.
- Semantic Views reference only `ACOCO_L2.ONTOLOGY.ENT_*`/`REL_*` and mart `DT_*` objects.
- The front end issues only `SELECT ... FROM SEMANTIC_VIEW(ACOCO_L2.SEMANTIC.SV_*)` or `SELECT ... FROM ACOCO_L2.SERVING.VW_*`,
  plus agent and `AI_COMPLETE` calls. No metric is computed in TypeScript.
- Build-time checks write to `ACOCO_L2.QUALITY.Q_CHECK_RESULTS` and fail the build on any violation (7.2 ontology rules).

### 5.6 Fee boundary without custom roles

With one `ACCOUNTADMIN` role, grants cannot stop the app from reading a CLD. The boundary is therefore:

1. **Server allow-list.** The Express server only executes statements from a static registry (`server/src/registry.sql`);
   ad-hoc SQL from Cortex Analyst is accepted only if every referenced object is in `ACOCO_L2` (checked by parsing the
   `EXPLAIN` object list before execution).
2. **Build-time lint.** CI fails if `service/` contains a `*_V1` CLD name, `ACOCO_SIM.` or `ACOCO_L1.`, or any `ACOCO_L2` schema other than
   `SERVING`, `SEMANTIC` and `ONTOLOGY`.
3. **Runtime evidence.** `QUERY_TAG = 'ACOCO_APP'` on the service's session; the Data Trust page reads a captured
   `ACCESS_HISTORY` snapshot proving app traffic touched only `ACOCO_L2.SERVING`, `ACOCO_L2.SEMANTIC` and `ACOCO_L2.ONTOLOGY` objects, while dynamic-table refresh is the only
   reader of L0/L1.
4. **The presenter says it.** "In production this is a grant; for the demo it is a code rule plus an audit trail."

The commercial rate quoted in v1.1 (0.604 CU per USD) remains **unconfirmed** and must be validated against the
Service Consumption Table and the BDC Connect terms before it is stated to a customer.

---

## 6. Time, calendar and synthetic data

### 6.1 Calendar

| Item | Value |
|---|---|
| Fiscal year | **1 Oct - 30 Sep**, named by end year (FY26 = Oct 2025-Sep 2026) |
| Window | 2021-10-01 to 2026-09-30 = FY22-FY26 = 60 fiscal months |
| Demo today | `AS_OF_CONTROL.AS_OF_DATE = 2026-10-01` |
| "This fiscal year" | FY27, day 1 - **empty by construction**. Every tile defaults to **FY26 (last closed)** and "last closed month" = Sep 2026 |
| Forward horizon | Roll-off and pipeline: 2026-10-01 to 2026-12-30 (90 days); assignments and opportunities are generated up to 2027-03-31 so the forward view is populated |
| Fiscal variant | Pick the `FISCALYEAR_V1` variant whose periods start in October if one exists; otherwise generate `DT_FISCAL_CALENDAR` from `GEN_PARAMS` and record the deviation |

### 6.2 Generator

Reuse `gen/` (seeded, deterministic, G2 determinism check), re-parameterised:

| Parameter | v1.1 | v2 |
|---|---|---|
| Months | 24 | 60 |
| Start / end | 2024-09-01 / 2026-08-31 | 2021-10-01 / 2026-09-30 (+ forward plan to 2027-03-31) |
| Headcount | ~1,000 static | ~1,000 average; ~14 % annual voluntary attrition and matching hiring -> ~1,700 distinct people |
| Projects | 151 | ~400 (Large ~20 % of count / ~80 % of revenue) |
| Opportunities | ~260 | ~800 |
| AI adoption curve | flat-ish | **S-curve**: negligible FY22, pilots FY23, growth FY24-FY25, broad FY26 - so the five-year story shows the transition |
| Time categories | billable / pre-sales / training / admin; bench derived | **Delivery, Bid, Learning, Admin** booked; **Bench** derived. Calibrated so FS FY26 actuals sit well off target (2.1) - excess bench is the story |
| AI productivity effect | multiplier term only | Productivity multiplier keeps `+0.12 x (AI skill - 1) x AI-usage intensity`; usage drawn independently of skill so **skilled-but-inactive** people exist and show no uplift; two AI-enabled projects under-perform; learning completions add a decaying +3-6 % productivity for 6 months on work matching the curriculum's target skill |
| Keys | synthetic | **Keyed to CLD master data**: real `CostCenter`, `ProfitCenter`, `GLAccount`, `CostCtrActivityType`, `Customer`, and People Intelligence `userId` |

Volume estimate (design): ~6-7 M rows in `ACOCO_SIM` (timesheet dominates); L2 rebuild < 30 minutes on Medium.

### 6.3 Story anchors (design targets - re-measure before speaking)

| Anchor | Design target |
|---|---|
| One Large FS fixed-price project in loss at FY26 close | forecast margin < 0 %, CPI ~0.73, SPI ~0.8 |
| FY26 firm Delivery share (billability) / bench | ~65 % / ~7 % against targets ~70 % / ~2 % |
| Roll-off before 30 Dec 2026 without successor | 30-40 people in FS; > 75 % below the pipeline's required AI-skill level |
| Attrition trend | FY22 peak ~18 % -> FY26 ~13 % |
| AI return (FY26, FS) | People+Agents margin ~10 pts above People-only; CPI > 1.1 vs ~1.0 |
| Pre-sales | above-median intensity win-rate ~50 % vs ~30 % within size class |
| Pursuit-team fit | bids with skill fit >= 0.8 win ~55 % vs ~30 % below 0.5, within size class |
| Asset reuse | harvest rate FY22 ~15 % -> FY26 ~40 %; projects with reuse CPI ~1.05 vs ~0.95 without; the FS loss-making project reused none of the 2-3 matching assets |
| Time mix (FS, FY26) | Delivery ~65 %, Bid ~15 %, Learning ~10 %, Admin ~3 %, Bench ~7 % - vs target ~70 / ~15 / ~10 / ~3 / ~2 %; excess bench ~5 pts |
| AI productivity uplift (FS, FY26) | AI-active vs rest within level x work type: productivity index ~+0.08, 90 % CI excluding zero; skilled-but-inactive ~0 |
| Learning payback | AI-curriculum completers ~+4 % productivity in the following 6 months vs matched non-learners; non-AI curricula smaller and not significant |
| AI skilled but inactive | ~20 % of FS people with AI-skill level >= 3 have no AI-tool use in Jul-Sep 2026 |

Every figure is re-measured by a `validate.py` assertion and restated as **measured** in this document before the demo.
v1.1's measured figures (P-0417, Daniel Okafor, Omar Rodriguez, 38 roll-offs, etc.) **do not carry over**.

---

## 7. L1 domains and L2 assets

### 7.1 L1 - data domains (`ACOCO_L1`, views only)

Each L1 schema is one **business data domain**. It is aligned to the ontology's entities (5.3), not to the source
system, so a domain can combine an SAP CLD and a non-SAP source for the **same** business object (union, never join
across domains). Every view carries `SOURCE_SYSTEM` (`BDC_CLD`, `SIMULATED`, `ACCOUNT_USAGE`) and the conformed
ontology keys: `PERSON_ID` (= People Intelligence `userId`), `COST_CENTER_ID`, `LEVEL_CODE`, `CUSTOMER_ID`,
`PROJECT_ID`, `WBS_ID`, `OPPORTUNITY_ID`, `SKILL_ID`, `LEARNING_ITEM_ID`, `ASSET_ID`, `AI_TOOL_ID`, `FISCAL_PERIOD`.

| L1 domain (schema) | Business objects (views) | L0 SAP data products (CLDs) | L0 non-SAP / gap-fill (`ACOCO_SIM`) | Feeds ontology entity |
|---|---|---|---|---|
| `ORGANISATION` | `COST_CENTER`, `COST_CENTER_HIERARCHY`, `PROFIT_CENTER`, `ACTIVITY_TYPE` (level rates + `AGT_*`), `GL_ACCOUNT`, `FISCAL_PERIOD`, `MD_GROUP` (cost-centre nodes x `ACOCO_DB.OPS.MAP_MD_GROUP`), `LEVEL` (`payGrade` x `MAP_PAYGRADE_LEVEL`) | `COSTCENTER_V1`, `COSTCENTERACTIVITYTYPE_V1`, `PROFITCENTER_V1`, `GENERALLEDGERACCOUNT_V1`, `FISCALYEAR_V1` | - | MD group, Level |
| `FINANCE` | `JOURNAL_ENTRY_ITEM` (with reversal flag from header), `JOURNAL_ENTRY_HEADER`, `PLAN_ITEM`, `INTERNAL_ORDER` | `ENTRYVIEWJOURNALENTRY_V1`, `JOURNALENTRYHEADER_V1`, `FINANCIALPLANNINGENTRYITEM_V1`, code lists | ACoCo journal lines and plan FY22-FY26; `INTERNALORDER` | (facts only) |
| `PROJECTS` | `PROJECT`, `WBS_ELEMENT`, `WBS_MILESTONE`, `CUSTOMER_PROJECT` (contract terms, delivery model), `WORK_PACKAGE`, `WORK_PACKAGE_SKILL_REQUIREMENT`, `RESOURCE_ASSIGNMENT`, `PROJECT_STATUS_NOTE` (PM commentary) | `PROJECT_V1` | `CUSTOMERPROJECT`, `RESOURCEASSIGNMENT`, `PROJECTCOMMENTARY` | Project, Work package |
| `TIME` | `TIMESHEET_RECORD` (with time category Delivery / Bid / Learning / Admin), `EMPLOYEE_AVAILABILITY`, `PLANNED_WORKING_TIME` | `EMPLOYEEAVAILABILITY_V1`, `WORKFORCEPLANNEDWORKINGTIME_V1` | `TIMESHEET` | Time category |
| `SALES` | `CUSTOMER`, `SALES_CONTRACT`, `OPPORTUNITY`, `OPPORTUNITY_SKILL_REQUIREMENT` | `CUSTOMER_V1`, `SALESCONTRACT_V1` | `OPPORTUNITY` (CRM shape) | Customer, Opportunity |
| `WORKFORCE` | `WORKFORCE_JOB` (effective-dated job record), `JOB_RELATIONSHIP`, `PERFORMANCE_RATING`, `COMPENSATION_SUMMARY` (banded, no individual pay downstream), `SUCCESSION_NOMINATION` | `COREWORKFORCEDATA_V1`, `ASSIGNMENTADDITIONALINFORMATION_V1` | Core Workforce back-history Oct 2021-Dec 2022; Performance, Compensation, Succession until shared | Person |
| `TALENT` | `SKILL`, `PERSON_SKILL`, `LEARNING_ITEM`, `LEARNING_COMPLETION` | (Skills, Learning when shared - 3.2) | Skills (incl. Agentic-AI family), Learning until shared | Skill, Learning item |
| `ASSETS` | `ASSET`, `ASSET_HARVEST`, `ASSET_USAGE` | - | `ASSETS` | Asset |
| `AI_TELEMETRY` | `AI_TOOL`, `AI_USAGE_EVENT` (OpenAI, Anthropic, Cortex), `AI_IDENTITY_MAP` | - | `TELEMETRY` + `SNOWFLAKE.ACCOUNT_USAGE` | AI tool / agent |

L1 is generated by `tools/gen_l1.py` from each source's `INFORMATION_SCHEMA` and a rename map
(`tools/l1_map.yml`: source column -> business name, type, key role). When SAP shares a People Intelligence product
that is simulated today (3.2), only the map entry changes: the L1 view switches its source from `ACOCO_SIM` to the new
CLD, and L2 is untouched. This is the main reason L1 exists.

### 7.2 L2 - data assets (`ACOCO_L2`)

| Schema | Assets | Built from | Consumed by |
|---|---|---|---|
| `CORE` | `DT_FISCAL_MONTH`, `VW_AS_OF` (override 2026-10-01), `DT_TIME_TARGET` (level x category, 2.1) | L1 `ORGANISATION`, `ACOCO_DB.OPS.GEN_PARAMS` | All L2 |
| `ONTOLOGY` | **Entities** (dynamic tables, one row per key, built from the owning L1 domain - not from facts): `ENT_PERSON` (latest job record <= as-of: level, bill code, MD group, manager, tenure), `ENT_LEVEL`, `ENT_MD_GROUP`, `ENT_CUSTOMER`, `ENT_PROJECT`, `ENT_WORK_PACKAGE`, `ENT_OPPORTUNITY`, `ENT_SKILL`, `ENT_LEARNING_ITEM`, `ENT_ASSET`, `ENT_AI_TOOL`, `ENT_TIME_CATEGORY`. **Relationships** (bridge DTs for the many-to-many edges): `REL_PERSON_SKILL`, `REL_PERSON_ASSIGNMENT`, `REL_PURSUIT_TEAM`, `REL_WP_SKILL`, `REL_OPPORTUNITY_SKILL`, `REL_ASSET_SKILL`, `REL_ASSET_USE`. **Registry**: `ONT_ENTITY`, `ONT_RELATIONSHIP`, `ONT_METRIC` | L1 domains; registry from `DESCRIBE SEMANTIC VIEW` | Marts, Semantic Views, agent instructions, C2/C4 pages |
| `PORTFOLIO_360` | `DT_PORTFOLIO_MONTH`, `DT_CAPACITY_MIX_MONTH` (Delivery / Bid / Learning / Admin / Bench by group x level x month), `DT_RISK_REGISTER` (top cross-pillar risks) | marts below + `CORE` | `SV_PORTFOLIO_360`, P0 |
| `PROJECT_DELIVERY` | `DT_PROJECT_MONTH_FINANCIALS`, `DT_PROJECT_TEAM`, `DT_PROJECT_PYRAMID`, `DT_ASSET_USAGE_MONTH`, `DT_PROJECT_HEALTH` | L1 `FINANCE`, `PROJECTS`, `TIME`, `ASSETS` + `ENT_*` | `SV_PROJECT_DELIVERY` |
| `PIPELINE_PRESALES` | `DT_OPPORTUNITY_FACT`, `DT_PRESALES_MONTH`, `DT_PURSUIT_TEAM` | L1 `SALES`, `FINANCE`, `TIME` + `ENT_*`, `REL_PURSUIT_TEAM` | `SV_PIPELINE_PRESALES` |
| `WORKFORCE_PERFORMANCE` | `DT_PERSON_MONTH_SCORECARD` (available hours from Employee Availability; five-way time mix vs target), `DT_HEADCOUNT_MONTH`, `DT_ROLL_OFF` | L1 `TIME`, `WORKFORCE`, `PROJECTS` + `ENT_*` | `SV_WORKFORCE_PERFORMANCE` |
| `AI_ADOPTION` | `DT_AI_USAGE_DAILY`, `DT_AI_COST_MONTH` (`AGT_*` journal allocations), `DT_AI_PRODUCTIVITY` (R13), `DT_LEARNING_PAYBACK` (R14) | L1 `AI_TELEMETRY`, `FINANCE`, `TALENT`, `TIME` + `ENT_*` | `SV_AI_ADOPTION` |
| `REASONING` | `DT_ATTRITION_RISK`, `FC_DEMAND_BY_SKILL`, `VW_BENCH_TO_PIPELINE_MATCH` (R1), `VW_ASSET_MATCH` (R12), `CSS_PROJECT_COMMENTARY`, `CSS_ASSET_LIBRARY` | marts + `ONTOLOGY` (search services index L2 copies of note and asset text, not L1) | Agent tools, P4, P5, P7, P11 |
| `SEMANTIC` | `SV_PORTFOLIO_360`, `SV_PROJECT_DELIVERY`, `SV_PIPELINE_PRESALES`, `SV_WORKFORCE_PERFORMANCE`, `SV_AI_ADOPTION` | Logical tables = shared `ENT_*` + the mart's `DT_*` only | Agent (Cortex Analyst tools), app `SEMANTIC_VIEW()` calls |
| `SERVING` | `VW_PROJECT_HEALTH_NOW`, `VW_ROLL_OFF_90D`, `VW_PERSON_LAST_CLOSED_MONTH`, `VW_PORTFOLIO_PACING`, `VW_ONTOLOGY_GRAPH`, `VW_LINEAGE`, `VW_TRUST` ... | L2 only | App registry statements (8.4) |
| `QUALITY` | `Q_CHECK_RESULTS` (gate log, SC360 guard pattern), `Q_FRESHNESS`, `Q_COMPLETENESS`, `Q_LINEAGE_COUNTS` (row counts per L0/L1 object, snapshotted so the app never reads L0/L1), `Q_ACCESS_SNAPSHOT` | L0/L1 metadata via build-time procedure | P8, P9 |

**Ontology rules (how the five Semantic Views stay one model)**

1. Every Semantic View uses the **same** `ENT_*` tables as its dimension logical tables, with the same names
   (`PERSON`, `PROJECT`, `OPPORTUNITY`...) and primary keys. A fact DT never doubles as a dimension.
2. Every fact DT carries the ontology keys of the entities it relates to; every Semantic View relationship is a fact
   -> `ENT_*` (many-to-one) or a `REL_*` bridge. `ONT_RELATIONSHIP` lists each one with the views that implement it.
3. Entity attributes (level, bill code, MD group, skill proficiency) are defined once in `ENT_*`; marts never
   re-derive them.
4. Metrics are defined once in the Semantic View that owns the fact (2.7) and registered in `ONT_METRIC` with their
   pillar; a metric needed in two views is defined in one and referenced by the agent, never copied with different
   logic.
5. CI (`tools/gen_ontology.py --check`) fails if a Semantic View joins two entities with no registered relationship,
   if an `ENT_*` key is not unique, or if any L2 object references `*_V1`, `ACOCO_SIM` or another L0 object.

**Dynamic-table rules**: deterministic (no `CURRENT_DATE`; "today" only via `CORE.VW_AS_OF`); `TARGET_LAG = '1 hour'`
on every DT a Semantic View or `SERVING` view reads and `DOWNSTREAM` on intermediates (a whole chain on `DOWNSTREAM`
never refreshes - SC360 finding F6); `REFRESH_MODE = INCREMENTAL` where the shape allows; warehouse `WH_ACOCO_BUILD`.

**Removed from v2.0**: `RAP_PERSON_SCOPE`, `VW_MY_SCOPE`, SM/IC-only views; `DT_PERSON_DIM`, `DT_PROJECT_DIM`,
`DT_ASSET_DIM`, `DT_OPPORTUNITY` as dimensions (replaced by `ONTOLOGY.ENT_*`); `VW_*` inside mart schemas (moved to
`SERVING`).

---

## 8. Front end - ACoCo Command Center on SPCS

### 8.1 Why a container instead of Streamlit

| Consideration | Streamlit in Snowflake (v1.1) | SPCS container (v2) |
|---|---|---|
| UI fidelity | Theme hacks, widget limits (`st.tabs` state, page routing traps) | Full React; design system identical to Supply Chain 360 |
| Cold start | 26-53 s measured boot | Container stays warm while the pool runs; first paint < 2 s |
| Agent UX | Polling inside reruns | Server-sent streaming from the Agent REST API |
| Reuse | ACoCo only | Same skeleton as SC360 / Finance 360 / Mining 360 demos on this account |
| Cost | Warehouse only | Compute pool node-hours + warehouse - suspend the pool after the demo |

### 8.2 Stack (cloned from `sap-bdc-supply-chain-360/service/app`)

- **Client:** Vite + React 18 + TypeScript, Tailwind, Recharts, lucide-react icons, react-markdown; components reused
  as-is: `Sidebar`, `MetricCard`, `ChartCard`, `Chart`, `DataTable`, `AskCortex`; hooks `useQuery`, `useFilters`.
- **Server:** Express (Node 20, TypeScript), `snowflake-sdk`; routes `api.ts` (page data), `lineage.ts`, `analyst.ts`
  (agent); serves the built client statically; `/healthcheck` for the readiness probe.
- **Auth inside SPCS:** OAuth token from `/snowflake/session/token`, host/account from `SNOWFLAKE_HOST` /
  `SNOWFLAKE_ACCOUNT` env vars injected by SPCS; session runs as the service owner (`ACCOUNTADMIN`),
  `QUERY_TAG = 'ACOCO_APP'`, warehouse `WH_ACOCO_APP`.
- **Local dev:** same server with key-pair auth against connection `ACOCO_BUILD` equivalent for this account.
- **Container:** multi-stage Dockerfile from SC360 (node:20-bookworm-slim, port 8080).

### 8.3 Pages (sidebar order)

**Context pages (static content plus a few live figures; no story logic).** They open the demo and can be shown to a
viewer joining cold. They replace v2.1's single top-bar "Demo Context" link.

| # | Page | Purpose | Content | Source |
|---|---|---|---|---|
| C1 | **Business Overview** | Explain the business ACoCo runs | ACoCo in numbers (six groups, ~1,000 people, ~400 projects, ~800 opportunities FY22-FY26); the bill-code table and how a team's pyramid sets margin; the life cycle of an hour (bid -> project -> harvest -> bench/learning); the **five uses of time with their targets by level** and the objective of each (2.1); the three pillars and the ProServe360 overlay; why Agentic AI matters and the productivity hypothesis; Priya Nair's situation on 1 Oct 2026 | static (`content/business.md`) + live headline KPIs from `SV_PORTFOLIO_360` |
| C2 | **Dashboard Overview** | Explain how to read the dashboard | Sitemap by pillar; for each page: the question it answers, the epic and stories, the main metrics with their one-line definitions (from `ONT_METRIC`), and the filters; how Ask Cortex and the Advisor work; the honesty markers (`SOURCE_SYSTEM` badge, ESTIMATED, design-target vs measured) | static + `ACOCO_L2.ONTOLOGY.ONT_METRIC` |
| C3 | **Demo Overview** | Explain the demo itself | The 30-minute flow (section 11) as a clickable storyboard - beat, page, claim; the four epics and which SAP data alone cannot answer each; which data is real CLD and which is simulated, and why; what goes back to SAP for each pillar | static (`content/demo.md`) |
| C4 | **Platform Architecture** | Explain the solution | Five-layer view (5.2) with the reference architecture (5.1); **ontology graph** (5.3) coloured by owning system (S/4HANA / People Intelligence / non-SAP), click an entity for its SAP data product, L1 domain object, L2 `ENT_*` table, Semantic Views and metrics; medallion contract (L0 CLD -> L1 domain -> L2 asset); zero-copy and fee-boundary explanation; object inventory | static diagram + `ACOCO_L2.SERVING.VW_ONTOLOGY_GRAPH` (over `ONTOLOGY.ONT_*`) |

**Dashboard pages**

| # | Page | Story | Content | Source |
|---|---|---|---|---|
| P0 | **ProServe360 Overview** | PMD-0 | Three pillar panels (Operational Excellence: margin, on-time %, asset reuse rate; Value Creation: win-rate, pursuit cost per won USD, book-to-bill; People Development: Delivery share vs target, excess bench cost, admin share, AI productivity uplift, attrition) FY26 vs FY25; **time-mix bar actual vs target by level** (Delivery / Bid / Learning / Admin / Bench); 60-month revenue/margin trend with "As of 1 Oct 2026" rule; top 5 cross-pillar risks | `SV_PORTFOLIO_360`, `DT_CAPACITY_MIX_MONTH`, `DT_TIME_TARGET`, `VW_PORTFOLIO_PACING` |
| P1 | **Portfolio & Pareto** | PMD-1 | Revenue by size class FY22-FY26; Pareto curve; fixed-price projects < 10 % forecast margin table (click -> P2) | `SV_PORTFOLIO_360`, `SV_PROJECT_DELIVERY` |
| P2 | **Project Health** (drill) | PMD-2, PMD-8 | Project header (contract, CPI, SPI, EAC, LD exposure, RAG); plan vs actual by month; work-package table with critical path; sold vs actual pyramid; "Why?" button -> Cortex Search; "Assets that fit" panel (link to P11) | `SV_PROJECT_DELIVERY`, `VW_PROJECT_HEALTH_NOW`, CSS |
| P3 | **Time Mix & Bench** | PMD-3 | Five-way time mix by level vs target (12 and 60 months); excess bench (above 2 %) cost by month; admin share vs 5 % ceiling; roll-off-90-day table with skills and AI-skill level | `SV_WORKFORCE_PERFORMANCE`, `DT_TIME_TARGET`, `VW_ROLL_OFF_90D` |
| P4 | **People Intelligence** | PMD-4, PMD-5 | Headcount and attrition FY22-FY26; attrition-risk list (Manager+) with drivers; skills supply vs pipeline demand heatmap; AI-curriculum items for the gap | `SV_WORKFORCE_PERFORMANCE`, `DT_ATTRITION_RISK`, `FC_DEMAND_BY_SKILL` |
| P5 | **Pipeline & Pursuit** | PMD-6, PMD-10 | Pipeline by stage/size; win-rate by intensity and by skill fit within size; pursuit cost per won USD; open-bid table with team fit, Principal flag and suggested bench additions; bookings and book-to-bill FY22-FY26 | `SV_PIPELINE_PRESALES`, `VW_BENCH_TO_PIPELINE_MATCH` |
| P6 | **AI Productivity & Learning Payback** | PMD-7, PMD-12 | Adoption S-curve FY22-FY26; **productivity index by AI-skill level x AI-usage band within level and work type, with confidence interval** ("no significant effect" shown when it spans zero); skilled-but-inactive list; learning payback by curriculum (before/after vs matched group); AI cost by vendor; margin and CPI by delivery model | `SV_AI_ADOPTION` (`DT_AI_PRODUCTIVITY`, `DT_LEARNING_PAYBACK`), `SV_WORKFORCE_PERFORMANCE` |
| P7 | **Context & Reasoning** | section 9 | Gallery of the System-of-Context use cases with live mini-tiles (bench-to-pipeline match, demand forecast, margin-leak detector) | `ACOCO_L2.REASONING` |
| P8 | **BDC Sources & Lineage** | - | CLD inventory (name, rows, freshness, `SOURCE_SYSTEM` share), connector status; lineage graph in true medallion order - L0 CLD -> L1 domain view -> L2 `ENT_*`/`DT_*` -> Semantic View -> agent tool / page | `ACOCO_L2.SERVING.VW_LINEAGE` over `QUALITY.Q_LINEAGE_COUNTS` and captured lineage |
| P9 | **Data Trust** | - | Freshness, completeness, fee-boundary evidence (`ACCESS_HISTORY` snapshot) | `ACOCO_L2.QUALITY` |
| P10 | **Ask the Advisor** | PMD-0..12 | Full-page chat with `ACOCO_ADVISOR`; streams text, tables, charts, cited SQL; suggested prompts per story | Agent REST API |
| P11 | **Asset Library** | PMD-9 | Harvest and reuse rate FY22-FY26; top reused assets with hours saved (ESTIMATED); CPI and margin of projects with vs without reuse; search box over the library; assets matching the selected project's critical work package | `SV_PROJECT_DELIVERY`, `CSS_ASSET_LIBRARY`, `VW_ASSET_MATCH` |
| - | **Ask Cortex** (on P0-P7, P11) | - | Button per card: server fetches the registry facts behind that card and calls `AI_COMPLETE` to explain them, citing the numbers shown (SC360 pattern) | `SNOWFLAKE.CORTEX.AI_COMPLETE` |

Sidebar groups pages: **Context** (C1 Business Overview, C2 Dashboard Overview, C3 Demo Overview, C4 Platform
Architecture) - **ProServe360** (P0, P7, P10) - **Operational Excellence** (P1, P2, P11) - **Value Creation** (P5) -
**People Development** (P3, P4, P6) - **Data** (P8, P9). The app opens on C1.

Global filters (left rail, `useFilters`): **MD group** (default Financial Services, or Firm-wide), **fiscal year range**
(default FY22-FY26), **size class**. They become `WHERE` clauses on the `SEMANTIC_VIEW()` call - never client-side filtering of
fetched rows.

### 8.4 API contract (server)

| Route | Method | Returns |
|---|---|---|
| `/api/filters` | GET | MD groups, fiscal years, size classes |
| `/api/overview`, `/api/portfolio`, `/api/project/:id`, `/api/workforce`, `/api/people`, `/api/pipeline`, `/api/ai`, `/api/assets`, `/api/reasoning`, `/api/ontology`, `/api/context/:page`, `/api/lineage`, `/api/trust` | GET | JSON per page, from registry statements with bound filter parameters |
| `/api/advisor` | POST | Streams the Cortex Agent `:run` response (`POST /api/v2/databases/ACOCO_DB/schemas/AGENT/agents/ACOCO_ADVISOR:run`) |
| `/api/ask-cortex` | POST | `{topic, args, question?}` -> AI_COMPLETE answer over the topic's facts |
| `/healthcheck` | GET | 200 |

All SQL uses bind variables; no string concatenation of user input.

### 8.5 Service DDL

```sql
USE ROLE ACCOUNTADMIN;
CREATE COMPUTE POOL IF NOT EXISTS ACOCO_POOL
  MIN_NODES = 1 MAX_NODES = 1 INSTANCE_FAMILY = CPU_X64_XS
  AUTO_RESUME = TRUE AUTO_SUSPEND_SECS = 3600;
CREATE IMAGE REPOSITORY IF NOT EXISTS ACOCO_DB.APP.IMAGES;
-- docker build --platform linux/amd64 -t <repo_url>/acoco_command_center:v1 service/app && docker push ...
CREATE SERVICE IF NOT EXISTS ACOCO_DB.APP.ACOCO_COMMAND_CENTER
  IN COMPUTE POOL ACOCO_POOL
  QUERY_WAREHOUSE = WH_ACOCO_APP
  FROM SPECIFICATION $$
spec:
  containers:
  - name: app
    image: /acoco_db/app/images/acoco_command_center:v1
    env: { PORT: "8080", SNOWFLAKE_WAREHOUSE: WH_ACOCO_APP, ACOCO_AS_OF: "2026-10-01" }
    resources: { requests: { memory: 1Gi, cpu: 500m }, limits: { memory: 2Gi, cpu: 1000m } }
    readinessProbe: { port: 8080, path: /healthcheck }
  endpoints:
  - name: ui
    port: 8080
    public: true
$$;
SHOW ENDPOINTS IN SERVICE ACOCO_DB.APP.ACOCO_COMMAND_CENTER;   -- ingress URL
```

Upgrade: push a new tag, `ALTER SERVICE ... FROM SPECIFICATION ...`. Rollback: previous tag. Pre-demo: `ALTER COMPUTE POOL
ACOCO_POOL RESUME`, open the URL once, wait for `READY`. Post-demo: `ALTER COMPUTE POOL ACOCO_POOL SUSPEND` (requires
`ALTER SERVICE ... SUSPEND` first). Packaging as a Native App (SC360's `app/manifest.yml` pattern) is **optional, phase 2**.

---

## 9. Snowflake as System of Context and Reasoning - new use cases

SAP remains the system of record for every transaction and every person. Snowflake adds **context** SAP does not hold
(CRM pipeline, AI telemetry, unstructured notes, five years of history across modules, external benchmarks) and
**reasoning** (semantic layer, agents, search, ML). Each use case ends in an **action back in SAP** or a **data product back to BDC**.

| # | Use case | Context joined in Snowflake | Reasoning | Action / record stays in SAP |
|---|---|---|---|---|
| R1 | **Bench-to-pipeline matching** | People Intelligence skills + availability, roll-off dates, CRM opportunities with required skills and expected start | Similarity of skill vectors (`AI_EMBED` + `VECTOR_COSINE_SIMILARITY`) ranked by availability overlap and win probability | Staffing request / soft booking created in S/4 Resource Management |
| R2 | **Attrition early warning** | Core Workforce tenure, pay vs midpoint, performance, manager changes, utilization strain, project loss exposure | Snowflake ML classification, SHAP-style top drivers, agent explains per person | Retention action logged in SuccessFactors |
| R3 | **Skills demand forecast** | Weighted pipeline x required skills, historical project mix, AI adoption curve | `SNOWFLAKE.ML.FORECAST` per skill family, 12 months | Learning assignments in SF Learning; hiring requisitions in SF Recruiting |
| R4 | **Fixed-price bid advisor** | Five years of EAC vs sold margin by size class, delivery model and team AI skill | Agent + regression on historical overrun; Cortex Search over past lessons-learned | Price/contingency recommendation attached to the quote; contract in S/4 |
| R5 | **Margin-leak detector** | Timesheet write-offs, unbilled WIP, journal postings, PM commentary | Anomaly detection on write-off rate per project/month; `AI_CLASSIFY` of commentary into root causes | Billing block review / WBS re-plan in S/4 |
| R6 | **AI agents as a costed resource** | `AGT_*` activity allocations in the Universal Journal + OpenAI/Anthropic/Cortex telemetry | Agent cost per delivered hour vs human cost; optimal human:agent mix per work type | Updated activity-type planned prices in S/4 Controlling |
| R7 | **Redeployment what-if** | Roll-off list, pipeline, availability | Agent runs scenarios over Semantic Views ("if Opp X slips 30 days, bench cost +USD y") | Decision recorded; assignment dates changed in S/4 |
| R8 | **Key-account succession risk** | Succession nominations, attrition risk, account revenue concentration | Joins risk x revenue; agent lists accounts with single-point-of-failure leaders | Successor nomination in SF Succession |
| R9 | **Project "why" and early-warning narrative** | PM status notes, milestones, CPI/SPI trend | Cortex Search + agent summarises leading indicators weeks before RAG turns red | Escalation note on the project in S/4 |
| R10 | **Publish-back: Agentic-AI Readiness data product** | Skills + learning + AI usage + productivity per person | Derived in L2 | Published to BDC as a customer-managed data product; consumed by SAP People Intelligence and SAC |
| R11 | **Cash and DSO risk** | Unbilled value, billing milestones, client payment history (Customer CLD) | Forecast days-to-cash per project | Billing-plan adjustment in S/4 |
| R12 | **Asset recommender** | Asset library (skill tags, descriptions, past reuse and hours saved), work-package / bid required skills, PM commentary | `CSS_ASSET_LIBRARY` + `AI_EMBED` similarity between work-package scope and asset description, ranked by past hours saved | Asset reference attached to the WBS element / quote; re-plan of the WBS in S/4 |
| R13 | **AI productivity test** | People Intelligence Skills (AI-skill level) + AI-tool telemetry (usage) + timesheet earned vs actual hours, by level and work type | Stratified comparison of productivity index, bootstrap 90 % CI; agent explains size and certainty, flags "no significant effect" | AI-tool licence and AI-learning allocation; AI-assisted planned rates in S/4 activity types |
| R14 | **Learning payback** | SF Learning completions + Skills + later delivery productivity on matching work | Before/after vs matched non-learners (same level, work type, starting productivity) | Learning assignments in SF Learning prioritised by payback |

Pillar mapping: Operational Excellence - R5, R9, R11, R12; Value Creation - R4; People Development - R2, R3, R6, R8,
R10, R13, R14; ProServe360 overlay - R1, R7.

Demo scope: **R1, R2, R3, R9, R12 and R13 are live** on page P7 (R12 also on P11, R13 and R14 on P6) and through the Advisor. R5 and R6 appear as tiles. R4, R7, R8,
R10, R11 are shown as roadmap cards with their data lineage; R7 is answered by the agent over the Semantic Views for
the PMD-11 prompt. Write-back to SAP is **narrated, not executed** in the demo.

---

## 10. Cortex Agent `ACOCO_ADVISOR`

| Item | Specification |
|---|---|
| Location | `ACOCO_DB.AGENT.ACOCO_ADVISOR`, generated by `tools/gen_agent.py` |
| Tools | 5 Cortex Analyst (one per Semantic View) + 2 Cortex Search (`project_commentary`, `asset_library`) |
| Instructions | Persona = Partner MD Priya Nair, FS group unless asked firm-wide; frame answers by pillar (Operational Excellence, Value Creation, People Development) and say which pillar a trade-off affects; today = 2026-10-01, "this year" means FY26 (closed) unless the user says FY27; fiscal year Oct-Sep; state `SOURCE_SYSTEM` caveat when a figure includes simulated rows; mark asset hours saved as ESTIMATED; judge time against the level targets in 2.1 (Delivery first; Bid by win-rate, never by hours; Admin < 5 %; Bench ~2 % transition); report AI productivity as association within level x work type with its confidence interval, never as cause; never quote individual pay |
| Model | Use a model confirmed available on this account at build time (check `SHOW MODELS`/agent create success; do not assume) |
| Regression | One prompt per story PMD-0..PMD-12 (13) + 3 "why" prompts + 4 reasoning prompts (R1, R2, R12, R13) = 20; routing, figure and latency assertions; R13 must answer "no significant effect" for the skilled-but-inactive stratum |
| Permissions | Runs as the caller; the caller is `ACCOUNTADMIN` (service owner), so all tools resolve |

---

## 11. Demo script (30 minutes, Partner MD)

| Min | Beat | Screen | Spoken claim |
|---|---|---|---|
| 0-3 | Framing | C1 Business Overview -> C4 Platform Architecture | The business (2.1): bill codes, five uses of time and their targets, three pillars + ProServe360; the five-layer platform and the ontology graph; SAP = record, Snowflake = context and reasoning (C2/C3 are hand-outs, not presented) |
| 3-5 | Where the data comes from | P8 BDC Sources & Lineage | Real CLDs from connector `SNOWFLAKE_APJ` incl. four People Intelligence products; which rows are simulated and why |
| 5-8 | ProServe360 | P0 | FY26 vs FY25 per pillar; capacity mix by level; top cross-pillar risks (PMD-0) |
| 8-14 | **Operational Excellence** | P1 -> P2 -> P11 | Pareto tail; the FS project in loss, critical WP, pyramid drift, "why" from PM notes; assets it did not reuse and the hours they would have saved (PMD-1, 2, 8, 9) |
| 14-18 | **Value Creation** | P5 | Win-rate by pursuit intensity and team fit; open bids with weak fit and the bench people who would raise it (PMD-6, 10) |
| 18-24 | **People Development (People Intelligence)** | P3 -> P4 -> P6 | Utilisation vs level target; roll-off before 30 Dec; skills vs pipeline; attrition risk; AI-skilled but inactive; People+Agents margin (PMD-3, 4, 5, 7) |
| 24-28 | ProServe360 what-if | P7 + P10 | Bench-to-pipeline match; ask the Advisor the PMD-11 what-if and one free question |
| 28-30 | Close | P9 | Fee boundary evidence; publish-back to BDC; what goes back to SAP for each pillar |

---

## 12. Build plan

| Phase | Deliverable | Gate |
|---|---|---|
| B0 | Account inventory: CLD list, connector status, model availability; `ACOCO_DB`, warehouses, compute pool, image repo (as `ACCOUNTADMIN`) | Preflight read-only checks pass |
| B1 | Fiscal calendar decision (6.1), `MAP_MD_GROUP`, `MAP_PAYGRADE_LEVEL` over real CLD master data | Every MD group maps to >= 1 cost centre |
| B2 | Generator re-parameterised to 60 months, keyed to CLD keys; `ACOCO_SIM` loaded | G2 determinism; row counts in band |
| B3 | L1 nine domain schemas generated from `tools/l1_map.yml` over CLDs + SIM (`SOURCE_SYSTEM`, conformed keys) | Every view compiles; no technical columns; no cross-domain joins; union counts reconcile with L0 |
| B4 | L2 in build order (5.1): `CORE`, `ONTOLOGY.ENT_*`, marts, `REL_*`, `REASONING`, `SEMANTIC`, `ONT_*`, `SERVING`, `QUALITY` - DTs, VWs, 5 SVs, `REASONING` objects, 2 CSS (commentary, asset library), overlay, time-target, AI-productivity, learning-payback and asset tables; `ACOCO_L2.ONTOLOGY` via `tools/gen_ontology.py` | `validate.py` steps; `gen_ontology.py --check` passes (unique `ENT_*` keys, every SV join registered, no L0 reference in L2); story anchors measured and written back into section 6.3 |
| B5 | Agent + regression | 13/13 routing and figures |
| B6 | Container app: clone SC360 skeleton, implement context pages C1-C4 (incl. ontology graph) and P0-P10, registry, lint | Logic-free lint; every registry statement byte-identical to `tools/demo_queries.sql` |
| B7 | SPCS deploy, endpoint, warm-up runbook | First paint < 2 s warm; every page < 3 s |
| B8 | Demo script and two rehearsals | Presenter card with measured figures only |

---

## 13. Risks and open decisions

| # | Item | Mitigation / owner |
|---|---|---|
| OD-1 | CLD rows do not span the window; simulated rows dominate transactions | `SOURCE_SYSTEM` column everywhere; presenter states it (section 4.3) |
| OD-2 | Exact names of the additional People Intelligence data products | Confirm in BDC catalog; SIM stand-ins until shared |
| OD-3 | Fiscal variant with an October start may not exist in `FISCALYEAR_V1` | Generate calendar from `GEN_PARAMS`, log deviation |
| OD-4 | `ACCOUNTADMIN` for a public SPCS endpoint is broad | Demo-only; endpoint requires Snowflake login; suspend pool after demo; production uses a service role |
| OD-5 | Fee boundary not grant-enforced | Section 5.6 controls + `ACCESS_HISTORY` evidence |
| OD-6 | Shared account - other demos own neighbouring objects | Exact-name matching only; never alter CLDs or the connector |
| OD-7 | Compute pool cost if left running | `AUTO_SUSPEND_SECS = 3600`; explicit suspend in the runbook |
| OD-8 | SC360 repo is private (public URL returns 404) | Cloned via authenticated `gh`; vendor the skeleton into this repo rather than linking |
| OD-9 | BDC sharing-fee rate unconfirmed | Do not quote until confirmed |
| OD-10 | Asset library and pursuit-team data have no SAP source and are fully simulated | `SOURCE_SYSTEM = SIMULATED`; hours saved marked ESTIMATED; presenter names the real source in production (knowledge-management catalogue, CRM pursuit team) |
| OD-11 | Time mix sums to 100 % only if timesheet categories and Employee Availability agree | `validate.py` reconciliation: Delivery + Bid + Learning + Admin + Bench = available hours per person-month (+/- 1 %) |
| OD-12 | AI productivity is observational - AI-active people may be stronger to begin with | Compare within level x work type; show CI; agent and presenter say "associated with", never "caused"; learning payback uses a matched control |
| OD-13 | Ontology registry drifts from the Semantic Views | Generated by `tools/gen_ontology.py` from `DESCRIBE SEMANTIC VIEW`; CI check (5.3) |

---

## Appendix A - CLD inventory used (verified 2026-10-26 on `SFSEAPAC.SNOWFLAKE_SAP_APJ`)

People Intelligence: `COREWORKFORCEDATA_V1`, `EMPLOYEEAVAILABILITY_V1`, `WORKFORCEPLANNEDWORKINGTIME_V1`,
`ASSIGNMENTADDITIONALINFORMATION_V1`.
S/4HANA: `ENTRYVIEWJOURNALENTRY_V1`, `JOURNALENTRYHEADER_V1`, `JOURNALENTRYCODES_V1`, `JOURNALENTRYITEMCODES_V1`,
`PROJECT_V1`, `FINANCIALPLANNINGENTRYITEM_V1`, `COSTCENTER_V1`, `COSTCENTERACTIVITYTYPE_V1`, `PROFITCENTER_V1`,
`GENERALLEDGERACCOUNT_V1`, `CUSTOMER_V1`, `SALESCONTRACT_V1`, `FISCALYEAR_V1`.
Connector: `SAP_BDC_CONNECTOR_APJ.PUBLIC.SNOWFLAKE_APJ` (`SAP_BDC`, `CONNECTED`).
Not used: supply-chain, maintenance, mining, oil, BOM, plant, supplier and configuration CLDs; `SAP_CUSTOMER` (duplicate of `CUSTOMER_V1`).

## Appendix B - Reference UI repo analysis (`snowflakethia/sap-bdc-supply-chain-360`)

| Aspect | SC360 | Adopted for ACoCo |
|---|---|---|
| Layers | L0 BDC-shaped tables -> L2 `ANALYTICS` DTs (no L1) -> `APP_REF` serving views (labelled L1) -> 1 semantic view -> agent | Strict L0 -> L1 domains -> L2 assets; serving views inside L2 (`SERVING`); see Appendix D |
| App | React/Vite/Tailwind client + Express server, one container, port 8080, `/healthcheck` | Adopted unchanged |
| Navigation | Left sidebar with lucide icons, plant multi-select filter | Same, with MD group / FY range / size class filters |
| AI in UI | "Ask Cortex" per card (AI_COMPLETE over SQL facts) + full Cortex Analyst page | Ask Cortex adopted; analyst page replaced by the full Cortex Agent (multi-SV + search) |
| Lineage page | BDC Sources & Lineage | Adopted (P8) |
| Packaging | Native App with bundled data, org listing in 3 regions | Plain SPCS service first; Native App optional phase 2 (would need restricted caller's rights to read live L2 instead of bundling) |
| Data window | Static Jan-Sep 2025, `TARGET_LAG = DOWNSTREAM` (does not refresh) | ACoCo sets explicit lags (v1.1 lesson D70) |

## Appendix C - SEC indicators (unchanged from v1.1 section 3.1)

I1 Revenue · I2 Bookings / book-to-bill · I3 Operating margin · I4 Utilization · I5 Voluntary attrition ·
I6 Fixed-price contract risk · I7 Days services outstanding · I8 Cost of services / S&M / G&A · I9 Skills supply vs demand ·
I10 Advanced-AI bookings and revenue · I11 AI workforce and skilling · I12 AI-driven demand / utilization risk.

## Appendix D - Medallion review of `sap-bdc-supply-chain-360` and what ACoCo does differently

Reviewed 27 Oct 2026 at commit `d8a6823` (`docs/ARCHITECTURE.md`, `sql/01-07`, `SupplyChainDemo_OntologyBuild.md`,
`service/app/server/src/routes/{api,lineage}.ts`).

**How SC360 is layered today**

```
L0  SAP_SUPPLY_CHAIN.<product schemas>.A_*  (21 BDC-shaped native tables, not mounted shares)
    + MANUFACTURING_CODES.A_*, OPS_EXT.A_*, SUPPLIER_EXT.A_*  (demo enrichment, same database)
      |  dynamic tables read L0 directly - no L1
L2  SAP_SUPPLY_CHAIN.ANALYTICS.DT_*  (15 DTs)  +  ENT_MATERIAL / ENT_SUPPLIER / ENT_PLANT (views)
    + one semantic view SAP_SUPPLY_CHAIN_360 (17 logical tables, 13 relationships) + agent
      |
"L1"  APP_REF.*  1:1 SELECT * views over L2 DTs (and two L0 tables)  -> app
```

| # | Finding | Effect | ACoCo decision |
|---|---|---|---|
| F1 | **No L1.** DTs in `ANALYTICS` read `A_*` objects directly; the architecture doc says it "collapses L1 into the raw L0 objects" | Renaming, typing and key cleansing are repeated inside each DT; swapping a source (e.g. a real BDC share) means editing every DT that reads it | **L1 domain layer is mandatory** (7.1); L2 never reads L0; source swap = one L1 map entry |
| F2 | **`APP_REF` is labelled "L1 - Silver" on the lineage page** but sits downstream of L2 as `SELECT *` serving views | The medallion shown to the customer is out of order; silver is presented as a serving layer | Serving views are **L2 `SERVING`**; L1 means domains only; the lineage page (P8) shows L0 -> L1 -> L2 in true order |
| F3 | `APP_REF.A_PLANT` and `A_SUPPLY_CHAIN_NODES` expose **L0 tables straight to the app** | Breaks the "consumers read L2 only" boundary | Every app table interface is an L2 `SERVING` view; CI lint rejects L0/L1 names in `service/` (5.6) |
| F4 | **Ontology entities are derived from facts** - `ENT_MATERIAL` is a `UNION` of material columns from seven DTs; `ENT_SUPPLIER` from two | An entity exists only if a fact mentions it; descriptions depend on which fact wins `MAX()`; master data (plant, supplier) in L0 is ignored | `ENT_*` are built from the owning **L1 master-data domain** (Person from `WORKFORCE`, Project from `PROJECTS`...), then facts reference them |
| F5 | **One semantic view with 17 tables**, and the build pack lists gaps: parent-BOM link missing, plant linked by name, no customer/work-centre entity, no named metrics, a wrong primary key on `INVENTORY_OVERVIEW` | Cortex Analyst routing depends on a long `ai_sql_generation` prompt; KPIs are re-derived per query | Five Semantic Views (one per mart) sharing the **same `ENT_*` logical tables**; metrics named once (2.7, `ONT_METRIC`); key and relationship checks in CI (7.2 rules) |
| F6 | Every DT uses `TARGET_LAG = 'DOWNSTREAM'` with nothing downstream that sets a lag | DTs never refresh after creation (the v1.1 lesson D70) | Explicit `'1 hour'` on DTs read by Semantic Views or `SERVING`; `DOWNSTREAM` on intermediates only |
| F7 | Demo enrichment (`MANUFACTURING_CODES`, `OPS_EXT`, `SUPPLIER_EXT`) lives in the same database and naming (`A_*`) as the SAP products | SAP and non-SAP rows are indistinguishable by name; honesty depends on a note in `lineage.ts` | Non-SAP and gap-fill data in a **separate L0 database `ACOCO_SIM`**; `SOURCE_SYSTEM` column on every L1 row; Data Trust page shows the split |
| F8 | The lineage page lists an "ONTOLOGY schema - knowledge graph", but no such schema is created; the ontology page reads fact tables, and the semantic-model page reads `DESCRIBE SEMANTIC VIEW` live | The graph shown is partly real (relationships) and partly illustrative | `ACOCO_L2.ONTOLOGY` is real: `ENT_*`, `REL_*` and an `ONT_*` registry generated from the Semantic Views; C4 draws from `SERVING.VW_ONTOLOGY_GRAPH` |
| F9 | The Native App bundles 11 copied tables into `SHARED_DATA` | Fine for distribution, but the bundled data does not refresh | ACoCo runs as a plain SPCS service over live L2 (Appendix B); Native App remains optional phase 2 |

**What SC360 does well and ACoCo keeps**: zero-copy L0 treated as read-only; dynamic tables for L2; a serving
interface that decouples the app from physical tables; conformed entity views as the ontology's shared keys; reading
`DESCRIBE SEMANTIC VIEW` live so the ontology graph shows what Cortex Analyst can actually traverse; a guard procedure
that logs named checks and fails the build (`07b_supplier_ext_guard.sql` -> ACoCo `QUALITY.Q_CHECK_RESULTS`); an
explicit honesty note on modelled vs real data.
