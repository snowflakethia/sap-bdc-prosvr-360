# ACoCo ProServe360 - Implementation Checkpoint Plan

**Implements:** `docs/acoco_proserve_prd.md` v2.3
**Account:** `SFSEAPAC.SNOWFLAKE_SAP_APJ`, role `ACCOUNTADMIN`, connection `sfseapac_kp` (key-pair JWT, user `BTHIA`; reused from `sap-bdc-supply-chain-360`, verified 2026-10-27)
**Status:** plan only - nothing has been executed

## How checkpoints work

Each checkpoint (CP) ends in the same four steps. The agent does steps 1-2 and then **stops**; the human does step 3;
step 4 runs only after the human says "CP-nn approved".

1. **Gate** - automated checks run (`python tools/gate.py cp<nn>`); results are logged to
   `ACOCO_L2.QUALITY.Q_CHECK_RESULTS` (or to `logs/gate_cp<nn>.json` before that table exists). A failed gate stops
   the checkpoint; it is not presented for validation.
2. **Backup** - `bash tools/checkpoint.sh <nn> "<title>" [DB ...]` (scripts run via `bash`; see `plan/deviations.md` D-00-4):
   - zero-copy clones of the **data-bearing** ACoCo databases changed in this CP:
     `CREATE DATABASE ACOCO_BKP_CP<nn>_<DB> CLONE <DB>;` (exact names only; CLDs and the connector are never cloned,
     altered or dropped - PRD 4.2);
   - exports DDL that a clone may not carry reliably (Semantic Views, agent, Cortex Search, service spec) to
     `backup/cp<nn>/*.sql` via `GET_DDL` / `DESCRIBE`;
   - `git add -A && git commit -m "CP-<nn>: <title>" && git tag cp-<nn> && git push --follow-tags`.
3. **Human validation** - at most 3 checks, listed per CP below, each with the exact command and the expected result.
4. **Approve** - the human replies "CP-nn approved" (or "CP-nn rejected: <reason>"). Only then does the next CP start.

**Rollback to CP-nn** (`bash tools/rollback.sh <nn>`, run only on the human's instruction):

```bash
git checkout cp-<nn>                                   # code, SQL, generator, app at that checkpoint
snow sql -c sfseapac_kp -q "CREATE OR REPLACE DATABASE ACOCO_SIM CLONE ACOCO_BKP_CP<nn>_ACOCO_SIM;"   # data, if cloned
snow sql -c sfseapac_kp -f sql/rebuild_from_checkpoint.sql   # re-creates L1 views, L2 DTs, SVs, agent from the tag
```

L1 (views) and L2 (dynamic tables, Semantic Views) are fully reproducible from git and `ACOCO_SIM`, so `ACOCO_SIM`
and `ACOCO_DB.OPS` (configuration) are the only data that must be restored from a clone. Clones of `ACOCO_L1`/
`ACOCO_L2` are taken anyway for fast rollback. **Retention:** the last three CP clones are kept; older ones are
dropped only after the human confirms (`tools/checkpoint.sh --prune`).

**Known limits (to verify in CP-00, not assumed):** whether `CREATE DATABASE ... CLONE` carries Semantic Views,
Cortex Search services and dynamic-table refresh state on this account. Where it does not, the `backup/cp<nn>/*.sql`
DDL and the git tag are the rollback path.

## Repository layout created in CP-00

```
sql/
  00_control/   ACOCO_DB, warehouses, pool, image repo, OPS config
  01_l0_sim/    ACOCO_SIM schemas (DDL); data loaded by gen/
  02_l1/        generated L1 domain views (tools/gen_l1.py)
  03_l2/        core, ontology, marts, reasoning, semantic, serving, quality
  04_agent/     ACOCO_ADVISOR
  05_service/   compute pool + service DDL
  rebuild_from_checkpoint.sql
gen/            seeded synthetic data generator (ACOCO_SIM)
tools/          gate.py, checkpoint.sh, rollback.sh, gen_l1.py, l1_map.yml, gen_ontology.py, validate.py, lint_app.py
service/app/    React + Express (from SC360 skeleton)
backup/cp<nn>/  exported DDL per checkpoint
logs/           gate results before QUALITY exists
plan/checkpoints.md   this file (status column updated at each CP)
```

## Checkpoint overview

| CP | Title | PRD | Creates in Snowflake | Data cloned at backup |
|---|---|---|---|---|
| 00 | Repo scaffold and read-only preflight | 12 B0, App. A | nothing | - |
| 01 | Control plane and configuration | 5.4, 6.1, B1 | `ACOCO_DB`, warehouses, pool (suspended), image repo, `OPS` maps and targets | `ACOCO_DB` |
| 02 | L0 gap-fill: synthetic data in `ACOCO_SIM` | 4.3, 6.2, B2 | `ACOCO_SIM` | `ACOCO_SIM` |
| 03 | L1 data domains | 7.1, B3 | `ACOCO_L1` (9 schemas, views) | `ACOCO_L1` |
| 04 | L2 core and ontology entities | 5.3, 7.2, B4 | `ACOCO_L2.CORE`, `ONTOLOGY.ENT_*`, `REL_*` | `ACOCO_L2` |
| 05 | L2 marts, serving and quality | 2.7, 7.2, 6.3 | 5 marts, `SERVING`, `QUALITY` | `ACOCO_L2` |
| 06 | L2 reasoning | 9, R1-R3, R12-R14 | `REASONING` (ML, CSS, match views) | `ACOCO_L2` |
| 07 | Semantic Views and ontology registry | 5.3, 7.2 | `SEMANTIC` (5 SVs), `ONTOLOGY.ONT_*` | `ACOCO_L2` + SV DDL |
| 08 | Cortex Agent and regression | 10, B5 | `ACOCO_DB.AGENT.ACOCO_ADVISOR` | agent DDL |
| 09 | Command Center app (local) | 8, B6 | nothing new | - (git only) |
| 10 | SPCS deployment | 8.5, B7 | image, service, endpoint | service spec |
| 11 | Demo readiness | 6.3, 11, B8 | nothing new | final tag `v1.0-demo` |

---

## CP-00 - Repo scaffold and read-only preflight

**Agent does**
- Creates the repository layout above, `tools/gate.py`, `tools/checkpoint.sh`, `tools/rollback.sh`, `.gitignore`
  additions (`logs/`, `.venv/`, `node_modules/`, secrets).
- Vendors the SC360 app skeleton (`service/app`) from the local clone - no build yet.
- Runs read-only preflight SQL and writes `logs/preflight.json`: CLD list and row counts (PRD 3.1, 3.3, App. A),
  connector status, available Cortex models, whether names in 5.4 are free, clone behaviour test on a scratch
  database (`ACOCO_SCRATCH_CLONETEST`, dropped afterwards) for Semantic View / DT / CSS.
- Records any deviation from the PRD in `plan/deviations.md`.

**Gate:** all 17 CLDs in App. A exist and are readable; connector `CONNECTED`; no existing object named `ACOCO_*`
except the scratch test.

**Human validation**
1. Confirm the CLDs and connector are as the PRD expects:
   ```sql
   SHOW DATABASES LIKE '%\_V1';
   SELECT SYSTEM$ZEROCOPY_CONNECTOR_LIST_SHARES('SAP_BDC_CONNECTOR_APJ.PUBLIC.SNOWFLAKE_APJ');
   ```
   Expected: the four People Intelligence and 13 S/4HANA `_V1` databases are listed; shares returned without error.
2. Read `logs/preflight.json` and `plan/deviations.md` (`cat logs/preflight.json | jq '.models, .clone_test'`).
   Expected: at least one agent-capable model; clone test states which object types survive a clone.
3. Review the scaffold: `git show --stat cp-00` - folders as listed above, no data files, no secrets.

**Rollback:** delete the repo changes (`git reset --hard cp-00~1` before tagging); nothing exists in Snowflake.

---

## CP-01 - Control plane and configuration

**Agent does**
- `sql/00_control/`: `ACOCO_DB` (`OPS`, `AGENT`, `APP`), `WH_ACOCO_BUILD`, `WH_ACOCO_APP`, `ACOCO_POOL`
  (created then immediately suspended), `ACOCO_DB.APP.IMAGES`.
- `OPS` configuration tables: `GEN_PARAMS` (window, seed, headcount, rates, time targets by level from PRD 2.1),
  `AS_OF_CONTROL` (2026-10-01), `MAP_MD_GROUP` (six groups -> real cost-centre hierarchy nodes in `COSTCENTER_V1`),
  `MAP_PAYGRADE_LEVEL` (`payGrade` in `COREWORKFORCEDATA_V1` -> level / bill code).
- Fiscal-calendar decision (PRD 6.1, OD-3): picks an October-start variant in `FISCALYEAR_V1` or records the
  fallback in `plan/deviations.md`.

**Gate:** every MD group maps to >= 1 cost centre; every `payGrade` present in Core Workforce maps to a level;
time targets sum to 100 % per level; pool state `SUSPENDED`.

**Human validation**
1. Check the mappings:
   ```sql
   SELECT md_group, COUNT(*) AS cost_centres FROM ACOCO_DB.OPS.MAP_MD_GROUP GROUP BY 1 ORDER BY 1;
   SELECT level, MIN(bill_code), MAX(bill_code), COUNT(*) FROM ACOCO_DB.OPS.MAP_PAYGRADE_LEVEL GROUP BY 1;
   ```
   Expected: six groups, each with >= 1 cost centre; five levels with bill codes 30-39 ... 70+.
2. Check the time targets match PRD 2.1:
   ```sql
   SELECT level, delivery, bid, learning, admin, bench, delivery+bid+learning+admin+bench AS total
   FROM ACOCO_DB.OPS.GEN_PARAMS_TIME_TARGET ORDER BY delivery DESC;
   ```
   Expected: Analyst 80/8/7/3/2 ... Principal 45/45/5/3/2; total = 100 on every row.
3. Confirm the fiscal-calendar decision and that nothing costly is running:
   `cat plan/deviations.md` and `SHOW COMPUTE POOLS LIKE 'ACOCO_POOL';` - expected state `SUSPENDED`.

**Rollback:** `DROP DATABASE ACOCO_DB; DROP WAREHOUSE WH_ACOCO_BUILD; DROP WAREHOUSE WH_ACOCO_APP; DROP COMPUTE POOL ACOCO_POOL;`
(exact names) and `git checkout cp-00`; or restore config from `ACOCO_BKP_CP01_ACOCO_DB`.

---

## CP-02 - L0 gap-fill: synthetic data in `ACOCO_SIM`

**Agent does**
- `sql/01_l0_sim/`: one schema per non-SAP source or not-yet-shared product (PRD 4.3): `CUSTOMERPROJECT`,
  `TIMESHEET`, `RESOURCEASSIGNMENT`, `OPPORTUNITY`, `INTERNALORDER`, `PROJECTCOMMENTARY`, `ASSETS`, `TELEMETRY`,
  `SKILLS`, `LEARNING`, `PERFORMANCE`, `COMPENSATION`, `SUCCESSION`, `COREWORKFORCE_BACKHISTORY`,
  `FINANCE_ACOCO` (journal lines and plan on ACoCo projects).
- `gen/` re-parameterised to 60 months (Oct 2021-Sep 2026, forward to Mar 2027), keyed to real CLD keys (cost
  centres, GL accounts, activity types, customers, `userId`), with the five time categories, AI-productivity
  effect, learning payback and asset harvest/reuse calibrated to PRD 6.2-6.3. Loaded via `write_pandas` / `COPY`.
- Determinism check: generate twice with the same seed, compare table hashes.

**Gate:** row counts within bands (~1,700 people, ~400 projects, ~800 opportunities, ~150 assets, ~6-7 M rows
total); determinism hashes equal; 100 % of foreign keys to CLD master data resolve; L0 CLDs untouched
(`ACCESS_HISTORY` shows no write).

**Human validation**
1. Volume and determinism: `python tools/validate.py --step sim --report` - expected all lines `PASS`, including
   `G2 determinism`.
2. Keys are real SAP keys, not invented ones:
   ```sql
   SELECT COUNT(*) AS orphan_cost_centres
   FROM ACOCO_SIM.TIMESHEET.TIMESHEET t
   LEFT JOIN COSTCENTER_V1."costcenter"."costcenter" c ON t.cost_center = c."CostCenter"
   WHERE c."CostCenter" IS NULL;
   ```
   Expected: `0`.
3. Spot-check the story shape on raw data:
   ```sql
   SELECT category, ROUND(100*SUM(hours)/SUM(SUM(hours)) OVER (),1) AS pct
   FROM ACOCO_SIM.TIMESHEET.TIMESHEET WHERE fiscal_year = 2026 GROUP BY 1 ORDER BY 2 DESC;
   ```
   Expected: Delivery is the largest category (~70 % of booked), Bid ~17 %, Learning ~11 %, Admin < 5 % (bench is derived later, so it does not appear here).

**Rollback:** `CREATE OR REPLACE DATABASE ACOCO_SIM CLONE ACOCO_BKP_CP02_ACOCO_SIM;` (to redo from CP-02) or
`DROP DATABASE ACOCO_SIM;` + `git checkout cp-01` (to undo CP-02).

---

## CP-03 - L1 data domains

**Agent does**
- `tools/l1_map.yml` (source column -> business name, type, key role) and `tools/gen_l1.py`; generates
  `sql/02_l1/` and creates `ACOCO_L1` with nine schemas: `ORGANISATION`, `FINANCE`, `PROJECTS`, `TIME`, `SALES`,
  `WORKFORCE`, `TALENT`, `ASSETS`, `AI_TELEMETRY` (PRD 7.1). Views only; CLD UNION SIM with `SOURCE_SYSTEM`;
  conformed keys.
- Lint `tools/gen_l1.py --lint` (D-03-7): no view references two domains, no aggregation, no `CURRENT_DATE`, no technical
  columns.

**Gate:** every view compiles; lint passes; per view, row count = sum of its L0 sources (reconciliation).

**Human validation**
1. Reconciliation report: `.venv/bin/python tools/gen_l1.py --reconcile` - expected `reconcile: 47/47 PASS`
   (per object and source: L1 rows = L0 rows in scope; declared keys unique) (D-03-7).
2. The domain layer is real and mixed-source:
   ```sql
   SELECT table_schema, COUNT(*) AS views FROM ACOCO_L1.INFORMATION_SCHEMA.VIEWS
   WHERE table_schema <> 'INFORMATION_SCHEMA' GROUP BY 1 ORDER BY 1;
   SELECT source_system, COUNT(DISTINCT person_id) FROM ACOCO_L1.WORKFORCE.WORKFORCE_JOB GROUP BY 1;
   ```
   Expected: nine schemas; `WORKFORCE_JOB` shows both `BDC_CLD` and `SIMULATED` people.
3. Open one generated view and read it: `cat sql/02_l1/workforce/workforce_job.sql` - business column names,
   `SOURCE_SYSTEM`, a `UNION ALL` of the CLD and the SIM back-history, nothing else.

**Rollback:** `DROP DATABASE ACOCO_L1;` + `git checkout cp-02` (views are regenerated from git).

---

## CP-04 - L2 core and ontology entities

**Agent does**
- `ACOCO_L2.CORE`: `DT_FISCAL_MONTH`, `VW_AS_OF`, `DT_TIME_TARGET`.
- `ACOCO_L2.ONTOLOGY`: 12 `ENT_*` dynamic tables built from the owning L1 master-data domain, and 7 `REL_*` bridge
  tables (PRD 7.2). Explicit `TARGET_LAG` per the DT rules.

**Gate:** every `ENT_*` key unique and not null; every `ENT_*` row count equals the distinct keys in its L1 source;
no L2 object references L0 (`tools/gen_ontology.py --check-refs`); all DTs `ACTIVE` with a successful refresh.

**Human validation**
1. Entity integrity: `.venv/bin/python tools/gen_ontology.py --check-refs --report` - expected `0 reference L0` and
   `ontology: 19/19 PASS` (12 entities: unique, not null, count = L1 distinct keys; 7 bridges) (D-04-3).
2. One entity end to end:
   ```sql
   SELECT level, md_group, COUNT(*) FROM ACOCO_L2.ONTOLOGY.ENT_PERSON
   WHERE is_active_as_of GROUP BY 1,2 ORDER BY 2,1;
   ```
   Expected: 1,940 active people across six groups (296-366 each); level mix 1,099 / 456 / 204 / 95 / 86
   (D-04-1: workforce = real People Intelligence users + simulated pool, CP-02).
3. Refresh health:
   ```sql
   SHOW DYNAMIC TABLES IN DATABASE ACOCO_L2;
   SELECT "schema_name", "name", "scheduling_state", "target_lag", "refresh_mode", "rows"
   FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())) ORDER BY 1, 2;
   ```
   Expected: 21 rows (2 CORE, 12 ENT_*, 7 REL_*), all `ACTIVE`, `target_lag` `1 hour`, none `DOWNSTREAM`
   (`DYNAMIC_TABLES()` lists the whole account, so `SHOW ... IN DATABASE` is used) (D-04-3).

**Rollback:** `CREATE OR REPLACE DATABASE ACOCO_L2 CLONE ACOCO_BKP_CP04_ACOCO_L2;` or `DROP DATABASE ACOCO_L2;`
+ `git checkout cp-03`.

---

## CP-05 - L2 marts, serving and quality

**Agent does**
- Five marts (`PORTFOLIO_360`, `PROJECT_DELIVERY`, `PIPELINE_PRESALES`, `WORKFORCE_PERFORMANCE`, `AI_ADOPTION`),
  fact DTs keyed to `ENT_*`, metrics per PRD 2.7.
- `SERVING.VW_*` (app interface) and `QUALITY` (`Q_CHECK_RESULTS`, freshness, completeness, `Q_LINEAGE_COUNTS`).
- `validate.py` measures every story anchor in PRD 6.3 and writes `plan/measured_anchors.md`.

**Gate:** reconciliations pass - time mix sums to 100 % per person-month (OD-11, +/- 1 %); billable hours = journal
activity quantity; overhead = 35 % of activity cost (Large-project revenue share 0.72-0.79 moved to anchor A13, D-05-1).

**Human validation**
1. Reconciliations: `.venv/bin/python tools/validate.py --step marts --report` - expected `marts: 8/8 PASS`.
2. Review the measured story figures against the design targets: `cat plan/measured_anchors.md` (re-measure with
   `.venv/bin/python tools/validate.py --step anchors --report`). Expected: each
   anchor has a measured value; any that miss their band are flagged `MISS` with a proposed fix (generator
   re-calibration goes back to CP-02, after your decision).
3. Spot-check the overlay figure the demo opens with:
   ```sql
   SELECT level, delivery_pct, bid_pct, learning_pct, admin_pct, bench_pct,
          delivery_target_pct, bench_target_pct
   FROM ACOCO_L2.SERVING.VW_TIME_MIX_FY WHERE md_group = 'Financial Services' AND fiscal_year = 2026;
   ```
   Expected: shares sum to 100 (+/- 0.1 rounding); bench 1.0-1.4 %, below the 2 % target (bench < 3 %, D-02-12);
   admin < 5 %; Delivery and Bid fall with level (Analyst ~77 / 11, Principal ~35 / 52).

**Rollback:** restore `ACOCO_BKP_CP05_ACOCO_L2`, or re-run `sql/03_l2/` from `cp-04`.

---

## CP-06 - L2 reasoning

**Agent does**
- `REASONING`: `DT_ATTRITION_RISK` (Snowflake ML classification + top drivers), `FC_DEMAND_BY_SKILL`
  (`SNOWFLAKE.ML.FORECAST`), `VW_BENCH_TO_PIPELINE_MATCH` (`AI_EMBED` similarity, R1), `VW_ASSET_MATCH` (R12),
  `CSS_PROJECT_COMMENTARY`, `CSS_ASSET_LIBRARY`.
- AI productivity (R13) and learning payback (R14) are confirmed in `AI_ADOPTION` with confidence intervals.

**Gate:** attrition model AUC recorded and > 0.70 on the hold-out; forecast produced for every skill family; both
search services `ACTIVE` and return results; R13 shows a non-significant effect for the skilled-but-inactive
stratum.

**Human validation**
1. Model and forecast quality: `.venv/bin/python tools/validate.py --step reasoning --report` - expected
   `reasoning: 8/8 PASS` (AUC, forecast coverage, both search services, R13, R14, R1, R12).
2. Ask the search service a "why" question:
   ```sql
   SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('ACOCO_L2.REASONING.CSS_PROJECT_COMMENTARY',
     '{"query":"why is the project behind schedule","columns":["PROJECT_ID","NOTE_DATE","SEARCH_TEXT"],
       "filter":{"@and":[{"@eq":{"MD_GROUP_ID":"FS"}},{"@eq":{"RAG_STATUS":"RED"}}]},"limit":3}'))['results'];
   ```
   Expected: three RED notes on `P-0615` (FS Large Data Migration, fixed price) - migration scripting behind plan,
   late client data / staffing gap. Unfiltered, the firm-wide top hits are other projects' slip notes (D-06-8).
3. The AI-productivity test is honest:
   ```sql
   SELECT stratum, ai_band, uplift, ci_low, ci_high, significant
   FROM ACOCO_L2.SERVING.VW_AI_PRODUCTIVITY_TEST WHERE fiscal_year = 2026 AND scope = 'FS' ORDER BY stratum, ai_band;
   ```
   Expected: `ALL LEVELS` AI_ACTIVE uplift ~+0.12, CI ~[+0.10, +0.14], `TRUE`; `ALL LEVELS` SKILLED_INACTIVE ~+0.03,
   CI spans zero, `FALSE`. Small level strata (Principal n 6, Consultant skilled-inactive n 6) are noisy.

**Rollback:** restore `ACOCO_BKP_CP06_ACOCO_L2` (or `DROP` the `REASONING` objects and re-run from `cp-05`).

---

## CP-07 - Semantic Views and ontology registry

**Agent does**
- `SEMANTIC`: five Semantic Views whose dimensions are the shared `ENT_*` tables and whose facts are the mart's
  `DT_*` only; metrics from PRD 2.7; verified queries per story.
- `tools/gen_ontology.py` generates `ONTOLOGY.ONT_ENTITY`, `ONT_RELATIONSHIP`, `ONT_METRIC` from
  `DESCRIBE SEMANTIC VIEW`, and runs `--check` (PRD 7.2 rule 5).
- Exports SV DDL to `backup/cp07/`.

**Gate:** `gen_ontology.py --check` passes; every verified query in each SV executes; Cortex Analyst answers one
question per SV with SQL that runs.

**Human validation**
1. Ontology check: `.venv/bin/python tools/gen_ontology.py --check` - expected `check: 0 errors`, with a summary of
   13 entities (12 + fiscal month), 18 relationships and 64 metrics, each mapped to a pillar (D-07-2).
2. Ask Cortex Analyst a cross-entity question through one Semantic View (Snowsight > AI & ML > Cortex Analyst, or):
   ```sql
   SELECT * FROM SEMANTIC_VIEW(ACOCO_L2.SEMANTIC.SV_WORKFORCE_PERFORMANCE
     DIMENSIONS person.person_level METRICS scorecard.bench_pct, scorecard.delivery_pct
     WHERE md_group.md_group = 'Financial Services' AND fiscal_month.fiscal_year = 2026);
   ```
   Expected: five rows (one per level), the same figures as `SERVING.VW_TIME_MIX_FY` (e.g. Analyst Delivery ~76 %,
   bench ~1.5 %; Principal Delivery ~35 %).
3. Review the registry the dashboard will draw:
   ```sql
   SELECT from_entity, verb, to_entity, semantic_views FROM ACOCO_L2.ONTOLOGY.ONT_RELATIONSHIP ORDER BY 1;
   ```
   Expected: 18 relationships (PRD 5.3's 16, with "books time to category on project / opportunity" split into three),
   each with a non-empty `semantic_views`.

**Rollback:** re-create the SVs from `backup/cp06/` (none) or `backup/cp07/*.sql` of the previous approved state;
`git checkout cp-06`.

---

## CP-08 - Cortex Agent and regression

**Agent does**
- `tools/gen_agent.py` -> `ACOCO_DB.AGENT.ACOCO_ADVISOR`: 5 Cortex Analyst tools + 2 Cortex Search tools, PRD 10
  instructions (pillars, time targets, as-of, honesty rules), entity -> Semantic View map from `ONT_RELATIONSHIP`.
- Regression suite of 20 prompts (PRD 10) with routing, figure and latency assertions; report in
  `logs/agent_regression.md`.

**Gate:** 20/20 routing correct; figures within tolerance of `measured_anchors.md`; p90 latency recorded.

**Human validation**
1. Read `logs/agent_regression.md` - expected 20/20 `PASS`; latency table present.
2. Ask two questions yourself in Snowflake Intelligence, or from the terminal with
   `cortex agents run ACOCO_DB.AGENT.ACOCO_ADVISOR "<question>" -c sfseapac_kp`:
   - *"Give me my FY26 ProServe360 scorecard against FY25."* -> expected: one figure per pillar, sources cited.
   - *"Which bench consultants with AI skill 3+ fit my open bids above USD 5 M?"* -> expected: a named list that
     uses the Pipeline and Workforce tools together.
3. Honesty check: ask *"Does AI make my skilled-but-inactive consultants more productive?"* (same command) - expected:
   "no significant effect" (~+2.6 %, 90 % CI ~-0.5 % to +5.8 %), stated as an association, not a cause.

**Rollback:** `CREATE OR REPLACE AGENT ... FROM backup/cp07/agent.sql` (previous) or `DROP AGENT` +
`git checkout cp-07`.

---

## CP-09 - Command Center app (local)

**Agent does**
- Builds `service/app` on the SC360 skeleton: context pages C1-C4 (incl. the ontology graph), P0-P11, Ask Cortex,
  Advisor streaming; server registry (`server/src/registry.sql`) and API (PRD 8.4).
- `tools/lint_app.py`: no `*_V1`, `ACOCO_SIM.`, `ACOCO_L1.`, or any `ACOCO_L2` schema other than `SERVING`,
  `SEMANTIC`, `ONTOLOGY` in `service/`; every registry statement identical to `tools/demo_queries.sql`; bind
  variables only.
- Runs locally against the account with key-pair auth via connection `sfseapac_kp`.

**Gate:** lint passes; `npm run build` succeeds; every `/api/*` route returns 200 with data in < 3 s locally.

**Human validation**
1. `python tools/lint_app.py && (cd service/app && npm run build)` - expected `lint: 0 violations`, build succeeds.
2. Run it and walk the pages: `cd service/app && npm run dev`, open `http://localhost:8080` - C1 opens first;
   check C4 (ontology graph renders, an entity click shows L0 -> L1 -> L2) and P0 (time-mix bar vs target).
3. Fee-boundary evidence from your local session:
   ```sql
   SELECT DISTINCT f.value:"objectName"::string AS object
   FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY ah
   JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q ON q.query_id = ah.query_id,
   LATERAL FLATTEN(ah.base_objects_accessed) f
   WHERE q.query_tag = 'ACOCO_APP' AND ah.query_start_time > DATEADD(hour,-3,CURRENT_TIMESTAMP())
   ORDER BY 1;
   ```
   Expected (base objects = the tables beneath the views): only `ACOCO_L2.*` tables (ONTOLOGY, the five marts,
   CORE, QUALITY, REASONING) plus `ACOCO_DB.OPS.AS_OF_CONTROL` (the as-of date read inside `VW_DEMAND_FORECAST`);
   no `_V1` CLD table, no `ACOCO_SIM` and no `ACOCO_L1`. (Corrected at CP-09: the JOIN must precede the FLATTEN.) (`ACCESS_HISTORY` latency can be up to ~3 h; re-check later if empty.)

**Rollback:** `git checkout cp-08` (no Snowflake change in this CP).

---

## CP-10 - SPCS deployment

**Agent does**
- Builds the `linux/amd64` image, pushes to `ACOCO_DB.APP.IMAGES`, resumes `ACOCO_POOL`, creates
  `ACOCO_DB.APP.ACOCO_COMMAND_CENTER` (PRD 8.5), waits for `READY`; writes the warm-up / suspend runbook
  `docs/RUNBOOK.md`; exports the service spec to `backup/cp10/`.

**Gate:** service `READY`; `/healthcheck` 200 through the endpoint; every page < 3 s warm; first paint < 2 s.

**Human validation**
1. Status and URL:
   ```sql
   SELECT SYSTEM$GET_SERVICE_STATUS('ACOCO_DB.APP.ACOCO_COMMAND_CENTER');
   SHOW ENDPOINTS IN SERVICE ACOCO_DB.APP.ACOCO_COMMAND_CENTER;
   ```
   Expected: `READY`; one public `ui` endpoint URL.
2. Open the URL, log in with Snowflake, and repeat CP-09 check 2 on the deployed app (C1, C4, P0, P10 one
   question).
3. Suspend and resume once, following `docs/RUNBOOK.md`, and confirm the pool reaches `SUSPENDED` - proves the
   cost control works before the demo.

**Rollback:** `ALTER SERVICE ... FROM SPECIFICATION` with the previous image tag, or `DROP SERVICE` +
`ALTER COMPUTE POOL ACOCO_POOL SUSPEND`; `git checkout cp-09`.

---

## CP-11 - Demo readiness

**Agent does**
- Replaces every design-target figure in PRD 6.3 and section 11 with the **measured** value (archiving the PRD
  first: `docs/archive/acoco_proserve_prd_v2.3_<timestamp>.md`); writes the presenter card `docs/PRESENTER_CARD.md`
  (measured figures only, source object per figure).
- One scripted dry run of the 30-minute flow with timings; final tag `v1.0-demo`; prunes old clones (with your
  confirmation).

**Gate:** `validate.py --all` passes; no figure on the presenter card without a `validate.py` assertion; agent
regression 20/20 re-run on the final build.

**Human validation**
1. Read `docs/PRESENTER_CARD.md` against the app (each figure shows the page and object it comes from).
2. Rehearse the demo once yourself, following PRD section 11, in <= 30 minutes; note any beat that fails.
3. Approve the clone clean-up list (`tools/checkpoint.sh --prune --dry-run`) and the final tag
   (`git show v1.0-demo --stat`).

**Rollback:** any earlier tag via `tools/rollback.sh <nn>`.

---

## Status

| CP | Status | Tag | Approved by / date | Notes |
|---|---|---|---|---|
| 00 | approved | cp-00 | Boon Sing Thia, 2026-10-27 | gate 8/8; deviations D-00-1..8 |
| 01 | approved | cp-01 | Boon Sing Thia, 2026-10-27 | gate 8/8; D-01-1..5; MD = role of 6 Principals (decision 2026-10-27) |
| 02 | approved | cp-02 | Boon Sing Thia, 2026-10-27 | gate 11/11; D-02-1..13; targets revised (Bid ~15, Learning 10); bench < 3 % |
| 03 | approved | cp-03 | Boon Sing Thia, 2026-10-27 | gate 9/9; reconcile 47/47; D-03-1..7 |
| 04 | approved | cp-04 | Boon Sing Thia, 2026-10-27 | gate 8/8; ontology 19/19; D-04-1..5 |
| 05 | approved | cp-05 | Boon Sing Thia, 2026-10-27 | gate 7/7; marts 8/8; anchors 4/13 OK, 9 MISS (decision); D-05-1..10 |
| 06 | approved | cp-06 | Boon Sing Thia, 2026-10-27 | gate 11/11; reasoning 8/8; anchors 9/13; D-06-1..10 |
| 07 | approved | cp-07 | Boon Sing Thia, 2026-10-27 | gate 6/6; ontology check 0 errors; D-07-1..5 |
| 08 | approved | cp-08 | Boon Sing Thia, 2026-10-28 | gate 5/5; regression 20/20; p90 84 s; D-08-1..4 |
| 09 | approved 2026-10-28 | cp-09, cp-09.1 | UI: Business Group label, (i) metric popovers (D-09-11) |
| 10 | not started | | | |
| 11 | not started | | | |
