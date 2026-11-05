# P6 AI Productivity & Learning - Requirement Specification

Version 0.3 (draft for checkpoint CP-P6a) - 2026-11-05
v0.4: targets reuse OPS.GEN_PARAMS_TIME_TARGET (learning 10 % every level); asset-building hours recorded, not budgeted (2.3).
v0.3: PD input weights confirmed and made level-dependent (2.4); Cortex model names confirmed against the account (4.1).
v0.2: learning input added to PD; asset creation/reuse redesigned; small-cell rules; all vendor models;
vendor/product effect matrix (Cortex -> OE all levels; Claude Code -> WIN Manager and below; Codex -> WIN Senior Manager+).
Approved at CP-P6a on 2026-11-05 by Boon Sing Thia (incl. ACREATE 15 %, small-cell rules 3.1 as written).
Scope: P6 "People Development - AI Productivity & Learning" and the data it needs.
Companion: `docs/impact_p6_productivity.md` (what existing work changes).

---

## 1. Purpose

Replace the single efficiency index used by P6 today (`PRODUCTIVITY_INDEX = EARNED_HOURS / DELIVERY_HOURS`)
with a professional, explainable **Workforce Productivity Score (WPS)**, and use it to answer:

| ID | Business question |
|---|---|
| Q1 | What is a balanced way to measure an individual's productivity? |
| Q2 | What is the productivity of the workforce at each level (Analyst to Principal)? |
| Q3 | Is AI token usage associated with productivity, within each level? |
| Q4 | Is usage of a specific vendor's tokens (Claude, OpenAI, Cortex) associated with productivity, within each level? |
| Q5 | Are training hours associated with productivity, within each level? |
| Q6 | Are hours in a specific curriculum associated with productivity, within each level? |

Design principles: simple to implement in SQL, explainable on one slide, fair across levels, and honest
(observational association only, with null results visible).

---

## 2. Workforce Productivity Score (Q1)

### 2.1 Grain and population

- Grain: person x fiscal quarter (fiscal variant V9, Oct-Sep).
- Population: delivery levels Analyst, Consultant, Manager, Senior Manager, Principal with at least
  80 available hours in the quarter. Leavers are scored for the quarters they were employed.

### 2.2 Scaling rule (applies to every input)

Every raw input `x` is normalised **within level and fiscal year** so people are compared with peers:

```
z     = (x - mean_level_fy(x)) / sd_level_fy(x)      -- clipped to [-3, +3]
score = LEAST(100, GREATEST(0, 50 + 15 * z))          -- 50 = level average
```

If `sd = 0` or the input is missing, the score is 50 (neutral), except where noted.

### 2.3 Inputs

| Input | Raw definition | Source |
|---|---|---|
| WIN | Shrunk win-rate on closed opportunities the person is named on in the bid team (`OPPORTUNITY_TEAM`: LEAD, MEMBER or SUPPORT) in the trailing 4 quarters: `(wins + 3 * level_win_rate) / (bids + 3)` | `DT_OPPORTUNITY_FACT`, `REL_PURSUIT_TEAM` |
| EFF | Earned-hour efficiency: `EARNED_HOURS / DELIVERY_HOURS` | timesheet |
| SCHED | Schedule score, hours-weighted over the work packages worked: ahead `1 + LEAST(ahead_wks / plan_wks, 0.2)`, on time `1`, late `GREATEST(0, 1 - slip_wks / plan_wks)`. Closed work uses `ACTUAL_END`, open work uses `FORECAST_END` | `ENT_WORK_PACKAGE` |
| BILL | Billability at level: `BILLABLE_HOURS / AVAILABLE_HOURS / BILLABILITY_TARGET(level)` | timesheet, `OPS.GEN_PARAMS_TIME_TARGET` |
| UTIL | Utilization at level: `(BILLABLE + PRESALES + ASSET_CONTRIBUTION hours) / AVAILABLE_HOURS / UTILIZATION_TARGET(level)` | timesheet, `ASSET_CONTRIBUTION`, `OPS.GEN_PARAMS_TIME_TARGET` |
| LEARN | Learning attainment: `0.7 * LEAST(learning_hours_T4Q / (LEARNING_TARGET * available_hours_T4Q), 1.2) + 0.3 * required_curricula_completed / required_curricula(level)` (trailing 4 quarters) | LMS, `OPS.GEN_PARAMS_TIME_TARGET`, `OPS.LEVEL_REQUIRED_CURRICULUM` |
| ACREATE | Asset creation: `SUM(role_weight * quality)` over assets contributed to in the trailing 4 quarters; role weight Author 1.0 / Contributor 0.5 / Reviewer 0.25; `quality = avg_rating / 5 * LN(1 + reuse_count)` (min 0.2 so new assets still count) | `ASSET_CONTRIBUTION`, `ASSET_USAGE` |
| AREUSE | Asset reuse: hours saved by reusing firm assets on own work / delivery hours, trailing 4 quarters (hours saved are recorded at the work-package start, so a single quarter is too lumpy) | `ASSET_USAGE` |
| TEAM | Mean WPS (excluding TEAM pillar) of the team in the quarter: Manager = direct reports; Senior Manager and Principal = whole reporting tree, direct and indirect, depth <= 4 (decision 2026-11-05) | `REL_PERSON_REPORTS_TO`, `REL_PERSON_REPORTING_LINE` |

Billability and utilization are now different measures: billability counts client-billable hours only;
utilization adds presales (bid) hours and asset-contribution hours.
Asset-building time is **recorded but not budgeted** (decision 2026-11-05): contributors log hours in
`ASSET_CONTRIBUTION.HOURS`, no timesheet time is set aside for it (no separate timesheet category), and those hours
are added to utilization only. Because they overlap delivery or bid time, utilization can exceed 100 % of
available hours; the page labels this.

Level targets reuse the existing CP-02 time targets (`OPS.GEN_PARAMS_TIME_TARGET`, decision 2026-11-05) - no new
target columns on `OPS.LEVEL`:

| Level | BILLABILITY_TARGET (= DELIVERY) | UTILIZATION_TARGET (= DELIVERY + BID) | LEARNING_TARGET (= LEARNING) | Required curricula (`OPS.LEVEL_REQUIRED_CURRICULUM`) |
|---|---|---|---|---|
| Analyst | 0.75 | 0.85 | 0.10 | 1 AI curriculum, SAP_FUNCTIONAL |
| Consultant | 0.71 | 0.85 | 0.10 | 1 AI curriculum, PROJECT_MGMT |
| Manager | 0.60 | 0.85 | 0.10 | 1 AI curriculum, LEADERSHIP, COMMERCIAL_BID |
| Senior Manager | 0.45 | 0.85 | 0.10 | 1 AI curriculum, LEADERSHIP, COMMERCIAL_BID |
| Principal | 0.35 | 0.85 | 0.10 | 1 AI curriculum, LEADERSHIP |

Learning stays at the CP-02 target of 10 % of available hours at every level (D-02-11).

### 2.4 Pillars

| Pillar | Inputs and weights inside the pillar (`OPS.WPS_INPUT_WEIGHTS`) |
|---|---|
| VC - Value Creation | WIN 50 %, EFF 50 % |
| OE - Operational Excellence | SCHED 50 %, EFF 50 % |
| PD - People Development | Manager and below: BILL 30 %, UTIL 20 %, AREUSE 20 %, LEARN 15 %, ACREATE 15 %<br>Senior Manager and above: BILL 20 %, UTIL 30 %, AREUSE 20 %, LEARN 15 %, ACREATE 15 % |
| TM - Team (Manager+ only) | TEAM 100 %; only when 3 or more team members (as defined for TEAM) are scored in the quarter |

Pillar score = weighted average of its input scores (0-100).
`OPS.WPS_INPUT_WEIGHTS` is keyed by LEVEL x PILLAR x INPUT, because the PD weights differ by level.
Input weights for each level x pillar must sum to 100 (gate).
Note: EFF feeds both VC and OE by design; the page discloses this and shows the VC-OE correlation.

### 2.5 Preset weights by level (`OPS.WPS_WEIGHTS`)

| Level | VC | OE | PD | TM |
|---|---|---|---|---|
| Analyst | 15 | 45 | 40 | 0 |
| Consultant | 25 | 40 | 35 | 0 |
| Manager | 30 | 30 | 15 | 25 |
| Senior Manager | 40 | 20 | 10 | 30 |
| Principal | 50 | 10 | 10 | 30 |

`WPS = SUM(weight * pillar) / SUM(weight of applicable pillars)` - when TM is not applicable its
weight is redistributed pro-rata. Weights in each row must sum to 100 (gate).

### 2.6 Reference SQL shape (illustrative)

```sql
WITH raw AS (...person x quarter inputs...),
z AS (
  SELECT r.*,
         LEAST(100, GREATEST(0, 50 + 15 * LEAST(3, GREATEST(-3,
           (EFF - AVG(EFF) OVER (PARTITION BY LEVEL, FISCAL_YEAR))
           / NULLIF(STDDEV(EFF) OVER (PARTITION BY LEVEL, FISCAL_YEAR), 0))))) AS EFF_S
         -- same for WIN, SCHED, BILL, UTIL, LEARN, ACREATE, AREUSE
  FROM raw r)
SELECT ..., 0.5*WIN_S + 0.5*EFF_S AS VC, 0.5*SCHED_S + 0.5*EFF_S AS OE,
       w.BILL*BILL_S + w.UTIL*UTIL_S + w.AREUSE*AREUSE_S + w.LEARN*LEARN_S + w.ACREATE*ACREATE_S AS PD
FROM z JOIN pd_weights w USING (LEVEL);   -- pivot of OPS.WPS_INPUT_WEIGHTS for PILLAR = 'PD'
```

---

## 3. Analysis methods (Q2-Q6)

Common rules:
- All tests are **within level** (avoids Simpson's paradox from level mix).
- Controls: work type and group (stratified, then hours-weighted across strata).
- Uncertainty: person-cluster bootstrap, 90 % CI (5th/95th), seed 20261001; 1000 resamples firm-level,
  400 per level cell.
- `SIGNIFICANT = CI excludes 0`. Wording: "associated with", never "causes".
- No self-measurement: Q5/Q6 test against `WPS_EX_LEARN` (WPS recomputed without LEARN); Q3/Q4 test
  against WPS and against the specific pillar or input the exposure is expected to move (see 4.4).

### 3.1 Small cells

A cell = level x scope (firm or group) x fiscal year (x vendor or curriculum for Q4/Q6).
- Minimum per cell: 15 distinct people AND 30 person-quarters.
- Group-scope cells pool FY2024-26 and are labelled "pooled FY24-26" (Principal per group ~70 person-quarters).
- The generator guarantees a minimum curriculum take-up per level (about 20 people per curriculum x level
  per year where the curriculum is relevant; see 4.2), so Q6 cells are populated by design.
- Cells still below the minimum show "insufficient data (n people)" with the firm-level result beside them.
- Headcount pyramid is NOT changed to create data (must stay aligned with real PI people).

| Q | Exposure | Statistic | Output table |
|---|---|---|---|
| Q2 | Level | Median, P25, P75 of WPS and each pillar; billability vs utilization median | `REASONING.WPS_BY_LEVEL` |
| Q3 | `LN(1 + tokens per delivery hour)` in the quarter | Spearman rho with CI; WPS by exposure quintile | `REASONING.TOKEN_WPS_TEST` (R15) |
| Q4 | Same, per product (Claude Code, Codex, Cortex) and for Cortex per model family | Spearman rho with CI per product x level, against WPS, OE and WIN | `REASONING.VENDOR_WPS_TEST` (R16) |
| Q5 | Training hours in the 2 prior quarters | Spearman rho with CI; WPS by quintile | `REASONING.TRAINING_WPS_TEST` (R17) |
| Q6 | Curriculum hours in the 2 prior quarters | Spearman rho with CI per curriculum x level, plus rho against the curriculum's target pillar | `REASONING.CURRICULUM_WPS_TEST` (R18) |

R13 (AI-active uplift) and R14 (learning payback) are kept but re-based on WPS.

---

## 4. Simulated data requirements

### 4.1 AI telemetry (extend `ACOCO_SIM.TELEMETRY.*_USAGE`)

| Column | Values |
|---|---|
| PRODUCT | ANTHROPIC = Claude Code; OPENAI = Codex; CORTEX = Cortex Code / AISQL (Snowflake) |
| MODEL | Kept in sync across vendors (table below) |
| INPUT_TOKENS / OUTPUT_TOKENS | split of TOKENS, output share 15-35 % |
| USE_CASE | CODE, DOCUMENT, ANALYSIS, BID |
| COST_USD | priced per vendor x model (input/output rates in `OPS.AI_MODEL_PRICE`) |

| Model family | ANTHROPIC (Claude Code) | OPENAI (Codex) | CORTEX (Snowflake) |
|---|---|---|---|
| Claude Sonnet 4.5 | claude-sonnet-4-5 | - | claude-sonnet-4-5 |
| Claude Haiku 4.5 | claude-haiku-4-5 | - | claude-haiku-4-5 |
| GPT-5 | - | gpt-5 | openai-gpt-5 |
| GPT-4.1 | - | gpt-4.1 | openai-gpt-4.1 |
| Open models | - | - | llama3.1-70b, mistral-large2 |

Cortex model names confirmed 2026-11-05 against `SHOW MODELS IN SNOWFLAKE.MODELS` (all six available).
Cortex model mix: ~45 % Claude family, ~45 % OpenAI family, ~10 % open models.

### 4.2 Learning taxonomy (extend LMS)

| Curriculum | Target pillar | AI curriculum |
|---|---|---|
| AGENTIC_AI_BUILD | OE | Y |
| PROMPT_COPILOT | OE | Y |
| CORTEX_DATA | OE | Y |
| SAP_FUNCTIONAL | PD (billability) | N |
| PROJECT_MGMT | OE (schedule) | N |
| COMMERCIAL_BID | VC (win) | N |
| LEADERSHIP | TM | N |
| INDUSTRY | VC | N |

Each learning item gains `PROVIDER`, `MODALITY` (eLearning / classroom / certification) and completions gain
`ASSESSMENT_SCORE`. Total learning share stays at the CP-02 target (~10 % of available hours).

Minimum take-up per level (generator guarantee, about 20 people per year per cell): AI curricula at every
level; SAP_FUNCTIONAL Analyst/Consultant; PROJECT_MGMT Consultant/Manager; COMMERCIAL_BID and LEADERSHIP
Manager and above; INDUSTRY all levels. Required curricula per level (2.3) drive most of this take-up.

### 4.3 Other new data
- Line managers for simulated people: Manager+ in the same group, span 4-8.
- `ACTUAL_END` on closed projects and work packages.
- No new timesheet category: asset-building hours are recorded on `ASSET_CONTRIBUTION.HOURS` only (2.3).

### 4.3a Assets (redesigned)

Today: 167 assets, 702 usages, 134 harvesters (mostly Senior Manager / Principal, 1 Analyst) - too sparse
for a within-level input. New simulation:

| Table | Content | Volume |
|---|---|---|
| ASSET | as today + `ASSET_TYPE` incl. AI_AGENT, `STATUS` (draft/published/retired) | ~1,000-1,200 (FY22-26) |
| ASSET_CONTRIBUTION (new) | ASSET_ID, PERSON_ID, ROLE (AUTHOR / CONTRIBUTOR / REVIEWER), HOURS, CONTRIBUTION_DATE | ~4,000-5,000 |
| ASSET_HARVEST | kept (lead author = HARVESTED_BY_USER_ID) | = assets |
| ASSET_USAGE | + USED_BY_USER_ID, RATING (1-5) | ~8,000-10,000 |

Participation: Analysts mostly Contributors, Consultants/Managers Contributors and Authors, Senior Manager /
Principal mostly Authors and Reviewers; roughly 35-45 % of each level contributes in a year.
AI_AGENT assets are authored mostly by heavy Cortex users.

### 4.4 Seeded true effects (`OPS.SIM_TRUTH_EFFECTS`)

| Product | Moves | Analyst | Consultant | Manager | Senior Manager | Principal |
|---|---|---|---|---|---|---|
| Cortex (Claude or OpenAI model, same effect) | OE (EFF and SCHED), dose-response with plateau | strong | strong | moderate | moderate | moderate |
| Claude Code (Anthropic) | WIN, via bid-team usage share | small* | yes | yes | null | null |
| Codex (OpenAI) | WIN, via bid-team usage share | null | null | null | yes | yes |

*Analysts rarely bid; their WIN is mostly shrunk to the level rate, so this cell is expected to be weak.
Direct Claude Code / Codex usage has no effect on OE (OE lever is Cortex). Cortex open models: small OE effect.

| Other effect | Shape |
|---|---|
| Asset reuse -> EFF, SCHED | positive, all levels |
| Curriculum -> pillar | Commercial -> WIN, Project Mgmt -> SCHED, AI curricula -> EFF, SAP Functional -> BILL, Leadership -> reports' WPS; Industry null |
| Honesty | Two AI-enabled projects under-perform (PRD PMD-7) |

Gates check the analysis recovers each true effect's sign, the CI covers the true value in at least 80 % of
non-null cells, and null cells are not significant.

---

## 5. P6 page specification

| Section | Tile | Data | Acceptance |
|---|---|---|---|
| A | WPS explainer: pillars, inputs, level weights | `OPS.WPS_WEIGHTS` | Weights match table 2.5 |
| B | WPS and pillars by level; billability vs utilization by level | `WPS_BY_LEVEL` | 5 levels shown, medians near 50 |
| C | Tokens vs WPS: rho with CI per level + quintile curve | R15 | Significant cells coloured |
| D | Product x level heatmap (vs OE and vs WIN) + Cortex by model family | R16 | 3 x 5 x 2 cells; null cells (Codex at Manager and below, Claude Code at Senior Manager+ on WIN) not significant |
| E | Training hours vs WPS (excluding learning input) per level; learning attainment vs target by level | R17 | as C |
| E2 | Asset creation and reuse by level; reuse vs OE | WPS mart | all levels populated |
| F | Curriculum x level heatmap + target pillar | R18 | Industry row not significant |
| G | Retained: AI cost by vendor/model, AI-skilled but inactive, delivery model | existing | unchanged behaviour |

Every tile keeps "Ask Cortex", a glossary key and significance colouring (D-09-8). Filters: group and fiscal year.

---

## 6. Non-functional

- Generator remains deterministic (`gen/run.py --check`); total runtime increase under 25 %.
- Reasoning build under 5 minutes.
- `registry.sql` and `tools/demo_queries.sql` stay byte-identical.
- Agent never states causation; regression set covers Q2-Q6.

## 7. Out of scope

Live weight slider, real (non-simulated) LMS integration, per-prompt telemetry.
