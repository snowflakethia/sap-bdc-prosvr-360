# Vendored skeleton

Copied unchanged in CP-00 from `snowflakethia/sap-bdc-supply-chain-360` at commit `d8a6823`
(`git archive HEAD service/app`, tracked files only: 57 files, no `node_modules`, no build output).

It still references the Supply Chain 360 objects (`APP_DATA.*`, `SAP_SUPPLY_CHAIN.*`, `APP_REF.*`, 50 occurrences in
`server/src`) and SC360 pages. Nothing here is built or deployed until CP-09, which replaces the pages, the registry
and every object reference with the ACoCo `ACOCO_L2.SERVING` / `SEMANTIC` / `ONTOLOGY` interface (PRD 8) and
enforces that with `tools/lint_app.py`.

Credentials: the server reads `SNOWFLAKE_PRIVATE_KEY_PATH` (local dev) or the SPCS OAuth token at runtime; no
secret is stored in this tree.
