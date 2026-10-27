"""Run the ACoCo generator and load ACOCO_SIM.

  .venv/bin/python gen/run.py --check     generate twice in memory, compare table hashes (no load)
  .venv/bin/python gen/run.py --load      generate once, load ACOCO_SIM, record hashes in ACOCO_SIM._META.GEN_RUN
  .venv/bin/python gen/run.py --stats     generate once, print story-shape statistics (no load)
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import acoco_gen as g  # noqa: E402
from calendar_ import AS_OF, weeks  # noqa: E402
from sfio import Sf  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def read_inputs(sf: Sf):
    p = sf.df("select param_name, param_value from ACOCO_DB.OPS.GEN_PARAMS")
    params = {r.PARAM_NAME: json.loads(r.PARAM_VALUE) for r in p.itertuples()}
    levels = sf.df("select * from ACOCO_DB.OPS.LEVEL order by level_sort")
    targets = sf.df("select * from ACOCO_DB.OPS.GEN_PARAMS_TIME_TARGET")
    paygrade = sf.df("select * from ACOCO_DB.OPS.MAP_PAYGRADE_LEVEL order by pay_grade")
    sfcc = sf.df("select * from ACOCO_DB.OPS.MAP_SF_COSTCENTER order by sf_cost_center")
    mdcc = sf.df("""select m.*, c."ProfitCenter" as profit_center from ACOCO_DB.OPS.MAP_MD_GROUP m
                    join COSTCENTER_V1."costcenter"."costcenter" c
                      on c."CostCenter" = m.cost_center and c."ValidityEndDate" = '9999-12-31'
                    order by m.cost_center""")
    at = sf.df("""select "CostCtrActivityType" at, "AllocationCostElement" ce
                  from COSTCENTERACTIVITYTYPE_V1."costcenteractivitytype"."costcenteractivitytype"
                  where "ControllingArea" = 'A000' and "ValidityEndDate" = '9999-12-31'
                    and "CostCtrActivityType" in ('ML-100','ML-101','ML-103','ML-104','ML-105')""")
    activity_ce = dict(zip(at.AT, at.CE))
    # CUSTOMER_V1 masks every customer key as '********' in this tenant (D-02-4): ACoCo clients get simulated
    # S/4-format customer IDs, carried on the simulated CRM account table.
    customers = [f"ACO{i:07d}" for i in range(1, 121)]
    real_people = sf.df("""
        with cw as (select * from COREWORKFORCEDATA_V1."coreworkforcedata"."coreworkforce_standardfields")
        select "userId" user_id,
               min("startDate") first_start, max("endDate") last_end,
               min("tenureStartDate") tenure_start,
               max(iff("employmentStatus" = 'D', "startDate", null)) term_date,
               max_by("payGrade", "startDate") pay_grade,
               max_by("costCenter"::varchar, "startDate") cost_center,
               max_by("gender", "startDate") gender
        from cw group by 1 order by try_to_number("userId"), "userId" """)
    for c in ("FIRST_START", "LAST_END", "TENURE_START", "TERM_DATE"):
        real_people[c] = pd.to_datetime(real_people[c]).dt.date
    real_people["TERM_DATE"] = real_people["TERM_DATE"].where(real_people["TERM_DATE"].notna(), None)
    assign_map = sf.df("select assignment_id, user_id from ACOCO_DB.OPS.MAP_ASSIGNMENT_USER order by assignment_id")
    real_avail = sf.df("""
        select m.user_id, date_trunc('week', e."workDate")::date week_start,
               sum(greatest(coalesce(e."plannedWorkHours", 0) - coalesce(e."dailyAbsenceHours", 0), 0)) available_hours
        from EMPLOYEEAVAILABILITY_V1."employeeavailability"."employeeavailability" e
        join ACOCO_DB.OPS.MAP_ASSIGNMENT_USER m on m.assignment_id = e."assignmentId"
        where e."workDate" >= '2024-07-08' and e."workDate" <= '2027-03-31'
        group by 1, 2 order by 1, 2""")
    real_avail["WEEK_START"] = pd.to_datetime(real_avail["WEEK_START"]).dt.date
    real_avail["AVAILABLE_HOURS"] = real_avail["AVAILABLE_HOURS"].astype(float)
    return dict(params=params, levels=levels, targets=targets, paygrade=paygrade, sfcc=sfcc, mdcc=mdcc,
                activity_ce=activity_ce, customers=customers, real_people=real_people, real_monthly=real_people,
                real_avail_week=real_avail, assign_map=assign_map)


def generate(inputs) -> dict:
    t0 = time.time()
    rng = np.random.default_rng(int(inputs["params"]["seed"]))
    ctx = g.Ctx(rng=rng, gl=dict(revenue="0041000000", receivable="0012100000", overhead="0094233007",
                                 plan_cost="0094308000", agent_cost="0094308000"), **inputs)
    wk = weeks()
    people = g.build_people(ctx)
    names, md = g.build_names_and_mds(ctx, people)
    skill, ps, ai_level = g.build_skills(ctx, people)
    latest = ps.sort_values("ASSESSED_DATE").groupby("USER_ID").SKILL_ID.apply(set)
    ctx.out["_skill_sets"] = latest.to_dict()
    # skill history: per person, ascending (assessment date, skills held at >= 3) - bid-team fit (D-06-1)
    held = ps[ps.PROFICIENCY >= 3].groupby(["USER_ID", "ASSESSED_DATE"]).SKILL_ID.apply(set)
    hist = {}
    for (u, d), sk in held.sort_index().items():
        hist.setdefault(u, []).append((d, sk))
    ctx.out["_skill_hist"] = hist
    learning = g.build_learning_catalogue(ctx, skill)
    perf, comp = g.build_hr_extras(ctx, people)
    avail, leave = g.weekly_availability(ctx, people, wk)
    assets = g.Assets()
    st, opps, projects, wps, wp_skills, wp_plan, opp_team, opp_skills, accounts = g.run_demand(
        ctx, people, wk, avail, ai_level, skill, learning, assets)
    ctx.out["_wp_plan"] = wp_plan
    g.allocate_bid_time(ctx, st, people, wk)
    comps = g.schedule_learning(ctx, st, people, learning, ps, wk)
    ts = g.build_timesheets(ctx, st, people, wk, projects)
    telem, agt, ident = g.build_telemetry_and_agt(ctx, st, people, ts, wk)
    je, docs, plan, io = g.build_finance(ctx, people, ts, projects, wps, opps, agt)
    notes = g.build_notes(ctx, projects, wps)
    cw = g.core_workforce_rows(ctx, people, perf, comp)
    ea = g.availability_rows(ctx, people, leave, wk)
    assign = pd.DataFrame([(people.user_id.iloc[pi], proj, wp, wk.week_start.iloc[w0],
                            wk.week_start.iloc[min(w1, len(wk) - 1)] - dt.timedelta(days=3), a, role)
                           for (pi, proj, wp, w0, w1, a, role) in st.assignments],
                          columns=["USER_ID", "PROJECT_ID", "WBS_ELEMENT", "ASSIGNMENT_START", "ASSIGNMENT_END",
                                   "ALLOCATION", "ROLE"])
    assign = g.shape_roll_off(ctx, people, assign, ai_level)
    assign.insert(0, "ASSIGNMENT_ID", [f"RA{i + 1:07d}" for i in range(len(assign))])
    assign["SOURCE_SYSTEM"] = "SIMULATED"
    succession = (people[(people.level.isin(["Manager", "Senior Manager", "Principal"]))]
                  .sort_values("user_id").head(0))
    lead_users = set(assign[assign.ROLE == "PROJECT_LEAD"].USER_ID)
    nom = [dict(USER_ID=u, NOMINATION_TYPE="KEY_POSITION", HAS_READY_SUCCESSOR=bool(rng.random() < 0.55),
                SOURCE_SYSTEM="SIMULATED") for u in sorted(lead_users)]
    activity_ext = pd.DataFrame([dict(ControllingArea="A000", CostCtrActivityType=f"AGT_{v}",
                                      CostCtrActivityTypeName=f"AI agent - {v.title()}", CostCtrActivityTypeQtyUnit="H",
                                      AllocationCostElement="0094308000", PlannedPrice=g.AGT_PRICE[v],
                                      SenderCostCenter=g.AI_CC[v]) for v in g.VENDORS])
    tables = {
        ("COREWORKFORCE", "COREWORKFORCE_STANDARDFIELDS", True): cw,
        ("EMPLOYEEAVAILABILITY", "EMPLOYEEAVAILABILITY", True): ea,
        ("DIRECTORY", "PERSON_NAME", False): names,
        ("DIRECTORY", "MD_ROLE", False): md,
        ("SKILLS", "SKILL", False): skill,
        ("SKILLS", "PERSON_SKILL", False): ps,
        ("LEARNING", "LEARNING_ITEM", False): learning,
        ("LEARNING", "LEARNING_COMPLETION", False): comps,
        ("PERFORMANCE", "PERFORMANCE_RATING", False): perf,
        ("COMPENSATION", "COMPENSATION_SUMMARY", False): comp,
        ("SUCCESSION", "NOMINATION", False): pd.DataFrame(nom),
        ("CRM", "ACCOUNT", False): pd.DataFrame(accounts),
        ("CRM", "OPPORTUNITY", False): pd.DataFrame(opps),
        ("CRM", "OPPORTUNITY_SKILL", False): pd.DataFrame(opp_skills, columns=["OPPORTUNITY_ID", "SKILL_ID"]),
        ("CRM", "OPPORTUNITY_TEAM", False): pd.DataFrame(opp_team, columns=["OPPORTUNITY_ID", "USER_ID", "TEAM_ROLE"]),
        ("CUSTOMERPROJECT", "CUSTOMER_PROJECT", False): pd.DataFrame(projects),
        ("CUSTOMERPROJECT", "WORK_PACKAGE", False): pd.DataFrame(wps),
        ("CUSTOMERPROJECT", "WORK_PACKAGE_SKILL", False): pd.DataFrame(wp_skills, columns=[
            "WBS_ELEMENT", "SKILL_ID", "REQUIRED_PROFICIENCY"]),
        ("CUSTOMERPROJECT", "WORK_PACKAGE_LEVEL_PLAN", False): pd.DataFrame(wp_plan, columns=[
            "WBS_ELEMENT", "LEVEL", "PLANNED_HOURS"]),
        ("RESOURCEASSIGNMENT", "RESOURCE_ASSIGNMENT", False): assign,
        ("TIMESHEET", "TIMESHEET", False): ts,
        ("INTERNALORDER", "INTERNAL_ORDER", True): io,
        ("FINANCE_ACOCO", "OPERATIONALACCTGDOCITEM", True): je,
        ("FINANCE_ACOCO", "JOURNALENTRY", True): docs,
        ("FINANCE_ACOCO", "FINANCIALPLANNINGENTRYITEM", True): plan,
        ("FINANCE_ACOCO", "ACTIVITYTYPE_EXT", True): activity_ext,
        ("ASSETS", "ASSET", False): pd.DataFrame(assets.assets),
        ("ASSETS", "ASSET_HARVEST", False): pd.DataFrame(assets.harvests),
        ("ASSETS", "ASSET_USAGE", False): pd.DataFrame(assets.uses),
        ("TELEMETRY", "OPENAI_USAGE", False): telem["OPENAI"],
        ("TELEMETRY", "ANTHROPIC_USAGE", False): telem["ANTHROPIC"],
        ("TELEMETRY", "CORTEX_USAGE", False): telem["CORTEX"],
        ("TELEMETRY", "AI_IDENTITY_MAP", False): ident,
        ("PROJECTCOMMENTARY", "STATUS_NOTE", False): notes,
    }
    stats = story_stats(people, ts, avail, st, wk, opps, projects, wps, assets)
    print(f"generated {sum(len(v) for v in tables.values()):,} rows in {time.time() - t0:.0f}s")
    return dict(tables=tables, stats=stats)


def story_stats(people, ts, avail, st, wk, opps, projects, wps, assets):
    fy = wk.fiscal_year.values
    out = {}
    for f in (2022, 2023, 2024, 2025, 2026):
        m = fy == f
        a = avail[:, m].sum()
        fs = (people.md_group == "FS").values
        out[f"FY{f % 100}_firm"] = {k: round(100 * v[:, m].sum() / a, 1) for k, v in
                                    (("delivery", st.deliv), ("bid", st.bid), ("learning", st.learn),
                                     ("admin", st.admin))}
        out[f"FY{f % 100}_firm"]["bench"] = round(100 - sum(out[f"FY{f % 100}_firm"].values()), 1)
        af = avail[fs][:, m].sum()
        out[f"FY{f % 100}_FS"] = {k: round(100 * v[fs][:, m].sum() / af, 1) for k, v in
                                  (("delivery", st.deliv), ("bid", st.bid), ("learning", st.learn),
                                   ("admin", st.admin))}
        out[f"FY{f % 100}_FS"]["bench"] = round(100 - sum(out[f"FY{f % 100}_FS"].values()), 1)
    o = pd.DataFrame(opps)
    closed = o[o.OUTCOME.notna()]
    out["opportunities"] = len(o)
    out["win_rate_pct"] = round(100 * (closed.OUTCOME == "WON").mean(), 1)
    out["open_pipeline"] = int(o.OUTCOME.isna().sum())
    p = pd.DataFrame(projects)
    out["projects"] = len(p)
    out["size_mix"] = p.SIZE_CLASS.value_counts().to_dict()
    out["seeded_loss"] = p[p.SEEDED_STORY == "FS_LOSS"].PROJECT_ID.tolist()
    out["assets"] = len(assets.assets)
    out["asset_uses"] = len(assets.uses)
    out["people"] = len(people)
    out["sim_people"] = int((people.source_system == "SIMULATED").sum())
    return out


def frame_hash(df: pd.DataFrame) -> str:
    h = pd.util.hash_pandas_object(df.astype(str), index=False).values
    return hashlib.sha256(h.tobytes()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--load", action="store_true")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    sf = Sf()
    try:
        inputs = read_inputs(sf)
        r1 = generate(inputs)
        print(json.dumps(r1["stats"], indent=1, default=str))
        hashes = {f"{s}.{t}": frame_hash(df) for (s, t, _), df in r1["tables"].items()}
        if a.check:
            r2 = generate(inputs)
            h2 = {f"{s}.{t}": frame_hash(df) for (s, t, _), df in r2["tables"].items()}
            diff = [k for k in hashes if hashes[k] != h2[k]]
            print("determinism:", "PASS" if not diff else f"FAIL {diff}")
            (ROOT / "logs" / "gen_determinism.json").write_text(json.dumps(
                {"pass": not diff, "differences": diff, "hashes": hashes}, indent=1))
        if a.load:
            sf.exec("CREATE DATABASE IF NOT EXISTS ACOCO_SIM COMMENT = 'ACoCo L0 gap-fill: non-SAP sources and "
                    "BDC-shaped stand-ins (SOURCE_SYSTEM = SIMULATED)'")
            counts = {}
            for (s, t, quote), df in r1["tables"].items():
                counts[f"{s}.{t}"] = sf.write(s, t, df, quote=quote)
                print(f"  loaded {s}.{t}: {counts[f'{s}.{t}']:,}")
            sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                 cwd=ROOT).stdout.strip()
            meta = pd.DataFrame([dict(RUN_AT=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                      SEED=int(inputs["params"]["seed"]), GIT_SHA=sha,
                                      ROW_COUNTS=json.dumps(counts), HASHES=json.dumps(hashes),
                                      STATS=json.dumps(r1["stats"], default=str))])
            sf.write("_META", "GEN_RUN", meta)
            (ROOT / "logs" / "gen_load.json").write_text(json.dumps(
                {"counts": counts, "hashes": hashes, "stats": r1["stats"]}, indent=1, default=str))
    finally:
        sf.close()


if __name__ == "__main__":
    main()
