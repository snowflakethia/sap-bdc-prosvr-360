# ACoCo ProServe360 Command Center - Runbook (SPCS)

Service `ACOCO_DB.APP.ACOCO_COMMAND_CENTER` on compute pool `ACOCO_POOL` (1 x CPU_X64_XS), owned by `ACOCO_APP_ROLE`,
queries on `WH_ACOCO_APP` (XS). DDL: `sql/05_service/01_service.sql`. Image repo `ACOCO_DB.APP.IMAGES`.

URL: `SHOW ENDPOINTS IN SERVICE ACOCO_DB.APP.ACOCO_COMMAND_CENTER;` -> `ingress_url` of endpoint `ui`
(currently `https://ictbqx-sfseapac-snowflake-sap-apj.snowflakecomputing.app`). Log in with your Snowflake user;
access needs `ACOCO_APP_ROLE` or `ACCOUNTADMIN` (granted `ALL_ENDPOINTS_USAGE`).

## Pre-demo warm-up (about 5 minutes before)

```sql
USE ROLE ACCOUNTADMIN;
ALTER COMPUTE POOL ACOCO_POOL RESUME IF SUSPENDED;
ALTER SERVICE ACOCO_DB.APP.ACOCO_COMMAND_CENTER RESUME;
-- repeat until status = READY (pool start 1-3 min, container start < 1 min)
SELECT SYSTEM$GET_SERVICE_STATUS('ACOCO_DB.APP.ACOCO_COMMAND_CENTER');
```

Then open the URL, log in, and click through C1, P0, P2 and P10 once: the first request opens the service's
Snowflake session and resumes `WH_ACOCO_APP`; afterwards results are cached for 10 minutes per statement.
Optional automated check: `.venv/bin/python tools/gate.py cp10` (8 checks, ~2 min).

## Post-demo suspend (stops all compute cost)

```sql
USE ROLE ACCOUNTADMIN;
ALTER SERVICE ACOCO_DB.APP.ACOCO_COMMAND_CENTER SUSPEND;
ALTER COMPUTE POOL ACOCO_POOL SUSPEND;          -- needs the service suspended first
SHOW COMPUTE POOLS LIKE 'ACOCO_POOL';           -- state = SUSPENDED (may show STOPPING briefly)
```

`WH_ACOCO_APP` auto-suspends on its own. If forgotten, the pool keeps running (it auto-suspends only after
3600 s with no service on it), so always suspend explicitly.

## Upgrade / rollback

```bash
cd service/app
snow spcs image-registry login -c sfseapac_kp
REPO=sfseapac-snowflake-sap-apj.registry.snowflakecomputing.com/acoco_db/app/images
docker build --platform linux/amd64 -t $REPO/acoco_command_center:vN . && docker push $REPO/acoco_command_center:vN
```

Edit the image tag in `sql/05_service/01_service.sql`, then run `ALTER SERVICE ACOCO_DB.APP.ACOCO_COMMAND_CENTER
FROM SPECIFICATION $$ ... $$` (as `ACOCO_APP_ROLE`) with the spec block from that file; wait for `READY`.
Rollback = the same with the previous tag (all tags v1-v5 stay in the repo; v1 does not start - registry.sql missing).
Full removal: `DROP SERVICE ACOCO_DB.APP.ACOCO_COMMAND_CENTER; ALTER COMPUTE POOL ACOCO_POOL SUSPEND;`.

## Troubleshooting

| Symptom | Check |
|---|---|
| Status `FAILED` / restarts | `SELECT SYSTEM$GET_SERVICE_LOGS('ACOCO_DB.APP.ACOCO_COMMAND_CENTER', 0, 'app', 100);` |
| URL shows "not authorized" | Your default role needs `ACOCO_APP_ROLE` or `ACCOUNTADMIN`; or `GRANT SERVICE ROLE ACOCO_DB.APP.ACOCO_COMMAND_CENTER!ALL_ENDPOINTS_USAGE TO ROLE <role>` |
| A page errors "does not exist or not authorized" | A new ACOCO_L2 object needs a grant to `ACOCO_APP_ROLE` (re-run the grant block in `01_service.sql`) |
| First click slow (5-10 s) | Expected once after resume: Snowflake login + warehouse resume |
| Queries the app ran | `QUERY_HISTORY` with `USER_NAME = 'ACOCO_COMMAND_CENTER'`, `QUERY_TAG = 'ACOCO_APP'` |
