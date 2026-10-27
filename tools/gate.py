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
    bands = {"projects": (400, 800), "opportunities": (800, 1600), "assets": (80, 300)}
    bad = {k: st[k] for k, (lo, hi) in bands.items() if not lo <= st[k] <= hi}
    pc = q("""select count(distinct user_id) n from ACOCO_SIM.DIRECTORY.PERSON_NAME""")[0]["N"]
    checks.append(("CP02-03", "volumes in band (projects 400-800, opps 800-1600, assets 80-300); 3,555 people",
                   "in band", f"projects {st['projects']}, opps {st['opportunities']}, assets {st['assets']}, "
                              f"people {pc}", not bad and pc == 3555))

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
    return checks


GATES = {"cp00": gate_cp00, "cp01": gate_cp01, "cp02": gate_cp02}


def main():
    cp = sys.argv[1] if len(sys.argv) > 1 else ""
    if cp not in GATES:
        sys.exit(f"usage: gate.py {{{','.join(GATES)}}}")
    results = GATES[cp]()
    rows = [dict(check_id=c, description=d, expected=e, actual=a, result="PASS" if p else "FAIL")
            for c, d, e, a, p in results]
    out = {"cp": cp, "run_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "checks": rows}
    (ROOT / "logs" / f"gate_{cp}.json").write_text(json.dumps(out, indent=2))
    for r in rows:
        print(f"{r['result']}  {r['check_id']}  {r['description']}  ->  {r['actual']}")
    failed = [r for r in rows if r["result"] == "FAIL"]
    print(f"\n{cp}: {len(rows) - len(failed)}/{len(rows)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
