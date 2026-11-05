"""Build the procedural part of ACOCO_L2.REASONING (PRD section 9): models, forecasts and the R13 / R14 statistics.

  .venv/bin/python tools/build_reasoning.py            all steps
  .venv/bin/python tools/build_reasoning.py attrition  forecast  r13  r14   (any subset)

Writes:
  REASONING.ATTRITION_MODEL (SNOWFLAKE.ML.CLASSIFICATION) trained on FY22-FY24 snapshots, evaluated on FY25 (hold-out),
  REASONING.DT_ATTRITION_RISK (table) - active people scored on their FY26 snapshot + global top drivers,
  REASONING.FC_DEMAND_BY_SKILL - 12-month SNOWFLAKE.ML.FORECAST per skill family,
  REASONING.AI_PRODUCTIVITY_TEST (R13) and REASONING.LEARNING_PAYBACK_TEST (R14) - effects with 90 % bootstrap CIs.
Metrics go to logs/reasoning_build.json (read by validate.py --step reasoning).
"""
import collections
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402

q = sf.query
LOG = ROOT / "logs" / "reasoning_build.json"
SEED = 20261001
FEATURES = ["LEVEL", "BILL_CODE", "TENURE_MONTHS", "BILLABILITY", "BID_SHARE", "LEARNING_SHARE", "BENCH_SHARE",
            "PRODUCTIVITY_INDEX", "PERFORMANCE_RATING", "COMPA_RATIO", "AI_SKILL_LEVEL", "MD_GROUP_ID"]


def log_update(key, value):
    d = json.loads(LOG.read_text()) if LOG.exists() else {}
    d[key] = value
    LOG.write_text(json.dumps(d, indent=1, default=str))


def auc(y, s):
    """Rank-based ROC AUC (Mann-Whitney)."""
    y, s = np.asarray(y, bool), np.asarray(s, float)
    order = s.argsort()
    ranks = np.empty(len(s)); ranks[order] = np.arange(1, len(s) + 1)
    # average ties
    _, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    sums = np.bincount(inv, ranks); ranks = (sums / cnt)[inv]
    n1, n0 = y.sum(), (~y).sum()
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else float("nan")


def attrition():
    cols = ", ".join(FEATURES)
    sf.query(f"""CREATE OR REPLACE VIEW ACOCO_L2.REASONING.VW_ATTRITION_TRAIN AS
                 SELECT {cols}, LEFT_NEXT_FY FROM ACOCO_L2.REASONING.DT_ATTRITION_FEATURES
                 WHERE FISCAL_YEAR BETWEEN 2022 AND 2024 AND ACTIVE_AT_FY_END""")
    sf.run_sql_block(f"""USE WAREHOUSE WH_ACOCO_BUILD;
        CREATE OR REPLACE SNOWFLAKE.ML.CLASSIFICATION ACOCO_L2.REASONING.ATTRITION_MODEL(
          INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'ACOCO_L2.REASONING.VW_ATTRITION_TRAIN'),
          TARGET_COLNAME => 'LEFT_NEXT_FY',
          CONFIG_OBJECT => {{'evaluate': TRUE, 'on_error': 'skip'}});""")
    # hold-out: FY25 snapshots, label = left during FY26
    rows = q(f"""SELECT LEFT_NEXT_FY y, SOURCE_SYSTEM src,
                        ACOCO_L2.REASONING.ATTRITION_MODEL!PREDICT(INPUT_DATA => OBJECT_CONSTRUCT({", ".join(f"'{c}', {c}" for c in FEATURES)})) p
                 FROM ACOCO_L2.REASONING.DT_ATTRITION_FEATURES WHERE FISCAL_YEAR = 2025 AND ACTIVE_AT_FY_END""")
    y = [r["Y"] for r in rows]
    s = [json.loads(r["P"])["probability"].get("True", json.loads(r["P"])["probability"].get("true", 0)) for r in rows]
    holdout_auc = auc(y, s)
    # only the simulated pool has voluntary leavers, so also score within it (tenure alone separates real people)
    sim = [i for i, r in enumerate(rows) if r["SRC"] == "SIMULATED"]
    holdout_auc_sim = auc([y[i] for i in sim], [s[i] for i in sim])
    imp = q("CALL ACOCO_L2.REASONING.ATTRITION_MODEL!SHOW_FEATURE_IMPORTANCE()")
    imp = sorted(({"feature": r["FEATURE"], "score": float(r["SCORE"])} for r in imp), key=lambda x: -x["score"])
    top = ", ".join(x["feature"] for x in imp[:3])
    sf.query(f"""CREATE OR REPLACE TABLE ACOCO_L2.REASONING.DT_ATTRITION_RISK
                 COMMENT = 'Active people scored on their FY26 snapshot by ATTRITION_MODEL (trained FY22-24, hold-out AUC {holdout_auc:.3f}); TOP_DRIVERS = global feature importance'
                 AS
                 WITH s AS (
                   SELECT f.PERSON_ID, f.MD_GROUP_ID, f.LEVEL, f.BILL_CODE, f.TENURE_MONTHS, f.BILLABILITY, f.BID_SHARE,
                          f.PRODUCTIVITY_INDEX, f.PERFORMANCE_RATING, f.COMPA_RATIO, f.AI_SKILL_LEVEL, f.SOURCE_SYSTEM,
                          ACOCO_L2.REASONING.ATTRITION_MODEL!PREDICT(INPUT_DATA => OBJECT_CONSTRUCT({", ".join(f"'{c}', f.{c}" for c in FEATURES)})) p
                   FROM ACOCO_L2.REASONING.DT_ATTRITION_FEATURES f
                   JOIN ACOCO_L2.ONTOLOGY.ENT_PERSON e ON e.PERSON_ID = f.PERSON_ID AND e.IS_ACTIVE_AS_OF
                   WHERE f.FISCAL_YEAR = 2026)
                 SELECT s.* EXCLUDE (p),
                        COALESCE(p:probability:"True", p:probability:"true")::FLOAT AS ATTRITION_RISK,
                        NTILE(10) OVER (ORDER BY COALESCE(p:probability:"True", p:probability:"true")::FLOAT DESC) AS RISK_DECILE,
                        '{top}' AS TOP_DRIVERS
                 FROM s""")
    n = q("SELECT COUNT(*) n, AVG(ATTRITION_RISK) a FROM ACOCO_L2.REASONING.DT_ATTRITION_RISK")[0]
    base = sum(y) / len(y)
    log_update("attrition", dict(holdout_auc=holdout_auc, holdout_auc_simulated_pool=holdout_auc_sim,
                                 holdout_rows=len(y), holdout_rows_simulated=len(sim), holdout_base_rate=base,
                                 scored_people=n["N"], mean_risk=float(n["A"]), feature_importance=imp[:8]))
    print(f"attrition: hold-out AUC {holdout_auc:.3f} on {len(y)} FY25 snapshots (base rate {base:.3f}), "
          f"{holdout_auc_sim:.3f} within the simulated pool ({len(sim)}); "
          f"scored {n['N']} active people; top drivers {top}")


def forecast():
    sf.query("""CREATE OR REPLACE VIEW ACOCO_L2.REASONING.VW_DEMAND_TRAIN AS
                SELECT SKILL_FAMILY, MONTH_START::TIMESTAMP_NTZ AS TS, DEMAND_HOURS
                FROM ACOCO_L2.REASONING.DT_DEMAND_BY_SKILL_MONTH
                WHERE MONTH_START < (SELECT DATE_TRUNC(month, AS_OF_DATE) FROM ACOCO_L2.CORE.VW_AS_OF)""")
    sf.run_sql_block("""USE WAREHOUSE WH_ACOCO_BUILD;
        CREATE OR REPLACE SNOWFLAKE.ML.FORECAST ACOCO_L2.REASONING.DEMAND_FORECAST_MODEL(
          INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'ACOCO_L2.REASONING.VW_DEMAND_TRAIN'),
          SERIES_COLNAME => 'SKILL_FAMILY', TIMESTAMP_COLNAME => 'TS', TARGET_COLNAME => 'DEMAND_HOURS');
        CREATE OR REPLACE TABLE ACOCO_L2.REASONING.FC_DEMAND_BY_SKILL
          COMMENT = '12-month delivery-demand forecast (hours) per skill family, SNOWFLAKE.ML.FORECAST, 95 % interval'
        AS SELECT SERIES::VARCHAR AS SKILL_FAMILY, TS::DATE AS MONTH_START, FORECAST AS DEMAND_HOURS_FORECAST,
                  LOWER_BOUND, UPPER_BOUND
           FROM TABLE(ACOCO_L2.REASONING.DEMAND_FORECAST_MODEL!FORECAST(FORECASTING_PERIODS => 12));""")
    r = q("""SELECT SKILL_FAMILY, COUNT(*) n, MIN(MONTH_START) a, MAX(MONTH_START) b, SUM(DEMAND_HOURS_FORECAST) h
             FROM ACOCO_L2.REASONING.FC_DEMAND_BY_SKILL GROUP BY 1 ORDER BY 1""")
    fam = [x["SKILL_FAMILY"] for x in q("SELECT DISTINCT SKILL_FAMILY FROM ACOCO_L2.ONTOLOGY.ENT_SKILL")]
    log_update("forecast", dict(families=fam, series=[{k.lower(): v for k, v in x.items()} for x in r]))
    print(f"forecast: {len(r)} of {len(fam)} skill families, {r[0]['N'] if r else 0} months each")


def boot_ci(people_rows, est, rng, n_boot=1000):
    people = list(people_rows)
    point = est(people)
    bs = [est(list(rng.choice(people, len(people), replace=True))) for _ in range(n_boot)]
    lo, hi = np.nanpercentile(bs, [5, 95])
    return point, float(lo), float(hi)


def r13():
    rng = np.random.default_rng(SEED)
    rows = q("""SELECT MD_GROUP_ID, FISCAL_YEAR, LEVEL, LEVEL_SORT, STRATUM, PERSON_ID, AI_ACTIVE, AI_SKILLED_INACTIVE,
                       EARNED_HOURS, DELIVERY_HOURS
                FROM ACOCO_L2.AI_ADOPTION.DT_AI_PRODUCTIVITY WHERE FISCAL_YEAR BETWEEN 2024 AND 2026""")
    out = []
    scopes = [("FIRM", lambda r: True)] + [(g, (lambda g: lambda r: r["MD_GROUP_ID"] == g)(g))
                                           for g in sorted({r["MD_GROUP_ID"] for r in rows})]
    bands = {"AI_ACTIVE": lambda r: r["AI_ACTIVE"], "SKILLED_INACTIVE": lambda r: r["AI_SKILLED_INACTIVE"]}
    for fy in (2024, 2025, 2026):
        for scope, keep in scopes:
            sub = [r for r in rows if r["FISCAL_YEAR"] == fy and keep(r)]
            levels = sorted({(r["LEVEL_SORT"], r["LEVEL"]) for r in sub})
            for stratum, srows in [("ALL LEVELS", sub)] + [(l, [r for r in sub if r["LEVEL"] == l]) for _, l in levels]:
                by_p = collections.defaultdict(list)
                for r in srows:
                    by_p[r["PERSON_ID"]].append(r)
                for band, is_band in bands.items():
                    def est(sample, is_band=is_band):
                        st = collections.defaultdict(lambda: [[0.0, 0.0], [0.0, 0.0]])
                        for pid in sample:
                            for r in by_p[pid]:
                                if band == "SKILLED_INACTIVE" and r["AI_ACTIVE"]:
                                    continue                     # compare skilled-inactive with the non-active rest
                                k = st[r["STRATUM"]][1 if is_band(r) else 0]
                                k[0] += float(r["EARNED_HOURS"]); k[1] += float(r["DELIVERY_HOURS"])
                        num = den = 0.0
                        for rest, grp in st.values():
                            if rest[1] > 0 and grp[1] > 0:
                                w = rest[1] + grp[1]
                                num += w * (grp[0] / grp[1] - rest[0] / rest[1]); den += w
                        return num / den if den else float("nan")
                    n_band = len({r["PERSON_ID"] for r in srows if is_band(r)})
                    if n_band < 5:
                        continue
                    pt, lo, hi = boot_ci(by_p, est, rng, 400 if stratum != "ALL LEVELS" else 1000)
                    out.append(dict(SCOPE=scope, FISCAL_YEAR=fy, STRATUM=stratum, AI_BAND=band, PEOPLE_IN_BAND=n_band,
                                    PEOPLE_TOTAL=len(by_p), UPLIFT=pt, CI_LOW=lo, CI_HIGH=hi,
                                    SIGNIFICANT=bool(lo > 0 or hi < 0)))
    write_table("AI_PRODUCTIVITY_TEST", out,
                "R13: productivity-index uplift of an AI band vs the non-active rest within level x work type strata "
                "(hours-weighted), 90 % bootstrap CI over people; SIGNIFICANT = CI excludes zero")
    fs = [x for x in out if x["SCOPE"] == "FS" and x["FISCAL_YEAR"] == 2026 and x["STRATUM"] == "ALL LEVELS"]
    log_update("r13", fs)
    for x in fs:
        print(f"r13 FS FY26 {x['AI_BAND']}: uplift {x['UPLIFT']:+.3f} CI [{x['CI_LOW']:+.3f}, {x['CI_HIGH']:+.3f}] "
              f"significant={x['SIGNIFICANT']} (n {x['PEOPLE_IN_BAND']})")


def r14():
    rng = np.random.default_rng(SEED + 1)
    rows = q("""SELECT PERSON_ID, CURRICULUM, IS_AI_CURRICULUM, MD_GROUP_ID, PAYBACK, HOURS_SAVED
                FROM ACOCO_L2.AI_ADOPTION.DT_LEARNING_PAYBACK WHERE PAYBACK IS NOT NULL""")
    out = []
    for scope in ["FIRM", "FS"]:
        for cur in sorted({r["CURRICULUM"] for r in rows}):
            sub = [r for r in rows if r["CURRICULUM"] == cur and (scope == "FIRM" or r["MD_GROUP_ID"] == scope)]
            by_p = collections.defaultdict(list)
            for r in sub:
                by_p[r["PERSON_ID"]].append(float(r["PAYBACK"]))
            est = lambda sample: float(np.mean([v for p in sample for v in by_p[p]]))
            pt, lo, hi = boot_ci(by_p, est, rng, 1000)
            out.append(dict(SCOPE=scope, CURRICULUM=cur, IS_AI_CURRICULUM=sub[0]["IS_AI_CURRICULUM"], EPISODES=len(sub),
                            PEOPLE=len(by_p), PAYBACK=pt, CI_LOW=lo, CI_HIGH=hi, SIGNIFICANT=bool(lo > 0 or hi < 0),
                            HOURS_SAVED=float(sum(float(r["HOURS_SAVED"] or 0) for r in sub))))
    write_table("LEARNING_PAYBACK_TEST", out,
                "R14: mean productivity change 6 months after vs before a curriculum episode minus the matched "
                "comparison change, 90 % bootstrap CI over people; HOURS_SAVED = payback x hours after")
    log_update("r14", out)
    for x in out:
        print(f"r14 {x['SCOPE']} {x['CURRICULUM']}: payback {x['PAYBACK']:+.4f} CI [{x['CI_LOW']:+.4f}, {x['CI_HIGH']:+.4f}] "
              f"significant={x['SIGNIFICANT']}")


def write_table(name, rows, comment, schema="REASONING"):
    cols = list(rows[0])

    def kind(c):   # first non-null value decides the type (insufficient-data cells carry NULLs)
        v = next((r[c] for r in rows if r[c] is not None and not (isinstance(r[c], float) and np.isnan(r[c]))), None)
        return ("BOOLEAN" if isinstance(v, (bool, np.bool_)) else "FLOAT" if isinstance(v, (float, np.floating))
                else "NUMBER" if isinstance(v, (int, np.integer)) else "VARCHAR")
    types = {c: kind(c) for c in cols}
    lit = lambda v: "NULL" if v is None or (isinstance(v, float) and np.isnan(v)) else (
        str(v).upper() if isinstance(v, (bool, np.bool_)) else repr(float(v)) if isinstance(v, (float, np.floating))
        else str(int(v)) if isinstance(v, (int, np.integer)) else "'" + str(v).replace("'", "''") + "'")
    sf.query(f"CREATE OR REPLACE TABLE ACOCO_L2.{schema}.{name} ({', '.join(f'{c} {types[c]}' for c in cols)}) "
             f"COMMENT = '{comment.replace(chr(39), chr(39) * 2)}'")
    for i in range(0, len(rows), 500):
        vals = ",\n".join("(" + ", ".join(lit(r[c]) for c in cols) + ")" for r in rows[i:i + 500])
        sf.query(f"INSERT INTO ACOCO_L2.{schema}.{name} VALUES {vals}")


def main():
    steps = sys.argv[1:] or ["attrition", "forecast", "r13", "r14", "p6", "serving"]
    for s in steps:
        {"attrition": attrition, "forecast": forecast, "r13": r13, "r14": r14,
         # P6 WPS tests R13w, R14w, R15-R18 and the truth-recovery table (tools/p6_reasoning.py)
         "p6": lambda: __import__("p6_reasoning").main_steps(),
         "serving": lambda: ([sf.run_file(str(f)) for f in sorted((ROOT / "sql" / "03_l2" / "post").glob("*.sql"))],
                             print("serving: post-build views built"))}[s]()


if __name__ == "__main__":
    main()
