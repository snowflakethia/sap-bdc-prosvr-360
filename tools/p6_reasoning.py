"""P6 reasoning (spec docs/spec_p6_productivity.md v0.4, section 3): WPS-based tests R13w, R14w, R15-R18.

  .venv/bin/python tools/p6_reasoning.py            all
  .venv/bin/python tools/p6_reasoning.py r15 r16    any subset of r13w r14w r15 r16 r17 r18

Method (spec 3): every test is within level; strata = fiscal year x MD group (firm scope) or fiscal year (group scope);
statistic = Spearman rho on ranks centred within stratum; R16 / R18 use the partial rho holding the other products /
curricula constant (their usage moves together); 90 % person-cluster bootstrap (5th / 95th), seed 20261001,
1000 resamples for ALL LEVELS, 400 per level cell. Small cells (spec 3.1): >= 15 people and >= 30 person-quarters,
group scope pooled FY24-26. Wording: "associated with", never "causes".
Bootstraps reuse per-person sums (counts drawn once per resample), so the full build runs in well under 5 minutes.
"""
import collections
import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402
from build_reasoning import write_table, log_update, SEED  # noqa: E402

LEVELS = ["Analyst", "Consultant", "Manager", "Senior Manager", "Principal"]
YEARS = (2024, 2025, 2026)
MIN_PEOPLE, MIN_PQ = 15, 30
MIN_RHO = 0.05      # practical-significance floor (decision 2026-11-05, D-P6-25): smaller CI-excluding-zero = NEGLIGIBLE
TARGET_COL = {"EFF": "S_EFF", "SCHED": "S_SCHED", "WIN": "S_WIN", "BILL": "S_BILL", "TEAM": "TM"}
OUTCOME_COL = {"WPS": "WPS", "OE": "OE", "WIN": "S_WIN", "WPS_EX_LEARN": "WPS_EX_LEARN"}


def frame(sql):
    df = pd.DataFrame(sf.query(sql))
    for c in df.columns:
        if c not in ("PERSON_ID", "LEVEL", "MD_GROUP_ID", "PRODUCT", "MODEL_FAMILY", "CURRICULUM", "TARGET_INPUT"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load():
    w = frame("""SELECT PERSON_ID, FISCAL_YEAR, FISCAL_QUARTER, FISCAL_YEAR * 4 + FISCAL_QUARTER AS QIDX, LEVEL, LEVEL_SORT,
                        MD_GROUP_ID, DELIVERY_HOURS, WPS, WPS_EX_LEARN, VC, OE, PD, TM, S_WIN, S_EFF, S_SCHED, S_BILL,
                        LEARNING_HOURS / NULLIF(AVAILABLE_HOURS, 0) AS LEARN_SHARE_NOW
                 FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_QUARTER_WPS""")
    t = frame("""SELECT PERSON_ID, FISCAL_YEAR * 4 + FISCAL_QUARTER AS QIDX, PRODUCT, MODEL_FAMILY, TOKENS
                 FROM ACOCO_L2.AI_ADOPTION.DT_AI_TOKENS_PERSON_QUARTER""")
    l = frame("""SELECT PERSON_ID, FISCAL_YEAR * 4 + FISCAL_QUARTER AS QIDX, CURRICULUM, LEARNING_HOURS
                 FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_LEARNING_PERSON_QUARTER""")
    a = frame("""SELECT PERSON_ID, FISCAL_YEAR * 4 + FISCAL_QUARTER AS QIDX, IFF(BOOLOR_AGG(AI_ACTIVE), 1, 0) AS AI_ACTIVE
                 FROM ACOCO_L2.AI_ADOPTION.DT_AI_PRODUCTIVITY GROUP BY 1, 2""")
    cat = frame("SELECT CURRICULUM, TARGET_INPUT FROM ACOCO_L2.ONTOLOGY.ENT_LEARNING_CATEGORY")
    # industry-skill proficiency at the quarter (latest assessment <= quarter end): opportunities require the group's
    # industry skill and skill fit drives WIN (A7), so R18 holds it constant (D-P6-27)
    ind = frame("""SELECT w.PERSON_ID, w.FISCAL_YEAR * 4 + w.FISCAL_QUARTER AS QIDX, MAX(ps.PROFICIENCY) AS IND_SKILL
                   FROM ACOCO_L2.WORKFORCE_PERFORMANCE.DT_PERSON_QUARTER_WPS w
                   JOIN ACOCO_L1.TALENT.PERSON_SKILL ps ON ps.PERSON_ID = w.PERSON_ID AND ps.ASSESSED_DATE <= w.Q_END
                   JOIN ACOCO_L2.ONTOLOGY.ENT_SKILL s ON s.SKILL_ID = ps.SKILL_ID AND s.SKILL_FAMILY = 'INDUSTRY'
                   GROUP BY 1, 2""")
    w = w.merge(ind, on=["PERSON_ID", "QIDX"], how="left")
    w["IND_SKILL"] = w.IND_SKILL.fillna(0)
    # Complete history only: trailing-4-quarter inputs (ACREATE, AREUSE, WIN) and the 2-quarter learning lag are only
    # comparable for people scored in the 3 quarters before (otherwise "has prior exposure" stands in for tenure).
    have = set(zip(w.PERSON_ID, w.QIDX))
    w["FULL_HISTORY"] = [all((p, q - k) in have for k in (1, 2, 3)) for p, q in zip(w.PERSON_ID, w.QIDX)]
    w = w[w.FULL_HISTORY].drop(columns="FULL_HISTORY").reset_index(drop=True)
    return w, t, l, a, cat


# ------------------------------------------------------------------------------------------------ engine
def centred_ranks(df, cols, strata):
    """Percent ranks within stratum, centred on the stratum mean (so the pooled correlation is within-stratum)."""
    g = df.groupby(strata, sort=False)
    out = np.empty((len(df), len(cols)))
    for j, c in enumerate(cols):
        r = g[c].rank(pct=True)
        out[:, j] = (r - r.groupby([df[s] for s in strata]).transform("mean")).values
    return out


def rho_cells(df, y, x, controls, strata, n_boot, rng):
    """Spearman (partial if controls) of y with x within strata, with a person-cluster bootstrap CI."""
    cols = [y, x] + list(controls)
    d = df.dropna(subset=cols)
    people, pq = d.PERSON_ID.nunique(), len(d)
    if people < MIN_PEOPLE or pq < MIN_PQ:
        return dict(RHO=None, CI_LOW=None, CI_HIGH=None, CI_EXCLUDES_ZERO=False, SIGNIFICANT=False, EFFECT_SIZE=None,
                    PEOPLE=people, PERSON_QUARTERS=pq, CELL_STATUS=f"INSUFFICIENT_DATA ({people} people)")
    R = centred_ranks(d, cols, strata)
    pid, inv = np.unique(d.PERSON_ID.values, return_inverse=True)
    k = len(cols)
    M = np.zeros((len(pid), k, k))
    np.add.at(M, inv, R[:, :, None] * R[:, None, :])          # per-person sums of rank cross-products

    def corr(C):
        if k == 2:
            return C[..., 0, 1] / np.sqrt(C[..., 0, 0] * C[..., 1, 1])
        P = np.linalg.pinv(C)
        return -P[..., 0, 1] / np.sqrt(P[..., 0, 0] * P[..., 1, 1])

    point = float(corr(M.sum(axis=0)))
    W = rng.multinomial(len(pid), np.full(len(pid), 1.0 / len(pid)), size=n_boot).astype(float)
    bs = corr(np.einsum("bp,pij->bij", W, M))
    lo, hi = np.nanpercentile(bs, [5, 95])
    excl = bool(lo > 0 or hi < 0)
    sig = excl and abs(point) >= MIN_RHO
    return dict(RHO=point, CI_LOW=float(lo), CI_HIGH=float(hi), CI_EXCLUDES_ZERO=excl, SIGNIFICANT=sig,
                EFFECT_SIZE="MATERIAL" if sig else "NEGLIGIBLE" if excl else "NOT_SIGNIFICANT", PEOPLE=people,
                PERSON_QUARTERS=pq, CELL_STATUS="OK")


def scopes(df, by_year=True):
    """(scope, fiscal-year label, rows, strata): firm per FY and pooled; MD groups pooled FY24-26 (spec 3.1)."""
    d = df[df.FISCAL_YEAR.isin(YEARS)]
    out = [("FIRM", "FY24-26", d, ["FISCAL_YEAR", "MD_GROUP_ID"])]
    if by_year:
        out += [("FIRM", f"FY{y % 100}", d[d.FISCAL_YEAR == y], ["MD_GROUP_ID"]) for y in YEARS]
    out += [(g, "FY24-26 pooled", d[d.MD_GROUP_ID == g], ["FISCAL_YEAR"]) for g in sorted(d.MD_GROUP_ID.unique())]
    return out


def run_test(df, tests, rng, by_year=True):
    """tests: list of (labels dict, y, x, controls). Rows per scope x stratum (ALL LEVELS + each level)."""
    rows = []
    for scope, fy, sd, strata in scopes(df, by_year):
        for stratum in ["ALL LEVELS"] + LEVELS:
            cell = sd if stratum == "ALL LEVELS" else sd[sd.LEVEL == stratum]
            st = strata + (["LEVEL"] if stratum == "ALL LEVELS" else [])
            for labels, y, x, controls in tests:
                r = rho_cells(cell, y, x, controls, st, 1000 if stratum == "ALL LEVELS" else 400, rng)
                rows.append(dict(SCOPE=scope, FISCAL_YEARS=fy, STRATUM=stratum, **labels, **r))
    return rows


def quintiles(df, x, y, users_only_label="NON_USER"):
    """Mean outcome by exposure quintile within level (firm, FY24-26); zero exposure is its own bucket."""
    d = df[df.FISCAL_YEAR.isin(YEARS)].dropna(subset=[x, y]).copy()
    out = []
    for lvl in LEVELS:
        s = d[d.LEVEL == lvl].copy()
        pos = s[x] > 0
        s["BUCKET"] = users_only_label
        if pos.sum() >= 5:
            s.loc[pos, "BUCKET"] = pd.qcut(s.loc[pos, x].rank(method="first"), 5, labels=[f"Q{i}" for i in range(1, 6)]).astype(str)
        for b, g in s.groupby("BUCKET"):
            out.append(dict(LEVEL=lvl, LEVEL_SORT=LEVELS.index(lvl) + 1, BUCKET=b, PERSON_QUARTERS=len(g),
                            PEOPLE=int(g.PERSON_ID.nunique()), EXPOSURE_MEDIAN=float(g[x].median()),
                            OUTCOME_MEAN=float(g[y].mean())))
    return out


def summarise(name, rows, keys):
    firm = [r for r in rows if r["SCOPE"] == "FIRM" and r["FISCAL_YEARS"] == "FY24-26"]
    log_update(name, firm)
    for r in firm:
        lab = " ".join(str(r[k]) for k in keys)
        rho = "n/a" if r["RHO"] is None else f"{r['RHO']:+.3f} [{r['CI_LOW']:+.3f}, {r['CI_HIGH']:+.3f}]"
        print(f"{name} {r['STRATUM']:<15} {lab:<34} rho {rho} {'SIG' if r['SIGNIFICANT'] else ''}")


# ------------------------------------------------------------------------------------------------ tests
def with_tokens(w, t):
    t = t.copy()
    t["EXPOSURE"] = np.where(t.PRODUCT == "CORTEX", "CORTEX_" + t.MODEL_FAMILY, t.PRODUCT)
    piv = t.pivot_table(index=["PERSON_ID", "QIDX"], columns="EXPOSURE", values="TOKENS", aggfunc="sum", fill_value=0)
    piv["CORTEX"] = piv.filter(like="CORTEX_").sum(axis=1)
    piv["ALL_TOKENS"] = piv[["CODEX", "CLAUDE_CODE", "CORTEX"]].sum(axis=1)
    d = w.merge(piv.reset_index(), on=["PERSON_ID", "QIDX"], how="left")
    for c in piv.columns:
        d[c] = d[c].fillna(0)
        d["X_" + c] = np.log1p(d[c] / d.DELIVERY_HOURS.where(d.DELIVERY_HOURS > 0))   # LN(1 + tokens / delivery h)
    return d


def r15(w, t, rng):
    d = with_tokens(w, t)
    rows = run_test(d, [(dict(EXPOSURE="ALL_TOKENS", OUTCOME="WPS"), "WPS", "X_ALL_TOKENS", [])], rng)
    write_table("TOKEN_WPS_TEST", rows, "R15 (Q3): Spearman rho of LN(1 + tokens per delivery hour) with WPS within "
                "level, strata FY x group; 90 % person-cluster bootstrap CI; association, not causation")
    write_table("TOKEN_WPS_QUINTILE", quintiles(d, "X_ALL_TOKENS", "WPS"),
                "R15 (Q3): mean WPS by token-intensity quintile within level, FY24-26 firm; NON_USER = no tokens")
    summarise("r15", rows, ["EXPOSURE"])


def r16(w, t, rng):
    d = with_tokens(w, t)
    prods = ["CORTEX", "CLAUDE_CODE", "CODEX"]
    fams = ["CORTEX_CLAUDE", "CORTEX_GPT", "CORTEX_OPEN"]
    tests = []
    for out in ("WPS", "OE", "WIN"):
        for p in prods:
            tests.append((dict(EXPOSURE=p, EXPOSURE_KIND="PRODUCT", OUTCOME=out), OUTCOME_COL[out], "X_" + p,
                          ["X_" + o for o in prods if o != p]))
        for f in fams:
            tests.append((dict(EXPOSURE=f, EXPOSURE_KIND="CORTEX_MODEL_FAMILY", OUTCOME=out), OUTCOME_COL[out], "X_" + f,
                          ["X_" + o for o in fams + prods[1:] if o != f]))
    rows = run_test(d, tests, rng, by_year=False)
    write_table("VENDOR_WPS_TEST", rows, "R16 (Q4): partial Spearman rho of a product's (or Cortex model family's) "
                "token intensity with WPS / OE / WIN score, holding the other products constant, within level; "
                "90 % person-cluster bootstrap CI; association, not causation")
    summarise("r16", [r for r in rows if r["EXPOSURE_KIND"] == "PRODUCT"], ["EXPOSURE", "OUTCOME"])


def with_learning(w, l, lag_from=1, lag_to=2):
    """Hours per curriculum and in total in the 2 quarters before each person-quarter (spec 3: Q5 / Q6)."""
    piv = l.pivot_table(index=["PERSON_ID", "QIDX"], columns="CURRICULUM", values="LEARNING_HOURS", aggfunc="sum",
                        fill_value=0)
    curr = list(piv.columns)
    piv["ALL_LEARNING"] = piv.sum(axis=1)
    piv = piv.reset_index()
    parts = []
    for lag in range(lag_from, lag_to + 1):
        p = piv.copy()
        p["QIDX"] = p.QIDX + lag
        parts.append(p)
    lagged = pd.concat(parts).groupby(["PERSON_ID", "QIDX"]).sum().reset_index()
    d = w.merge(lagged, on=["PERSON_ID", "QIDX"], how="left")
    for c in curr + ["ALL_LEARNING"]:
        d["H_" + c] = d[c].fillna(0)
    return d, curr


def r17(w, l, rng):
    d, _ = with_learning(w, l)
    # current-quarter learning share held constant: the yearly learning budget makes prior and current learning
    # substitutes, so prior hours would otherwise pick up the billable time freed this quarter (D-P6-20)
    rows = run_test(d, [(dict(EXPOSURE="ALL_LEARNING", OUTCOME="WPS_EX_LEARN"), "WPS_EX_LEARN", "H_ALL_LEARNING",
                         ["LEARN_SHARE_NOW"])], rng)
    write_table("TRAINING_WPS_TEST", rows, "R17 (Q5): partial Spearman rho of training hours in the 2 prior quarters with "
                "WPS excluding the learning input, holding current-quarter learning share constant, within level; "
                "90 % person-cluster bootstrap CI; association, not causation")
    write_table("TRAINING_WPS_QUINTILE", quintiles(d, "H_ALL_LEARNING", "WPS_EX_LEARN", "NO_TRAINING"),
                "R17 (Q5): mean WPS (excl. learning) by prior-2-quarter training-hours quintile within level, FY24-26 firm")
    summarise("r17", rows, ["EXPOSURE"])


def r18(w, l, cat, rng):
    d, curr = with_learning(w, l)
    target = dict(zip(cat.CURRICULUM, cat.TARGET_INPUT))
    tests = []
    for c in curr:
        ctrl = ["H_" + o for o in curr if o != c] + ["LEARN_SHARE_NOW", "IND_SKILL"]
        tests.append((dict(CURRICULUM=c, TARGET_INPUT=target.get(c), OUTCOME="WPS_EX_LEARN"), "WPS_EX_LEARN", "H_" + c, ctrl))
        tests.append((dict(CURRICULUM=c, TARGET_INPUT=target.get(c), OUTCOME="TARGET:" + target.get(c, "")),
                      TARGET_COL[target[c]], "H_" + c, ctrl))
    rows = run_test(d, tests, rng, by_year=False)
    write_table("CURRICULUM_WPS_TEST", rows, "R18 (Q6): partial Spearman rho of a curriculum's hours in the 2 prior "
                "quarters with WPS excl. learning and with its target input score, holding the other curricula constant, "
                "within level; 90 % person-cluster bootstrap CI; association, not causation")
    summarise("r18", rows, ["CURRICULUM", "OUTCOME"])


def r13w(w, a, rng):
    """R13 re-based: WPS of AI-active person-quarters minus the rest, within level x group x FY strata."""
    d = w[w.FISCAL_YEAR.isin(YEARS)].merge(a, on=["PERSON_ID", "QIDX"], how="left")
    d["AI_ACTIVE"] = d.AI_ACTIVE.fillna(0)
    rows = []
    for scope, fy, sd, strata in scopes(d):
        for stratum in ["ALL LEVELS"] + LEVELS:
            cell = sd if stratum == "ALL LEVELS" else sd[sd.LEVEL == stratum]
            n_act = int(cell[cell.AI_ACTIVE == 1].PERSON_ID.nunique())
            if n_act < MIN_PEOPLE or cell.PERSON_ID.nunique() < MIN_PEOPLE:
                rows.append(dict(SCOPE=scope, FISCAL_YEARS=fy, STRATUM=stratum, PEOPLE_ACTIVE=n_act,
                                 PEOPLE=int(cell.PERSON_ID.nunique()), UPLIFT_WPS=None, CI_LOW=None, CI_HIGH=None,
                                 SIGNIFICANT=False, CELL_STATUS=f"INSUFFICIENT_DATA ({n_act} active)"))
                continue
            key = cell[strata + ["LEVEL"]].astype(str).agg("|".join, axis=1)
            s_id, s_inv = np.unique(key.values, return_inverse=True)
            p_id, p_inv = np.unique(cell.PERSON_ID.values, return_inverse=True)
            A = np.zeros((len(p_id), len(s_id), 4))           # per person x stratum: sum y / n, active and rest
            act = cell.AI_ACTIVE.values == 1
            y = cell.WPS.values
            np.add.at(A, (p_inv, s_inv, np.where(act, 0, 2)), y)
            np.add.at(A, (p_inv, s_inv, np.where(act, 1, 3)), 1)

            def est(S):
                ok = (S[..., 1] > 0) & (S[..., 3] > 0)
                diff = np.where(ok, S[..., 0] / np.where(ok, S[..., 1], 1) - S[..., 2] / np.where(ok, S[..., 3], 1), 0)
                wgt = np.where(ok, S[..., 1] + S[..., 3], 0)
                return (diff * wgt).sum(axis=-1) / wgt.sum(axis=-1)

            pt = float(est(A.sum(axis=0)))
            W = rng.multinomial(len(p_id), np.full(len(p_id), 1.0 / len(p_id)),
                                size=1000 if stratum == "ALL LEVELS" else 400).astype(float)
            lo, hi = np.nanpercentile(est(np.einsum("bp,psk->bsk", W, A)), [5, 95])
            rows.append(dict(SCOPE=scope, FISCAL_YEARS=fy, STRATUM=stratum, PEOPLE_ACTIVE=n_act,
                             PEOPLE=int(cell.PERSON_ID.nunique()), UPLIFT_WPS=pt, CI_LOW=float(lo), CI_HIGH=float(hi),
                             SIGNIFICANT=bool(lo > 0 or hi < 0), CELL_STATUS="OK"))
    write_table("AI_WPS_TEST", rows, "R13 re-based on WPS: mean WPS of AI-active person-quarters minus the rest within "
                "level x group x FY strata (weighted); 90 % person-cluster bootstrap CI; association, not causation")
    firm = [r for r in rows if r["SCOPE"] == "FIRM" and r["FISCAL_YEARS"] == "FY24-26"]
    log_update("r13w", firm)
    for r in firm:
        v = "n/a" if r["UPLIFT_WPS"] is None else f"{r['UPLIFT_WPS']:+.2f} [{r['CI_LOW']:+.2f}, {r['CI_HIGH']:+.2f}]"
        print(f"r13w {r['STRATUM']:<15} WPS uplift {v} {'SIG' if r['SIGNIFICANT'] else ''}")


def r14w(w, l, rng):
    """R14 re-based: WPS (excl. learning) change from the 2 quarters before to the 2 after a curriculum episode, minus
    the same change for same-level people without that curriculum in the +/- 2 quarters (matched comparison)."""
    y = w.set_index(["PERSON_ID", "QIDX"]).WPS_EX_LEARN
    lv = w.groupby("PERSON_ID").LEVEL.first()
    grp = w.groupby("PERSON_ID").MD_GROUP_ID.first()
    base = w[["PERSON_ID", "QIDX", "LEVEL"]].copy()

    def win(q_off):
        k = pd.MultiIndex.from_arrays([base.PERSON_ID, base.QIDX + q_off])
        return y.reindex(k).values
    before = np.nanmean(np.vstack([win(-1), win(-2)]), axis=0)
    after = np.nanmean(np.vstack([win(1), win(2)]), axis=0)
    base["CHANGE"] = after - before
    base = base.dropna(subset=["CHANGE"])
    # AI-year status (any AI-curriculum hours in the fiscal year): the comparison is matched on it, because AI-year
    # learners get the AI-curriculum uplift and non-AI curricula are taken in non-AI years (D-P6-20)
    ai_fy = l[l.CURRICULUM.isin(["AGENTIC_AI_BUILD", "PROMPT_COPILOT", "CORTEX_DATA"])].assign(FY=lambda x: (x.QIDX - 1) // 4)
    ai_fy = set(zip(ai_fy.PERSON_ID, ai_fy.FY))
    base["AI_YEAR"] = [int((p, (q - 1) // 4) in ai_fy) for p, q in zip(base.PERSON_ID, base.QIDX)]
    ep = l[l.LEARNING_HOURS > 0].copy()
    ep["FY"] = (ep.QIDX - 1) // 4
    ep = ep.sort_values("QIDX").groupby(["PERSON_ID", "CURRICULUM", "FY"]).QIDX.first().reset_index()
    ep = ep.merge(base, on=["PERSON_ID", "QIDX"])
    ep = ep[((ep.QIDX - 1) // 4).isin(YEARS)]
    tot = base.groupby(["LEVEL", "QIDX", "AI_YEAR"]).CHANGE.agg(["sum", "count"])
    out = []
    for c, e in ep.groupby("CURRICULUM"):
        # comparison excludes anyone with this curriculum within +/- 2 quarters
        took = l[(l.CURRICULUM == c) & (l.LEARNING_HOURS > 0)][["PERSON_ID", "QIDX"]]
        near = pd.concat([took.assign(QIDX=took.QIDX + o) for o in range(-2, 3)]).drop_duplicates()
        ex = base.merge(near, on=["PERSON_ID", "QIDX"]).groupby(["LEVEL", "QIDX", "AI_YEAR"]).CHANGE.agg(["sum", "count"])
        cmp_ = (tot["sum"] - ex["sum"].reindex(tot.index).fillna(0)) / (tot["count"] - ex["count"].reindex(tot.index).fillna(0))
        # AI curricula are compared with people who had no AI curriculum that year; others within the same AI-year status
        match_ai = np.zeros(len(e), dtype=int) if c in ("AGENTIC_AI_BUILD", "PROMPT_COPILOT", "CORTEX_DATA") else e.AI_YEAR.values
        e = e.assign(PAYBACK=e.CHANGE.values - cmp_.reindex(pd.MultiIndex.from_arrays([e.LEVEL, e.QIDX, match_ai])).values)
        e = e.dropna(subset=["PAYBACK"])
        for scope in ("FIRM", "FS"):
            s = e if scope == "FIRM" else e[e.PERSON_ID.map(grp) == "FS"]
            if s.PERSON_ID.nunique() < MIN_PEOPLE:
                continue
            p_id, inv = np.unique(s.PERSON_ID.values, return_inverse=True)
            S = np.zeros((len(p_id), 2))
            np.add.at(S, (inv, 0), s.PAYBACK.values)
            np.add.at(S, (inv, 1), 1)
            W = rng.multinomial(len(p_id), np.full(len(p_id), 1.0 / len(p_id)), size=1000).astype(float)
            b = W @ S
            lo, hi = np.percentile(b[:, 0] / b[:, 1], [5, 95])
            out.append(dict(SCOPE=scope, CURRICULUM=c, EPISODES=len(s), PEOPLE=len(p_id),
                            PAYBACK_WPS=float(S[:, 0].sum() / S[:, 1].sum()), CI_LOW=float(lo), CI_HIGH=float(hi),
                            SIGNIFICANT=bool(lo > 0 or hi < 0)))
    write_table("LEARNING_WPS_PAYBACK_TEST", out, "R14 re-based on WPS: WPS (excl. learning) change 2 quarters after vs "
                "before a curriculum episode minus the matched same-level comparison change; 90 % person-cluster "
                "bootstrap CI; association, not causation")
    log_update("r14w", out)
    for r in out:
        print(f"r14w {r['SCOPE']} {r['CURRICULUM']:<17} payback {r['PAYBACK_WPS']:+.2f} "
              f"[{r['CI_LOW']:+.2f}, {r['CI_HIGH']:+.2f}] {'SIG' if r['SIGNIFICANT'] else ''}")


def main_steps(steps=None):
    steps = steps or ["r13w", "r14w", "r15", "r16", "r17", "r18", "truth"]
    if steps == ["truth"]:
        return truth_report()
    w, t, l, a, cat = load()
    for s in steps:
        if s == "truth":
            truth_report()
            continue
        rng = np.random.default_rng(SEED + 10 + ["r13w", "r14w", "r15", "r16", "r17", "r18"].index(s))
        {"r13w": lambda: r13w(w, a, rng), "r14w": lambda: r14w(w, l, rng), "r15": lambda: r15(w, t, rng),
         "r16": lambda: r16(w, t, rng), "r17": lambda: r17(w, l, rng), "r18": lambda: r18(w, l, cat, rng)}[s]()



# ------------------------------------------------------------------------------------------------ truth recovery
R16_EFFECT = {("CORTEX", "OE"): "CORTEX_OE", ("CLAUDE_CODE", "WIN"): "CLAUDE_CODE_WIN", ("CODEX", "WIN"): "CODEX_WIN",
              ("CLAUDE_CODE", "OE"): "CLAUDE_CODE_OE", ("CODEX", "OE"): "CODEX_OE"}
R18_EFFECT = {"AGENTIC_AI_BUILD": "CUR_AI", "PROMPT_COPILOT": "CUR_AI", "CORTEX_DATA": "CUR_AI",
              "PROJECT_MGMT": "CUR_PROJECT_MGMT", "COMMERCIAL_BID": "CUR_COMMERCIAL", "SAP_FUNCTIONAL": "CUR_SAP",
              "LEADERSHIP": "CUR_LEADERSHIP", "INDUSTRY": "CUR_INDUSTRY"}


def truth_report():
    """Firm FY24-26 level cells vs OPS.SIM_TRUTH_EFFECTS (spec 4.4): seeded cells recover the sign (significant, or
    sign only for expected-weak cells), null cells are not significant. Curricula only where relevant to the level."""
    sys.path.insert(0, str(ROOT / "gen"))
    from acoco_gen import CUR_RELEVANT                  # levels where each curriculum has guaranteed take-up
    truth = {(r["EFFECT_ID"], r["LEVEL"]): float(r["COEF"]) for r in
             sf.query("SELECT EFFECT_ID, LEVEL, COEF FROM ACOCO_DB.OPS.SIM_TRUTH_EFFECTS")}
    cells = sf.query("""SELECT 'R16' t, STRATUM, EXPOSURE x, OUTCOME o, RHO, CI_LOW, CI_HIGH hi, SIGNIFICANT sig, CELL_STATUS
                        FROM ACOCO_L2.REASONING.VENDOR_WPS_TEST
                        WHERE SCOPE = 'FIRM' AND EXPOSURE_KIND = 'PRODUCT' AND STRATUM <> 'ALL LEVELS'
                        UNION ALL
                        SELECT 'R18', STRATUM, CURRICULUM, OUTCOME, RHO, CI_LOW, CI_HIGH, SIGNIFICANT, CELL_STATUS
                        FROM ACOCO_L2.REASONING.CURRICULUM_WPS_TEST
                        WHERE SCOPE = 'FIRM' AND OUTCOME LIKE 'TARGET:%' AND STRATUM <> 'ALL LEVELS'""")
    rows = []
    for c in cells:
        eff = R16_EFFECT.get((c["X"], c["O"])) if c["T"] == "R16" else R18_EFFECT.get(c["X"])
        if eff is None or (c["T"] == "R18" and c["STRATUM"] not in CUR_RELEVANT[c["X"]]):
            continue
        coef = truth[(eff, c["STRATUM"])]
        rho = None if c["RHO"] in (None, "") else float(c["RHO"])
        sig = str(c["SIG"]).lower() == "true"          # MATERIAL: CI excludes 0 and |rho| >= MIN_RHO
        lo = None if c["CI_LOW"] in (None, "") else float(c["CI_LOW"])
        # spec 4.4: seeded cells recover the sign (rho > 0 and the CI not wholly below 0); null cells not significant
        if c["CELL_STATUS"] != "OK" or rho is None or rho != rho:
            verdict = "INSUFFICIENT"
        elif coef != 0:
            verdict = ("RECOVERED" if rho > 0 and sig else "SIGN_RECOVERED" if rho > 0 and (c["HI"] is None or float(c["HI"]) > 0)
                       else "MISSED")
        else:
            verdict = "NULL_OK" if not sig else "NULL_SIGNIFICANT"
        rows.append(dict(TEST=c["T"], STRATUM=c["STRATUM"], EXPOSURE=c["X"], OUTCOME=c["O"], EFFECT_ID=eff,
                         TRUE_COEF=coef, RHO=rho, SIGNIFICANT=sig, VERDICT=verdict))
    write_table("P6_TRUTH_RECOVERY", rows, "P6 gate: firm FY24-26 level cells of R16 / R18 vs the seeded true effects "
                "(OPS.SIM_TRUTH_EFFECTS): RECOVERED (material, right sign) / SIGN_RECOVERED (right sign) / MISSED for seeded "
                "cells, NULL_OK / NULL_SIGNIFICANT (material) for null cells")
    n = collections.Counter(r["VERDICT"] for r in rows)
    log_update("p6_truth", dict(n))
    print("truth recovery:", dict(n))
    return rows


def main():
    main_steps(sys.argv[1:])


if __name__ == "__main__":
    main()
