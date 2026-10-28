"""Presenter card (CP-11): every spoken figure, re-measured from the registry statement its page runs.

Each item = (id, demo beat, page, claim, registry statement, row pick -> value, format, pinned value, tolerance).
The value is read exactly as the app reads it (same statement, same binds: FS, FY22-FY26, P-0615), checked
against the pinned measured value, and written to docs/PRESENTER_CARD.md with the page and source object.

  python tools/presenter_card.py          # measure, assert, write the card (exit 1 on any drift)
"""
import re
import sys
from pathlib import Path

import snowflake.connector

sys.path.insert(0, str(Path(__file__).parent))
import lint_app as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "service" / "app" / "server" / "src" / "registry.sql"


def f(x):
    return None if x is None else float(x)


def last(rows, col):
    return f(rows[-1][col])


def year(rows, fy, col):
    return f(next(r for r in rows if r["FISCAL_YEAR"] == fy)[col])


def band(rows, col, **eq):
    return f(next(r for r in rows if all(r[k] == v for k, v in eq.items()))[col])


PCT, PTS, USD, USDM, RATIO, NUM, SIGNED = "pct", "pts", "usd", "usdm", "ratio", "num", "signed"

# (id, beat, page, claim, statement, extractor, format, pinned, tolerance, extra binds)
ITEMS = [
    ("F1", "0-3 Framing", "C1", "Firm FY26 revenue", "cx_firm", lambda r: f(r[0]["REVENUE"]), USDM, 327.94e6, 0.5e6, {}),
    ("F2", "0-3 Framing", "C1", "Firm FY26 margin", "cx_firm", lambda r: f(r[0]["MARGIN_PCT"]), PCT, 35.2, 0.05, {}),
    ("F3", "0-3 Framing", "C1", "Firm people at end FY26", "cx_firm", lambda r: f(r[0]["HEADCOUNT_END"]), NUM, 1956, 0, {}),
    ("F4", "0-3 Framing", "C1", "Firm FY26 Delivery share", "cx_firm", lambda r: f(r[0]["DELIVERY_PCT"]), PCT, 70.9, 0.05, {}),
    ("F5", "0-3 Framing", "C1", "Firm FY26 voluntary attrition", "cx_firm", lambda r: f(r[0]["ATTRITION_PCT"]), PCT, 12.9, 0.05, {}),
    ("F6", "0-3 Framing", "C1", "Firm FY26 win-rate", "cx_firm", lambda r: f(r[0]["WIN_RATE_PCT"]), PCT, 49.7, 0.05, {}),
    ("S1", "3-5 Sources", "P8", "Rows read from BDC CLDs (L0)", "ln_layers",
     lambda r: band(r, "ROW_COUNT", LAYER="L0", OBJECT_KIND="CLD"), NUM, 16944014, 0, {}),
    ("S2", "3-5 Sources", "P8", "CLD tables read (L0)", "ln_layers",
     lambda r: band(r, "OBJECTS", LAYER="L0", OBJECT_KIND="CLD"), NUM, 13, 0, {}),
    ("S3", "3-5 Sources", "P8", "Simulated tables (L0, ACOCO_SIM)", "ln_layers",
     lambda r: band(r, "OBJECTS", LAYER="L0", OBJECT_KIND="ACOCO_SIM"), NUM, 34, 0, {}),
    ("O1", "5-8 ProServe360", "P0", "FS FY26 margin", "ov_scorecard", lambda r: year(r, 2026, "MARGIN_PCT"), PCT, 34.3, 0.05, {}),
    ("O2", "5-8 ProServe360", "P0", "FS FY26 margin change vs FY25", "ov_scorecard",
     lambda r: year(r, 2026, "MARGIN_PCT") - year(r, 2025, "MARGIN_PCT"), PTS, -0.7, 0.05, {}),
    ("O3", "5-8 ProServe360", "P0", "FS FY26 revenue", "ov_scorecard", lambda r: year(r, 2026, "REVENUE"), USDM, 70.29e6, 0.1e6, {}),
    ("O4", "5-8 ProServe360", "P0", "FS on-time (active projects)", "ov_on_time", lambda r: f(r[0]["ON_TIME_PCT"]), PCT, 90.0, 0.05, {}),
    ("O5", "5-8 ProServe360", "P0", "FS FY26 win-rate", "ov_scorecard", lambda r: year(r, 2026, "WIN_RATE_PCT"), PCT, 50.0, 0.05, {}),
    ("O6", "5-8 ProServe360", "P0", "FS FY26 Delivery share (target ~70 %)", "ov_scorecard", lambda r: year(r, 2026, "DELIVERY_PCT"), PCT, 71.3, 0.05, {}),
    ("O7", "5-8 ProServe360", "P0", "FS FY26 bench share (allowance ~2 %)", "ov_scorecard", lambda r: year(r, 2026, "BENCH_PCT"), PCT, 1.4, 0.05, {}),
    ("O8", "5-8 ProServe360", "P0", "FS FY26 voluntary attrition", "ov_scorecard", lambda r: year(r, 2026, "ATTRITION_PCT"), PCT, 13.1, 0.05, {}),
    ("D1", "8-14 Operational Excellence", "P1 / P2", "P-0615 (Atlas Bank, Large FS fixed price) forecast margin", "pf_fp_watch",
     lambda r: f(next(x for x in r if x["PROJECT_ID"] == "P-0615")["FORECAST_MARGIN_PCT"]), PCT, -16.9, 0.05, {}),
    ("D2", "8-14 Operational Excellence", "P2", "P-0615 CPI", "pf_fp_watch",
     lambda r: f(next(x for x in r if x["PROJECT_ID"] == "P-0615")["CPI"]), RATIO, 0.70, 0.005, {}),
    ("D3", "8-14 Operational Excellence", "P2", "P-0615 SPI", "pf_fp_watch",
     lambda r: f(next(x for x in r if x["PROJECT_ID"] == "P-0615")["SPI"]), RATIO, 0.96, 0.005, {}),
    ("D4", "8-14 Operational Excellence", "P2", "P-0615 LD exposure", "pf_fp_watch",
     lambda r: f(next(x for x in r if x["PROJECT_ID"] == "P-0615")["LD_EXPOSURE"]), USDM, 1.46e6, 0.01e6, {}),
    ("D5", "8-14 Operational Excellence", "P2 / P11", "P-0615 matching library assets it did not reuse", "pj_assets",
     lambda r: float(len({x["ASSET_ID"] for x in r if x["REUSE_STATUS"] == "MISSED"})), NUM, 3, 0, {}),
    ("D6", "8-14 Operational Excellence", "P11", "FS FY26 harvest rate (FY22 9.1 %)", "as_fy", lambda r: year(r, 2026, "HARVEST_RATE_PCT"), PCT, 29.2, 0.05, {}),
    ("D7", "8-14 Operational Excellence", "P11", "FS FY26 median CPI with reuse", "as_fy", lambda r: year(r, 2026, "CPI_WITH_REUSE"), RATIO, 1.193, 0.005, {}),
    ("D8", "8-14 Operational Excellence", "P11", "FS FY26 median CPI without reuse", "as_fy", lambda r: year(r, 2026, "CPI_WITHOUT_REUSE"), RATIO, 1.105, 0.005, {}),
    ("V1", "14-18 Value Creation", "P5", "FS Large bids, above-median intensity + high fit, win-rate", "pi_win_rate",
     lambda r: band(r, "WIN_RATE_PCT", SIZE_CLASS="Large", INTENSITY_BAND="Above median", SKILL_FIT_BAND="HIGH (>= 0.8)"), PCT, 55.2, 0.05, {}),
    ("V2", "14-18 Value Creation", "P5", "FS Large bids, below-median intensity + low fit, win-rate", "pi_win_rate",
     lambda r: band(r, "WIN_RATE_PCT", SIZE_CLASS="Large", INTENSITY_BAND="Below median", SKILL_FIT_BAND="LOW (< 0.5)"), PCT, 33.3, 0.05, {}),
    ("V3", "14-18 Value Creation", "P5", "FS open bids", "pi_open", lambda r: float(len(r)), NUM, 22, 0, {}),
    ("P1", "18-24 People Development", "P3", "FS people rolling off in the next 90 days", "wf_roll_off", lambda r: float(len(r)), NUM, 36, 0, {}),
    ("P2", "18-24 People Development", "P3", "... of whom below the pipeline's AI-skill level", "wf_roll_off",
     lambda r: 100.0 * sum(bool(x["BELOW_PIPELINE_AI_LEVEL"]) for x in r) / len(r), PCT, 88.9, 0.05, {}),
    ("P3", "18-24 People Development", "P6", "FS AI-active productivity uplift FY26 (90 % CI [+9.8, +13.8 %], significant)", "ov_ai_uplift",
     lambda r: 100 * band(r, "UPLIFT", AI_BAND="AI_ACTIVE"), SIGNED, 11.85, 0.05, {}),
    ("P4", "18-24 People Development", "P6", "FS skilled-but-inactive uplift (CI spans zero: no significant effect)", "ov_ai_uplift",
     lambda r: 100 * band(r, "UPLIFT", AI_BAND="SKILLED_INACTIVE"), SIGNED, 2.6, 0.05, {}),
    ("P5", "18-24 People Development", "P6", "FS people AI-skilled (3+) but not using AI tools, FY26 (test band)", "ai_test",
     lambda r: band(r, "PEOPLE_IN_BAND", STRATUM="ALL LEVELS", AI_BAND="SKILLED_INACTIVE"), NUM, 37, 0, {}),
    ("P6", "18-24 People Development", "P6", "FS Agentic-AI curriculum payback (significant)", "ai_payback",
     lambda r: 100 * band(r, "PAYBACK", CURRICULUM="AGENTIC_AI"), SIGNED, 3.66, 0.05, {}),
    ("P7", "18-24 People Development", "P6", "FS margin, Human + Agent delivery", "ai_delivery_model",
     lambda r: band(r, "MARGIN_PCT", DELIVERY_MODEL="HUMAN_AGENT"), PCT, 40.7, 0.05, {}),
    ("P8", "18-24 People Development", "P6", "FS margin, Human-only delivery", "ai_delivery_model",
     lambda r: band(r, "MARGIN_PCT", DELIVERY_MODEL="HUMAN"), PCT, 26.3, 0.05, {}),
    ("R1", "24-28 What-if", "P7", "FS projects forecast to finish at a loss", "rs_margin_leak", lambda r: float(len(r)), NUM, 1, 0, {}),
]


def fmt(v, kind):
    if kind == USDM:
        return f"${v / 1e6:,.2f}M" if abs(v) >= 1e6 else f"${v:,.0f}"
    if kind == PCT:
        return f"{v:.1f} %"
    if kind == PTS:
        return f"{v:+.1f} pts"
    if kind == SIGNED:
        return f"{v:+.1f} %"
    if kind == RATIO:
        return f"{v:.2f}"
    return f"{v:,.0f}"


def source_objects(sql):
    return sorted(set(re.findall(r"ACOCO_L2\.[A-Z_]+\.[A-Z0-9_]+", sql)))


def measure():
    stmts = {n: (b, s) for n, b, s in L.parse_registry(REG.read_text())}
    con = snowflake.connector.connect(connection_name="sfseapac_kp", paramstyle="qmark",
                                      session_parameters={"QUERY_TAG": "ACOCO_CARD"})
    cur = con.cursor(snowflake.connector.DictCursor)
    cur.execute("USE WAREHOUSE WH_ACOCO_APP")
    cache, out = {}, []
    try:
        for iid, beat, page, claim, name, pick, kind, pinned, tol, extra in ITEMS:
            binds, sql = stmts[name]
            if name not in cache:
                cur.execute(sql, [extra.get(b, L.DEFAULTS[b]) for b in binds])
                cache[name] = cur.fetchall()
            try:
                v = pick(cache[name])
                ok = v is not None and abs(v - pinned) <= tol + 1e-9
            except (StopIteration, ZeroDivisionError, TypeError, KeyError):
                v, ok = None, False
            out.append(dict(id=iid, beat=beat, page=page, claim=claim, statement=name, objects=source_objects(sql),
                            value=v, shown="-" if v is None else fmt(v, kind), pinned=fmt(pinned, kind), ok=ok))
    finally:
        con.close()
    return out


def write_card(items):
    lines = ["# ACoCo ProServe360 - Presenter card", "",
             "Measured figures only, as of 1 Oct 2026 (FY26 closed). Default view: **Business Group Financial Services (FS)**, "
             "FY22-FY26, all sizes, story project **P-0615**. Every row is re-measured by `tools/presenter_card.py` "
             "(also `tools/validate.py --step card`) from the same registry statement the page runs.", "",
             "Honesty lines: simulated rows are demo data; hours saved are ESTIMATED; AI results are associations within "
             "level x work type (90 % CI), never causation; the attrition list is a conversation prompt, not a prediction.", "",
             "Timing (dry run `logs/dry_run_cp11.md`): every page loads in about 1-2 s after the warm-up (`docs/RUNBOOK.md`). "
             "The Advisor takes about 1 minute for a simple question and about 2 minutes for the PMD-11 what-if - ask it at "
             "the start of the 24-28 beat and walk through P7 while it runs.", ""]
    beat = None
    for x in items:
        if x["beat"] != beat:
            beat = x["beat"]
            lines += ["", f"## {beat} min", "", "| # | Page | Say | Figure | Source (registry statement -> object) |", "|---|---|---|---|---|"]
        lines.append(f"| {x['id']} | {x['page']} | {x['claim']} | **{x['shown']}** | `{x['statement']}` -> {', '.join(x['objects'])} |")
    ok = sum(x["ok"] for x in items)
    lines += ["", f"_{ok} / {len(items)} figures verified against the pinned measured values._", ""]
    (ROOT / "docs" / "PRESENTER_CARD.md").write_text("\n".join(lines))


def main():
    items = measure()
    for x in items:
        print(f"{'PASS' if x['ok'] else 'FAIL'}  {x['id']:<3} {x['page']:<9} {x['claim'][:60]:<60} {x['shown']:>12}  (pinned {x['pinned']})")
    write_card(items)
    bad = [x for x in items if not x["ok"]]
    print(f"card: {len(items) - len(bad)}/{len(items)} PASS (written docs/PRESENTER_CARD.md)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
