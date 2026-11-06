"""Generate and deploy the six ACoCo Semantic Views (PRD 7.2 ontology rules) from one spec.

  .venv/bin/python tools/gen_semantic.py --render          write sql/03_l2/semantic/<sv>.yaml
  .venv/bin/python tools/gen_semantic.py --deploy [SV...]  render + deploy via `cortex agent-studio sv-deploy`

Rules enforced by construction:
  1. dimension logical tables are the shared ONTOLOGY.ENT_* (+ CORE.DT_FISCAL_MONTH) with the same logical names
     and primary keys in every view; facts are the owning mart's DT_* / REL_* only;
  2. every relationship is fact -> entity (many-to-one) or a registered entity -> entity edge, and no fact has two
     join paths to the same entity (role-playing copies get their own logical name, e.g. source_project);
  3. entity attributes are defined once here (ENTITY_DIMS) and reused; metrics are defined once (METRICS).
Column data types are read from INFORMATION_SCHEMA so the YAML always matches the deployed tables.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402

OUT = ROOT / "sql" / "03_l2" / "semantic"
CONNECTION = sf.CONNECTION

# ---------------------------------------------------------------------------------------------- shared entities
# logical name -> (schema.table, primary key, dimensions {logical: (column, description, synonyms)}, owner)
ENTITIES = {
    "person": ("ONTOLOGY.ENT_PERSON", "PERSON_ID", {
        "person_id": ("PERSON_ID", "People Intelligence userId", ["employee id", "user id"]),
        "person_name": ("DISPLAY_NAME", "Person's display name", ["name", "employee", "consultant"]),
        "person_level": ("LEVEL", "Career level at the as-of date (Analyst .. Principal)", ["level", "grade", "rank"]),
        "bill_code": ("BILL_CODE", "Bill code 30-79 within the level band (higher = more senior, more bid time)", ["billing code"]),
        "is_active": ("IS_ACTIVE_AS_OF", "Employed on the as-of date (1 Oct 2026)", ["active", "current employee"]),
        "is_managing_director": ("IS_MANAGING_DIRECTOR", "Holds the Managing Director role for a group", ["MD"]),
        "person_source": ("SOURCE_SYSTEM", "BDC_CLD = real People Intelligence person; SIMULATED = simulated pool", []),
    }, "SAP People Intelligence (Core Workforce)"),
    "md_group": ("ONTOLOGY.ENT_MD_GROUP", "MD_GROUP_ID", {
        "md_group_id": ("MD_GROUP_ID", "MD group code (FS, CMT, HPS, PRD, RES, XAI)", ["group code"]),
        "md_group": ("MD_GROUP_NAME", "MD group name, e.g. Financial Services", ["group", "industry group", "practice"]),
        "managing_director": ("MANAGING_DIRECTOR_NAME", "Managing Director of the group", ["MD name", "partner"]),
    }, "S/4HANA cost centre hierarchy"),
    "level": ("ONTOLOGY.ENT_LEVEL", "LEVEL", {
        "level": ("LEVEL", "Career level", ["grade"]),
        "level_sort": ("LEVEL_SORT", "1 = Analyst .. 5 = Principal", []),
        "activity_type": ("ACTIVITY_TYPE", "S/4 activity type that prices the level (ML-100 .. ML-105)", []),
    }, "People Intelligence payGrade + S/4 activity type"),
    "fiscal_month": ("CORE.DT_FISCAL_MONTH", "MONTH_START", {
        "fiscal_year": ("FISCAL_YEAR", "ACoCo fiscal year (Oct-Sep, V9); FY26 = Oct 2025 - Sep 2026", ["FY", "year"]),
        "fiscal_period": ("FISCAL_PERIOD", "Fiscal period 1-12 (1 = October)", ["period"]),
        "fiscal_quarter": ("FISCAL_QUARTER", "Fiscal quarter 1-4 (1 = Oct-Dec)", ["quarter"]),
        "month_label": ("MONTH_LABEL", "Calendar month label, e.g. SEP 2026", ["month"]),
    }, "S/4HANA fiscal year variant V9"),
    "project": ("ONTOLOGY.ENT_PROJECT", "PROJECT_ID", {
        "project_id": ("PROJECT_ID", "Customer project (S/4 project / WBS)", ["project", "engagement"]),
        "size_class": ("SIZE_CLASS", "Project size class (XX-Small .. Large)", ["size"]),
        "work_type": ("WORK_TYPE", "Type of work (Data Migration, AI Engineering, ...)", ["service line"]),
        "contract_type": ("CONTRACT_TYPE", "FIXED_PRICE or TIME_AND_MATERIALS", ["pricing"]),
        "delivery_model": ("DELIVERY_MODEL", "HUMAN, HUMAN_AGENT (people + agents) or AGENT_LED", ["AI delivery model"]),
        "project_status": ("STATUS_AS_OF", "ACTIVE / CLOSED / NOT_STARTED at the as-of date", ["status"]),
        "is_story_project": ("IS_STORY_PROJECT", "The seeded at-risk FS fixed-price project", []),
    }, "S/4HANA Project"),
    "customer": ("ONTOLOGY.ENT_CUSTOMER", "CUSTOMER_ID", {
        "customer_id": ("CUSTOMER_ID", "Customer account id", []),
        "customer_name": ("CUSTOMER_NAME", "Customer account name", ["client", "account"]),
    }, "CRM account (S/4 customer keys masked)"),
    "work_package": ("ONTOLOGY.ENT_WORK_PACKAGE", "WBS_ID", {
        "wbs_id": ("WBS_ID", "Work package (WBS element)", ["work package", "WBS"]),
        "is_critical_path": ("IS_CRITICAL_PATH", "On the project's critical path", []),
    }, "S/4HANA Project WBS element"),
    "opportunity": ("ONTOLOGY.ENT_OPPORTUNITY", "OPPORTUNITY_ID", {
        "opportunity_id": ("OPPORTUNITY_ID", "CRM opportunity (bid)", ["bid", "deal", "pursuit"]),
        "opportunity_size": ("SIZE_CLASS", "Opportunity size class", []),
        "opportunity_work_type": ("WORK_TYPE", "Type of work bid for", []),
        "opportunity_status": ("STATUS_AS_OF", "OPEN / WON / LOST at the as-of date", ["outcome", "stage"]),
        "required_ai_skill_level": ("REQUIRED_AI_SKILL_LEVEL", "AI-skill level (1-5) the bid requires", []),
    }, "CRM (non-SAP)"),
    "skill": ("ONTOLOGY.ENT_SKILL", "SKILL_ID", {
        "skill_id": ("SKILL_ID", "Skill code", []),
        "skill_name": ("SKILL_NAME", "Skill name", ["skill", "capability"]),
        "skill_family": ("SKILL_FAMILY", "AGENTIC_AI, TECHNICAL or INDUSTRY", ["skill category"]),
    }, "SAP People Intelligence Skills"),
    "learning_item": ("ONTOLOGY.ENT_LEARNING_ITEM", "LEARNING_ITEM_ID", {
        "learning_item_id": ("LEARNING_ITEM_ID", "Learning item", ["course"]),
        "learning_item_title": ("LEARNING_ITEM_TITLE", "Learning item title", ["course name"]),
        "curriculum": ("CURRICULUM", "Curriculum: AGENTIC_AI_BUILD, PROMPT_COPILOT, CORTEX_DATA (AI), SAP_FUNCTIONAL, PROJECT_MGMT, "
                                     "COMMERCIAL_BID, LEADERSHIP, INDUSTRY", ["learning path"]),
    }, "SAP People Intelligence Learning"),
    "asset": ("ONTOLOGY.ENT_ASSET", "ASSET_ID", {
        "asset_id": ("ASSET_ID", "Reusable delivery asset", []),
        "asset_title": ("ASSET_TITLE", "Asset title", ["accelerator", "template"]),
        "asset_type": ("ASSET_TYPE", "Accelerator, code template, test pack ...", []),
        "asset_work_type": ("WORK_TYPE", "Work type the asset serves", []),
    }, "Asset library (non-SAP)"),
    "ai_tool": ("ONTOLOGY.ENT_AI_TOOL", "AI_TOOL_ID", {
        "ai_tool_id": ("AI_TOOL_ID", "AI assistant (OPENAI, ANTHROPIC, CORTEX) or S/4 agent activity type (AGT_*)", []),
        "ai_tool_name": ("AI_TOOL_NAME", "AI tool / agent name", ["AI tool", "assistant", "agent"]),
        "tool_kind": ("TOOL_KIND", "ASSISTANT (people use it) or AGENT (charged to projects)", []),
    }, "AI telemetry + S/4 AGT_* activity types"),
    "time_category": ("ONTOLOGY.ENT_TIME_CATEGORY", "TIME_CATEGORY", {
        "time_category": ("TIME_CATEGORY", "DELIVERY, BID, LEARNING, ADMIN or BENCH", ["use of time", "category"]),
        "time_category_objective": ("OBJECTIVE", "What the category is judged on", []),
    }, "Timesheet attendance type"),
    # P6 (spec 4.1, 4.2)
    "ai_model": ("ONTOLOGY.ENT_AI_MODEL", "AI_MODEL_ID", {
        "ai_product": ("PRODUCT", "AI product: CHATGPT / CLAUDE_CHAT (chat, 2023 - Apr 2025), CODEX / CLAUDE_CODE (from May 2025), "
                                 "CORTEX (from Nov 2025)", ["product", "Claude Code", "Codex", "Cortex"]),
        "ai_product_name": ("PRODUCT_NAME", "AI product name", []),
        "ai_model_name": ("MODEL", "Model, e.g. claude-sonnet-4-5, gpt-5, openai-gpt-5 (via Cortex)", ["model", "LLM"]),
        "model_family": ("MODEL_FAMILY", "CLAUDE, GPT or OPEN (open models via Cortex)", ["model vendor"]),
    }, "AI telemetry + model price list"),
    "learning_category": ("ONTOLOGY.ENT_LEARNING_CATEGORY", "CURRICULUM", {
        "learning_category": ("CURRICULUM", "Curriculum code (8 curricula)", ["curriculum", "training category"]),
        "learning_category_name": ("CURRICULUM_NAME", "Curriculum name", ["training", "course category"]),
        "is_ai_curriculum": ("IS_AI_CURRICULUM", "One of the three AI curricula", ["AI training"]),
        "target_pillar": ("TARGET_PILLAR", "WPS pillar the curriculum is meant to move (VC, OE, PD, TM)", []),
        "target_input": ("TARGET_INPUT", "WPS input the curriculum is meant to move (EFF, SCHED, WIN, BILL, TEAM)", []),
    }, "SAP People Intelligence Learning"),
}
# role-playing copies (logical name -> entity)
ROLES = {"source_project": "project"}

# ---------------------------------------------------------------------------------------------- metrics (once)
METRICS = {
    # name: (expression over fact names, description, synonyms, pillar)
    "billability_pct": ("100 * SUM(<f>.delivery_hours) / NULLIF(SUM(<f>.available_hours), 0)",
                        "Billability: client-billable (Delivery) hours as % of available hours (Employee Availability)",
                        ["billability", "delivery share", "billable %"], "Operational Excellence"),
    "utilization_pct": ("100 * SUM(<f>.utilized_hours) / NULLIF(SUM(<f>.available_hours), 0)",
                        "Utilization: Delivery + Bid + recorded asset-contribution hours as % of available hours (asset hours "
                        "are recorded, not budgeted, so it can exceed 100)", ["utilisation", "utilization rate"], "Operational Excellence"),
    "bid_pct": ("100 * SUM(<f>.bid_hours) / NULLIF(SUM(<f>.available_hours), 0)", "Bid (pre-sales) hours as % of available hours", ["presales share"], "Value Creation"),
    "learning_pct": ("100 * SUM(<f>.learning_hours) / NULLIF(SUM(<f>.available_hours), 0)", "Learning hours as % of available hours", [], "People Development"),
    "admin_pct": ("100 * SUM(<f>.admin_hours) / NULLIF(SUM(<f>.available_hours), 0)", "Admin hours as % of available hours (ceiling 5 %)", [], "Operational Excellence"),
    "bench_pct": ("100 * SUM(<f>.bench_hours) / NULLIF(SUM(<f>.available_hours), 0)", "Bench = available minus booked hours, % of available (target ~2 %, < 3 %)", ["idle time", "unutilised"], "Operational Excellence"),
    "available_hours_total": ("SUM(<f>.available_hours)", "Available hours (planned work hours minus absence)", ["capacity"], "Operational Excellence"),
    "bench_cost": ("SUM(<f>.bench_cost)", "Bench hours x level cost rate (USD)", [], "Operational Excellence"),
    "productivity_index": ("SUM(<f>.earned_hours) / NULLIF(SUM(<f>.delivery_hours), 0)", "Earned-hour efficiency: earned hours / actual delivery hours (> 1 = faster than plan); one input of the WPS", ["earned-hour efficiency"], "People Development"),
    "category_share_pct": ("100 * SUM(<f>.hours) / NULLIF(SUM(<f>.available_hours), 0)", "Hours of the time category as % of available hours", ["time mix"], "Operational Excellence"),
    "revenue": ("SUM(<f>.revenue)", "Recognised revenue (USD, S/4 journal GL 0041000000)", ["sales", "fees"], "Value Creation"),
    "total_cost": ("SUM(<f>.total_cost)", "People + AI-agent + 35 % overhead cost (USD)", ["cost"], "Value Creation"),
    "margin": ("SUM(<f>.margin)", "Revenue minus total cost (USD)", ["profit"], "Value Creation"),
    "margin_pct": ("100 * SUM(<f>.margin) / NULLIF(SUM(<f>.revenue), 0)", "Margin as % of revenue", ["profit margin"], "Value Creation"),
    "agent_cost": ("SUM(<f>.agent_cost)", "AI-agent cost charged to projects (S/4 AGT_* allocations, USD)", ["AI cost"], "Value Creation"),
    "agent_hours": ("SUM(<f>.agent_hours)", "AI-agent hours charged to projects", [], "Value Creation"),
    "cpi": ("SUM(<f>.earned_value_td) / NULLIF(SUM(<f>.actual_cost_td), 0)", "Cost performance index = earned value / actual cost (< 1 = over budget)", ["cost performance"], "Operational Excellence"),
    "spi": ("SUM(<f>.earned_value_td) / NULLIF(SUM(<f>.planned_value_td), 0)", "Schedule performance index = earned value / planned value (< 1 = late)", ["schedule performance"], "Operational Excellence"),
    "forecast_margin_pct": ("100 * (SUM(<f>.contract_value) - SUM(<f>.eac) - SUM(<f>.ld_exposure)) / NULLIF(SUM(<f>.contract_value), 0)",
                            "(Contract - EAC - LD exposure) / contract", ["forecast profitability"], "Operational Excellence"),
    "ld_exposure": ("SUM(<f>.ld_exposure)", "Liquidated damages exposure on late fixed-price projects (USD)", ["penalties"], "Operational Excellence"),
    "eac": ("SUM(<f>.eac)", "Estimate at completion = sold cost / CPI (USD)", [], "Operational Excellence"),
    "project_count": ("COUNT(DISTINCT <f>.project_key)", "Number of projects", ["projects"], "Operational Excellence"),
    "asset_reuse_rate_pct": ("100 * AVG(IFF(<f>.reused_asset, 1, 0))", "Projects with >= 1 recorded asset use / projects", ["reuse rate"], "Value Creation"),
    "hours_saved_estimated": ("SUM(<f>.hours_saved_estimated)", "ESTIMATED hours saved by asset reuse (catalogued saving per use)", [], "Value Creation"),
    "asset_uses": ("SUM(<f>.uses)", "Recorded asset uses", [], "Value Creation"),
    "team_delivery_hours": ("SUM(<f>.delivery_hours)", "Delivery hours booked by the person on the project", [], "Operational Excellence"),
    "win_rate_pct": ("100 * SUM(IFF(<f>.is_won, 1, 0)) / NULLIF(SUM(IFF(<f>.is_closed, 1, 0)), 0)", "Won / (won + lost) bids", ["hit rate", "conversion"], "Value Creation"),
    "pursuit_cost": ("SUM(<f>.pursuit_cost)", "Pre-sales people cost booked to the bid's internal order (USD)", ["bid cost", "presales cost"], "Value Creation"),
    "pursuit_cost_per_won_usd": ("SUM(IFF(<f>.is_closed, <f>.pursuit_cost, 0)) / NULLIF(SUM(IFF(<f>.is_won, <f>.estimated_value, 0)), 0)",
                                 "Pursuit cost of closed bids per USD won", [], "Value Creation"),
    "avg_skill_fit": ("AVG(<f>.skill_fit)", "Share of required skills held at >= 3 by the pursuit team", ["team fit"], "Value Creation"),
    "won_value": ("SUM(IFF(<f>.is_won, <f>.estimated_value, 0))", "Value of won bids (USD)", ["bookings"], "Value Creation"),
    "open_pipeline_value": ("SUM(IFF(<f>.is_open, <f>.estimated_value, 0))", "Value of open bids at the as-of date (USD)", ["pipeline"], "Value Creation"),
    "bid_count": ("COUNT(<f>.opportunity_key)", "Number of bids", ["opportunities"], "Value Creation"),
    "pursuit_team_bid_hours": ("SUM(<f>.bid_hours)", "Bid hours booked by the team member", [], "Value Creation"),
    "headcount_closing": ("SUM(<f>.closing_headcount)", "Headcount at month end (sum over a single month only)", ["headcount", "FTE"], "People Development"),
    "voluntary_leavers": ("SUM(<f>.voluntary_leavers)", "Voluntary leavers", ["attrition count", "quits"], "People Development"),
    "hires": ("SUM(<f>.hires)", "Hires", [], "People Development"),
    "roll_off_people": ("COUNT(<f>.roll_off_person_key)", "People whose last assignment ends in the 90 days after the as-of date", ["roll-offs"], "People Development"),
    "roll_off_below_ai_level": ("SUM(IFF(<f>.below_pipeline_ai_level, 1, 0))", "Roll-offs below the pipeline's required AI-skill level", [], "People Development"),
    "avg_proficiency": ("AVG(<f>.proficiency)", "Average skill proficiency (1-5)", [], "People Development"),
    "ai_cost_usd": ("SUM(<f>.cost_usd)", "AI assistant spend (USD)", ["AI spend"], "People Development"),
    "ai_sessions": ("SUM(<f>.sessions)", "AI assistant sessions", [], "People Development"),
    "ai_active_people": ("COUNT(DISTINCT IFF(<f>.ai_active, <f>.person_key, NULL))", "People AI-active in the quarter (AI-skill >= 3 and use on >= 50 % of working days)", [], "People Development"),
    "ai_skilled_inactive_people": ("COUNT(DISTINCT IFF(<f>.ai_skilled_inactive, <f>.person_key, NULL))", "People with AI-skill >= 3 and no AI use in the quarter", [], "People Development"),
    "pi_ai_active": ("SUM(IFF(<f>.ai_active, <f>.earned_hours, 0)) / NULLIF(SUM(IFF(<f>.ai_active, <f>.delivery_hours, 0)), 0)", "Productivity index of AI-active people (unstratified)", [], "People Development"),
    "pi_not_ai_active": ("SUM(IFF(NOT <f>.ai_active, <f>.earned_hours, 0)) / NULLIF(SUM(IFF(NOT <f>.ai_active, <f>.delivery_hours, 0)), 0)", "Productivity index of everyone else (unstratified; the stratified test is VW_AI_PRODUCTIVITY_TEST)", [], "People Development"),
    "learning_payback": ("AVG(<f>.payback)", "Productivity change after vs before a learning episode minus the matched comparison change", ["learning ROI"], "People Development"),
    "learning_hours_saved": ("SUM(<f>.hours_saved)", "Hours saved by learning payback", [], "People Development"),
    "voluntary_attrition_pct": ("100 * SUM(<f>.voluntary_leavers) / NULLIF(SUM(<f>.closing_headcount) / COUNT(DISTINCT <f>.month_key), 0)",
                                "Voluntary leavers / average monthly headcount (annual when over one fiscal year; correct for any group or firm-wide)", ["attrition rate", "turnover"], "People Development"),
    "avg_attrition_risk": ("AVG(<f>.attrition_risk)", "Modelled probability of voluntary leaving in the next year (indicative: hold-out AUC 0.90 overall, 0.57 within the simulated pool)", ["flight risk"], "People Development"),
    "high_risk_people": ("SUM(IFF(<f>.risk_decile = 1, 1, 0))", "People in the top attrition-risk decile", [], "People Development"),
    "avg_match_score": ("AVG(<f>.match_score)", "R1: 0.6 x semantic skill similarity + 0.4 x exact skill coverage between a roll-off person and an open bid", ["fit score"], "ProServe360"),
    "matched_people": ("COUNT(DISTINCT <f>.match_person_key)", "Roll-off people with at least one matching open bid", [], "ProServe360"),
    "missed_reuse_hours": ("SUM(IFF(<f>.reuse_status = 'MISSED', <f>.effort_saving_hours, 0))", "ESTIMATED hours a matching asset would have saved but was not reused", [], "Value Creation"),
    "productivity_uplift": ("AVG(<f>.uplift)", "R13: stratified productivity-index uplift of the AI band vs the non-active rest (one row per scope x year x stratum x band)", ["AI uplift"], "People Development"),
    "uplift_ci_low": ("AVG(<f>.ci_low)", "R13: lower bound of the 90 % bootstrap confidence interval", [], "People Development"),
    "uplift_ci_high": ("AVG(<f>.ci_high)", "R13: upper bound of the 90 % bootstrap confidence interval", [], "People Development"),
    "payback_estimate": ("AVG(<f>.payback)", "R14: learning payback with bootstrap CI (one row per scope x curriculum)", [], "People Development"),
    "payback_ci_low": ("AVG(<f>.ci_low)", "R14: lower bound of the 90 % confidence interval", [], "People Development"),
    "payback_ci_high": ("AVG(<f>.ci_high)", "R14: upper bound of the 90 % confidence interval", [], "People Development"),
    "risk_usd_at_stake": ("SUM(<f>.usd_at_stake)", "Money at stake on cross-pillar risk items (USD)", [], "ProServe360"),
    "risk_items": ("COUNT(<f>.risk_key)", "Number of risk items", [], "ProServe360"),
    # P6 Workforce Productivity Score (spec 2, 3) - WPS / pillars are 0-100, 50 = level average
    "avg_wps": ("AVG(<f>.wps)", "Workforce Productivity Score, 0-100 (50 = average of the level in the fiscal year)", ["WPS", "productivity score"], "People Development"),
    "median_wps": ("MEDIAN(<f>.wps)", "Median WPS (0-100, 50 = level average)", ["median productivity"], "People Development"),
    "avg_value_creation": ("AVG(<f>.vc)", "Value Creation pillar score (win-rate, earned-hour efficiency), 0-100", ["VC pillar"], "Value Creation"),
    "avg_operational_excellence": ("AVG(<f>.oe)", "Operational Excellence pillar score (schedule, earned-hour efficiency), 0-100", ["OE pillar"], "Operational Excellence"),
    "avg_people_development": ("AVG(<f>.pd)", "People Development pillar score (billability, utilization, asset reuse, learning, asset creation), 0-100", ["PD pillar"], "People Development"),
    "avg_team": ("AVG(<f>.tm)", "Team pillar score (mean WPS of the team; Manager+ with >= 3 scored team members), 0-100", ["TM pillar"], "People Development"),
    "avg_wps_ex_learn": ("AVG(<f>.wps_ex_learn)", "WPS recomputed without the learning input (used to test training)", [], "People Development"),
    "team_pillar_coverage_pct": ("100 * AVG(IFF(<f>.tm_applies, 1, 0))", "Share of person-quarters where the Team pillar applies", [], "People Development"),
    "scored_person_quarters": ("COUNT(<f>.person_quarter_key)", "Person-quarters scored (>= 80 available hours)", [], "People Development"),
    "ai_tokens": ("SUM(<f>.tokens)", "AI tokens (input + output)", ["tokens", "token usage"], "People Development"),
    "ai_token_cost_usd": ("SUM(<f>.cost_usd)", "AI spend priced per model (USD)", [], "People Development"),
    "tokens_per_delivery_hour": ("SUM(<f>.tokens) / NULLIF(SUM(<f>.delivery_hours), 0)", "AI tokens per delivery hour", ["token intensity"], "People Development"),
    "curriculum_learning_hours": ("SUM(<f>.learning_hours)", "Learning hours in the curriculum", ["training hours"], "People Development"),
    "curriculum_completions": ("SUM(<f>.completions)", "Learning-item completions", [], "People Development"),
    "avg_assessment_score": ("AVG(<f>.avg_assessment_score)", "Mean assessment score of completions (0-100)", [], "People Development"),
    "association_rho": ("AVG(<f>.rho)", "Spearman rho of the exposure with the outcome within level (one row per test cell); "
                        "associated with, not causes", ["correlation", "association"], "People Development"),
    "association_ci_low": ("AVG(<f>.ci_low)", "Lower bound of the 90 % person-cluster bootstrap CI", [], "People Development"),
    "association_ci_high": ("AVG(<f>.ci_high)", "Upper bound of the 90 % person-cluster bootstrap CI", [], "People Development"),
    "wps_uplift": ("AVG(<f>.uplift_wps)", "R13 re-based: WPS of AI-active person-quarters minus the rest (WPS points)", [], "People Development"),
    "wps_payback": ("AVG(<f>.payback_wps)", "R14 re-based: WPS change after a curriculum episode minus the matched comparison (WPS points)", [], "People Development"),
    "level_median_wps": ("AVG(<f>.wps_median)", "Median WPS of the level cell (one row per scope x years x level)", [], "People Development"),
    "level_median_billability_pct": ("100 * AVG(<f>.billability_median)", "Median billability of the level cell (%)", [], "Operational Excellence"),
    "level_median_utilization_pct": ("100 * AVG(<f>.utilization_median)", "Median utilization of the level cell (%)", [], "Operational Excellence"),
}


def F(col, desc, syn=None, kind="fact"):
    return dict(col=col, desc=desc, syn=syn or [], kind=kind)


def test_fields(prefix, extra=None):
    """Shared columns of the P6 association tests (spec 3.3); dimension names are prefixed (unique within the view)."""
    out = {"rho": F("RHO", "Spearman rho within level (partial rho for R16 / R18)"),
           "ci_low": F("CI_LOW", "90 % person-cluster bootstrap CI low"), "ci_high": F("CI_HIGH", "90 % CI high"),
           f"{prefix}_scope": F("SCOPE", "FIRM or MD group id", kind="dim"),
           f"{prefix}_fiscal_years": F("FISCAL_YEARS", "Fiscal year(s) tested, e.g. FY24-26 (pooled) or FY26", kind="dim"),
           f"{prefix}_stratum": F("STRATUM", "ALL LEVELS or a level", kind="dim"),
           f"{prefix}_outcome": F("OUTCOME", "WPS or a pillar / input (VC, OE, PD, TM, WIN, EFF, ...)", kind="dim"),
           f"{prefix}_significant": F("SIGNIFICANT", "90 % CI excludes 0 AND |rho| >= 0.05", kind="dim"),
           f"{prefix}_effect_size": F("EFFECT_SIZE", "SIGNIFICANT / NEGLIGIBLE / NOT_SIGNIFICANT", kind="dim"),
           f"{prefix}_cell_status": F("CELL_STATUS", "OK or SMALL_CELL (< 15 people or < 30 person-quarters; suppressed)", kind="dim")}
    out.update(extra or {})
    return out


# ---------------------------------------------------------------------------------------------- the views
# fact logical table: (schema.table, key or None, {logical: F(...)}, [(relationship target, [(fact col, entity col)])], [metrics])
SVS = {
    "SV_WORKFORCE_PERFORMANCE": dict(
        description="People pillar: five-way time mix (Delivery, Bid, Learning, Admin, Bench) vs level targets, productivity, "
                    "headcount, attrition, roll-off and skills. Use for billability, bench, time mix, headcount and roll-off questions.",
        entities=["person", "md_group", "level", "fiscal_month", "skill", "time_category"],
        entity_edges=[("person", "md_group", "MD_GROUP_ID"), ("person", "level", "LEVEL")],
        facts={
            "scorecard": ("WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_SCORECARD", "PERSON_MONTH_ID", {
                "available_hours": F("AVAILABLE_HOURS", "Available hours"), "delivery_hours": F("DELIVERY_HOURS", "Delivery hours"),
                "bid_hours": F("BID_HOURS", "Bid hours"), "learning_hours": F("LEARNING_HOURS", "Learning hours"),
                "admin_hours": F("ADMIN_HOURS", "Admin hours"), "bench_hours": F("BENCH_HOURS", "Bench hours"),
                "bench_cost": F("BENCH_COST", "Bench cost USD"), "earned_hours": F("EARNED_HOURS", "Earned hours"),
                "utilized_hours": F("UTILIZED_HOURS", "Delivery + bid + recorded asset-contribution hours")},
                [("person", [("PERSON_ID", "PERSON_ID")]), ("fiscal_month", [("MONTH_START", "MONTH_START")])],
                ["billability_pct", "utilization_pct", "bid_pct", "learning_pct", "admin_pct", "bench_pct", "available_hours_total",
                 "bench_cost", "productivity_index"]),
            "time_booking": ("WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_TIME", "PERSON_MONTH_TIME_ID", {
                "hours": F("HOURS", "Hours in the time category"), "available_hours": F("AVAILABLE_HOURS", "Person-month available hours"),
                "target_pct": F("TARGET_PCT", "Level target % for the category")},
                [("person", [("PERSON_ID", "PERSON_ID")]), ("fiscal_month", [("MONTH_START", "MONTH_START")]),
                 ("time_category", [("TIME_CATEGORY", "TIME_CATEGORY")])],
                ["category_share_pct"]),
            "headcount": ("WORKFORCE_PERFORMANCE.DT_HEADCOUNT_MONTH", None, {
                "closing_headcount": F("CLOSING_HEADCOUNT", "Month-end headcount"), "voluntary_leavers": F("VOLUNTARY_LEAVERS", "Voluntary leavers"),
                "hires": F("HIRES", "Hires")},
                [("md_group", [("MD_GROUP_ID", "MD_GROUP_ID")]), ("fiscal_month", [("MONTH_START", "MONTH_START")])],
                ["headcount_closing", "voluntary_leavers", "hires"]),
            "roll_off": ("WORKFORCE_PERFORMANCE.DT_ROLL_OFF", "PERSON_ID", {
                "roll_off_person_key": F("PERSON_ID", "Person rolling off"), "below_pipeline_ai_level": F("BELOW_PIPELINE_AI_LEVEL", "Below pipeline AI level"),
                "roll_off_date": F("ROLL_OFF_DATE", "Last assignment end date", kind="time")},
                [("person", [("PERSON_ID", "PERSON_ID")])],
                ["roll_off_people", "roll_off_below_ai_level"]),
            "attrition_risk": ("REASONING.DT_ATTRITION_RISK", "PERSON_ID", {
                "attrition_risk": F("ATTRITION_RISK", "Modelled probability of leaving"), "risk_decile": F("RISK_DECILE", "1 = highest risk decile", kind="dim"),
                "top_drivers": F("TOP_DRIVERS", "Global top model drivers", kind="dim")},
                [("person", [("PERSON_ID", "PERSON_ID")])],
                ["avg_attrition_risk", "high_risk_people"]),
            "person_skill": ("ONTOLOGY.REL_PERSON_SKILL", None, {
                "proficiency": F("PROFICIENCY", "Latest proficiency 1-5")},
                [("person", [("PERSON_ID", "PERSON_ID")]), ("skill", [("SKILL_ID", "SKILL_ID")])],
                ["avg_proficiency"]),
        },
        vqrs=[("What was the FY26 time mix by level for Financial Services?",
               """SELECT p.LEVEL, ROUND(100 * SUM(s.DELIVERY_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS DELIVERY_PCT,
       ROUND(100 * SUM(s.BID_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS BID_PCT,
       ROUND(100 * SUM(s.LEARNING_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS LEARNING_PCT,
       ROUND(100 * SUM(s.ADMIN_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS ADMIN_PCT,
       ROUND(100 * SUM(s.BENCH_HOURS) / SUM(s.AVAILABLE_HOURS), 1) AS BENCH_PCT
FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_SCORECARD s
JOIN ACOCO_L2.ONTOLOGY.ENT_PERSON p ON p.PERSON_ID = s.PERSON_ID
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = p.MD_GROUP_ID
JOIN ACOCO_L2.CORE.DT_FISCAL_MONTH f ON f.MONTH_START = s.MONTH_START
WHERE g.MD_GROUP_NAME = 'Financial Services' AND f.FISCAL_YEAR = 2026
GROUP BY p.LEVEL, p.LEVEL_SORT ORDER BY p.LEVEL_SORT"""),
              ("How many Financial Services people roll off in the next 90 days and how many are below the pipeline AI-skill level?",
               """SELECT COUNT(*) AS ROLL_OFF_PEOPLE, SUM(IFF(r.BELOW_PIPELINE_AI_LEVEL, 1, 0)) AS BELOW_AI_LEVEL
FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_ROLL_OFF r
JOIN ACOCO_L2.ONTOLOGY.ENT_PERSON p ON p.PERSON_ID = r.PERSON_ID
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = p.MD_GROUP_ID
WHERE g.MD_GROUP_NAME = 'Financial Services'""")],
    ),
    "SV_PROJECT_DELIVERY": dict(
        description="Operational Excellence pillar: project P&L, earned value (CPI, SPI, EAC), liquidated-damages exposure, "
                    "forecast margin, teams, asset reuse and the skills work packages need.",
        entities=["project", "customer", "md_group", "work_package", "fiscal_month", "person", "asset", "skill", "source_project"],
        entity_edges=[("project", "customer", "CUSTOMER_ID"), ("project", "md_group", "MD_GROUP_ID"),
                      ("work_package", "project", "PROJECT_ID"), ("asset", "source_project", "SOURCE_PROJECT_ID")],
        facts={
            "project_month": ("PROJECT_DELIVERY.DT_PROJECT_MONTH_FINANCIALS", None, {
                "revenue": F("REVENUE", "Revenue USD"), "total_cost": F("TOTAL_COST", "Total cost USD"), "margin": F("MARGIN", "Margin USD"),
                "agent_cost": F("AGENT_COST", "AI-agent cost USD"), "agent_hours": F("AGENT_HOURS", "AI-agent hours"),
                "delivery_hours": F("DELIVERY_HOURS", "Delivery hours"), "earned_hours": F("EARNED_HOURS", "Earned hours")},
                [("work_package", [("WBS_ID", "WBS_ID")]), ("fiscal_month", [("MONTH_START", "MONTH_START")])],
                ["revenue", "total_cost", "margin", "margin_pct", "agent_cost", "agent_hours", "productivity_index"]),
            "project_health": ("PROJECT_DELIVERY.DT_PROJECT_HEALTH", "PROJECT_ID", {
                "project_key": F("PROJECT_ID", "Project"), "earned_value_td": F("EARNED_VALUE_TD", "Earned value to date"),
                "actual_cost_td": F("ACTUAL_COST_TD", "Actual cost to date"), "planned_value_td": F("PLANNED_VALUE_TD", "Planned value to date"),
                "contract_value": F("CONTRACT_VALUE", "Contract value"), "eac": F("EAC", "Estimate at completion"),
                "ld_exposure": F("LD_EXPOSURE", "LD exposure"), "reused_asset": F("REUSED_ASSET", "Reused >= 1 asset"),
                "forecast_slip_weeks": F("FORECAST_SLIP_WEEKS", "Forecast slip in weeks")},
                [("project", [("PROJECT_ID", "PROJECT_ID")])],
                ["cpi", "spi", "forecast_margin_pct", "ld_exposure", "eac", "project_count", "asset_reuse_rate_pct"]),
            "project_team": ("PROJECT_DELIVERY.DT_PROJECT_TEAM", None, {
                "delivery_hours": F("DELIVERY_HOURS", "Delivery hours on the project")},
                [("project", [("PROJECT_ID", "PROJECT_ID")]), ("person", [("PERSON_ID", "PERSON_ID")])],
                ["team_delivery_hours"]),
            "asset_use": ("ONTOLOGY.REL_ASSET_USE", "ASSET_USE_ID", {
                "hours_saved_estimated": F("HOURS_SAVED_ESTIMATED", "ESTIMATED hours saved"), "uses": F("1", "One recorded use")},
                [("asset", [("ASSET_ID", "ASSET_ID")]), ("project", [("PROJECT_ID", "PROJECT_ID")])],
                ["hours_saved_estimated", "asset_uses"]),
            "asset_match": ("REASONING.VW_ASSET_MATCH", None, {
                "similarity": F("SIMILARITY", "Semantic similarity of the work package need and the asset"),
                "effort_saving_hours": F("EFFORT_SAVING_HOURS", "Catalogued effort saving (ESTIMATED)"),
                "reuse_status": F("REUSE_STATUS", "REUSED or MISSED", kind="dim"),
                "same_work_type": F("SAME_WORK_TYPE", "Asset built for the same work type", kind="dim")},
                [("work_package", [("WBS_ID", "WBS_ID")]), ("asset", [("ASSET_ID", "ASSET_ID")])],
                ["missed_reuse_hours"]),
            "wp_skill": ("ONTOLOGY.REL_WP_SKILL", None, {
                "required_proficiency": F("REQUIRED_PROFICIENCY", "Required proficiency")},
                [("work_package", [("WBS_ID", "WBS_ID")]), ("skill", [("SKILL_ID", "SKILL_ID")])], []),
            "asset_skill": ("ONTOLOGY.REL_ASSET_SKILL", None, {},
                [("asset", [("ASSET_ID", "ASSET_ID")]), ("skill", [("SKILL_ID", "SKILL_ID")])], []),
        },
        vqrs=[("Which active Financial Services projects have a negative forecast margin?",
               """SELECT h.PROJECT_ID, h.SIZE_CLASS, h.CONTRACT_TYPE, ROUND(h.CPI, 2) AS CPI, ROUND(h.SPI, 2) AS SPI,
       ROUND(100 * h.FORECAST_MARGIN_PCT, 1) AS FORECAST_MARGIN_PCT, ROUND(h.LD_EXPOSURE, 0) AS LD_EXPOSURE
FROM ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_HEALTH h
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = h.MD_GROUP_ID
WHERE g.MD_GROUP_NAME = 'Financial Services' AND h.STATUS_AS_OF = 'ACTIVE' AND h.FORECAST_MARGIN_PCT < 0
ORDER BY h.FORECAST_MARGIN_PCT"""),
              ("What was FY26 margin % by delivery model?",
               """SELECT p.DELIVERY_MODEL, ROUND(100 * SUM(m.MARGIN) / SUM(m.REVENUE), 1) AS MARGIN_PCT
FROM ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_MONTH_FINANCIALS m
JOIN ACOCO_L2.ONTOLOGY.ENT_WORK_PACKAGE w ON w.WBS_ID = m.WBS_ID
JOIN ACOCO_L2.ONTOLOGY.ENT_PROJECT p ON p.PROJECT_ID = w.PROJECT_ID
JOIN ACOCO_L2.CORE.DT_FISCAL_MONTH f ON f.MONTH_START = m.MONTH_START
WHERE f.FISCAL_YEAR = 2026 GROUP BY p.DELIVERY_MODEL ORDER BY MARGIN_PCT DESC""")],
    ),
    "SV_PIPELINE_PRESALES": dict(
        description="Value Creation pillar: bids, win-rate, pursuit cost and intensity, pursuit-team skill fit, required skills, "
                    "and which bids became projects.",
        entities=["opportunity", "customer", "md_group", "fiscal_month", "person", "skill", "project"],
        entity_edges=[("customer", "md_group", "MD_GROUP_ID")],
        facts={
            "bid": ("PIPELINE_PRESALES.DT_OPPORTUNITY_FACT", "OPPORTUNITY_ID", {
                "opportunity_key": F("OPPORTUNITY_ID", "Bid"), "is_won": F("IS_WON", "Won"), "is_closed": F("IS_CLOSED", "Decided"),
                "is_open": F("IS_OPEN_AS_OF", "Open at the as-of date"), "estimated_value": F("ESTIMATED_VALUE", "Estimated value USD"),
                "pursuit_cost": F("PURSUIT_COST", "Pursuit cost USD"), "skill_fit": F("SKILL_FIT", "Team skill fit 0-1"),
                "pursuit_intensity": F("PURSUIT_INTENSITY", "Pursuit cost / estimated value"),
                "decision_fiscal_year": F("DECISION_FISCAL_YEAR", "Fiscal year the bid was decided (or created if open)", kind="dim"),
                "skill_fit_band": F("SKILL_FIT_BAND", "HIGH (>= 0.8) / MEDIUM / LOW (< 0.5)", ["fit band"], kind="dim"),
                "is_above_median_intensity": F("IS_ABOVE_MEDIAN_INTENSITY", "Pursuit intensity above the size-class median", kind="dim")},
                [("opportunity", [("OPPORTUNITY_ID", "OPPORTUNITY_ID")]), ("customer", [("CUSTOMER_ID", "CUSTOMER_ID")]),
                 ("project", [("PROJECT_ID", "PROJECT_ID")])],
                ["win_rate_pct", "pursuit_cost", "pursuit_cost_per_won_usd", "avg_skill_fit", "won_value", "open_pipeline_value", "bid_count"]),
            "pursuit_team": ("PIPELINE_PRESALES.DT_PURSUIT_TEAM", None, {
                "bid_hours": F("BID_HOURS", "Bid hours booked"), "team_role": F("TEAM_ROLE", "LEAD, MEMBER or SUPPORT (support members are named on the bid but outside skill fit)", kind="dim")},
                [("opportunity", [("OPPORTUNITY_ID", "OPPORTUNITY_ID")]), ("person", [("PERSON_ID", "PERSON_ID")])],
                ["pursuit_team_bid_hours"]),
            "bench_match": ("REASONING.VW_BENCH_TO_PIPELINE_MATCH", None, {
                "match_person_key": F("PERSON_ID", "Roll-off person"), "match_score": F("MATCH_SCORE", "Match score 0-1"),
                "skill_coverage": F("SKILL_COVERAGE", "Share of required skills the person holds at >= 3"),
                "match_rank": F("RANK_FOR_PERSON", "1 = best open bid for the person", kind="dim"),
                "meets_ai_level": F("MEETS_AI_LEVEL", "Person's AI-skill level meets the bid's requirement", kind="dim"),
                "roll_off_date": F("ROLL_OFF_DATE", "Date the person rolls off", kind="time")},
                [("person", [("PERSON_ID", "PERSON_ID")]), ("opportunity", [("OPPORTUNITY_ID", "OPPORTUNITY_ID")])],
                ["avg_match_score", "matched_people"]),
            "bid_skill": ("ONTOLOGY.REL_OPPORTUNITY_SKILL", None, {},
                [("opportunity", [("OPPORTUNITY_ID", "OPPORTUNITY_ID")]), ("skill", [("SKILL_ID", "SKILL_ID")])], []),
        },
        vqrs=[("What is the win-rate by pursuit-team skill fit band?",
               """SELECT SKILL_FIT_BAND, COUNT(*) AS BIDS, ROUND(100 * AVG(IFF(IS_WON, 1, 0)), 1) AS WIN_RATE_PCT
FROM ACOCO_L2.PIPELINE_PRESALES.DT_OPPORTUNITY_FACT WHERE IS_CLOSED GROUP BY SKILL_FIT_BAND ORDER BY SKILL_FIT_BAND"""),
              ("What is the open pipeline value by MD group?",
               """SELECT g.MD_GROUP_NAME, ROUND(SUM(o.ESTIMATED_VALUE), 0) AS OPEN_PIPELINE_VALUE
FROM ACOCO_L2.PIPELINE_PRESALES.DT_OPPORTUNITY_FACT o
JOIN ACOCO_L2.ONTOLOGY.ENT_CUSTOMER c ON c.CUSTOMER_ID = o.CUSTOMER_ID
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = c.MD_GROUP_ID
WHERE o.IS_OPEN_AS_OF GROUP BY g.MD_GROUP_NAME ORDER BY OPEN_PIPELINE_VALUE DESC""")],
    ),
    "SV_AI_ADOPTION": dict(
        description="AI adoption: AI tool, product and model use and spend (chat assistants 2023 - Apr 2025; Claude Code and "
                    "Codex from May 2025; Cortex from Nov 2025), agent cost on projects, AI-active vs other earned-hour efficiency, "
                    "and learning payback. WPS-based productivity tests are in SV_WORKFORCE_PRODUCTIVITY.",
        entities=["person", "md_group", "ai_tool", "ai_model", "project", "learning_item", "skill", "fiscal_month"],
        entity_edges=[("person", "md_group", "MD_GROUP_ID"), ("learning_item", "skill", "TARGET_SKILL_ID")],
        facts={
            "ai_usage": ("AI_ADOPTION.DT_AI_USAGE_DAILY", None, {
                "cost_usd": F("COST_USD", "Spend USD"), "sessions": F("SESSIONS", "Sessions"), "tokens": F("TOKENS", "Tokens"),
                "usage_date": F("USAGE_DATE", "Usage date", kind="time")},
                [("person", [("PERSON_ID", "PERSON_ID")]), ("ai_tool", [("AI_TOOL_ID", "AI_TOOL_ID")]),
                 ("ai_model", [("AI_MODEL_ID", "AI_MODEL_ID")])],
                ["ai_cost_usd", "ai_sessions", "ai_tokens"]),
            "agent_on_project": ("AI_ADOPTION.DT_AI_AGENT_PROJECT_MONTH", "AGENT_PROJECT_MONTH_ID", {
                "agent_cost": F("AGENT_COST", "Agent cost USD"), "agent_hours": F("AGENT_HOURS", "Agent hours")},
                [("project", [("PROJECT_ID", "PROJECT_ID")]), ("ai_tool", [("AI_TOOL_ID", "AI_TOOL_ID")]),
                 ("fiscal_month", [("MONTH_START", "MONTH_START")])],
                ["agent_cost", "agent_hours"]),
            "ai_productivity": ("AI_ADOPTION.DT_AI_PRODUCTIVITY", None, {
                "person_key": F("PERSON_ID", "Person"), "ai_active": F("AI_ACTIVE", "AI-active in the quarter"),
                "ai_skilled_inactive": F("AI_SKILLED_INACTIVE", "AI-skilled but no use"), "earned_hours": F("EARNED_HOURS", "Earned hours"),
                "delivery_hours": F("DELIVERY_HOURS", "Delivery hours"),
                "productivity_work_type": F("WORK_TYPE", "Work type of the delivery", kind="dim")},
                [("person", [("PERSON_ID", "PERSON_ID")]), ("fiscal_month", [("QUARTER_START", "MONTH_START")])],
                ["ai_active_people", "ai_skilled_inactive_people", "pi_ai_active", "pi_not_ai_active"]),
            "productivity_test": ("REASONING.AI_PRODUCTIVITY_TEST", None, {
                "uplift": F("UPLIFT", "Stratified uplift"), "ci_low": F("CI_LOW", "90 % CI low"), "ci_high": F("CI_HIGH", "90 % CI high"),
                "test_scope": F("SCOPE", "FIRM or MD group id (FS, CMT, ...)", ["scope"], kind="dim"),
                "test_fiscal_year": F("FISCAL_YEAR", "Fiscal year tested", kind="dim"),
                "test_stratum": F("STRATUM", "ALL LEVELS or a level", kind="dim"),
                "ai_band": F("AI_BAND", "AI_ACTIVE or SKILLED_INACTIVE (each vs the non-active rest)", kind="dim"),
                "is_significant": F("SIGNIFICANT", "90 % CI excludes zero", kind="dim"),
                "people_in_band": F("PEOPLE_IN_BAND", "People in the band")},
                [], ["productivity_uplift", "uplift_ci_low", "uplift_ci_high"]),
            "payback_test": ("REASONING.LEARNING_PAYBACK_TEST", None, {
                "payback": F("PAYBACK", "Payback"), "ci_low": F("CI_LOW", "90 % CI low"), "ci_high": F("CI_HIGH", "90 % CI high"),
                "payback_scope": F("SCOPE", "FIRM or FS", kind="dim"), "payback_curriculum": F("CURRICULUM", "Curriculum (8 curricula)", kind="dim"),
                "payback_significant": F("SIGNIFICANT", "90 % CI excludes zero", kind="dim")},
                [], ["payback_estimate", "payback_ci_low", "payback_ci_high"]),
            "learning_episode": ("AI_ADOPTION.DT_LEARNING_PAYBACK", None, {
                "payback": F("PAYBACK", "Productivity payback"), "hours_saved": F("HOURS_SAVED", "Hours saved")},
                [("person", [("PERSON_ID", "PERSON_ID")]), ("learning_item", [("LEARNING_ITEM_ID", "LEARNING_ITEM_ID")]),
                 ("fiscal_month", [("COMPLETION_MONTH", "MONTH_START")])],
                ["learning_payback", "learning_hours_saved"]),
        },
        vqrs=[("What is FY26 AI assistant spend by tool?",
               """SELECT t.AI_TOOL_NAME, ROUND(SUM(u.COST_USD), 0) AS AI_COST_USD
FROM ACOCO_L2.AI_ADOPTION.DT_AI_USAGE_DAILY u JOIN ACOCO_L2.ONTOLOGY.ENT_AI_TOOL t ON t.AI_TOOL_ID = u.AI_TOOL_ID
WHERE u.USAGE_DATE BETWEEN '2025-10-01' AND '2026-09-30' GROUP BY t.AI_TOOL_NAME ORDER BY AI_COST_USD DESC"""),
              ("What is FY26 AI spend and tokens by product and model?",
               """SELECT m.PRODUCT, m.MODEL, ROUND(SUM(u.COST_USD), 0) AS AI_COST_USD, SUM(u.TOKENS) AS TOKENS
FROM ACOCO_L2.AI_ADOPTION.DT_AI_USAGE_DAILY u JOIN ACOCO_L2.ONTOLOGY.ENT_AI_MODEL m ON m.AI_MODEL_ID = u.AI_MODEL_ID
WHERE u.USAGE_DATE BETWEEN '2025-10-01' AND '2026-09-30' GROUP BY m.PRODUCT, m.MODEL ORDER BY AI_COST_USD DESC"""),
              ("What is the average learning payback by curriculum?",
               """SELECT li.CURRICULUM, ROUND(AVG(l.PAYBACK), 4) AS LEARNING_PAYBACK
FROM ACOCO_L2.AI_ADOPTION.DT_LEARNING_PAYBACK l JOIN ACOCO_L2.ONTOLOGY.ENT_LEARNING_ITEM li ON li.LEARNING_ITEM_ID = l.LEARNING_ITEM_ID
GROUP BY li.CURRICULUM ORDER BY li.CURRICULUM""")],
    ),
    "SV_WORKFORCE_PRODUCTIVITY": dict(
        description="Workforce Productivity Score (P6): WPS 0-100 per person x fiscal quarter (50 = level average in the year), its "
                    "pillars Value Creation, Operational Excellence, People Development and Team, billability and utilization vs "
                    "targets, AI tokens by product, learning by curriculum, and the association tests R13w-R18 (Spearman rho "
                    "with 90 % CI). Results are associations, not causes.",
        entities=["person", "md_group", "level", "fiscal_month", "learning_category"],
        entity_edges=[("person", "md_group", "MD_GROUP_ID"), ("person", "level", "LEVEL")],
        facts={
            "person_quarter": ("WORKFORCE_PERFORMANCE.DT_PERSON_QUARTER_WPS", "PERSON_QUARTER_ID", {
                "person_quarter_key": F("PERSON_QUARTER_ID", "Person-quarter"), "wps": F("WPS", "Workforce Productivity Score 0-100"),
                "vc": F("VC", "Value Creation pillar 0-100"), "oe": F("OE", "Operational Excellence pillar 0-100"),
                "pd": F("PD", "People Development pillar 0-100"), "tm": F("TM", "Team pillar 0-100 (null when it does not apply)"),
                "wps_ex_learn": F("WPS_EX_LEARN", "WPS without the learning input"),
                "available_hours": F("AVAILABLE_HOURS", "Available hours"), "delivery_hours": F("DELIVERY_HOURS", "Delivery hours"),
                "asset_contribution_hours": F("ASSET_CONTRIBUTION_HOURS", "Recorded asset-building hours"),
                "tm_applies": F("TM_APPLIES", "Team pillar applies (Manager+ with >= 3 scored team members)", kind="dim"),
                "team_scope": F("TEAM_SCOPE", "DIRECT (Manager) or TREE (Senior Manager+, reporting tree)", kind="dim"),
                "wps_fiscal_quarter_label": F("FISCAL_QUARTER_LABEL", "Fiscal quarter, e.g. FY26Q4", ["quarter label"], kind="dim")},
                [("person", [("PERSON_ID", "PERSON_ID")]), ("fiscal_month", [("Q_START", "MONTH_START")])],
                ["avg_wps", "median_wps", "avg_value_creation", "avg_operational_excellence", "avg_people_development", "avg_team",
                 "avg_wps_ex_learn", "team_pillar_coverage_pct", "scored_person_quarters", "billability_pct"]),
            "token_quarter": ("AI_ADOPTION.DT_AI_TOKENS_PERSON_QUARTER", "ROW_ID", {
                "tokens": F("TOKENS", "Tokens"), "cost_usd": F("COST_USD", "Spend USD"), "delivery_hours": F("DELIVERY_HOURS", "Delivery hours"),
                "token_product": F("PRODUCT", "AI product (CHATGPT, CLAUDE_CHAT, CODEX, CLAUDE_CODE, CORTEX)", ["product"], kind="dim"),
                "token_model_family": F("MODEL_FAMILY", "CLAUDE, GPT or OPEN", kind="dim"),
                "token_fiscal_year": F("FISCAL_YEAR", "Fiscal year", kind="dim"),
                "token_fiscal_quarter": F("FISCAL_QUARTER", "Fiscal quarter 1-4", kind="dim")},
                [("person", [("PERSON_ID", "PERSON_ID")])],
                ["ai_tokens", "ai_token_cost_usd", "tokens_per_delivery_hour"]),
            "learning_quarter": ("WORKFORCE_PERFORMANCE.DT_LEARNING_PERSON_QUARTER", "ROW_ID", {
                "learning_hours": F("LEARNING_HOURS", "Learning hours"), "completions": F("COMPLETIONS", "Completions"),
                "avg_assessment_score": F("AVG_ASSESSMENT_SCORE", "Mean assessment score"),
                "is_required_at_level": F("IS_REQUIRED_AT_LEVEL", "Curriculum is required at the person's level", kind="dim"),
                "learning_fiscal_year": F("FISCAL_YEAR", "Fiscal year", kind="dim"),
                "learning_fiscal_quarter": F("FISCAL_QUARTER", "Fiscal quarter 1-4", kind="dim")},
                [("person", [("PERSON_ID", "PERSON_ID")]), ("learning_category", [("CURRICULUM", "CURRICULUM")])],
                ["curriculum_learning_hours", "curriculum_completions", "avg_assessment_score"]),
            "wps_by_level": ("REASONING.WPS_BY_LEVEL", None, {
                "wps_median": F("WPS_MEDIAN", "Median WPS"), "billability_median": F("BILLABILITY_MEDIAN", "Median billability 0-1"),
                "utilization_median": F("UTILIZATION_MEDIAN", "Median utilization 0-1"),
                "level_scope": F("SCOPE", "FIRM or MD group id", kind="dim"),
                "level_fiscal_years": F("FISCAL_YEARS", "Fiscal year(s)", kind="dim"),
                "level_cell": F("LEVEL", "Level of the cell", kind="dim"),
                "level_cell_status": F("CELL_STATUS", "OK or SMALL_CELL", kind="dim")},
                [], ["level_median_wps", "level_median_billability_pct", "level_median_utilization_pct"]),
            "token_test": ("REASONING.TOKEN_WPS_TEST", None, test_fields("token_test", {
                "token_test_exposure": F("EXPOSURE", "Token measure (tokens per delivery hour, ...)", kind="dim")}), [], ["association_rho", "association_ci_low", "association_ci_high"]),
            "vendor_test": ("REASONING.VENDOR_WPS_TEST", None, test_fields("vendor_test", {
                "vendor_test_exposure": F("EXPOSURE", "Product or model family (share of tokens); tested only in product-available quarters", kind="dim"),
                "vendor_test_exposure_kind": F("EXPOSURE_KIND", "PRODUCT or MODEL_FAMILY", kind="dim")}), [], ["association_rho", "association_ci_low", "association_ci_high"]),
            "training_test": ("REASONING.TRAINING_WPS_TEST", None, test_fields("training_test", {
                "training_test_exposure": F("EXPOSURE", "Learning share of available hours", kind="dim")}), [], ["association_rho", "association_ci_low", "association_ci_high"]),
            "curriculum_test": ("REASONING.CURRICULUM_WPS_TEST", None, test_fields("curriculum_test", {
                "curriculum_test_curriculum": F("CURRICULUM", "Curriculum tested", kind="dim"),
                "curriculum_test_target_input": F("TARGET_INPUT", "WPS input the curriculum targets", kind="dim")}), [], ["association_rho", "association_ci_low", "association_ci_high"]),
            "ai_wps_test": ("REASONING.AI_WPS_TEST", None, {
                "uplift_wps": F("UPLIFT_WPS", "WPS uplift of AI-active person-quarters"), "ci_low": F("CI_LOW", "90 % CI low"),
                "ci_high": F("CI_HIGH", "90 % CI high"), "ai_wps_scope": F("SCOPE", "FIRM or MD group id", kind="dim"),
                "ai_wps_fiscal_years": F("FISCAL_YEARS", "Fiscal year(s)", kind="dim"),
                "ai_wps_stratum": F("STRATUM", "ALL LEVELS or a level", kind="dim"),
                "ai_wps_significant": F("SIGNIFICANT", "90 % CI excludes 0", kind="dim")},
                [], ["wps_uplift", "association_ci_low", "association_ci_high"]),
            "payback_wps_test": ("REASONING.LEARNING_WPS_PAYBACK_TEST", None, {
                "payback_wps": F("PAYBACK_WPS", "WPS payback of the curriculum"), "ci_low": F("CI_LOW", "90 % CI low"),
                "ci_high": F("CI_HIGH", "90 % CI high"), "payback_wps_scope": F("SCOPE", "FIRM or MD group id", kind="dim"),
                "payback_wps_curriculum": F("CURRICULUM", "Curriculum", kind="dim"),
                "payback_wps_significant": F("SIGNIFICANT", "90 % CI excludes 0", kind="dim")},
                [], ["wps_payback", "association_ci_low", "association_ci_high"]),
        },
        vqrs=[("What was the median WPS and billability by level in FY26?",
               """SELECT LEVEL, ROUND(WPS_MEDIAN, 1) AS MEDIAN_WPS, ROUND(100 * BILLABILITY_MEDIAN, 1) AS MEDIAN_BILLABILITY_PCT,
       ROUND(100 * UTILIZATION_MEDIAN, 1) AS MEDIAN_UTILIZATION_PCT
FROM ACOCO_L2.REASONING.WPS_BY_LEVEL WHERE SCOPE = 'FIRM' AND FISCAL_YEARS = 'FY26' AND CELL_STATUS = 'OK'
ORDER BY LEVEL_SORT"""),
              ("Which AI products are significantly associated with WPS, by level?",
               """SELECT STRATUM, EXPOSURE, OUTCOME, ROUND(RHO, 3) AS RHO, ROUND(CI_LOW, 3) AS CI_LOW, ROUND(CI_HIGH, 3) AS CI_HIGH
FROM ACOCO_L2.REASONING.VENDOR_WPS_TEST
WHERE SCOPE = 'FIRM' AND FISCAL_YEARS NOT LIKE '%pooled' AND EXPOSURE_KIND = 'PRODUCT' AND OUTCOME = 'WPS'
  AND SIGNIFICANT AND CELL_STATUS = 'OK'
ORDER BY STRATUM, RHO DESC"""),
              ("What was average WPS by MD group in FY26?",
               """SELECT g.MD_GROUP_NAME, ROUND(AVG(w.WPS), 1) AS AVG_WPS
FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_QUARTER_WPS w
JOIN ACOCO_L2.ONTOLOGY.ENT_PERSON p ON p.PERSON_ID = w.PERSON_ID
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = p.MD_GROUP_ID
JOIN ACOCO_L2.CORE.DT_FISCAL_MONTH f ON f.MONTH_START = w.Q_START
WHERE f.FISCAL_YEAR = 2026 GROUP BY g.MD_GROUP_NAME ORDER BY AVG_WPS DESC""")],
    ),
    "SV_PORTFOLIO_360": dict(
        description="ProServe360 overlay for the Managing Director: group P&L, capacity mix by time category vs target, "
                    "headcount and attrition, win-rate and the cross-pillar risk register.",
        entities=["md_group", "fiscal_month", "level", "time_category"],
        entity_edges=[],
        facts={
            "portfolio_month": ("PORTFOLIO_360.DT_PORTFOLIO_MONTH", None, {
                "revenue": F("REVENUE", "Revenue USD"), "total_cost": F("TOTAL_COST", "Total cost USD"), "margin": F("MARGIN", "Margin USD"),
                "available_hours": F("AVAILABLE_HOURS", "Available hours"), "delivery_hours": F("DELIVERY_HOURS", "Delivery hours"),
                "bid_hours": F("BID_HOURS", "Bid hours"), "learning_hours": F("LEARNING_HOURS", "Learning hours"),
                "admin_hours": F("ADMIN_HOURS", "Admin hours"), "bench_hours": F("BENCH_HOURS", "Bench hours"),
                "bench_cost": F("BENCH_COST", "Bench cost USD"), "closing_headcount": F("CLOSING_HEADCOUNT", "Month-end headcount"),
                "voluntary_leavers": F("VOLUNTARY_LEAVERS", "Voluntary leavers"),
                "month_key": F("MONTH_START", "Month of the row (counts months for averages)")},
                [("md_group", [("MD_GROUP_ID", "MD_GROUP_ID")]), ("fiscal_month", [("MONTH_START", "MONTH_START")])],
                ["revenue", "total_cost", "margin", "margin_pct", "billability_pct", "bid_pct", "learning_pct", "admin_pct",
                 "bench_pct", "bench_cost", "voluntary_attrition_pct"]),
            "capacity_mix": ("PORTFOLIO_360.DT_CAPACITY_MIX_LONG", None, {
                "hours": F("HOURS", "Hours in the category"), "available_hours": F("AVAILABLE_HOURS", "Available hours"),
                "target_pct": F("TARGET_PCT", "Level target %")},
                [("md_group", [("MD_GROUP_ID", "MD_GROUP_ID")]), ("level", [("LEVEL", "LEVEL")]),
                 ("fiscal_month", [("MONTH_START", "MONTH_START")]), ("time_category", [("TIME_CATEGORY", "TIME_CATEGORY")])],
                ["category_share_pct"]),
            "risk_item": ("PORTFOLIO_360.DT_RISK_REGISTER", "RISK_ID", {
                "risk_key": F("RISK_ID", "Risk item"), "usd_at_stake": F("USD_AT_STAKE", "USD at stake"),
                "pillar": F("PILLAR", "OPERATIONAL / PEOPLE / VALUE", kind="dim"), "risk_type": F("RISK_TYPE", "Risk type", kind="dim"),
                "risk_object_id": F("OBJECT_ID", "Project / person / opportunity the risk is about", kind="dim"),
                "risk_detail": F("DETAIL", "Short explanation", kind="dim")},
                [("md_group", [("MD_GROUP_ID", "MD_GROUP_ID")])],
                ["risk_usd_at_stake", "risk_items"]),
        },
        vqrs=[("What were FY26 revenue, margin % and bench % for Financial Services?",
               """SELECT ROUND(SUM(p.REVENUE), 0) AS REVENUE, ROUND(100 * SUM(p.MARGIN) / SUM(p.REVENUE), 1) AS MARGIN_PCT,
       ROUND(100 * SUM(p.BENCH_HOURS) / SUM(p.AVAILABLE_HOURS), 1) AS BENCH_PCT
FROM ACOCO_L2.PORTFOLIO_360.DT_PORTFOLIO_MONTH p
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = p.MD_GROUP_ID
WHERE g.MD_GROUP_NAME = 'Financial Services' AND p.FISCAL_YEAR = 2026"""),
              ("What are the top 5 risks for Financial Services by USD at stake?",
               """SELECT r.PILLAR, r.RISK_TYPE, r.OBJECT_ID, r.DETAIL, ROUND(r.USD_AT_STAKE, 0) AS USD_AT_STAKE
FROM ACOCO_L2.PORTFOLIO_360.DT_RISK_REGISTER r
JOIN ACOCO_L2.ONTOLOGY.ENT_MD_GROUP g ON g.MD_GROUP_ID = r.MD_GROUP_ID
WHERE g.MD_GROUP_NAME = 'Financial Services' ORDER BY r.USD_AT_STAKE DESC LIMIT 5""")],
    ),
}

TYPE_MAP = {"TEXT": "VARCHAR", "NUMBER": "NUMBER", "FLOAT": "FLOAT", "BOOLEAN": "BOOLEAN", "DATE": "DATE",
            "TIMESTAMP_NTZ": "TIMESTAMP_NTZ", "TIMESTAMP_TZ": "TIMESTAMP_TZ", "TIMESTAMP_LTZ": "TIMESTAMP_LTZ"}
_types = {}


def col_types():
    if not _types:
        for r in sf.query("""SELECT table_schema || '.' || table_name t, column_name c, data_type d
                             FROM ACOCO_L2.INFORMATION_SCHEMA.COLUMNS WHERE table_schema <> 'INFORMATION_SCHEMA'"""):
            _types[(r["T"], r["C"])] = TYPE_MAP.get(r["D"], r["D"])
    return _types


def entity_table(logical):
    ent = ROLES.get(logical, logical)
    tbl, pk, dims, _ = ENTITIES[ent]
    t = col_types()
    schema, name = tbl.split(".")
    out = dict(name=logical, description=f"Shared ontology entity {ent.upper()} (ACOCO_L2.{tbl})"
                                         + (f" in the role {logical}" if logical != ent else ""),
               base_table=dict(database="ACOCO_L2", schema=schema, table=name), primary_key=dict(columns=[pk]))
    out["dimensions"] = []
    for lname, (col, desc, syn) in dims.items():
        d = dict(name=lname if logical == ent else f"{logical}_{lname}", expr=col, data_type=t[(tbl, col)], description=desc)
        if syn and logical == ent:
            d["synonyms"] = syn
        out["dimensions"].append(d)
    if ent == "fiscal_month":
        out["time_dimensions"] = [dict(name="month_start", expr="MONTH_START", data_type="DATE",
                                       description="First day of the fiscal month (join key)")]
    return out


def metric_name(m, tbl):
    """A metric may not share a name with a physical column of its table (Snowflake resolves the column to the
    metric -> cycle), so colliding metrics are published as total_<name>."""
    cols = {c for (t, c) in col_types() if t == tbl}
    return f"total_{m}" if m.upper() in cols else m


def fact_table(logical, spec):
    tbl, key, fields, _, metrics = spec
    t = col_types()
    schema, name = tbl.split(".")
    out = dict(name=logical, description=f"Fact {tbl}", base_table=dict(database="ACOCO_L2", schema=schema, table=name))
    if key:
        out["primary_key"] = dict(columns=[key])
    dims, tdims, facts = [], [], []
    for lname, fdef in fields.items():
        dtype = "NUMBER" if fdef["col"] == "1" else t[(tbl, fdef["col"])]
        item = dict(name=lname, expr=fdef["col"], data_type=dtype, description=fdef["desc"])
        if fdef["syn"]:
            item["synonyms"] = fdef["syn"]
        (dims if fdef["kind"] == "dim" else tdims if fdef["kind"] == "time" else facts).append(item)
    if dims:
        out["dimensions"] = dims
    if tdims:
        out["time_dimensions"] = tdims
    if facts:
        out["facts"] = facts
    if metrics:
        out["metrics"] = []
        for m in metrics:
            expr, desc, syn, _ = METRICS[m]
            item = dict(name=metric_name(m, tbl), expr=expr.replace("<f>.", ""), description=desc)
            if syn:
                item["synonyms"] = syn
            out["metrics"].append(item)
    return out


def build_model(sv_name, sv):
    model = dict(name=sv_name, description=sv["description"], tables=[], relationships=[])
    for e in sv["entities"]:
        model["tables"].append(entity_table(e))
    for fname, spec in sv["facts"].items():
        model["tables"].append(fact_table(fname, spec))
        for target, cols in spec[3]:
            model["relationships"].append(dict(
                name=f"{fname}_to_{target}", left_table=fname, right_table=target,
                relationship_columns=[dict(left_column=lc, right_column=rc) for lc, rc in cols],
                join_type="left_outer", relationship_type="many_to_one"))
    for left, right, col in sv["entity_edges"]:
        rpk = ENTITIES[ROLES.get(right, right)][1]
        model["relationships"].append(dict(
            name=f"{left}_to_{right}", left_table=left, right_table=right,
            relationship_columns=[dict(left_column=col, right_column=rpk)], join_type="left_outer",
            relationship_type="many_to_one"))
    model["verified_queries"] = [dict(name=f"vq_{i + 1}", question=qn, sql=sql, verified_by="ACoCo build (CP-07)",
                                      verified_at=1793059200, use_as_onboarding_question=i == 0)
                                 for i, (qn, sql) in enumerate(sv["vqrs"])]
    model["custom_instructions"] = ("Fiscal years run October to September (FY26 = Oct 2025 - Sep 2026); the as-of date is "
                                    "1 Oct 2026, so FY26 is the last closed year. Percentages are 0-100. Filter MD groups by "
                                    "md_group name (e.g. 'Financial Services').")
    return model


def check_single_paths(sv_name, sv):
    """No logical table may be reachable from a fact by two different relationship paths."""
    edges = collections.defaultdict(list)
    for fname, spec in sv["facts"].items():
        for target, _ in spec[3]:
            edges[fname].append(target)
    for left, right, _ in sv["entity_edges"]:
        edges[left].append(right)
    errors = []
    for fname in sv["facts"]:
        paths = collections.Counter()

        def walk(node, seen):
            for nxt in edges.get(node, []):
                if nxt in seen:
                    continue
                paths[nxt] += 1
                walk(nxt, seen | {nxt})
        walk(fname, {fname})
        errors += [f"{sv_name}.{fname} reaches {t} by {n} paths" for t, n in paths.items() if n > 1]
    return errors


import collections  # noqa: E402


class NoAliasDumper(yaml.SafeDumper):
    """Shared Python lists (synonyms, test fields) must be written out, not as YAML anchors / aliases."""
    def ignore_aliases(self, data):
        return True


def render():
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    for sv_name, sv in SVS.items():
        errors += check_single_paths(sv_name, sv)
        (OUT / f"{sv_name.lower()}.yaml").write_text(yaml.dump(build_model(sv_name, sv), Dumper=NoAliasDumper, sort_keys=False, width=120))
    if errors:
        sys.exit("path errors:\n  " + "\n  ".join(errors))
    print(f"rendered {len(SVS)} semantic views to {OUT}")


def deploy(names):
    sf.query("CREATE SCHEMA IF NOT EXISTS ACOCO_L2.SEMANTIC COMMENT = 'Semantic Views over ENT_* + mart DT_* (PRD 7.2)'")
    for sv_name in names or list(SVS):
        path = OUT / f"{sv_name.lower()}.yaml"
        proc = subprocess.run(["cortex", "agent-studio", "sv-deploy", "-c", CONNECTION, "--file-path", str(path),
                               "--fqn", f"ACOCO_L2.SEMANTIC.{sv_name}"], capture_output=True, text=True)
        tail = (proc.stdout + proc.stderr).strip()[-600:]
        ok = proc.returncode == 0 and "error" not in tail.lower()
        if not ok and "authentication method" in tail:
            # org policy blocks the CLI's auth method: deploy the same YAML through the SQL procedure
            # (verify first; replacing an existing view copies its grants)
            spec = path.read_text()
            assert "$$" not in spec
            try:
                for verify in ("TRUE", "FALSE"):
                    sf.query(f"CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML('ACOCO_L2.SEMANTIC', $${spec}$$, {verify})")
                ok, tail = True, ""
            except Exception as e:  # noqa: BLE001
                tail = str(e)[-600:]
        print(f"{'deployed' if ok else 'FAILED  '} {sv_name}" + ("" if ok else f"\n{tail}"))
        if not ok:
            sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--deploy", nargs="*")
    a = ap.parse_args()
    render()
    if a.deploy is not None:
        deploy(a.deploy)


if __name__ == "__main__":
    main()
