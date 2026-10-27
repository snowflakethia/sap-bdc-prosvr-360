# Deviations from the PRD and the checkpoint plan

Each entry: what differs, why, and what changes downstream. Added at the checkpoint where it was found.

## CP-00 (2026-10-27)

| # | Deviation | Evidence | Consequence |
|---|---|---|---|
| D-00-1 | **Clones do not carry Cortex Search services.** Tables, views, dynamic tables and Semantic Views are carried | `logs/preflight.json` -> `clone_test.in_clone` | Rollback re-creates `CSS_*` from `sql/03_l2/reasoning/` via `sql/rebuild_from_checkpoint.sql`; `tools/export_ddl.py` records their definition at each CP |
| D-00-2 | **Cloned dynamic tables start `SUSPENDED`** (lag preserved) | `clone_test.clone_dt_state` | `rebuild_from_checkpoint.sql` resumes every `ACOCO_L2` DT after a restore (from CP-04) |
| D-00-3 | **Available models:** `claude-sonnet-4-5`, `claude-haiku-4-5`, `llama3.3-70b`. Not available: `claude-4-sonnet`, `claude-3-5-sonnet`, `claude-3-7-sonnet`; `mistral-large2` is legacy | `preflight.json` -> `models` | Agent (CP-08) uses `claude-sonnet-4-5`; Ask Cortex `AI_COMPLETE` (CP-09) uses `claude-haiku-4-5` for latency. Re-check at CP-08 |
| D-00-4 | **Shell scripts run as `bash tools/<script>.sh`** - `chmod +x` is blocked by the managed-settings policy | tool policy | All plan commands `tools/checkpoint.sh ...` / `tools/rollback.sh ...` are run as `bash tools/checkpoint.sh ...` |
| D-00-5 | **`logs/` is tracked in git** (plan said ignored), except `logs/*.tmp` | - | Gate results and preflight are part of each checkpoint's audit trail and roll back with the tag. They contain no secrets |
| D-00-6 | **Tools use the Snowflake CLI, not the Python connector** (connector not installed for system `python3`) | `ModuleNotFoundError: snowflake` | `tools/sf.py` wraps `snow sql -c sfseapac_kp --format json`. The generator (CP-02) will need a venv with `snowflake-connector-python[pandas]` for bulk loads |
| D-00-7 | **No PRD figure changes.** All 17 CLDs and the key-table row counts match PRD 3.1 / 3.3 exactly (e.g. Core Workforce 70,738; Employee Availability 1,545,495; Universal Journal 13,713,866) | `preflight.json` -> `clds` | None |
| D-00-8 | The connector also lists a share `bdfs_bdc_supplier_quality_share` (another demo) | `preflight.json` -> `connector.shares` | Not used by ACoCo; read-only rule (PRD 4.2) applies |

## CP-01 (2026-10-27)

| # | Deviation | Evidence | Consequence |
|---|---|---|---|
| D-01-1 | **The S/4 tenant is a bike / manufacturing company** (hierarchy `0101/A000/0001`: "Velotics", "Production Operations"...). There are no consulting groups to reuse | profiling of `costcenterhierarchynode` / `costcentertext` | ACoCo = company code **`USC1`** (46 real cost centres under node `0USC1`). `OPS.MAP_MD_GROUP` assigns 18 of them as DELIVERY home cost centres (3 per MD group), 3 as AI_PLATFORM (`USC1_IT1/2/3` = OpenAI / Anthropic / Cortex agent senders), 25 as CORPORATE. Each row keeps the SAP name next to the ACoCo label; the presenter says the labels are ACoCo's |
| D-01-2 | **SuccessFactors `costCenter` IDs are numeric and do not exist in S/4** (244 values, e.g. `6871355`), so People Intelligence cannot be joined to S/4 cost centres on value | numeric-cast error joining `costCenter` to `CostCenter` | New `OPS.MAP_SF_COSTCENTER`: every SF cost centre (incl. NULL -> `UNASSIGNED`) dealt to one delivery cost centre, balanced by headcount (snake order over interleaved groups): 256-335 people per group. L1 `WORKFORCE` applies it |
| D-01-3 | **`payGrade` runs 61-87** (not ACoCo bill codes) and the jobs are manufacturing titles | profile of Core Workforce | `OPS.MAP_PAYGRADE_LEVEL` cuts at the cumulative distribution: 61-68 Analyst, 69-72 Consultant, 73-76 Manager, 77-81 Senior Manager, 82-87 Principal -> ~57/23/11/5/5 % (PRD design 50/27/13/7/3). Bill code spread linearly within the level. 22 people with NULL `payGrade` take the Analyst floor in L1, flagged. Job titles are not shown in the app |
| D-01-4 | **Fiscal variant `V9` = Oct-Sep, FY by end year** (FY2026 starts 2025-10-01) - no generated calendar needed (OD-3 closed) | `fiscalperiod` | V9 covers FY1996-FY2026 only; FY27 forward months (Oct 2026-Mar 2027) are generated in L2 `CORE.DT_FISCAL_MONTH` from `GEN_PARAMS` |
| D-01-5 | Validation query in the plan used `MAP_MD_GROUP.md_group`; the column is **`MD_GROUP_ID`** (names in `OPS.MD_GROUP`) | DDL | Validation SQL below uses the real column names |
