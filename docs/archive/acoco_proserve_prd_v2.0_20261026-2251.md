# PRD - ACoCo Consulting: Partner MD Decision Support on SAP BDC + Snowflake (v2, SPCS edition)

**Document type:** Product Requirements Document (rebuild blueprint)
**Version:** 2.0 - 26 October 2026
**Supersedes:** `PRD/ACoCo_Agentic_AI_Decision_Support_Demo_PRD.md` v1.1 (Streamlit edition, three personas, four roles)
**Target account:** `<ORG>.<ACCOUNT>` (AWS, connector `SNOWFLAKE_APJ`, status `CONNECTED`)
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
| C7 | Fee boundary | Enforced by grants (`ACOCO_APP` has no privilege on L0/L1) | **Enforced by design, evidenced by `ACCESS_HISTORY`** - grants cannot enforce it under a single `ACCOUNTADMIN` role | Consequence of C1; see section 5.4 |
| C8 | Story figures | Measured on the v1.1 dataset (e.g. P-0417 forecast margin -0.6 %) | **All story figures are design targets until re-measured** on the new 60-month dataset | The generator, window and calendar change; no v1.1 figure carries over |

Everything not listed - the medallion discipline, single definition of every metric, logic-free front end, the
as-of control view, honesty markers - carries over unchanged.

---

## 1. Executive summary

| Item | Decision |
|---|---|
| Story | ACoCo's revenue is people-hours; its risks are fixed-price overrun, bench cost and skills mismatch. Agentic AI lifts productivity per consultant only where consultants have the skills to use it. A **Partner MD** uses one app and one agent to find where margin, bench and AI return sit across five years of history - and to act on it in SAP. |
| Persona | **Partner MD, Financial Services group** - owns the group's client portfolio (projects, opportunities) and the group's people (home cost centre). Can toggle to firm-wide. |
| Data | **L0** = SAP BDC data products as **catalog-linked databases** (S/4HANA finance/project + SAP People Intelligence workforce) + `ACOCO_SIM` (BDC-shaped synthetic data for products not yet shared) + AI-agent telemetry. **L1** passthrough views. **L2** dynamic tables + 5 Semantic Views. |
| Reasoning | Cortex Agent `ACOCO_ADVISOR` (5 Cortex Analyst tools + 1 Cortex Search tool), Cortex `AI_COMPLETE` for in-page "Ask Cortex" explanations, Snowflake ML for forecasts and risk scores. |
| Front end | **ACoCo Command Center** - React (Vite, Tailwind, Recharts) + Express (Node 20) in one container, served by an SPCS **service** on compute pool `ACOCO_POOL`, public endpoint, sidebar navigation and Ask-Cortex buttons as in Supply Chain 360. |
| Security model | Everything runs as `ACCOUNTADMIN`. The service's identity is the service owner (`ACCOUNTADMIN`). |
| Time | Demo today = **2026-10-01**. Data = 2021-10-01 to 2026-09-30. FY = Oct-Sep. "Current" = last closed month **Sep 2026** = FY26 close. |
| Scale (design) | ~1,000 consultants (with hires and leavers over 5 years: ~1,700 distinct people), ~400 projects, ~800 opportunities, 60 closed fiscal months, six MD groups. |

---

## 2. Persona and user stories

### 2.1 The Partner MD

| Attribute | Value |
|---|---|
| Title | Partner, Managing Director - Financial Services (bill code 70+) |
| Scope | Group portfolio: projects/opportunities whose client belongs to the FS group; group people: home cost centre in the FS group. Toggle: **Firm-wide**. |
| Horizon | Five fiscal years for trend; FY26 (just closed) for performance; next 90 days (from 2026-10-01) for forward risk |
| Decisions | Where to intervene on margin/delivery risk; where bench is forming and how to redeploy; whether pre-sales and AI investment pay back; which skills to build or hire; which people are at risk of leaving |
| Scoping mechanism | **No row access policy.** The app passes `MD_GROUP_ID` as a filter into every `SEMANTIC_VIEW()` query; the agent receives it in its instructions. This is a demo convenience, not a security boundary, and the presenter says so. |

### 2.2 User stories (all for the Partner MD)

Format: story -> demo question -> data products -> L2 / Semantic View -> SEC indicator (indicators I1-I12 are
unchanged from v1.1 section 3.1 and reproduced in Appendix C).

**PMD-1 - Portfolio health and the Pareto tail.** I need revenue, margin, bookings and on-time status for my
portfolio over five years, with Large projects separated, so I intervene on the few projects that decide the year.
- *"Show FY22-FY26 revenue and margin by project size class for my group, and list every live fixed-price project whose forecast margin is below 10 %."*
- EntryViewJournalEntry, JournalEntryHeader, Project, FinancialPlanningEntryItem, CostCenter, ProfitCenter, Customer, SalesContract.
- `SV_PORTFOLIO_360`, `SV_PROJECT_DELIVERY`. SEC: I1, I3, I6.

**PMD-2 - Fixed-price exposure (drill: project -> work package).** I need CPI, SPI, EAC, liquidated-damages
exposure and margin erosion for one at-risk project and its work packages, so I re-plan before it turns into a loss.
- *"For my worst fixed-price project, show plan vs actual by month, EAC, SPI, and which work package is the critical path."*
- EntryViewJournalEntry, FinancialPlanningEntryItem, Project (WBS), `ACOCO_SIM` CustomerProject. `SV_PROJECT_DELIVERY`. SEC: I6, I8.
- (Absorbs v1.1 SM-1, SM-2.)

**PMD-3 - Bench and capacity.** I need utilization, billability and bench cost by level and month, and the
90-day roll-off list from 1 Oct 2026, so I redeploy or retrain before bench cost lands.
- *"What is my group's utilization by level over the last 12 months, the September bench cost, and who rolls off before 30 Dec 2026 without a next assignment?"*
- **People Intelligence:** Core Workforce Data, Employee Availability, Workforce Planned Working Time, Assignment Additional Information; `ACOCO_SIM` Timesheet, ResourceAssignment. `SV_WORKFORCE_PERFORMANCE`. SEC: I4, I8.

**PMD-4 - Skills supply vs demand.** I need the skills profile (incl. the Agentic-AI family) of my people against
the skills my open pipeline requires, so I decide to train, hire or partner.
- *"Which skills does my open pipeline need that my roll-off population lacks, and what AI-curriculum learning would close the gap?"*
- **People Intelligence:** Skills / Talent Intelligence Hub, Learning; `ACOCO_SIM` Opportunity. `SV_WORKFORCE_PERFORMANCE`, `SV_PIPELINE_PRESALES`. SEC: I9, I11.

**PMD-5 - Attrition and retention risk.** I need annualized voluntary attrition by level over five years and the
people currently at elevated risk, so I act on retention before key-account knowledge walks out.
- *"What is voluntary attrition by level FY22-FY26, and which of my Managers and above on Large accounts have an elevated attrition-risk score?"*
- **People Intelligence:** Core Workforce Data (`terminations`, `moveOutReason`, `organizationalTenure`, `payGrade`, `compa` from salary range), Compensation, Performance. `SV_WORKFORCE_PERFORMANCE` + ML score in `DT_ATTRITION_RISK`. SEC: I5.
- **New in v2** (five years of history makes it credible).

**PMD-6 - Pre-sales and pipeline payback.** I need win-rate by pre-sales intensity, bookings and book-to-bill,
so I decide where to place the next pre-sales hour.
- *"Compare win-rate for above- vs below-median pre-sales investment within deal size, and show FY26 book-to-bill."*
- `ACOCO_SIM` Opportunity, InternalOrder; EntryViewJournalEntry (pre-sales GL). `SV_PIPELINE_PRESALES`. SEC: I2, I8.

**PMD-7 - Agentic-AI return.** I need AI spend against margin, CPI and productivity on AI-enabled vs human-only
projects, and adoption by AI-skill level, so I decide where to put AI capacity.
- *"Show AI cost and margin for People+Agents vs People-only projects over FY24-FY26, and productivity by AI-skill quartile."*
- EntryViewJournalEntry (`AGT_*` activity allocations), CostCenterActivityType, AI telemetry, Skills. `SV_AI_ADOPTION`. SEC: I10, I11, I12.

**PMD-8 - "Why?" questions.** I need the delivery narrative behind a number, so I can challenge the project lead.
- *"Why is P-xxxx behind schedule?"* -> Cortex Search over PM status commentary (`CSS_PROJECT_COMMENTARY`).

---

## 3. SAP People Intelligence - the data products needed

SAP People Intelligence (on SAP Business Data Cloud) packages SuccessFactors data as SAP-managed data products and
ships its own insight apps on top. For ACoCo, Snowflake consumes the **same data products** zero-copy and joins them
with S/4HANA project finance - something People Intelligence alone does not do.

### 3.1 Already shared to `<ORG>.<ACCOUNT>` (verified 2026-10-26)

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
| Master data (cost centres, profit centres, GL, activity types, customers, fiscal calendar) | CLDs | Used as-is at L1. ACoCo's six MD groups are a **mapping table** (`ACOCO_DB.OPS.MAP_MD_GROUP`) over real cost-centre hierarchy nodes |
| People master and capacity | People Intelligence CLDs | Used as-is for the population they cover; **back-history** Oct 2021-Dec 2022 is generated in `ACOCO_SIM` in the identical column shape, keyed to the same `userId` |
| Transactions Oct 2021-Sep 2026 (journal lines on ACoCo projects, plan, timesheets, assignments, opportunities) | `ACOCO_SIM` | Generated by the seeded generator, keyed to CLD master data (real cost centres, GL accounts, activity types, customers, WBS where possible) |
| Products SAP does not ship for professional services (CustomerProject, Timesheet, ResourceAssignment, Opportunity, InternalOrder, BillableControl) | `ACOCO_SIM` | One schema per product, CDS-shaped, as in v1.1 |
| Products requested but not yet shared (Skills, Learning, Performance, Compensation, Succession) | `ACOCO_SIM` | Same shape as the expected product; swapped for the real CLD when it arrives (L1 regenerated from `INFORMATION_SCHEMA`) |
| AI-agent telemetry | `ACOCO_SIM.TELEMETRY` (OpenAI, Anthropic shapes) + `SNOWFLAKE.ACCOUNT_USAGE` (Cortex) | As v1.1 section 2.4 |

**L1 unions CLD and `ACOCO_SIM` rows per business object** where both exist (e.g. `HUMAN_CAPITAL.WORKFORCE_JOB` =
CLD `coreworkforce_standardfields` UNION ALL `ACOCO_SIM` back-history), carrying a `SOURCE_SYSTEM` column
(`BDC_CLD` / `SIMULATED`). The Data Trust page shows the split. The presenter states plainly which numbers are
real-tenant shape and which are simulated.

> **Open decision OD-1.** Alternative: restrict L0 to the CLDs only and accept a 2023-2026 window for people data.
> Rejected here because the user fixed a five-year window; flag it if the customer prefers "real CLD rows only".

---

## 5. Architecture

### 5.1 Reference architecture

```
SAP S/4HANA (PCE) + SAP SuccessFactors        SAP Business Data Cloud / SAP People Intelligence
  (System of Record)               ------>     SAP-managed data products (CSN/ORD)
                                                   | zero-copy, connector SNOWFLAKE_APJ
=============================== Snowflake <ORG>.<ACCOUNT> (System of Context & Reasoning) ====
L0  CLDs (read-only)  *_V1  ...............  ACOCO_SIM (BDC-shaped gap-fill)  SNOWFLAKE.ACCOUNT_USAGE
L1  ACOCO_L1.{FINANCE,PROJECTS,SALES,HUMAN_CAPITAL,MASTER_DATA,TELEMETRY}   views, typed, unioned
L2  ACOCO_L2.{CORE,WORKFORCE_PERFORMANCE,PROJECT_DELIVERY,PIPELINE_PRESALES,AI_ADOPTION,
              PORTFOLIO_360,QUALITY,REASONING}  dynamic tables + VW_* + 5 Semantic Views + CSS + ML
        ^ fee boundary: every consumer reads here
Reason  Cortex Agent ACOCO_ADVISOR  |  AI_COMPLETE (Ask Cortex)  |  Snowflake ML (forecast, risk)
Serve   SPCS service ACOCO_COMMAND_CENTER on compute pool ACOCO_POOL  (React + Express, public endpoint)
Act     -> SAP: staffing request / project re-plan (write-back via API, roadmap)
        -> BDC: derived data products published back (SYSTEM$SAP_PUBLISH_DATA_PRODUCT, roadmap)
```

### 5.2 Object inventory (all owned by `ACCOUNTADMIN`)

| Kind | Name | Notes |
|---|---|---|
| Databases | `ACOCO_DB` (`OPS`, `AGENT`, `APP`), `ACOCO_SIM`, `ACOCO_L1`, `ACOCO_L2` | `ACOCO_L0` of v1.1 is **retired** - L0 is the CLDs plus `ACOCO_SIM` |
| Warehouses | `WH_ACOCO_BUILD` (Medium, auto-suspend 60 s, timeout 3600 s), `WH_ACOCO_APP` (X-Small, auto-suspend 60 s, timeout 300 s) | Exact names; never prefix-matched |
| Compute pool | `ACOCO_POOL` - `INSTANCE_FAMILY = CPU_X64_XS`, `MIN_NODES = 1`, `MAX_NODES = 1`, `AUTO_SUSPEND_SECS = 3600`, `AUTO_RESUME = TRUE` | Resume and warm the service before a demo |
| Image repository | `ACOCO_DB.APP.IMAGES` | Image `acoco_command_center:<tag>` |
| Service | `ACOCO_DB.APP.ACOCO_COMMAND_CENTER` | Spec in 8.5; `QUERY_WAREHOUSE = WH_ACOCO_APP` |
| Agent | `ACOCO_DB.AGENT.ACOCO_ADVISOR` | 6 tools |
| Cortex Search | `ACOCO_L2.PROJECT_DELIVERY.CSS_PROJECT_COMMENTARY` | PM status notes |
| Semantic Views | `SV_PORTFOLIO_360`, `SV_PROJECT_DELIVERY`, `SV_WORKFORCE_PERFORMANCE`, `SV_PIPELINE_PRESALES`, `SV_AI_ADOPTION` | Names frozen (mirrored in agent tools) |
| ML | `ACOCO_L2.REASONING`: `DT_ATTRITION_RISK`, `FC_DEMAND_BY_SKILL` (forecast), model registry entries | New schema in v2 |
| Roles | **none created** | Everything as `ACCOUNTADMIN` |
| Row access policies | **none** | Group scoping is a query filter |

### 5.3 Layer rules (carried over)

- L0 is never modified. L1 = views only, one per business object, typed dates, `UPPER(TRIM())` identifiers, technical
  columns dropped, CLD + SIM union with `SOURCE_SYSTEM`.
- L2 dynamic tables are deterministic - no `CURRENT_DATE` - with explicit `TARGET_LAG` (`'1 hour'` on tables a Semantic
  View reads, `DOWNSTREAM` on intermediates) and `REFRESH_MODE = INCREMENTAL` where the shape allows.
- "Today" lives only in `ACOCO_L2.CORE.VW_AS_OF` = `COALESCE(override, CURRENT_DATE())`, override **2026-10-01**.
- Semantic Views reference only L2 objects.
- The front end issues only `SELECT ... FROM SEMANTIC_VIEW(...)` or `SELECT ... FROM ACOCO_L2.<schema>.VW_*`, plus agent
  and `AI_COMPLETE` calls. No metric is computed in TypeScript.

### 5.4 Fee boundary without custom roles

With one `ACCOUNTADMIN` role, grants cannot stop the app from reading a CLD. The boundary is therefore:

1. **Server allow-list.** The Express server only executes statements from a static registry (`server/src/registry.sql`);
   ad-hoc SQL from Cortex Analyst is accepted only if every referenced object is in `ACOCO_L2` (checked by parsing the
   `EXPLAIN` object list before execution).
2. **Build-time lint.** CI fails if `service/` contains a `*_V1` CLD name, `ACOCO_SIM.` or `ACOCO_L1.`.
3. **Runtime evidence.** `QUERY_TAG = 'ACOCO_APP'` on the service's session; the Data Trust page reads a captured
   `ACCESS_HISTORY` snapshot proving app traffic touched only `ACOCO_L2` objects, while dynamic-table refresh is the only
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
| Keys | synthetic | **Keyed to CLD master data**: real `CostCenter`, `ProfitCenter`, `GLAccount`, `CostCtrActivityType`, `Customer`, and People Intelligence `userId` |

Volume estimate (design): ~6-7 M rows in `ACOCO_SIM` (timesheet dominates); L2 rebuild < 30 minutes on Medium.

### 6.3 Story anchors (design targets - re-measure before speaking)

| Anchor | Design target |
|---|---|
| One Large FS fixed-price project in loss at FY26 close | forecast margin < 0 %, CPI ~0.73, SPI ~0.8 |
| FY26 firm utilization / billability | ~74 % / ~66 % (bench ~26 %) |
| Roll-off before 30 Dec 2026 without successor | 30-40 people in FS; > 75 % below the pipeline's required AI-skill level |
| Attrition trend | FY22 peak ~18 % -> FY26 ~13 % |
| AI return (FY26, FS) | People+Agents margin ~10 pts above People-only; CPI > 1.1 vs ~1.0 |
| Pre-sales | above-median intensity win-rate ~50 % vs ~30 % within size class |

Every figure is re-measured by a `validate.py` assertion and restated as **measured** in this document before the demo.
v1.1's measured figures (P-0417, Daniel Okafor, Omar Rodriguez, 38 roll-offs, etc.) **do not carry over**.

---

## 7. L1 and L2 content

### 7.1 L1 (views, `ACOCO_L1`)

| Schema | Views (source) |
|---|---|
| `FINANCE` | `JOURNAL_ENTRY_ITEM` (CLD `operationalacctgdocitem` filtered to ACoCo company codes UNION SIM), `JOURNAL_ENTRY_HEADER`, `PROJECT_PLAN_ITEM`, `INTERNAL_ORDER` (SIM) |
| `PROJECTS` | `PROJECT`, `WBS_ELEMENT`, `WBS_MILESTONE` (CLD + SIM), `CUSTOMER_PROJECT`, `WORK_PACKAGE`, `WORK_PACKAGE_SKILL_REQUIREMENT`, `TIMESHEET_RECORD`, `RESOURCE_ASSIGNMENT` (SIM) |
| `SALES` | `OPPORTUNITY` (SIM), `SALES_CONTRACT` (CLD) |
| `HUMAN_CAPITAL` | `WORKFORCE_JOB` (Core Workforce CLD + SIM back-history), `EMPLOYEE_AVAILABILITY`, `PLANNED_WORKING_TIME`, `JOB_RELATIONSHIP` (CLD), `PERSON_SKILL`, `LEARNING_COMPLETION`, `LEARNING_ITEM`, `PERFORMANCE_RATING`, `SUCCESSION_NOMINATION` (SIM until shared) |
| `MASTER_DATA` | `COST_CENTER`, `COST_CENTER_HIERARCHY`, `ACTIVITY_TYPE`, `PROFIT_CENTER`, `GL_ACCOUNT`, `CUSTOMER`, `FISCAL_PERIOD` (CLD) |
| `TELEMETRY` | as v1.1 (11 views) |

L1 is generated (`tools/gen_l1.py`) from `INFORMATION_SCHEMA` of each CLD and `ACOCO_SIM`, so a newly shared People
Intelligence product replaces its SIM stand-in by regeneration.

### 7.2 L2 (`ACOCO_L2`)

As v1.1 section 2.6 (18 dynamic tables, `VW_*` views, 5 Semantic Views, quality snapshots), with these changes:

| Change | Detail |
|---|---|
| `DT_PERSON_DIM` | Built from `WORKFORCE_JOB` (People Intelligence): latest effective record <= as-of; `payGrade` -> level/bill code via `MAP_PAYGRADE_LEVEL`; home MD group via `costCenter` -> `MAP_MD_GROUP`; `managerId`; tenure |
| `DT_PERSON_MONTH_SCORECARD` | Available hours from **Employee Availability** (`plannedWorkHours - dailyAbsenceHours`), not from a generated calendar |
| `DT_HEADCOUNT_MONTH` (new) | sop/eop/avg headcount, hires, voluntary/involuntary terminations by group x level x month -> annualized attrition |
| `VW_PERSON_MTD` | Becomes `VW_PERSON_LAST_CLOSED_MONTH` (Sep 2026), because Oct 2026 has one day |
| `VW_ROLL_OFF_90D` | Window 2026-10-01 to 2026-12-30 |
| `REASONING` schema (new) | `DT_ATTRITION_RISK` (person score + top drivers), `FC_DEMAND_BY_SKILL` (12-month demand forecast from weighted pipeline), `VW_BENCH_TO_PIPELINE_MATCH` |
| Semantic Views | Same five; `SV_WORKFORCE_PERFORMANCE` gains headcount/attrition metrics and the attrition-risk table; all comments state `SOURCE_SYSTEM` caveats |
| Removed | `RAP_PERSON_SCOPE`, `VW_MY_SCOPE`, SM/IC-only views not used by the MD drill |

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

| # | Page | Story | Content | Source |
|---|---|---|---|---|
| P0 | **Executive Overview** | PMD-1 | KPI cards (FY26 revenue, margin, book-to-bill, utilization, bench cost, attrition, AI spend) vs FY25; 60-month revenue/margin trend with "As of 1 Oct 2026" rule; top 5 risks list | `SV_PORTFOLIO_360`, `VW_PORTFOLIO_PACING` |
| P1 | **Portfolio & Pareto** | PMD-1 | Revenue by size class FY22-FY26; Pareto curve; fixed-price projects < 10 % forecast margin table (click -> P2) | `SV_PORTFOLIO_360`, `SV_PROJECT_DELIVERY` |
| P2 | **Project Health** (drill) | PMD-2 | Project header (contract, CPI, SPI, EAC, LD exposure, RAG); plan vs actual by month; work-package table with critical path; "Why?" button -> Cortex Search | `SV_PROJECT_DELIVERY`, `VW_PROJECT_HEALTH_NOW`, CSS |
| P3 | **Workforce & Bench** | PMD-3 | Utilization/billability by level (12 and 60 months); bench cost by month; roll-off-90-day table with skills | `SV_WORKFORCE_PERFORMANCE`, `VW_ROLL_OFF_90D` |
| P4 | **People Intelligence** | PMD-4, PMD-5 | Headcount and attrition FY22-FY26; attrition-risk list (Manager+) with drivers; skills supply vs pipeline demand heatmap; AI-curriculum items for the gap | `SV_WORKFORCE_PERFORMANCE`, `DT_ATTRITION_RISK`, `FC_DEMAND_BY_SKILL` |
| P5 | **Pipeline & Pre-sales** | PMD-6 | Pipeline by stage/size; win-rate by intensity within size; bookings and book-to-bill FY22-FY26 | `SV_PIPELINE_PRESALES` |
| P6 | **Agentic-AI Return** | PMD-7 | Adoption S-curve FY22-FY26; AI cost by vendor; margin and CPI by delivery model; productivity by AI-skill quartile | `SV_AI_ADOPTION` |
| P7 | **Context & Reasoning** | section 9 | Gallery of the System-of-Context use cases with live mini-tiles (bench-to-pipeline match, demand forecast, margin-leak detector) | `ACOCO_L2.REASONING` |
| P8 | **BDC Sources & Lineage** | - | CLD inventory (name, rows, freshness, `SOURCE_SYSTEM` share), connector status, L0 -> L1 -> L2 -> SV lineage graph | `ACOCO_L2.QUALITY` snapshots, captured lineage |
| P9 | **Data Trust** | - | Freshness, completeness, fee-boundary evidence (`ACCESS_HISTORY` snapshot) | `ACOCO_L2.QUALITY` |
| P10 | **Ask the Advisor** | PMD-1..8 | Full-page chat with `ACOCO_ADVISOR`; streams text, tables, charts, cited SQL; suggested prompts per story | Agent REST API |
| - | **Ask Cortex** (on P0-P7) | - | Button per card: server fetches the registry facts behind that card and calls `AI_COMPLETE` to explain them, citing the numbers shown (SC360 pattern) | `SNOWFLAKE.CORTEX.AI_COMPLETE` |
| - | **Demo Context** (top-bar link) | - | Static briefing: ACoCo, KPIs, levels, persona, demo flow | static |

Global filters (left rail, `useFilters`): **MD group** (default Financial Services, or Firm-wide), **fiscal year range**
(default FY22-FY26), **size class**. They become `WHERE` clauses on the `SEMANTIC_VIEW()` call - never client-side filtering of
fetched rows.

### 8.4 API contract (server)

| Route | Method | Returns |
|---|---|---|
| `/api/filters` | GET | MD groups, fiscal years, size classes |
| `/api/overview`, `/api/portfolio`, `/api/project/:id`, `/api/workforce`, `/api/people`, `/api/pipeline`, `/api/ai`, `/api/reasoning`, `/api/lineage`, `/api/trust` | GET | JSON per page, from registry statements with bound filter parameters |
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

Demo scope: **R1, R2, R3 and R9 are live** on page P7 and through the Advisor. R5 and R6 appear as tiles. R4, R7, R8,
R10, R11 are shown as roadmap cards with their data lineage. Write-back to SAP is **narrated, not executed** in the demo.

---

## 10. Cortex Agent `ACOCO_ADVISOR`

| Item | Specification |
|---|---|
| Location | `ACOCO_DB.AGENT.ACOCO_ADVISOR`, generated by `tools/gen_agent.py` |
| Tools | 5 Cortex Analyst (one per Semantic View) + 1 Cortex Search (`project_commentary`) |
| Instructions | Persona = Partner MD, FS group unless asked firm-wide; today = 2026-10-01, "this year" means FY26 (closed) unless the user says FY27; fiscal year Oct-Sep; state `SOURCE_SYSTEM` caveat when a figure includes simulated rows; never quote individual pay |
| Model | Use a model confirmed available on this account at build time (check `SHOW MODELS`/agent create success; do not assume) |
| Regression | One prompt per story PMD-1..PMD-8 + 3 "why" prompts + 2 reasoning prompts (R1, R2) = 13; routing, figure and latency assertions |
| Permissions | Runs as the caller; the caller is `ACCOUNTADMIN` (service owner), so all tools resolve |

---

## 11. Demo script (30 minutes, Partner MD)

| Min | Beat | Screen | Spoken claim |
|---|---|---|---|
| 0-3 | Framing | Demo Context | SAP = record; Snowflake = context and reasoning; zero-copy from BDC and People Intelligence |
| 3-6 | Where the data comes from | P8 BDC Sources & Lineage | Real CLDs from connector `SNOWFLAKE_APJ`; which rows are simulated and why |
| 6-10 | Five-year portfolio | P0 -> P1 | FY22-FY26 revenue/margin; the Pareto tail; the FS project in loss |
| 10-14 | Drill and why | P2 + Ask "why" | CPI/SPI, critical work package, Cortex Search answer from PM notes |
| 14-18 | Bench and people | P3 -> P4 | Roll-off before 30 Dec; attrition trend and who is at risk (People Intelligence) |
| 18-21 | Reasoning | P7 | Bench-to-pipeline match and skills demand forecast |
| 21-24 | AI return | P6 | Adoption S-curve; People+Agents margin; agent cost inside the Universal Journal |
| 24-28 | Ask anything | P10 | Two live questions to the Advisor, one cross-domain |
| 28-30 | Close | P9 | Fee boundary evidence; publish-back to BDC; what goes back to SAP |

---

## 12. Build plan

| Phase | Deliverable | Gate |
|---|---|---|
| B0 | Account inventory: CLD list, connector status, model availability; `ACOCO_DB`, warehouses, compute pool, image repo (as `ACCOUNTADMIN`) | Preflight read-only checks pass |
| B1 | Fiscal calendar decision (6.1), `MAP_MD_GROUP`, `MAP_PAYGRADE_LEVEL` over real CLD master data | Every MD group maps to >= 1 cost centre |
| B2 | Generator re-parameterised to 60 months, keyed to CLD keys; `ACOCO_SIM` loaded | G2 determinism; row counts in band |
| B3 | L1 regenerated over CLDs + SIM (`SOURCE_SYSTEM`) | Every view compiles; no technical columns; union counts reconcile |
| B4 | L2 DTs, VWs, 5 SVs, `REASONING` objects, CSS | `validate.py` steps; story anchors measured and written back into section 6.3 |
| B5 | Agent + regression | 13/13 routing and figures |
| B6 | Container app: clone SC360 skeleton, implement P0-P10, registry, lint | Logic-free lint; every registry statement byte-identical to `tools/demo_queries.sql` |
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
| OD-5 | Fee boundary not grant-enforced | Section 5.4 controls + `ACCESS_HISTORY` evidence |
| OD-6 | Shared account - other demos own neighbouring objects | Exact-name matching only; never alter CLDs or the connector |
| OD-7 | Compute pool cost if left running | `AUTO_SUSPEND_SECS = 3600`; explicit suspend in the runbook |
| OD-8 | SC360 repo is private (public URL returns 404) | Cloned via authenticated `gh`; vendor the skeleton into this repo rather than linking |
| OD-9 | BDC sharing-fee rate unconfirmed | Do not quote until confirmed |

---

## Appendix A - CLD inventory used (verified 2026-10-26 on `<ORG>.<ACCOUNT>`)

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
| Layers | L0 BDC products -> L2 `ANALYTICS` DTs -> `APP_REF` serving views -> 1 semantic view -> agent | Keep ACoCo's L1 (needed for CLD + SIM union) and 5 SVs; adopt the serving-view idea as `VW_*` |
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
