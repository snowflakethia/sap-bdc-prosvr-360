"""Checkpoint gates. Usage: python3 tools/gate.py cp00

Each gate returns a list of (check_id, description, expected, actual, passed). Results are written to
logs/gate_<cp>.json (and, from CP-05 on, also to ACOCO_L2.QUALITY.Q_CHECK_RESULTS). Exit code 1 if any check fails.
"""
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

REQUIRED_DIRS = ["sql/00_control", "sql/01_l0_sim", "sql/02_l1", "sql/03_l2", "sql/04_agent", "sql/05_service",
                 "gen", "tools", "backup", "logs", "service/app/server", "service/app/client", "plan"]
REQUIRED_TOOLS = ["tools/sf.py", "tools/gate.py", "tools/checkpoint.sh", "tools/rollback.sh", "tools/preflight.py"]
PREFERRED_MODELS = ["claude-sonnet-4-5", "claude-haiku-4-5"]


def gate_cp00():
    checks = []
    pf_path = ROOT / "logs" / "preflight.json"
    pf = json.loads(pf_path.read_text()) if pf_path.exists() else {}
    checks.append(("CP00-01", "preflight.json present", "exists", "exists" if pf else "missing", bool(pf)))

    clds = pf.get("clds", {})
    missing = [k for k, v in clds.items() if not v.get("exists") or v.get("kind") != "CATALOG-LINKED DATABASE"]
    checks.append(("CP00-02", "17 PRD CLDs exist as catalog-linked databases", "17 / 0 missing",
                   f"{len(clds) - len(missing)} / {len(missing)} missing {missing}", len(clds) == 17 and not missing))

    bad = {f"{db}.{t}": n for db, v in clds.items() for t, n in v.get("tables", {}).items()
           if not isinstance(n, int) or n <= 0}
    checks.append(("CP00-03", "every key CLD table readable and non-empty", "0 failures",
                   f"{len(bad)} failures {bad}", not bad))

    conn = pf.get("connector", {}).get("show", [])
    state = next((c.get("status") or c.get("state") for c in conn if isinstance(c, dict) and c.get("name") == "SNOWFLAKE_APJ"), None)
    checks.append(("CP00-04", "connector SNOWFLAKE_APJ connected", "CONNECTED", str(state), state == "CONNECTED"))

    names = pf.get("names", {})
    taken = [k for k, v in names.items() if v == "taken"] + names.get("other_ACOCO_databases", [])
    checks.append(("CP00-05", "ACoCo object names free; no stray ACOCO_* objects", "0 taken",
                   f"{len(taken)} {taken}", not taken))

    models = pf.get("models", {})
    ok = [m for m in PREFERRED_MODELS if models.get(m) == "available"]
    checks.append(("CP00-06", "an agent-capable Claude model is available", ">= 1", str(ok), bool(ok)))

    ct = pf.get("clone_test", {})
    cleaned = all(v == "dropped" for v in ct.get("cleanup", {}).values()) and ct.get("cleanup")
    checks.append(("CP00-07", "clone test ran and scratch databases were dropped", "clone ok, dropped",
                   f"clone={ct.get('clone')} cleanup={ct.get('cleanup')}", ct.get("clone") == "ok" and bool(cleaned)))

    missing_dirs = [d for d in REQUIRED_DIRS + REQUIRED_TOOLS if not (ROOT / d).exists()]
    checks.append(("CP00-08", "repository scaffold complete", "0 missing", f"{missing_dirs}", not missing_dirs))
    return checks


def gate_cp01():
    import sf
    q = sf.query
    checks = []
    CW = 'COREWORKFORCEDATA_V1."coreworkforcedata"."coreworkforce_standardfields"'

    g = q("""select m.md_group_id, count(*) n from ACOCO_DB.OPS.MD_GROUP g
             left join ACOCO_DB.OPS.MAP_MD_GROUP m on m.md_group_id = g.md_group_id and m.cc_role = 'DELIVERY'
             group by 1 order by 1""")
    short = [r["MD_GROUP_ID"] for r in g if r["N"] < 1 or r["MD_GROUP_ID"] is None]
    checks.append(("CP01-01", "six MD groups, each with >= 1 real S/4 delivery cost centre", "6 groups, 0 short",
                   f"{len(g)} groups {dict((r['MD_GROUP_ID'], r['N']) for r in g)}", len(g) == 6 and not short))

    orphan_cc = q("""select count(*) n from ACOCO_DB.OPS.MAP_MD_GROUP m
                     left join COSTCENTER_V1."costcenter"."costcenter" c
                       on c."CostCenter" = m.cost_center and c."ValidityEndDate" = '9999-12-31'
                     where c."CostCenter" is null""")[0]["N"]
    checks.append(("CP01-02", "every mapped cost centre exists in COSTCENTER_V1", "0", str(orphan_cc), orphan_cc == 0))

    pg = q(f"""select count(distinct w."payGrade") n from {CW} w
               left join ACOCO_DB.OPS.MAP_PAYGRADE_LEVEL m on m.pay_grade = w."payGrade"
               where w."payGrade" is not null and m.pay_grade is null""")[0]["N"]
    checks.append(("CP01-03", "every payGrade in Core Workforce maps to a level", "0 unmapped", str(pg), pg == 0))

    sfcc = q(f"""select count(distinct coalesce(w."costCenter"::varchar, 'UNASSIGNED')) n from {CW} w
                 left join ACOCO_DB.OPS.MAP_SF_COSTCENTER m on m.sf_cost_center = coalesce(w."costCenter"::varchar, 'UNASSIGNED')
                 where m.sf_cost_center is null""")[0]["N"]
    checks.append(("CP01-04", "every People Intelligence costCenter maps to a delivery cost centre", "0 unmapped",
                   str(sfcc), sfcc == 0))

    tt = q("select level, delivery, bid, learning, admin, bench from ACOCO_DB.OPS.GEN_PARAMS_TIME_TARGET")
    expected = {"Analyst": (75, 10, 10, 3, 2), "Consultant": (71, 14, 10, 3, 2), "Manager": (60, 25, 10, 3, 2),
                "Senior Manager": (45, 40, 10, 3, 2), "Principal": (35, 50, 10, 3, 2)}
    got = {r["LEVEL"]: tuple(float(r[k]) for k in ("DELIVERY", "BID", "LEARNING", "ADMIN", "BENCH")) for r in tt}
    ok = got == {k: tuple(float(x) for x in v) for k, v in expected.items()}
    checks.append(("CP01-05", "time targets match PRD 2.1 and sum to 100", "5 levels, PRD values",
                   str(got), ok and all(abs(sum(v) - 100) < 1e-9 for v in got.values())))

    fy = q("""select count(*) n from FISCALYEAR_V1."fiscalyear"."fiscalperiod"
              where "FiscalYearVariant" = 'V9' and "FiscalPeriod" = '001'
                and "FiscalYear" between '2022' and '2026' and month(try_to_date("FiscalPeriodStartDate")) = 10""")[0]["N"]
    checks.append(("CP01-06", "fiscal variant V9 starts in October for FY22-FY26", "5", str(fy), fy == 5))

    asof = q("select max(as_of_date)::varchar d, count(*) n from ACOCO_DB.OPS.AS_OF_CONTROL")[0]
    checks.append(("CP01-07", "as-of date is 2026-10-01", "2026-10-01 (1 row)", f"{asof['D']} ({asof['N']} row)",
                   asof["D"] == "2026-10-01" and asof["N"] == 1))

    pool = q("show compute pools like 'ACOCO_POOL'")
    whs = {r["name"]: r for r in q("show warehouses like 'WH_ACOCO%'")}
    repo = q("show image repositories in schema ACOCO_DB.APP")
    state = pool[0]["state"] if pool else None
    ok = state == "SUSPENDED" and set(whs) == {"WH_ACOCO_BUILD", "WH_ACOCO_APP"} and len(repo) == 1
    checks.append(("CP01-08", "pool suspended; both warehouses and image repo exist", "SUSPENDED, 2 wh, 1 repo",
                   f"{state}, {sorted(whs)}, {len(repo)} repo", ok))
    return checks


def gate_cp02():
    import sf
    q = sf.query
    checks = []
    det = json.loads((ROOT / "logs" / "gen_determinism.json").read_text()) \
        if (ROOT / "logs" / "gen_determinism.json").exists() else {}
    checks.append(("CP02-01", "generator determinism (two runs, identical table hashes)", "PASS",
                   "PASS" if det.get("pass") else f"FAIL {det.get('differences')}", bool(det.get("pass"))))

    load = json.loads((ROOT / "logs" / "gen_load.json").read_text())
    rows = q("""select table_schema || '.' || table_name t, row_count n from ACOCO_SIM.INFORMATION_SCHEMA.TABLES
                where table_schema not in ('INFORMATION_SCHEMA', '_META')""")
    sfc = {r["T"]: r["N"] for r in rows}
    mism = {k: (v, sfc.get(k)) for k, v in load["counts"].items() if sfc.get(k) != v}
    total = sum(sfc.values())
    checks.append(("CP02-02", "every generated table loaded with its exact row count; total 3-8 M rows",
                   "0 mismatches, 3-8 M", f"{len(mism)} mismatches {mism}; total {total:,}",
                   not mism and 3_000_000 <= total <= 8_000_000))

    st = load["stats"]
    bands = {"projects": (400, 1000), "opportunities": (800, 2600), "assets": (80, 300)}
    bad = {k: st[k] for k, (lo, hi) in bands.items() if not lo <= st[k] <= hi}
    pc = q("""select count(distinct user_id) n from ACOCO_SIM.DIRECTORY.PERSON_NAME""")[0]["N"]
    checks.append(("CP02-03", "volumes in band (projects 400-1000, opps 800-2600 (D-06-4), assets 80-300); people 3,300-3,700 (D-06-7)",
                   "in band", f"projects {st['projects']}, opps {st['opportunities']}, assets {st['assets']}, "
                              f"people {pc}", not bad and 3300 <= pc <= 3700))

    fk = q("""select
        (select count(*) from ACOCO_SIM.TIMESHEET.TIMESHEET t left join ACOCO_DB.OPS.MAP_MD_GROUP m
            on m.cost_center = t.cost_center where m.cost_center is null) cc,
        (select count(*) from ACOCO_SIM.FINANCE_ACOCO.OPERATIONALACCTGDOCITEM j
            left join (select distinct "GLAccount" g from GENERALLEDGERACCOUNT_V1."generalledgeraccount"."generalledgeraccounttext"
                       where "ChartOfAccounts" = 'YCOA') a on a.g = j."GLAccount" where a.g is null) gl,
        (select count(*) from ACOCO_SIM.FINANCE_ACOCO.OPERATIONALACCTGDOCITEM j
            left join (select "CostCtrActivityType" t from COSTCENTERACTIVITYTYPE_V1."costcenteractivitytype"."costcenteractivitytype"
                       where "ControllingArea" = 'A000' union select "CostCtrActivityType" from ACOCO_SIM.FINANCE_ACOCO.ACTIVITYTYPE_EXT) a
            on a.t = j."CostCtrActivityType" where j."CostCtrActivityType" is not null and a.t is null) act,
        (select count(*) from ACOCO_SIM.COREWORKFORCE.COREWORKFORCE_STANDARDFIELDS c
            left join ACOCO_DB.OPS.MAP_SF_COSTCENTER m on m.sf_cost_center = c."costCenter" where m.sf_cost_center is null) sfcc,
        (select count(*) from ACOCO_SIM.COREWORKFORCE.COREWORKFORCE_STANDARDFIELDS c
            left join ACOCO_DB.OPS.MAP_PAYGRADE_LEVEL m on m.pay_grade = c."payGrade" where m.pay_grade is null) pg""")[0]
    checks.append(("CP02-04", "every key resolves to real SAP / OPS master data (cost centre, GL, activity type, "
                              "SF cost centre, pay grade)", "0 orphans", str(fk), all(v == 0 for v in fk.values())))

    mix = {r["CATEGORY"]: float(r["PCT"]) for r in q(
        """select category, 100 * sum(hours) / sum(sum(hours)) over () pct from ACOCO_SIM.TIMESHEET.TIMESHEET
           where fiscal_year = 2026 group by 1""")}
    checks.append(("CP02-05", "FY26 booked time: Delivery largest, Admin < 5 % of booked hours", "Delivery max, Admin < 5",
                   str({k: round(v, 1) for k, v in mix.items()}),
                   max(mix, key=mix.get) == "DELIVERY" and mix.get("ADMIN", 99) < 5))

    md = q("""select count(*) n, count(distinct md_group_id) g,
                     count_if(l.level = 'Principal') principals
              from ACOCO_SIM.DIRECTORY.MD_ROLE r
              join (select "userId" u, max_by("payGrade", "startDate") pg from COREWORKFORCEDATA_V1."coreworkforcedata"."coreworkforce_standardfields" group by 1) w on w.u = r.user_id
              join ACOCO_DB.OPS.MAP_PAYGRADE_LEVEL l on l.pay_grade = w.pg""")[0]
    checks.append(("CP02-06", "exactly one MD per group, each a real Principal", "6 / 6 groups / 6 Principals",
                   f"{md['N']} / {md['G']} / {md['PRINCIPALS']}", md["N"] == 6 and md["G"] == 6 and md["PRINCIPALS"] == 6))

    loss = q("""select p.project_id,
                  sum(iff(j."GLAccount" = '0041000000', -j."AmountInCompanyCodeCurrency", 0)) rev,
                  sum(iff(j."GLAccount" <> '0041000000' and j."WBSElement" is not null, j."AmountInCompanyCodeCurrency", 0)) cost
                from ACOCO_SIM.CUSTOMERPROJECT.CUSTOMER_PROJECT p
                join ACOCO_SIM.FINANCE_ACOCO.OPERATIONALACCTGDOCITEM j on left(j."WBSElement", 6) = p.project_id
                where p.seeded_story = 'FS_LOSS' and p.md_group_id = 'FS' and p.contract_type = 'FIXED_PRICE'
                group by 1""")
    ok = len(loss) == 1 and loss[0]["COST"] > loss[0]["REV"]
    checks.append(("CP02-07", "story project: one FS Large fixed-price project with total cost > revenue",
                   "1 project, cost > revenue", str(loss), ok))

    writes = q("""select count(*) n from SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY ah, lateral flatten(ah.objects_modified) f
                  where ah.query_start_time > dateadd(day, -2, current_timestamp())
                    and f.value:"objectName"::string ilike any ('%\\_V1.%', 'SAP\\_BDC\\_CONNECTOR\\_APJ.%')
                    and ah.user_name = current_user()""")[0]["N"]
    checks.append(("CP02-08", "no write by this user to any CLD or the connector (ACCESS_HISTORY, 2 days)", "0",
                   str(writes), writes == 0))

    fy26 = load["stats"]["FY26_firm"]
    bid, learn = float(fy26["bid"]), float(fy26["learning"])
    checks.append(("CP02-09", "FY26 firm share of available hours: Bid 12-18 %, Learning 8-12 % (D-02-11)",
                   "Bid 12-18, Learning 8-12", f"Bid {bid}, Learning {learn}, Delivery {fy26['delivery']}",
                   12 <= bid <= 18 and 8 <= learn <= 12))

    mono = q("""with w as (select "userId" u, max_by("payGrade", "startDate") pg from COREWORKFORCEDATA_V1."coreworkforcedata"."coreworkforce_standardfields" group by 1
                           union all select "userId", max_by("payGrade", "startDate") from ACOCO_SIM.COREWORKFORCE.COREWORKFORCE_STANDARDFIELDS where "userId" like 'S%' group by 1),
                b as (select l.level, iff(mod(l.bill_code, 10) >= 5, 'U', 'L') band,
                             sum(iff(t.category = 'BID', t.hours, 0)) / sum(t.hours) bid_share
                      from ACOCO_SIM.TIMESHEET.TIMESHEET t join w on w.u = t.user_id
                      join ACOCO_DB.OPS.MAP_PAYGRADE_LEVEL l on l.pay_grade = w.pg
                      where t.fiscal_year = 2026 group by 1, 2)
             select level, max(iff(band = 'L', bid_share, null)) lo, max(iff(band = 'U', bid_share, null)) hi
             from b group by 1""")
    bad = [r["LEVEL"] for r in mono if r["HI"] is None or r["LO"] is None or r["HI"] <= r["LO"]]
    checks.append(("CP02-10", "within every level, higher bill codes spend a larger share on Bid (FY26)",
                   "upper > lower in 5 levels",
                   str({r["LEVEL"]: (round(100 * r["LO"], 1), round(100 * r["HI"], 1)) for r in mono}),
                   len(mono) == 5 and not bad))

    benches = {k: v["bench"] for k, v in load["stats"].items() if k.startswith("FY") and k.endswith("_firm")}
    checks.append(("CP02-11", "firm bench (available - booked) < 3 % of available hours in every fiscal year (D-02-12)",
                   "all < 3", str(benches), bool(benches) and all(b < 3 for b in benches.values())))
    return checks


def gate_cp03():
    import re
    import sf
    import gen_l1
    q = sf.query
    checks = []
    objs = [(d, n) for d, n, _, _ in gen_l1.objects()]
    doms = list(gen_l1.MAP["domains"])

    sch = {r["SCHEMA_NAME"] for r in q("select schema_name from ACOCO_L1.information_schema.schemata")}
    miss = [d for d in doms if d not in sch]
    checks.append(("CP03-01", "ACOCO_L1 has the nine domain schemas", "9 / 0 missing", f"{len(doms) - len(miss)} / {miss}",
                   len(doms) == 9 and not miss))

    tabs = q("select table_schema s, table_name t, table_type k from ACOCO_L1.information_schema.tables where table_schema <> 'INFORMATION_SCHEMA'")
    views = {(r["S"], r["T"]) for r in tabs if r["K"] == "VIEW"}
    non_views = [f"{r['S']}.{r['T']}" for r in tabs if r["K"] != "VIEW"]
    missing = [f"{d}.{n}" for d, n in objs if (d, n) not in views]
    extra = [f"{s}.{t}" for s, t in views if (s, t) not in set(objs)]
    checks.append(("CP03-02", "every mapped object is a view; L1 holds no tables and nothing unmapped",
                   f"{len(objs)} views / 0 tables / 0 extra",
                   f"{len(views)} views / tables {non_views} / missing {missing} / extra {extra}",
                   not missing and not non_views and not extra))

    errs = gen_l1.lint()
    checks.append(("CP03-03", "L1 lint: domain-only sources, no aggregation, no CURRENT_DATE, no technical columns",
                   "0 errors", f"{len(errs)} {errs[:3]}", not errs))

    rec_p = ROOT / "logs" / "l1_reconcile.json"
    fresh = rec_p.exists() and rec_p.stat().st_mtime > (ROOT / "tools" / "l1_map.yml").stat().st_mtime
    rec = json.loads(rec_p.read_text()) if rec_p.exists() else []
    bad = [f"{r['object']}/{r['source_system']}" for r in rec if not r["ok"]]
    checks.append(("CP03-04", "reconcile: L1 rows = base L0 rows per object and source; declared keys unique",
                   "all PASS, newer than l1_map.yml", f"{len(rec) - len(bad)}/{len(rec)} fresh={fresh} {bad}",
                   fresh and bool(rec) and not bad))

    nosrc = q("""select table_schema||'.'||table_name t from ACOCO_L1.information_schema.tables v
                 where table_schema <> 'INFORMATION_SCHEMA' and not exists (select 1 from ACOCO_L1.information_schema.columns c
                 where c.table_schema = v.table_schema and c.table_name = v.table_name and c.column_name = 'SOURCE_SYSTEM')""")
    checks.append(("CP03-05", "every view carries SOURCE_SYSTEM", "0 without", str([r["T"] for r in nosrc]), not nosrc))

    mix = {}
    for obj in ("WORKFORCE.WORKFORCE_JOB", "TIME.EMPLOYEE_AVAILABILITY", "ORGANISATION.ACTIVITY_TYPE"):
        mix[obj] = sorted(r["S"] for r in q(f"select distinct SOURCE_SYSTEM s from ACOCO_L1.{obj}"))
    checks.append(("CP03-06", "CLD UNION SIM: mixed objects return both BDC_CLD and SIMULATED rows",
                   "both in 3 objects", str(mix), all(v == ["BDC_CLD", "SIMULATED"] for v in mix.values())))

    norm = lambda s: re.sub(r"\s+", " ", s).strip().rstrip(";").upper()
    drift = []
    for d, n in objs:
        live = q(f"select get_ddl('VIEW', 'ACOCO_L1.{d}.{n}') ddl")[0]["DDL"]
        body = (gen_l1.OUT / d.lower() / f"{n.lower()}.sql").read_text()
        if norm(body.split("\nAS\n", 1)[1]) not in norm(live):
            drift.append(f"{d}.{n}")
    checks.append(("CP03-07", "deployed view definitions match the generated SQL (no hand edits)", "0 drifted",
                   str(drift), not drift))

    orphans = q("""select
      (select count(*) from ACOCO_L1.TIME.TIMESHEET_RECORD t where not exists
         (select 1 from ACOCO_L1.WORKFORCE.WORKFORCE_JOB w where w.PERSON_ID = t.PERSON_ID)) ts_person,
      (select count(*) from ACOCO_L1.TIME.TIMESHEET_RECORD t where t.WBS_ID is not null and not exists
         (select 1 from ACOCO_L1.PROJECTS.WBS_ELEMENT w where w.WBS_ID = t.WBS_ID)) ts_wbs,
      (select count(*) from ACOCO_L1.TIME.TIMESHEET_RECORD t where t.ORDER_ID is not null and not exists
         (select 1 from ACOCO_L1.FINANCE.INTERNAL_ORDER o where o.ORDER_ID = t.ORDER_ID)) ts_order,
      (select count(*) from (select distinct COST_CENTER_ID from ACOCO_L1.WORKFORCE.WORKFORCE_JOB) w where not exists
         (select 1 from ACOCO_L1.ORGANISATION.COST_CENTER c where c.COST_CENTER_ID = w.COST_CENTER_ID)) job_cc,
      (select count(*) from ACOCO_L1.FINANCE.JOURNAL_ENTRY_ITEM j where j.WBS_ID is not null and not exists
         (select 1 from ACOCO_L1.PROJECTS.WBS_ELEMENT w where w.WBS_ID = j.WBS_ID)) je_wbs,
      (select count(*) from ACOCO_L1.PROJECTS.PROJECT p where p.SOURCE_SYSTEM = 'SIMULATED' and not exists
         (select 1 from ACOCO_L1.SALES.CUSTOMER c where c.CUSTOMER_ID = p.CUSTOMER_ID)) prj_customer,
      (select count(*) from ACOCO_L1.TIME.EMPLOYEE_AVAILABILITY e where e.PERSON_ID is null
         and e.PERSON_LINK <> 'UNMATCHED') ea_unlinked_unflagged""")[0]
    checks.append(("CP03-08", "conformed keys resolve across domains (person, WBS, order, cost centre, customer)",
                   "all 0", str(orphans), all(v == 0 for v in orphans.values())))

    um = q("""select count(distinct ASSIGNMENT_ID) a, count(*) n,
                     100 * count(*) / (select count(*) from ACOCO_L1.TIME.EMPLOYEE_AVAILABILITY where SOURCE_SYSTEM = 'BDC_CLD') pct
              from ACOCO_L1.TIME.EMPLOYEE_AVAILABILITY where PERSON_LINK = 'UNMATCHED'""")[0]
    checks.append(("CP03-09", "real availability assignments with no Core Workforce person are flagged UNMATCHED and < 1 % of CLD rows (D-03-4)",
                   "< 1 %", f"{um['A']} assignments, {um['N']:,} rows, {float(um['PCT']):.2f} %", float(um["PCT"]) < 1))
    return checks


def gate_cp04():
    import re
    import sf
    import gen_ontology as go
    q = sf.query
    checks = []
    rep = go.report()
    ent = [r for r in rep if r["object"].startswith("ENT_")]
    rel = [r for r in rep if r["object"].startswith("REL_")]
    bad_e = [r["object"] for r in ent if not r["ok"]]
    checks.append(("CP04-01", "12 ENT_* entities: key unique and not null; rows = distinct keys in the owning L1 source",
                   "12 / 0 failing", f"{len(ent)} / {bad_e}", len(ent) == 12 and not bad_e))
    bad_r = [r["object"] for r in rel if not r["ok"]]
    checks.append(("CP04-02", "7 REL_* bridges: non-empty, key unique and not null", "7 / 0 failing",
                   f"{len(rel)} / {bad_r}", len(rel) == 7 and not bad_r))

    n, refs = go.check_refs()
    checks.append(("CP04-03", "no L2 object references L0 (*_V1 CLDs, ACOCO_SIM)", "0", f"{n} scanned, {refs}", not refs))

    dts = q("""SELECT name, state st FROM TABLE(ACOCO_L2.INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(RESULT_LIMIT => 10000))
               WHERE state IN ('SUCCEEDED', 'FAILED', 'UPSTREAM_FAILED', 'CANCELLED')
                 AND SPLIT_PART(qualified_name, '.', 2) IN ('CORE', 'ONTOLOGY')
               QUALIFY ROW_NUMBER() OVER (PARTITION BY qualified_name ORDER BY data_timestamp DESC, refresh_start_time DESC NULLS LAST) = 1""")
    dts_show = [r for r in q("SHOW DYNAMIC TABLES IN DATABASE ACOCO_L2") if r["schema_name"] in ("CORE", "ONTOLOGY")]
    unhealthy = [f"{r['name']}:{r['scheduling_state']}" for r in dts_show if r["scheduling_state"] != "ACTIVE"]
    failed = [r["NAME"] for r in dts if r["ST"] != "SUCCEEDED"] + [r["name"] for r in dts_show if r["name"] not in {d["NAME"] for d in dts}]
    checks.append(("CP04-04", "every L2 dynamic table ACTIVE with a successful last refresh", "21 / 0 / 0",
                   f"{len(dts_show)} / not active {unhealthy} / not succeeded {failed}",
                   len(dts_show) == 21 and not unhealthy and not failed))

    lags = {r["name"]: r["target_lag"] for r in dts_show}
    downstream = [k for k, v in lags.items() if str(v).upper() == "DOWNSTREAM"]
    checks.append(("CP04-05", "explicit TARGET_LAG on every DT (none DOWNSTREAM-only chains)", "0 DOWNSTREAM",
                   f"{sorted(set(lags.values()))} downstream {downstream}", not downstream))

    cd = []
    for kind, fqn in go.l2_objects():
        if kind == "TABLE":
            continue
        ddl = q(f"SELECT GET_DDL('{'VIEW' if kind == 'VIEW' else 'TABLE'}', '{fqn}') d")[0]["D"]
        if re.search(r"\bCURRENT_DATE\b|\bCURRENT_TIMESTAMP\b|\bSYSDATE\b|\bGETDATE\b", ddl, re.I):
            cd.append(fqn)
    checks.append(("CP04-06", "deterministic: no CURRENT_DATE / CURRENT_TIMESTAMP in L2 (today = CORE.VW_AS_OF)", "0",
                   str(cd), not cd))

    fm = q("""SELECT COUNT(*) n, COUNT(DISTINCT MONTH_START) d, COUNT_IF(FISCAL_YEAR = 2027) fy27,
                     MIN(IFF(FISCAL_YEAR = 2027 AND FISCAL_PERIOD = 1, MONTH_START, NULL))::VARCHAR p1
              FROM ACOCO_L2.CORE.DT_FISCAL_MONTH""")[0]
    checks.append(("CP04-07", "fiscal calendar: unique months, FY27 forward months generated (P01 = Oct 2026)",
                   "12 FY27 months, P01 2026-10-01", str(fm), fm["N"] == fm["D"] and fm["FY27"] == 12 and fm["P1"] == "2026-10-01"))

    p = q("""SELECT COUNT_IF(IS_ACTIVE_AS_OF) active, COUNT_IF(IS_ACTIVE_AS_OF AND (LEVEL IS NULL OR MD_GROUP_ID IS NULL
                     OR DISPLAY_NAME IS NULL)) incomplete, COUNT(DISTINCT IFF(IS_ACTIVE_AS_OF, MD_GROUP_ID, NULL)) groups_,
                     COUNT_IF(IS_MANAGING_DIRECTOR AND IS_ACTIVE_AS_OF AND LEVEL = 'Principal') mds
              FROM ACOCO_L2.ONTOLOGY.ENT_PERSON""")[0]
    checks.append(("CP04-08", "ENT_PERSON as of 2026-10-01: active people complete, six groups, six active Principal MDs",
                   "incomplete 0, 6 groups, 6 MDs", str(p), p["INCOMPLETE"] == 0 and p["GROUPS_"] == 6 and p["MDS"] == 6))
    return checks


def dt_health(schemas):
    import sf
    show = [r for r in sf.query("SHOW DYNAMIC TABLES IN DATABASE ACOCO_L2") if r["schema_name"] in schemas]
    last = {r["NAME"]: r["ST"] for r in sf.query(f"""SELECT name, state st
              FROM TABLE(ACOCO_L2.INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(RESULT_LIMIT => 10000))
              WHERE state IN ('SUCCEEDED', 'FAILED', 'UPSTREAM_FAILED', 'CANCELLED')
                AND SPLIT_PART(qualified_name, '.', 2) IN ({", ".join("'" + x + "'" for x in schemas)})
              QUALIFY ROW_NUMBER() OVER (PARTITION BY qualified_name ORDER BY data_timestamp DESC, refresh_start_time DESC NULLS LAST) = 1""")}
    bad = [f"{r['schema_name']}.{r['name']}:{r['scheduling_state']}/{last.get(r['name'])}" for r in show
           if r["scheduling_state"] != "ACTIVE" or last.get(r["name"]) != "SUCCEEDED"]
    lags = sorted({r["target_lag"] for r in show})
    return show, bad, lags


def gate_cp05():
    import subprocess
    import sf
    import gen_ontology as go
    q = sf.query
    checks = []
    py = str(ROOT / ".venv" / "bin" / "python")

    subprocess.run([py, str(ROOT / "tools" / "validate.py"), "--step", "marts", "--report"], capture_output=True)
    rec = json.loads((ROOT / "logs" / "validate_marts.json").read_text())
    bad = [f"{r['id']}: {r['actual']}" for r in rec if not r["ok"]]
    checks.append(("CP05-01", "mart reconciliations (time mix = 100 % OD-11, billable / pursuit hours = journal quantity, "
                   "overhead 35 %, balanced journal, revenue / available / booked hours tie L1 -> L2)",
                   "8/8 PASS", f"{len(rec) - len(bad)}/{len(rec)} {bad}", len(rec) == 8 and not bad))

    marts = ["PORTFOLIO_360", "PROJECT_DELIVERY", "PIPELINE_PRESALES", "WORKFORCE_PERFORMANCE", "AI_ADOPTION"]
    show, bad_dt, lags = dt_health(marts)
    per = {m: sum(1 for r in show if r["schema_name"] == m) for m in marts}
    checks.append(("CP05-02", "five marts built; every mart DT ACTIVE with a successful last refresh; explicit 1-hour lag",
                   "5 marts, 0 unhealthy, ['1 hour']", f"{per} unhealthy {bad_dt} lags {lags}",
                   all(per.values()) and not bad_dt and lags == ["1 hour"]))

    n, refs = go.check_refs()
    checks.append(("CP05-03", "no L2 object (marts, serving, quality) references L0", "0", f"{n} scanned, {refs}", not refs))

    srv = q("""SELECT table_name t FROM ACOCO_L2.INFORMATION_SCHEMA.TABLES WHERE table_schema = 'SERVING'""")
    leak = []
    for r in srv:
        ddl = q(f"SELECT GET_DDL('VIEW', 'ACOCO_L2.SERVING.{r['T']}') d")[0]["D"]
        if "ACOCO_L1" in ddl.upper():
            leak.append(r["T"])
    checks.append(("CP05-04", "SERVING views read L2 only (no ACOCO_L1)", ">= 8 views, 0 reading L1",
                   f"{len(srv)} views, {leak}", len(srv) >= 8 and not leak))

    mix = q("""SELECT MD_GROUP_ID, LEVEL, FISCAL_YEAR,
                      DELIVERY_PCT + BID_PCT + LEARNING_PCT + ADMIN_PCT + BENCH_PCT tot FROM ACOCO_L2.SERVING.VW_TIME_MIX_FY
               WHERE FISCAL_YEAR BETWEEN 2022 AND 2026""")
    off = [r for r in mix if abs(float(r["TOT"]) - 100) > 0.3]
    checks.append(("CP05-05", "overlay VW_TIME_MIX_FY: five shares sum to 100 for every group x level x FY22-26", "0 off (+/- 0.3 rounding)",
                   f"{len(mix)} rows, {len(off)} off", len(mix) == 150 and not off))

    qc = {r["T"]: r["N"] for r in q("""SELECT 'LINEAGE' t, COUNT(*) n FROM ACOCO_L2.QUALITY.Q_LINEAGE_COUNTS
                 UNION ALL SELECT 'FRESHNESS', COUNT(*) FROM ACOCO_L2.QUALITY.Q_FRESHNESS
                 UNION ALL SELECT 'COMPLETENESS', COUNT(*) FROM ACOCO_L2.QUALITY.Q_COMPLETENESS
                 UNION ALL SELECT 'ACCESS', COUNT(*) FROM ACOCO_L2.QUALITY.Q_ACCESS_SNAPSHOT""")}
    checks.append(("CP05-06", "QUALITY snapshots present (lineage counts, freshness, completeness, access)", "all > 0",
                   str(qc), all(v > 0 for v in qc.values())))

    anc = json.loads((ROOT / "logs" / "validate_anchors.json").read_text())
    fresh = (ROOT / "plan" / "measured_anchors.md").stat().st_mtime > (ROOT / "sql" / "03_l2").stat().st_mtime - 1
    unmeasured = [a["id"] for a in anc if not a["measured"] or "nan" in a["measured"]]
    no_fix = [a["id"] for a in anc if a["status"] == "MISS" and not a["proposed_fix"]]
    checks.append(("CP05-07", "every PRD 6.3 story anchor measured; each MISS carries a proposed fix (decision is the user's)",
                   "13 measured, 0 MISS without fix", f"{len(anc)} measured, OK {sum(a['status'] == 'OK' for a in anc)}, "
                   f"unmeasured {unmeasured}, MISS without fix {no_fix}", len(anc) == 13 and not unmeasured and not no_fix and fresh))
    return checks


def gate_cp06():
    import subprocess
    import gen_ontology as go
    checks = []
    py = str(ROOT / ".venv" / "bin" / "python")
    subprocess.run([py, str(ROOT / "tools" / "validate.py"), "--step", "reasoning", "--report"], capture_output=True)
    rec = json.loads((ROOT / "logs" / "validate_reasoning.json").read_text())
    for r in rec:
        checks.append((f"CP06-{r['id']}", r["name"], r["expected"], r["actual"], r["ok"]))
    show, bad, lags = dt_health(["REASONING"])
    checks.append(("CP06-DT", "REASONING dynamic tables ACTIVE with a successful last refresh, 1-hour lag",
                   "0 unhealthy", f"{len(show)} DTs, unhealthy {bad}, lags {lags}", bool(show) and not bad))
    n, refs = go.check_refs()
    checks.append(("CP06-REF", "no L2 object references L0", "0", f"{n} scanned, {refs}", not refs))
    subprocess.run([py, str(ROOT / "tools" / "validate.py"), "--step", "marts", "--report"], capture_output=True)
    m = json.loads((ROOT / "logs" / "validate_marts.json").read_text())
    bad_m = [r["id"] for r in m if not r["ok"]]
    checks.append(("CP06-MARTS", "mart reconciliations still pass after the recalibrated reload", "8/8",
                   f"{len(m) - len(bad_m)}/{len(m)} {bad_m}", len(m) == 8 and not bad_m))
    return checks


GATES = {"cp00": gate_cp00, "cp01": gate_cp01, "cp02": gate_cp02, "cp03": gate_cp03, "cp04": gate_cp04,
         "cp05": gate_cp05, "cp06": gate_cp06}


def log_to_quality(cp, run_at, rows):
    """Append gate results to ACOCO_L2.QUALITY.Q_CHECK_RESULTS once that table exists (CP-05 on)."""
    import sf
    try:
        if not sf.query("SHOW TABLES LIKE 'Q_CHECK_RESULTS' IN SCHEMA ACOCO_L2.QUALITY"):
            return
    except sf.SqlError:
        return
    lit = lambda v: "'" + str(v).replace("'", "''")[:4000] + "'"
    vals = ",\n".join(f"({lit(run_at)}::TIMESTAMP_TZ, {lit(cp)}, {lit(r['check_id'])}, {lit(r['description'])}, "
                       f"{lit(r['expected'])}, {lit(r['actual'])}, {lit(r['result'])})" for r in rows)
    sf.query(f"INSERT INTO ACOCO_L2.QUALITY.Q_CHECK_RESULTS VALUES {vals}")


def main():
    cp = sys.argv[1] if len(sys.argv) > 1 else ""
    if cp not in GATES:
        sys.exit(f"usage: gate.py {{{','.join(GATES)}}}")
    results = GATES[cp]()
    rows = [dict(check_id=c, description=d, expected=e, actual=a, result="PASS" if p else "FAIL")
            for c, d, e, a, p in results]
    out = {"cp": cp, "run_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "checks": rows}
    (ROOT / "logs" / f"gate_{cp}.json").write_text(json.dumps(out, indent=2))
    log_to_quality(cp, out["run_at"], rows)
    for r in rows:
        print(f"{r['result']}  {r['check_id']}  {r['description']}  ->  {r['actual']}")
    failed = [r for r in rows if r["result"] == "FAIL"]
    print(f"\n{cp}: {len(rows) - len(failed)}/{len(rows)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
