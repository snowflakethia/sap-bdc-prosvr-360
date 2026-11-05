# P6 Productivity Redesign - Impact Analysis

Version 0.3 (draft for checkpoint CP-P6a) - 2026-11-05
Companion to `docs/spec_p6_productivity.md`.
Legend: ADD = new object, CHG = changed, KEEP = unchanged but must be re-verified, RET = retired.

## 1. Generator (`gen/acoco_gen.py`, `gen/run.py`)

| Item | Action | Note |
|---|---|---|
| `Staffing.person_prod` (flat +0.11 / +0.02, line ~423) | CHG | Replace with Cortex -> OE dose-response by level (model-agnostic within Cortex) |
| Win logit in `run_demand` (~565) | CHG | Add bid-team usage share terms: Claude Code (Manager and below), Codex (Senior Manager+), plus Commercial training |
| `_usage_bands`, `build_telemetry_and_agt` (~410, ~1059) | CHG | Add PRODUCT, MODEL (synced across vendors), INPUT/OUTPUT_TOKENS, USE_CASE, per-model cost |
| `Assets` class (~691) | CHG | ~1,000-1,200 assets, contributors by role, usage by person with rating; contribution HOURS recorded (not budgeted, counted in UTIL) |
| Learning targets by level, required curricula, minimum take-up per curriculum x level | ADD | Feeds LEARN input and fills Q6 cells |
| `build_learning_catalogue`, `schedule_learning` (~289, ~761) | CHG | 8 curricula, provider, modality, assessment score |
| `AI_LEARN_BOOST` (+7 %, 26 wks) | CHG | Per-curriculum effect on its target input |
| Managers for simulated people | ADD | Feeds `MANAGER_ID` (today NULL, `workforce_job.sql:47`) |
| `ACTUAL_END` on closed projects / WPs | ADD | |
| `OPS.SIM_TRUTH_EFFECTS` | ADD | Ground truth for gates |
| Two under-performing AI-enabled projects | ADD | PRD PMD-7 honesty rule (not present today) |

**Risk:** every calibrated anchor can move. Must re-measure CP-02 targets (Bid ~15 %, Learning ~10 %,
bench < 3 %), A6/A7 win-rate (39.1 %), A10 (AI uplift +0.119), A11 (learning payback), A12 (skilled-inactive 34),
and keep story projects P-0679 / P-0460 behaving as narrated. Record each move in `plan/deviations.md`.

## 2. Control and L1

| Object | Action |
|---|---|
| `OPS.LEVEL`, `OPS.GEN_PARAMS_TIME_TARGET` | KEEP - targets reused (BILL = DELIVERY, UTIL = DELIVERY + BID, LEARN = LEARNING) |
| `OPS.LEVEL_REQUIRED_CURRICULUM` | ADD |
| `ACOCO_SIM.ASSETS.ASSET_CONTRIBUTION` + L1 view | ADD |
| `ACOCO_SIM.ASSETS.ASSET_USAGE`, `sql/02_l1/assets/*` | CHG - USED_BY_USER_ID, RATING |
| `OPS.WPS_WEIGHTS`, `OPS.WPS_INPUT_WEIGHTS` (keyed LEVEL x PILLAR x INPUT), `OPS.AI_MODEL_PRICE` | ADD |
| `ai_telemetry/ai_usage_event.sql` | CHG - new columns |
| `talent/learning_item.sql`, `learning_completion.sql` | CHG - taxonomy, assessment |
| `workforce/workforce_job.sql` | CHG - sim MANAGER_ID (generator now writes `managerId`; L1 still casts NULL) |
| `sales/opportunity_team.sql` | KEEP - new TEAM_ROLE value SUPPORT |
| `12_mart_pipeline_presales.sql` skill fit (`covered`, `held`) | CHG - exclude SUPPORT members so SKILL_FIT stays on the core team (A7) |
| `projects/*` | CHG - ACTUAL_END |
| `tools/l1_map.yml`, `sql/02_l1/_all.sql` | CHG - regenerate |

## 3. L2

| Object | Action | Note |
|---|---|---|
| `WORKFORCE_PERFORMANCE.DT_PERSON_QUARTER_WPS` | ADD | Inputs, pillars, WPS |
| `AI_ADOPTION.DT_AI_TOKENS_PERSON_QUARTER` | ADD | Tokens by vendor/model |
| `WORKFORCE_PERFORMANCE.DT_LEARNING_PERSON_QUARTER` | ADD | Hours by curriculum |
| `REL_PERSON_CONTRIBUTES_ASSET`, `REL_PERSON_REUSES_ASSET` | ADD | Ontology edges for asset creation / reuse |
| P2 missed-reuse story (`pj_reuse`, CSS_ASSET_LIBRARY) | KEEP | Asset volume grows ~7x; re-verify story project P-0679 matches and Cortex Search index refresh |
| `ENT_AI_MODEL`, `ENT_LEARNING_CATEGORY`, `REL_PERSON_REPORTS_TO` | ADD | + ONT_ENTITY / ONT_RELATIONSHIP / ONT_METRIC via `gen_ontology.py` |
| `DT_AI_PRODUCTIVITY` | CHG | Add WPS; keep PRODUCTIVITY_INDEX as drill-down |
| `DT_LEARNING_PAYBACK` | CHG | Measure on WPS, per curriculum |
| `DT_PERSON_MONTH_SCORECARD`, `VW_SCORECARD_FY`, `VW_PORTFOLIO_FY`, `VW_PERSON_LAST_CLOSED_MONTH` | CHG | Split BILLABILITY vs UTILIZATION (today both = DELIVERY/AVAILABLE) |
| `DT_AI_COST_MONTH` | CHG | Model dimension |
| Reasoning R13/R14 (`tools/build_reasoning.py`) | CHG | Re-based on WPS |
| R15-R18 + `WPS_BY_LEVEL` | ADD | Q2-Q6 |
| `post/41_serving_reasoning.sql`, `post/42_serving_app.sql` | CHG/ADD | Serving views for new tables |
| Attrition features (`40_reasoning.sql`) | KEEP | Uses PRODUCTIVITY_INDEX, LEARNING_SHARE - re-verify after generator change |
| Cortex Search services | KEEP | Not affected |

## 4. Semantic views and agent

| Object | Action |
|---|---|
| `SV_WORKFORCE_PRODUCTIVITY` | ADD (WPS, pillars, R15-R18) |
| `SV_AI_ADOPTION` | CHG (model, tokens metric, re-based R13/R14) |
| `SV_WORKFORCE_PERFORMANCE` | CHG (`delivery_pct` -> `billability_pct`, add `utilization_pct`) |
| `SV_PIPELINE_PRESALES`, `SV_PROJECT_DELIVERY` | KEEP (values move) |
| `agent/acoco_advisor.agent.yaml`, `tools/gen_agent.py` | CHG - routing for Q2-Q6, regression questions, "associated" rule |

## 5. App pages

| Page | Action | What changes |
|---|---|---|
| P6 AI Productivity | CHG (rebuild) | Sections A-G per spec |
| P0 Overview | CHG | `ov_ai_uplift` re-based; scorecard shows billability and utilization |
| C1 Business context | KEEP | Firm win-rate / delivery values move |
| C2 Metrics glossary | KEEP | Picks up new ONT_METRIC rows automatically |
| P2 Project health | CHG | Label PRODUCTIVITY_INDEX as "Earned-hour efficiency" |
| P3 Time mix | CHG | Billability vs utilization (categories unchanged) |
| P4 People | CHG | Curriculum list uses new taxonomy; person WPS + team view |
| P5 Pipeline | KEEP | Win-rate values move (Commercial training term) |
| P7 Reasoning | KEEP | Re-verify bench / attrition |
| P10 Advisor | CHG | Agent update |
| C4 / P8 / P9 | KEEP | Ontology graph, lineage, trust list new objects - verify |

App plumbing: `server/src/registry.sql` + `tools/demo_queries.sql` (byte-identical, `lint_app.py`),
`registry.ts`, `client/src/lib/glossary.ts`, `tools/presenter_card.py`, `docs/PRESENTER_CARD.md`,
`tools/dry_run.py`, `tools/gate.py`, `tools/build_playbook.py`.

## 6. Validation and docs

| Item | Action |
|---|---|
| `tools/validate.py` A10-A12, Q4/Q5 | CHG - re-based on WPS |
| Truth-recovery gates for R15-R18 | ADD |
| Stale A11 note (validate.py:250) | RET |
| `docs/acoco_proserve_prd.md` | CHG - archive v2.6 to `docs/archive/`, then v2.7: EPIC-PD, PMD-7/12, 6.2 (fix mismatch), 6.3, 7.2, 8.3, R13-R18 |
| `plan/checkpoints.md`, `measured_anchors.md`, `deviations.md` | CHG |
| `docs/PRESENTER_CARD.md`, playbook | CHG |

## 7. Volumes and performance

- Telemetry: same rows (~572k), 4 extra columns.
- Learning completions: ~286k -> ~300k (8 curricula, level targets keep share ~10 %).
- Assets: 167 -> ~1,100; contributions ~4.5k (new); usages 702 -> ~9k.
- New marts: person x quarter ~3.5k people x 20 quarters = ~50-70k rows each.
- Reasoning: ~4x more bootstrap cells; vectorise in numpy to stay under 5 min.

## 8. Key risks and mitigations

| Risk | Mitigation |
|---|---|
| Anchors / story projects drift | Re-measure; tune constants; deviations logged |
| WPS shared EFF inflates VC-OE correlation | Disclosed on page; VC-OE rho reported |
| Team pillar circularity | TM uses reports' WPS excluding their own TM pillar |
| Win data sparse for juniors | Beta shrinkage toward level rate (k = 3); Analyst Claude Code -> WIN expected weak |
| Training / assets measured against a score that contains them | Q5/Q6 use WPS_EX_LEARN; asset tests use pillar-level outcomes |
| Small cells (group x Principal ~6 people per FY) | Pool FY24-26 for group scope; minimum curriculum take-up; 15 people / 30 PQ rule |
| Vendor story reads as rigged | Null cells by design (Codex at Manager and below, Claude Code at Senior Manager+ on WIN) shown as not significant |
| Overclaiming causality | Wording gate in agent regression and glossary |
| Breaking downstream pages | Old views kept side by side until sign-off; `dry_run.py` over all routes |
