# ACoCo ProServe360 — SAP BDC × Snowflake

> **SAP is the System of Record. Snowflake is the System of Context and Reasoning.**

ProServe360 is a demo of decision support for a Partner / MD at **ACoCo**, a fictional professional-services firm of about 2,000 people. It is built on **SAP Business Data Cloud (BDC)** data products, shared zero-copy into Snowflake. Snowflake then adds context and reasoning on top: medallion layers, an ontology, semantic views, Cortex Search, a Cortex Agent, and a React command center running on Snowpark Container Services.

- **Pillars:** Operational Excellence, Value Creation and People Development, plus a ProServe360 overlay. The overlay includes a Workforce Productivity Score (WPS) and AI-adoption analytics.
- **Time model:** every hour is booked as Delivery, Bid, Learning, Admin or Bench, with targets that vary by level.
- **Demo window:** "today" is **2026-10-01**. History runs from Oct 2021 to Sep 2026 (FY22–FY26; the fiscal year runs Oct–Sep).
- **Scale:** about 1,956 people, 774 projects, 2,143 opportunities and 167 library assets.

Start with `docs/acoco_proserve_prd.md`, the master product and demo document. The presenter material is in `docs/RUNBOOK.md`, `docs/PRESENTER_CARD.md` and the Demo Playbook `.docx` files.

## Architecture

```
SAP BDC data products ──(zero-copy, catalog-linked DBs)──┐
                                                          ├─► L0  source (never altered)
ACOCO_SIM  (seeded synthetic, BDC-shaped gap fill) ───────┘
        │
        ▼
ACOCO_L1   views by domain: ORGANISATION, FINANCE, PROJECTS, TIME, SALES,
           WORKFORCE, TALENT, ASSETS, AI_TELEMETRY
        │
        ▼
ACOCO_L2   CORE · ONTOLOGY (ENT_/REL_/ONT_) · marts as dynamic tables (DT_*)
           REASONING (Cortex Search) · SEMANTIC (semantic views)
           SERVING (app contract) · QUALITY
        │
        ├─► Cortex Agent  ACOCO_DB.AGENT.ACOCO_ADVISOR
        │     (5 Cortex Analyst tools + 1 Cortex Search tool)
        └─► SPCS service  ACOCO_DB.APP.ACOCO_COMMAND_CENTER
              (React + Vite + Tailwind + Recharts / Express, Node 20)
```

| Object | Purpose |
|---|---|
| `ACOCO_DB` | Control plane: `OPS` (config, generator parameters, mapping tables), `AGENT`, `APP` (image repo `IMAGES`, service) |
| `ACOCO_SIM` | Synthetic data loaded by `gen/`; run metadata goes to `_META.GEN_RUN` |
| `ACOCO_L1` | Domain views over L0 and SIM, generated from `tools/l1_map.yml` |
| `ACOCO_L2` | Marts: WORKFORCE_PERFORMANCE, PROJECT_DELIVERY, PIPELINE_PRESALES, AI_ADOPTION, PORTFOLIO_360, WPS. Search services: `CSS_PROJECT_COMMENTARY`, `CSS_ASSET_LIBRARY` |
| Warehouses / compute | `WH_ACOCO_BUILD`, `WH_ACOCO_APP`, compute pool `ACOCO_POOL` |
| Roles | Everything is built as `ACCOUNTADMIN`. The app runs as `ACOCO_APP_ROLE`, which can read only L2, the agent and Cortex |

## Repository layout

| Path | Contents |
|---|---|
| `sql/00_control` | Databases, warehouses, roles, OPS config |
| `sql/01_l0_sim` | DDL for the synthetic L0 tables |
| `sql/02_l1/<domain>` | Generated L1 views (`_all.sql` for each domain) |
| `sql/03_l2` | L2 build in numeric order; `post/` holds serving extras, `semantic/` the semantic-view YAMLs |
| `sql/05_service` | SPCS service DDL |
| `sql/rebuild_from_checkpoint.sql` | Rebuilds the stack after a rollback |
| `gen/` | Deterministic data generator (`run.py`, `acoco_gen.py`, `calendar_.py`, `sfio.py`) |
| `agent/`, `cortex_project/` | Cortex Agent spec and Cortex project manifest |
| `service/app/` | Command-center app (`client/` React pages, `server/` Express API, `Dockerfile`, `.env.example`) |
| `tools/` | Build, deploy, validate, checkpoint and demo scripts |
| `plan/` | Checkpoint process, recorded deviations, measured story anchors |
| `docs/` | PRD, runbook, presenter card, playbooks, P6 productivity spec and impact docs |

## Prerequisites

- A Snowflake account with Cortex (Analyst, Search, Agents) and SPCS. Optional: an SAP BDC connector that shares the BDC data products.
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) with a configured connection (key-pair/JWT recommended).
- Python 3.11+, plus Docker and Node 20 for the app.

```bash
python -m venv .venv
.venv/bin/pip install -r gen/requirements.txt
export ACOCO_CONNECTION=<your_snow_cli_connection>
```

## Build

Run the steps in order. Use the `.venv` Python and run shell scripts with `bash tools/<script>.sh`.

```bash
# 1. Control plane
snow sql -c $ACOCO_CONNECTION -f sql/00_control/<each file in order>

# 2. Synthetic L0 (seed 20261001, ~3.8M rows)
snow sql -c $ACOCO_CONNECTION -f sql/01_l0_sim/<files>
.venv/bin/python gen/run.py --check     # determinism check (generates twice, compares hashes)
.venv/bin/python gen/run.py --load      # writes ACOCO_SIM
.venv/bin/python gen/run.py --stats     # stats only, no load

# 3. L1 views
.venv/bin/python tools/gen_l1.py

# 4. L2: core, ontology, marts, reasoning, serving
.venv/bin/python tools/build_l2.py      # re-run after any SIM reload (dynamic tables must be rebuilt)

# 5. Semantic views and agent
.venv/bin/python tools/gen_semantic.py --render && .venv/bin/python tools/gen_semantic.py --deploy
.venv/bin/python tools/gen_agent.py --render && .venv/bin/python tools/gen_agent.py --deploy
.venv/bin/python tools/gen_agent.py --regress   # agent regression questions

# 6. App: build linux/amd64 image, push to ACOCO_DB.APP.IMAGES, create service
#    (see docs/RUNBOOK.md for the full image push steps)
snow sql -c $ACOCO_CONNECTION -f sql/05_service/01_service.sql
```

To run the app locally, copy `service/app/.env.example` to `.env`. Then set `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PRIVATE_KEY_PATH`, `SNOWFLAKE_ROLE` and `SNOWFLAKE_WAREHOUSE`. The server listens on `PORT` (default 3001).

## Validate

```bash
.venv/bin/python tools/validate.py --all          # mart reconciliation, story anchors, reasoning, presenter card
.venv/bin/python tools/validate.py --step marts --report
.venv/bin/python tools/gate.py cp<nn>             # per-checkpoint gates (cp10 = app checks)
.venv/bin/python tools/verify_semantic.py
.venv/bin/python tools/preflight.py               # pre-demo checks
```

The measured story anchors are written to `plan/measured_anchors.md`.

## Checkpoints and rollback

```bash
bash tools/checkpoint.sh <nn> "<title>" [DB ...]   # gate, then zero-copy clone, export DDL, commit, tag cp-<nn>, push
bash tools/checkpoint.sh --prune [--dry-run]       # keep only the last 3 checkpoint clones
bash tools/rollback.sh <nn> [--yes]                # branch from the tag, restore clones, rebuild
```

Notes:
- Clones don't carry Cortex Search services, and cloned dynamic tables start SUSPENDED. `rebuild_from_checkpoint.sql` handles both (see `plan/deviations.md`).
- `backup/` and `logs/` are gitignored in this public repo. Rollback reads `backup/cp<nn>/clones.txt`, so keep that file locally.

## Running a demo

Before a demo, resume `ACOCO_POOL` and then the service. Afterwards, suspend both to stop spend. `docs/RUNBOOK.md` has the details, and `docs/PRESENTER_CARD.md` has the story beats.

## Data disclaimer

ACoCo is fictional. Every person, project, opportunity and AI-telemetry record in `ACOCO_SIM` is synthetic, produced by a seeded generator. Where real SAP demo-tenant data is used, keys are masked or remapped through `ACOCO_DB.OPS.MAP_*` tables.
