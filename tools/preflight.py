"""CP-00 read-only preflight. Writes logs/preflight.json.

Checks: the 17 CLDs the PRD uses (existence, kind, row count of the key tables), connector status and shares,
availability of the ACoCo object names, Cortex model availability, and which object types survive
`CREATE DATABASE ... CLONE` (tested on a scratch database that is dropped afterwards).
Only the scratch database ACOCO_SCRATCH_CLONETEST(_C) is ever created; CLDs are only read.
"""
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sf  # noqa: E402

CONNECTOR = "SAP_BDC_CONNECTOR_APJ.PUBLIC.SNOWFLAKE_APJ"

# CLD -> key tables (PRD 3.1, 3.3, Appendix A)
CLDS = {
    "COREWORKFORCEDATA_V1": ["coreworkforcedata.coreworkforce_standardfields"],
    "EMPLOYEEAVAILABILITY_V1": ["employeeavailability.employeeavailability"],
    "WORKFORCEPLANNEDWORKINGTIME_V1": ["workforceplannedworkingtime.plannedworkingtime"],
    "ASSIGNMENTADDITIONALINFORMATION_V1": ["assignmentadditionalinformation.jobrelationship"],
    "ENTRYVIEWJOURNALENTRY_V1": ["entryviewjournalentry.operationalacctgdocitem"],
    "JOURNALENTRYHEADER_V1": ["journalentryheader.journalentry"],
    "JOURNALENTRYCODES_V1": [],
    "JOURNALENTRYITEMCODES_V1": [],
    "PROJECT_V1": ["project.project", "project.workbreakdownstructureelement", "project.wbselementmilestone"],
    "FINANCIALPLANNINGENTRYITEM_V1": ["financialplanningentryitem.financialplanningentryitem"],
    "COSTCENTER_V1": ["costcenter.costcenter"],
    "COSTCENTERACTIVITYTYPE_V1": ["costcenteractivitytype.costcenteractivitytype"],
    "PROFITCENTER_V1": ["profitcenter.profitcenter"],
    "GENERALLEDGERACCOUNT_V1": ["generalledgeraccount.generalledgeraccount"],
    "CUSTOMER_V1": ["customer.customer"],
    "SALESCONTRACT_V1": ["salescontract.salescontract", "salescontract.salescontractitem"],
    "FISCALYEAR_V1": ["fiscalyear.fiscalperiod"],
}

ACOCO_NAMES = {
    "databases": ["ACOCO_DB", "ACOCO_SIM", "ACOCO_L1", "ACOCO_L2"],
    "warehouses": ["WH_ACOCO_BUILD", "WH_ACOCO_APP"],
    "compute_pools": ["ACOCO_POOL"],
}

MODELS = ["claude-sonnet-4-5", "claude-haiku-4-5", "llama3.3-70b", "claude-4-sonnet", "claude-3-5-sonnet", "mistral-large2"]


def safe(fn):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 - recorded, not raised
        return {"error": str(e)[-500:]}


def cld_checks():
    dbs = {r["name"]: r for r in sf.query("show databases")}
    out = {}
    for db, tables in CLDS.items():
        r = dbs.get(db)
        entry = {"exists": r is not None, "kind": r and r.get("kind"), "tables": {}}
        if r:
            schemas = safe(lambda: [s["name"] for s in sf.query(f"show schemas in database {db}")])
            entry["schemas"] = schemas
            for t in tables:
                sch, tab = t.split(".")
                entry["tables"][t] = safe(
                    lambda: sf.query(f'select count(*) as n from {db}."{sch}"."{tab}"')[0]["N"])
        out[db] = entry
    return out


def connector_checks():
    return {
        "show": safe(lambda: sf.query("show zerocopy connectors in account")),
        "shares": safe(lambda: sf.query(
            f"select system$zerocopy_connector_list_shares('{CONNECTOR}') as shares")[0]["SHARES"]),
    }


def name_checks():
    out = {}
    dbs = {r["name"] for r in sf.query("show databases like 'ACOCO%'")}
    whs = {r["name"] for r in sf.query("show warehouses like '%ACOCO%'")}
    pools = {r["name"] for r in sf.query("show compute pools like 'ACOCO%'")}
    for n in ACOCO_NAMES["databases"]:
        out[n] = "taken" if n in dbs else "free"
    for n in ACOCO_NAMES["warehouses"]:
        out[n] = "taken" if n in whs else "free"
    for n in ACOCO_NAMES["compute_pools"]:
        out[n] = "taken" if n in pools else "free"
    out["other_ACOCO_databases"] = sorted(dbs - set(ACOCO_NAMES["databases"]))
    return out


def model_checks():
    out = {}
    for m in MODELS:
        res = safe(lambda: sf.query(f"select snowflake.cortex.complete('{m}', 'Reply OK') as r")[0]["R"])
        out[m] = "available" if isinstance(res, str) else res
    return out


def clone_test():
    """Create scratch objects, clone the database, report which object types the clone carries."""
    src, dst = "ACOCO_SCRATCH_CLONETEST", "ACOCO_SCRATCH_CLONETEST_C"
    steps = [
        f"create or replace database {src}",
        f"create schema {src}.s",
        f"create table {src}.s.t (id int, txt varchar) as select seq4(), 'note ' || seq4() from table(generator(rowcount=>10))",
        f"create view {src}.s.v as select * from {src}.s.t",
        f"create dynamic table {src}.s.dt target_lag='1 hour' warehouse=XSMALL_WH as select id, txt from {src}.s.t",
        f"""create semantic view {src}.s.sv tables (t as {src}.s.t primary key (id))
            dimensions (t.txt as txt) metrics (t.n as count(id))""",
        f"""create cortex search service {src}.s.css on txt warehouse=XSMALL_WH target_lag='1 hour'
            as select id, txt from {src}.s.t""",
    ]
    result = {"created": {}, "in_clone": {}}
    try:
        for s in steps:
            kind = s.split()[1:4]
            result["created"][" ".join(kind)] = safe(lambda: (sf.query(s), "ok")[1])
        result["clone"] = safe(lambda: (sf.query(f"create or replace database {dst} clone {src}"), "ok")[1])
        probes = {
            "table": f"show tables in schema {dst}.s",
            "view": f"show views in schema {dst}.s",
            "dynamic_table": f"show dynamic tables in schema {dst}.s",
            "semantic_view": f"show semantic views in schema {dst}.s",
            "cortex_search": f"show cortex search services in schema {dst}.s",
        }
        for k, q in probes.items():
            rows = safe(lambda: sf.query(q))
            result["in_clone"][k] = len(rows) > 0 if isinstance(rows, list) else rows
        dts = safe(lambda: sf.query(f"show dynamic tables in schema {dst}.s"))
        if isinstance(dts, list) and dts:
            result["clone_dt_state"] = {"scheduling_state": dts[0].get("scheduling_state"),
                                        "target_lag": dts[0].get("target_lag")}
    finally:
        result["cleanup"] = {
            dst: safe(lambda: (sf.query(f"drop database if exists {dst}"), "dropped")[1]),
            src: safe(lambda: (sf.query(f"drop database if exists {src}"), "dropped")[1]),
        }
    return result


def main():
    report = {
        "run_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "connection": sf.CONNECTION,
        "identity": safe(lambda: sf.query(
            "select current_account() account, current_user() usr, current_role() role")[0]),
        "clds": cld_checks(),
        "connector": connector_checks(),
        "names": name_checks(),
        "models": model_checks(),
        "clone_test": clone_test(),
    }
    path = pathlib.Path(__file__).parent.parent / "logs" / "preflight.json"
    path.write_text(json.dumps(report, indent=2, default=str))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
