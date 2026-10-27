"""Reconcile the L2 marts and measure every story anchor (PRD 6.3, OD-11).

  .venv/bin/python tools/validate.py --step marts --report      reconciliations -> logs/validate_marts.json
  .venv/bin/python tools/validate.py --step anchors --report    anchors -> plan/measured_anchors.md, logs/validate_anchors.json

Reconciliations must PASS (gate CP-05). Anchors are measured against their design band; a MISS is reported with a
proposed fix and decided by the user (generator recalibration returns to CP-02).
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402

q = sf.query
AS_OF = "(SELECT AS_OF_DATE FROM ACOCO_L2.CORE.VW_AS_OF)"
CLOSED = f"< (SELECT DATE_TRUNC(month, AS_OF_DATE) FROM ACOCO_L2.CORE.VW_AS_OF)"


def one(sql):
    return q(sql)[0]


def f(x):
    return None if x is None else float(x)


# ------------------------------------------------------------------------------------------------ reconciliations
def reconcile_marts():
    out = []

    r = one("""SELECT COUNT(*) n,
                      COUNT_IF(ABS(DELIVERY_HOURS + BID_HOURS + LEARNING_HOURS + ADMIN_HOURS + BENCH_HOURS - AVAILABLE_HOURS)
                               > 0.01 * AVAILABLE_HOURS) off,
                      SUM(OVERBOOKED_HOURS) / SUM(AVAILABLE_HOURS) ob_share
               FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_SCORECARD WHERE AVAILABLE_HOURS > 0""")
    share_ok = 1 - r["OFF"] / r["N"]
    out.append(dict(id="R1", name="time mix sums to 100 % of available hours per person-month (+/- 1 %) (OD-11)",
                    expected=">= 99.5 % of person-months; overbooked < 0.1 % of available hours",
                    actual=f"{100 * share_ok:.2f} % of {r['N']:,}; overbooked {100 * f(r['OB_SHARE']):.3f} %",
                    ok=share_ok >= 0.995 and f(r["OB_SHARE"]) < 0.001))

    r = one(f"""WITH t AS (SELECT DATE_TRUNC(month, WEEK_START) m, SUM(HOURS) h FROM ACOCO_L1.TIME.TIMESHEET_RECORD
                           WHERE TIME_CATEGORY = 'DELIVERY' GROUP BY 1),
                     j AS (SELECT DATE_TRUNC(month, POSTING_DATE) m, SUM(QUANTITY) h FROM ACOCO_L1.FINANCE.JOURNAL_ENTRY_ITEM
                           WHERE BILLABLE_CONTROL = 'BILLABLE' AND DEBIT_CREDIT = 'S' AND WBS_ID IS NOT NULL GROUP BY 1)
                SELECT COUNT(*) months, MAX(ABS(t.h - j.h) / NULLIF(t.h, 0)) worst, SUM(t.h) th, SUM(j.h) jh
                FROM t JOIN j ON j.m = t.m WHERE t.m {CLOSED}""")
    out.append(dict(id="R2", name="billable hours: Delivery timesheet hours = journal activity quantity on WBS, per month",
                    expected="worst month within 0.5 %",
                    actual=f"{r['MONTHS']} months, worst {100 * f(r['WORST']):.3f} %, totals {f(r['TH']):,.0f} / {f(r['JH']):,.0f}",
                    ok=f(r["WORST"]) <= 0.005))

    r = one(f"""WITH t AS (SELECT DATE_TRUNC(month, WEEK_START) m, SUM(HOURS) h FROM ACOCO_L1.TIME.TIMESHEET_RECORD
                           WHERE TIME_CATEGORY = 'BID' GROUP BY 1),
                     j AS (SELECT DATE_TRUNC(month, POSTING_DATE) m, SUM(QUANTITY) h FROM ACOCO_L1.FINANCE.JOURNAL_ENTRY_ITEM
                           WHERE BILLABLE_CONTROL = 'NON_BILLABLE' AND DEBIT_CREDIT = 'S' AND ORDER_ID IS NOT NULL
                           AND ACTIVITY_TYPE LIKE 'ML%' GROUP BY 1)
                SELECT COUNT(*) months, MAX(ABS(t.h - j.h) / NULLIF(t.h, 0)) worst FROM t JOIN j ON j.m = t.m WHERE t.m {CLOSED}""")
    out.append(dict(id="R3", name="pursuit hours: Bid timesheets = journal activity quantity on pre-sales internal orders, per month (Learning / Admin stay on the cost centre)",
                    expected="worst month within 0.5 %", actual=f"{r['MONTHS']} months, worst {100 * f(r['WORST']):.3f} %",
                    ok=f(r["WORST"]) <= 0.005))

    r = one("""SELECT COUNT(*) n, COUNT_IF(ABS(OVERHEAD_COST_TD / NULLIF(PEOPLE_COST_TD, 0) - 0.35) > 0.005) off,
                      SUM(OVERHEAD_COST_TD) / SUM(PEOPLE_COST_TD) ratio
               FROM ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_HEALTH WHERE PEOPLE_COST_TD > 0""")
    out.append(dict(id="R4", name="overhead = 35 % of people activity cost, per project",
                    expected="every project 35 % +/- 0.5 pt", actual=f"{r['N']} projects, {r['OFF']} off; firm {100 * f(r['RATIO']):.2f} %",
                    ok=r["OFF"] == 0))

    r = one("""SELECT COUNT(*) docs, COUNT_IF(ABS(s) > 0.01) unbalanced FROM
               (SELECT COMPANY_CODE, FISCAL_YEAR, ACCOUNTING_DOCUMENT, SUM(AMOUNT) s FROM ACOCO_L1.FINANCE.JOURNAL_ENTRY_ITEM GROUP BY 1, 2, 3)""")
    out.append(dict(id="R5", name="every journal document balances (debits = credits)", expected="0 unbalanced",
                    actual=f"{r['DOCS']:,} documents, {r['UNBALANCED']} unbalanced", ok=r["UNBALANCED"] == 0))

    r = one(f"""SELECT (SELECT SUM(-j.AMOUNT) FROM ACOCO_L1.FINANCE.JOURNAL_ENTRY_ITEM j JOIN ACOCO_L1.ORGANISATION.GL_ACCOUNT g
                        ON g.GL_ACCOUNT = j.GL_ACCOUNT AND g.ACOCO_ROLE = 'REVENUE' WHERE DATE_TRUNC(month, j.POSTING_DATE) {CLOSED}) l1,
                       (SELECT SUM(REVENUE) FROM ACOCO_L2.PORTFOLIO_360.DT_PORTFOLIO_MONTH) l2_portfolio,
                       (SELECT SUM(REVENUE) FROM ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_MONTH_FINANCIALS) l2_delivery""")
    out.append(dict(id="R6", name="revenue: L1 journal = PROJECT_DELIVERY = PORTFOLIO_360 (closed months)", expected="all equal (< 1 USD)",
                    actual=f"{f(r['L1']):,.0f} / {f(r['L2_DELIVERY']):,.0f} / {f(r['L2_PORTFOLIO']):,.0f}",
                    ok=abs(f(r["L1"]) - f(r["L2_DELIVERY"])) < 1 and abs(f(r["L1"]) - f(r["L2_PORTFOLIO"])) < 1))

    r = one(f"""SELECT (SELECT SUM(AVAILABLE_HOURS) FROM ACOCO_L1.TIME.EMPLOYEE_AVAILABILITY e WHERE e.PERSON_ID IS NOT NULL
                        AND DATE_TRUNC(month, DATEADD(day, 1 - DAYOFWEEKISO(e.WORK_DATE), e.WORK_DATE)) >= '2021-10-01'
                        AND DATE_TRUNC(month, DATEADD(day, 1 - DAYOFWEEKISO(e.WORK_DATE), e.WORK_DATE)) {CLOSED}) l1,
                       (SELECT SUM(AVAILABLE_HOURS) FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_SCORECARD) l2,
                       (SELECT SUM(AVAILABLE_HOURS) FROM ACOCO_L2.PORTFOLIO_360.DT_CAPACITY_MIX_MONTH) l2p""")
    out.append(dict(id="R7", name="available hours: L1 Employee Availability = scorecard = capacity mix (closed months)",
                    expected="all equal (< 1 h)", actual=f"{f(r['L1']):,.0f} / {f(r['L2']):,.0f} / {f(r['L2P']):,.0f}",
                    ok=abs(f(r["L1"]) - f(r["L2"])) < 1 and abs(f(r["L2"]) - f(r["L2P"])) < 1))

    r = one(f"""SELECT (SELECT SUM(HOURS) FROM ACOCO_L1.TIME.TIMESHEET_RECORD t JOIN ACOCO_L2.ONTOLOGY.ENT_PERSON p USING (PERSON_ID)
                        WHERE DATE_TRUNC(month, t.WEEK_START) >= '2021-10-01' AND DATE_TRUNC(month, t.WEEK_START) {CLOSED}) l1,
                       (SELECT SUM(BOOKED_HOURS) FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_MONTH_SCORECARD) l2""")
    out.append(dict(id="R8", name="booked hours: L1 timesheets = scorecard (closed months)", expected="equal (< 1 h)",
                    actual=f"{f(r['L1']):,.0f} / {f(r['L2']):,.0f}", ok=abs(f(r["L1"]) - f(r["L2"])) < 1))
    return out


# ------------------------------------------------------------------------------------------------ anchors
def stratified_uplift(rows, rng, n_boot=1000):
    """Hours-weighted mean of (PI AI-active - PI rest) within level x work type strata; bootstrap over people."""
    import collections
    by_person = collections.defaultdict(list)
    for r in rows:
        by_person[r["PERSON_ID"]].append(r)
    people = list(by_person)

    def est(sample):
        st = collections.defaultdict(lambda: [[0.0, 0.0], [0.0, 0.0]])   # stratum -> [rest, active] x [earned, hours]
        for pid in sample:
            for r in by_person[pid]:
                k = st[r["STRATUM"]][1 if r["AI_ACTIVE"] else 0]
                k[0] += float(r["EARNED_HOURS"]); k[1] += float(r["DELIVERY_HOURS"])
        num = den = 0.0
        for rest, act in st.values():
            if rest[1] > 0 and act[1] > 0:
                w = rest[1] + act[1]
                num += w * (act[0] / act[1] - rest[0] / rest[1]); den += w
        return num / den if den else float("nan")

    point = est(people)
    boots = [est(rng.choice(people, len(people), replace=True)) for _ in range(n_boot)]
    lo, hi = np.nanpercentile(boots, [5, 95])
    return point, lo, hi


def measure_anchors():
    rng = np.random.default_rng(20261001)
    a = []

    def add(aid, name, target, measured, ok, fix=""):
        a.append(dict(id=aid, anchor=name, design_target=target, measured=measured, status="OK" if ok else "MISS",
                      proposed_fix="" if ok else fix))

    s = one("""SELECT PROJECT_ID, CPI, SPI, FORECAST_MARGIN_PCT fm, MARGIN_PCT_TD m, ASSET_USES, WORK_TYPE, MD_GROUP_ID, SIZE_CLASS, CONTRACT_TYPE
               FROM ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_HEALTH WHERE IS_STORY_PROJECT""")
    add("A1", "One Large FS fixed-price project in loss at FY26 close", "forecast margin < 0 %, CPI ~0.73 (0.65-0.80), SPI ~0.8 (0.75-0.90)",
        f"{s['PROJECT_ID']} ({s['MD_GROUP_ID']}, {s['SIZE_CLASS']}, {s['CONTRACT_TYPE']}): forecast margin {100 * f(s['FM']):.1f} %, CPI {f(s['CPI']):.2f}, SPI {f(s['SPI']):.2f}",
        f(s["FM"]) < 0 and 0.65 <= f(s["CPI"]) <= 0.80 and 0.75 <= f(s["SPI"]) <= 0.90,
        "SPI above band: lower the story project's critical-path productivity (0.58) or lengthen its slip; CP-02 generator")

    r = q("""SELECT FISCAL_YEAR, SUM(DELIVERY_HOURS) / SUM(AVAILABLE_HOURS) d, SUM(BENCH_HOURS) / SUM(AVAILABLE_HOURS) b
             FROM ACOCO_L2.PORTFOLIO_360.DT_CAPACITY_MIX_MONTH GROUP BY 1 ORDER BY 1""")
    fy26 = next(x for x in r if x["FISCAL_YEAR"] == 2026)
    bench = {x["FISCAL_YEAR"]: round(100 * f(x["B"]), 1) for x in r}
    add("A2", "FY26 firm Delivery share / bench", "~72 % (70-74) / 1-2 %, bench < 3 % every year",
        f"Delivery {100 * f(fy26['D']):.1f} %, bench {100 * f(fy26['B']):.1f} %; bench by FY {bench}",
        0.70 <= f(fy26["D"]) <= 0.74 and 0.01 <= f(fy26["B"]) <= 0.02 and all(v < 3 for v in bench.values()))

    r = one(f"""SELECT COUNT(*) n, COUNT_IF(BELOW_PIPELINE_AI_LEVEL) below FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_ROLL_OFF
               WHERE MD_GROUP_ID = 'FS' AND ROLL_OFF_DATE < '2026-12-30'""")
    pct = r["BELOW"] / r["N"] if r["N"] else 0
    add("A3", "FS roll-off before 30 Dec 2026 without successor", "30-40 people; > 75 % below the pipeline's required AI-skill level",
        f"{r['N']} people; {100 * pct:.0f} % below pipeline AI level", 30 <= r["N"] <= 40 and pct > 0.75,
        "Too many FS assignments end in Q1 FY27: shorten the forward staffing horizon or extend FS assignments to the "
        "project end in the generator; raise the share of low-AI-skill people among roll-offs (CP-02)")

    r = q("""SELECT FISCAL_YEAR, SUM(VOLUNTARY_LEAVERS) l, AVG(h) avg_hc FROM
             (SELECT FISCAL_YEAR, MONTH_START, SUM(VOLUNTARY_LEAVERS) VOLUNTARY_LEAVERS, SUM(CLOSING_HEADCOUNT) h
              FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_HEADCOUNT_MONTH GROUP BY 1, 2) GROUP BY 1 ORDER BY 1""")
    att = {x["FISCAL_YEAR"]: round(100 * f(x["L"]) / f(x["AVG_HC"]), 1) for x in r}
    add("A4", "Voluntary attrition trend", "FY22 peak ~18 % (16-20) -> FY26 ~13 % (11-15)", f"by FY {att}",
        16 <= att.get(2022, 0) <= 20 and 11 <= att.get(2026, 0) <= 15 and att.get(2022, 0) == max(att.values()),
        "Attrition is measured on the whole firm, but only the simulated pool leaves (real SF records carry ~20 "
        "terminations); either measure on the simulated pool only or raise simulated leavers (CP-02 ATTRITION)")

    r = q("""SELECT IFF(DELIVERY_MODEL = 'HUMAN', 'PEOPLE_ONLY', 'PEOPLE_AGENTS') k, SUM(MARGIN_TD) / SUM(REVENUE_TD) m,
                    MEDIAN(CPI) cpi, COUNT(*) n
             FROM ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_HEALTH
             WHERE MD_GROUP_ID = 'FS' AND STATUS_AS_OF <> 'NOT_STARTED' AND LAST_ACTIVE_MONTH >= '2025-10-01' GROUP BY 1""")
    d = {x["K"]: x for x in r}
    gap = 100 * (f(d["PEOPLE_AGENTS"]["M"]) - f(d["PEOPLE_ONLY"]["M"]))
    add("A5", "AI return (FY26, FS): People+Agents vs People-only", "margin ~+10 pts (7-13); CPI > 1.1 vs ~1.0",
        f"margin {100 * f(d['PEOPLE_AGENTS']['M']):.1f} % vs {100 * f(d['PEOPLE_ONLY']['M']):.1f} % ({gap:+.1f} pts); "
        f"median CPI {f(d['PEOPLE_AGENTS']['CPI']):.2f} vs {f(d['PEOPLE_ONLY']['CPI']):.2f} (n {d['PEOPLE_AGENTS']['N']} / {d['PEOPLE_ONLY']['N']})",
        7 <= gap <= 13 and f(d["PEOPLE_AGENTS"]["CPI"]) > 1.1,
        "Agent hours are billed as cost but not priced into the contract: raise HUMAN_AGENT / AGENT_LED sold margin "
        "(contract value) or their productivity in the generator (CP-02)")

    r = q("""SELECT IS_ABOVE_MEDIAN_INTENSITY hi, SIZE_CLASS, COUNT(*) n, AVG(IS_WON::INT) w
             FROM ACOCO_L2.PIPELINE_PRESALES.DT_OPPORTUNITY_FACT WHERE IS_CLOSED GROUP BY 1, 2""")
    def wavg(rows, flag):
        rs = [x for x in rows if x["HI"] == flag]
        return sum(f(x["W"]) * x["N"] for x in rs) / sum(x["N"] for x in rs)
    hi, lo = wavg(r, True), wavg(r, False)
    add("A6", "Pre-sales intensity and win-rate (within size class)", "above-median ~50 % vs below ~30 % (gap 15-25 pts)",
        f"above {100 * hi:.1f} % vs below {100 * lo:.1f} % (gap {100 * (hi - lo):.1f} pts; firm win-rate {100 * (hi + lo) / 2:.0f} %)",
        0.15 <= hi - lo <= 0.25 and 0.40 <= hi <= 0.60,
        "Effect direction right but the base win-rate is ~58 % (design ~40 %): lower the generator's base win "
        "probability (CP-02)")

    r = {x["B"]: x for x in q("""SELECT SKILL_FIT_BAND b, COUNT(*) n, AVG(IS_WON::INT) w FROM ACOCO_L2.PIPELINE_PRESALES.DT_OPPORTUNITY_FACT
                                  WHERE IS_CLOSED GROUP BY 1""")}
    hi, lo = f(r["HIGH (>= 0.8)"]["W"]), f(r["LOW (< 0.5)"]["W"])
    add("A7", "Pursuit-team skill fit and win-rate", "fit >= 0.8 ~55 % vs < 0.5 ~30 % (gap >= 15 pts)",
        f"high {100 * hi:.1f} % (n {r['HIGH (>= 0.8)']['N']}) vs low {100 * lo:.1f} % (n {r['LOW (< 0.5)']['N']})",
        hi - lo >= 0.15,
        "The generator draws the win outcome without reference to team skill fit: make win probability depend on the "
        "assigned team's coverage of the required skills (CP-02)")

    r = q("""SELECT YEAR(DATEADD(month, 3, h.FORECAST_END)) fy, COUNT(*) closed, COUNT(a.ASSET_ID) harvested
             FROM ACOCO_L2.ONTOLOGY.ENT_PROJECT h
             LEFT JOIN (SELECT DISTINCT SOURCE_PROJECT_ID, MIN(ASSET_ID) ASSET_ID FROM ACOCO_L2.ONTOLOGY.ENT_ASSET GROUP BY 1) a
               ON a.SOURCE_PROJECT_ID = h.PROJECT_ID
             WHERE h.STATUS_AS_OF = 'CLOSED' GROUP BY 1 ORDER BY 1""")
    hr = {x["FY"]: round(100 * x["HARVESTED"] / x["CLOSED"], 0) for x in r if x["FY"] and 2022 <= x["FY"] <= 2026}
    c = {x["R"]: f(x["CPI"]) for x in q("""SELECT REUSED_ASSET r, MEDIAN(CPI) cpi FROM ACOCO_L2.PROJECT_DELIVERY.DT_PROJECT_HEALTH
                                          WHERE STATUS_AS_OF <> 'NOT_STARTED' GROUP BY 1""")}
    m = one(f"""SELECT COUNT(*) n FROM ACOCO_L2.ONTOLOGY.ENT_ASSET WHERE WORK_TYPE = '{s['WORK_TYPE']}'
               AND HARVEST_DATE <= (SELECT PLANNED_START FROM ACOCO_L2.ONTOLOGY.ENT_PROJECT WHERE PROJECT_ID = '{s['PROJECT_ID']}')""")
    add("A8", "Asset harvest and reuse", "harvest FY22 ~15 % -> FY26 ~40 %; reuse CPI ~1.05 vs ~0.95; story project reused none of 2-3 matching assets",
        f"harvest by FY {hr}; median CPI reuse {c[True]:.3f} vs none {c[False]:.3f}; story project uses {s['ASSET_USES']}, "
        f"matching assets available at its start {m['N']}",
        10 <= hr.get(2022, 0) <= 20 and 35 <= hr.get(2026, 0) <= 45 and c[True] > c[False] and s["ASSET_USES"] == 0 and m["N"] >= 2,
        "Calibrate HARVEST_P by FY and the number of assets matching the story project's work type (CP-02)")

    r = one("""SELECT SUM(DELIVERY_HOURS) / SUM(AVAILABLE_HOURS) d, SUM(BID_HOURS) / SUM(AVAILABLE_HOURS) b,
                      SUM(LEARNING_HOURS) / SUM(AVAILABLE_HOURS) l, SUM(ADMIN_HOURS) / SUM(AVAILABLE_HOURS) a,
                      SUM(BENCH_HOURS) / SUM(AVAILABLE_HOURS) bn
               FROM ACOCO_L2.PORTFOLIO_360.DT_CAPACITY_MIX_MONTH WHERE MD_GROUP_ID = 'FS' AND FISCAL_YEAR = 2026""")
    v = {k: 100 * f(r[k]) for k in ("D", "B", "L", "A", "BN")}
    add("A9", "Time mix (FS, FY26)", "Delivery ~72 (70-74) / Bid ~16 (14-18) / Learning ~10 (8-12) / Admin ~1.5 (< 5) / Bench ~1.7 (< 3) %",
        f"Delivery {v['D']:.1f} / Bid {v['B']:.1f} / Learning {v['L']:.1f} / Admin {v['A']:.1f} / Bench {v['BN']:.1f} %",
        70 <= v["D"] <= 74 and 14 <= v["B"] <= 18 and 8 <= v["L"] <= 12 and v["A"] < 5 and v["BN"] < 3)

    rows = q("""SELECT PERSON_ID, STRATUM, AI_ACTIVE, AI_SKILLED_INACTIVE, EARNED_HOURS, DELIVERY_HOURS
                FROM ACOCO_L2.AI_ADOPTION.DT_AI_PRODUCTIVITY WHERE MD_GROUP_ID = 'FS' AND FISCAL_YEAR = 2026""")
    pt, lo, hi = stratified_uplift(rows, rng)
    inact = [x for x in rows if x["AI_SKILLED_INACTIVE"]]
    rest = [x for x in rows if not x["AI_ACTIVE"] and not x["AI_SKILLED_INACTIVE"]]
    pi = lambda rs: sum(float(x["EARNED_HOURS"]) for x in rs) / sum(float(x["DELIVERY_HOURS"]) for x in rs) if rs else float("nan")
    add("A10", "AI productivity uplift (FS, FY26), within level x work type", "~+0.08 (0.05-0.11), 90 % CI excluding zero; skilled-but-inactive ~0",
        f"uplift {pt:+.3f}, 90 % CI [{lo:+.3f}, {hi:+.3f}] ({len({x['PERSON_ID'] for x in rows})} people); "
        f"skilled-inactive PI {pi(inact):.3f} vs other non-active {pi(rest):.3f}",
        0.05 <= pt <= 0.11 and lo > 0)

    r = {x["AI"]: x for x in q("""SELECT IS_AI_CURRICULUM ai, COUNT(*) n, AVG(PAYBACK) pb, STDDEV(PAYBACK) / SQRT(COUNT(*)) se
                                  FROM ACOCO_L2.AI_ADOPTION.DT_LEARNING_PAYBACK WHERE PAYBACK IS NOT NULL GROUP BY 1""")}
    add("A11", "Learning payback (6 months after vs before, vs matched comparison)", "AI curriculum ~+4 % (+0.03-0.05), significant; non-AI smaller, not significant",
        f"AI {f(r[True]['PB']):+.4f} (se {f(r[True]['SE']):.4f}, n {r[True]['N']:,}); non-AI {f(r[False]['PB']):+.4f} (se {f(r[False]['SE']):.4f})",
        0.03 <= f(r[True]["PB"]) <= 0.05 and f(r[True]["PB"]) > 2 * f(r[True]["SE"]) and f(r[False]["PB"]) < f(r[True]["PB"]),
        "The generator books learning but never raises a learner's productivity afterwards (learn_boost is unused): "
        "apply ~+4 % productivity for 6 months after an AI-curriculum completion (CP-02)")

    r = one("""SELECT COUNT(DISTINCT PERSON_ID) skilled, COUNT(DISTINCT IFF(AI_SKILLED_INACTIVE, PERSON_ID, NULL)) inactive
               FROM ACOCO_L2.AI_ADOPTION.DT_AI_PRODUCTIVITY
               WHERE MD_GROUP_ID = 'FS' AND FISCAL_YEAR = 2026 AND FISCAL_QUARTER = 4 AND AI_SKILL_LEVEL >= 3""")
    pct = r["INACTIVE"] / r["SKILLED"] if r["SKILLED"] else 0
    add("A12", "AI skilled but inactive (FS, Jul-Sep 2026)", "~20 % (15-25) of FS people with AI-skill >= 3 have no AI-tool use",
        f"{r['INACTIVE']} of {r['SKILLED']} ({100 * pct:.0f} %)", 0.15 <= pct <= 0.25,
        "Adjust the share of AI-skilled people with zero telemetry in the generator (CP-02)")

    r = q("""SELECT FISCAL_YEAR, SUM(LARGE_PROJECT_REVENUE) / SUM(REVENUE) s FROM ACOCO_L2.PORTFOLIO_360.DT_PORTFOLIO_MONTH
             WHERE FISCAL_YEAR BETWEEN 2022 AND 2026 GROUP BY 1 ORDER BY 1""")
    ls = {x["FISCAL_YEAR"]: round(100 * f(x["S"]), 1) for x in r}
    tot = one("SELECT SUM(LARGE_PROJECT_REVENUE) / SUM(REVENUE) s FROM ACOCO_L2.PORTFOLIO_360.DT_PORTFOLIO_MONTH")
    add("A13", "Large-project revenue share (portfolio shape)", "0.72-0.79 of revenue",
        f"FY22-26 {100 * f(tot['S']):.1f} %; by FY {ls}", 0.72 <= f(tot["S"]) <= 0.79,
        "Raise the share of Large projects / their contract value in the generator's size mix (CP-02)")
    return a


# ------------------------------------------------------------------------------------------------ reasoning (CP-06)
def reasoning_checks():
    rb = json.loads((ROOT / "logs" / "reasoning_build.json").read_text())
    out = []
    a = rb["attrition"]
    out.append(dict(id="Q1", name="attrition model: hold-out AUC (FY25 snapshots, left in FY26)", expected="> 0.70",
                    actual=f"{a['holdout_auc']:.3f} overall on {a['holdout_rows']:,}; {a['holdout_auc_simulated_pool']:.3f} "
                           f"within the simulated pool ({a['holdout_rows_simulated']}); scored {a['scored_people']:,}",
                    ok=a["holdout_auc"] > 0.70))
    fam = set(rb["forecast"]["families"])
    got = {x["skill_family"]: x["n"] for x in rb["forecast"]["series"]}
    out.append(dict(id="Q2", name="demand forecast for every skill family, 12 months", expected=f"{len(fam)} families x 12",
                    actual=str(got), ok=set(got) == fam and all(v == 12 for v in got.values())))
    for svc, query, flt in [("CSS_PROJECT_COMMENTARY", "why is the project behind schedule",
                             {"@and": [{"@eq": {"MD_GROUP_ID": "FS"}}, {"@eq": {"RAG_STATUS": "RED"}}]}),
                            ("CSS_ASSET_LIBRARY", "data migration accelerator", None)]:
        st = q(f"SHOW CORTEX SEARCH SERVICES LIKE '{svc}' IN SCHEMA ACOCO_L2.REASONING")
        state = (st[0].get("indexing_state"), st[0].get("serving_state")) if st else (None, None)
        body = {"query": query, "limit": 3, "columns": ["SEARCH_TEXT"]}
        if flt:
            body["filter"] = flt
        res = json.loads(q(f"SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW('ACOCO_L2.REASONING.{svc}', '{json.dumps(body)}') r")[0]["R"])["results"]
        out.append(dict(id=f"Q3-{svc}", name=f"search service {svc} active and answering", expected="ACTIVE, 3 results",
                        actual=f"state {state}, {len(res)} results; top: {res[0]['SEARCH_TEXT'][:90] if res else '-'}",
                        ok=state[1] == "ACTIVE" and len(res) == 3))
    r13 = {x["AI_BAND"]: x for x in rb["r13"]}
    act, ina = r13["AI_ACTIVE"], r13["SKILLED_INACTIVE"]
    out.append(dict(id="Q4", name="R13 (FS FY26): AI-active uplift significant; skilled-but-inactive NOT significant",
                    expected="active CI > 0; inactive CI spans 0",
                    actual=f"active {act['UPLIFT']:+.3f} [{act['CI_LOW']:+.3f}, {act['CI_HIGH']:+.3f}]; "
                           f"inactive {ina['UPLIFT']:+.3f} [{ina['CI_LOW']:+.3f}, {ina['CI_HIGH']:+.3f}]",
                    ok=act["CI_LOW"] > 0 and not ina["SIGNIFICANT"]))
    r14 = {(x["SCOPE"], x["CURRICULUM"]): x for x in rb["r14"]}
    ai = r14[("FIRM", "AGENTIC_AI")]
    out.append(dict(id="Q5", name="R14: AI-curriculum learning payback positive and significant", expected="CI > 0",
                    actual=f"{ai['PAYBACK']:+.4f} [{ai['CI_LOW']:+.4f}, {ai['CI_HIGH']:+.4f}], {ai['EPISODES']:,} episodes",
                    ok=ai["CI_LOW"] > 0))
    r = one("""SELECT COUNT(DISTINCT PERSON_ID) p, COUNT(*) n, AVG(MATCH_SCORE) s FROM ACOCO_L2.SERVING.VW_BENCH_TO_PIPELINE""")
    fs = one("""SELECT COUNT(DISTINCT PERSON_ID) p FROM ACOCO_L2.SERVING.VW_BENCH_TO_PIPELINE WHERE MD_GROUP_ID = 'FS'""")
    out.append(dict(id="Q6", name="R1 bench-to-pipeline: every roll-off with skills gets matches", expected="> 0 people, FS included",
                    actual=f"{r['P']} people, {r['N']} matches, mean score {f(r['S']):.3f}; FS {fs['P']}", ok=r["P"] > 0 and fs["P"] > 0))
    m = one("""SELECT COUNT(DISTINCT ASSET_ID) a, COUNT_IF(REUSE_STATUS = 'MISSED') missed FROM ACOCO_L2.SERVING.VW_ASSET_MATCH
               WHERE IS_STORY_PROJECT AND SAME_WORK_TYPE""")
    out.append(dict(id="Q7", name="R12 asset match: story project had matching assets it did not reuse", expected=">= 2 MISSED",
                    actual=f"{m['MISSED']} missed matches over {m['A']} assets", ok=m["MISSED"] >= 2))
    return out


def write_anchor_md(anchors):
    lines = ["# Measured story anchors (PRD 6.3)", "",
             f"Measured {dt.date.today().isoformat()} against ACOCO_L2 as of 2026-10-01 by `tools/validate.py --step anchors`.",
             "Design targets are from PRD 6.3; `MISS` = outside the band, with the proposed fix (decision needed - a",
             "generator change returns to CP-02 and is re-measured here).", "",
             "| ID | Anchor | Design target | Measured | Status | Proposed fix |", "|---|---|---|---|---|---|"]
    for x in anchors:
        lines.append(f"| {x['id']} | {x['anchor']} | {x['design_target']} | {x['measured']} | **{x['status']}** | {x['proposed_fix']} |")
    ok = sum(x["status"] == "OK" for x in anchors)
    lines += ["", f"**{ok} OK, {len(anchors) - ok} MISS** of {len(anchors)}.", ""]
    (ROOT / "plan" / "measured_anchors.md").write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", choices=["marts", "anchors", "reasoning"], required=True)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.step in ("marts", "reasoning"):
        rows = reconcile_marts() if a.step == "marts" else reasoning_checks()
        (ROOT / "logs" / f"validate_{a.step}.json").write_text(json.dumps(rows, indent=1, default=str))
        for r in rows:
            print(f"{'PASS' if r['ok'] else 'FAIL'}  {r['id']}  {r['name']}  ->  {r['actual']}")
        bad = [r for r in rows if not r["ok"]]
        print(f"{a.step}: {len(rows) - len(bad)}/{len(rows)} PASS")
        sys.exit(1 if bad else 0)
    anchors = measure_anchors()
    (ROOT / "logs" / "validate_anchors.json").write_text(json.dumps(anchors, indent=1, default=str))
    write_anchor_md(anchors)
    for x in anchors:
        print(f"{x['status']:<4}  {x['id']:<3}  {x['anchor']}  ->  {x['measured']}")
    print(f"anchors: {sum(x['status'] == 'OK' for x in anchors)}/{len(anchors)} OK (written plan/measured_anchors.md)")


if __name__ == "__main__":
    main()
