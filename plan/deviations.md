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
