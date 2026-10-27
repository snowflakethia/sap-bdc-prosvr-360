"""ACoCo ProServe360 synthetic data generator (L0 gap-fill, ACOCO_SIM).

Deterministic: one numpy Generator seeded from OPS.GEN_PARAMS.seed, all iteration over sorted keys.
Keyed to real CLD master data: People Intelligence userId / costCenter / payGrade, S/4 cost centres (USC1),
activity types (ML-100..ML-105), GL accounts, customer IDs. See plan/deviations.md D-02-*.

Generation order (each step only uses the steps before it):
  1 people (real core + simulated churn pool)     6 opportunities, pursuit teams, projects, work packages
  2 names, MD roles                               7 staffing, productivity, timesheets (weekly)
  3 skills, AI skill trajectory, AI usage bands   8 assets (harvest / reuse), learning, admin
  4 learning catalogue                            9 finance (Universal Journal shape), plan, internal orders
  5 performance, compensation, succession        10 AI telemetry, status notes, availability (daily)
"""
from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from calendar_ import AS_OF, FORWARD_END, WINDOW_END, WINDOW_START, fiscal_period, fiscal_year, weeks, workdays

LEVELS = ["Analyst", "Consultant", "Manager", "Senior Manager", "Principal"]
LEVEL_IDX = {l: i for i, l in enumerate(LEVELS)}
ACTIVITY_BY_LEVEL = {"Analyst": "ML-100", "Consultant": "ML-101", "Manager": "ML-103",
                     "Senior Manager": "ML-104", "Principal": "ML-105"}
GROUPS = ["FS", "PRD", "HPS", "CMT", "RES", "XAI"]
VENDORS = ["OPENAI", "ANTHROPIC", "CORTEX"]
AI_CC = {"OPENAI": "USC1_IT1", "ANTHROPIC": "USC1_IT2", "CORTEX": "USC1_IT3"}
AGT_PRICE = {"OPENAI": 40.0, "ANTHROPIC": 45.0, "CORTEX": 35.0}       # USD per agent-hour (planned price)

WORK_TYPES = ["Data Migration", "Integration", "Analytics", "Testing", "PMO", "AI Engineering", "Cloud Platform"]
WT_SKILLS = {
    "Data Migration": ["SAP_S4_MIGRATION", "DATA_ENGINEERING", "SQL", "DATA_QUALITY"],
    "Integration": ["SAP_INTEGRATION", "API_DESIGN", "JAVA", "CLOUD_ARCH"],
    "Analytics": ["SQL", "BI_VISUALISATION", "DATA_MODELLING", "PYTHON"],
    "Testing": ["TEST_AUTOMATION", "QUALITY_ENGINEERING", "SQL", "DATA_QUALITY"],
    "PMO": ["PROGRAM_MGMT", "AGILE_DELIVERY", "CHANGE_MGMT", "STAKEHOLDER_MGMT"],
    "AI Engineering": ["PYTHON", "ML_ENGINEERING", "AI_AGENT_ORCHESTRATION", "AI_PROMPT_ENGINEERING"],
    "Cloud Platform": ["CLOUD_ARCH", "SNOWFLAKE", "DATA_ENGINEERING", "DEVOPS"],
}
AI_FAMILY = ["AI_AGENT_ORCHESTRATION", "AI_PROMPT_ENGINEERING", "AI_TOOL_INTEGRATION", "AI_AGENT_GOVERNANCE",
             "AI_OUTPUT_VALIDATION"]
INDUSTRY_SKILLS = {"FS": ["BANKING_DOMAIN", "INSURANCE_DOMAIN", "RISK_REGULATORY"],
                   "PRD": ["MANUFACTURING_DOMAIN", "SUPPLY_CHAIN_DOMAIN"],
                   "HPS": ["HEALTH_DOMAIN", "PUBLIC_SECTOR_DOMAIN"],
                   "CMT": ["TELCO_DOMAIN", "MEDIA_DOMAIN"],
                   "RES": ["ENERGY_DOMAIN", "UTILITIES_DOMAIN"],
                   "XAI": ["ML_ENGINEERING", "AI_STRATEGY"]}

# Size classes: team by level, duration in weeks, work packages, count mix (PRD 6.2: Large ~20 % / ~80 % revenue)
SIZES = {
    "XX-Small": dict(team={"Consultant": 1, "Analyst": 2}, weeks=(13, 17), wps=(1, 1), mix=0.10),
    "X-Small": dict(team={"Manager": 1, "Consultant": 2, "Analyst": 4}, weeks=(13, 17), wps=(1, 1), mix=0.10),
    "Small": dict(team={"Senior Manager": 1, "Manager": 2, "Consultant": 4, "Analyst": 7}, weeks=(12, 14),
                  wps=(1, 1), mix=0.50),
    "Medium": dict(team={"Principal": 1, "Senior Manager": 2, "Manager": 4, "Consultant": 8, "Analyst": 16},
                   weeks=(20, 26), wps=(2, 3), mix=0.10),
    "Large": dict(team={"Principal": 1, "Senior Manager": 4, "Manager": 10, "Consultant": 22, "Analyst": 45},
                  weeks=(26, 39), wps=(4, 6), mix=0.20),
}
# Delivery allocation of an assignment, close to the level Delivery target so Bid and Learning have room (D-02-11)
ALLOC = {"Analyst": 0.80, "Consultant": 0.76, "Manager": 0.65, "Senior Manager": 0.50, "Principal": 0.40}
# Pursuit hours per bid at intensity 1, by size class (calibrated so firm Bid ~15 % of available hours, D-02-11)
BID_HOURS = {"XX-Small": 900, "X-Small": 1800, "Small": 4000, "Medium": 9000, "Large": 19000}
LEARNING_SHARE = 0.106          # target Learning share of available hours per person-year (D-02-11)

# Firm-level target Delivery share of available hours by fiscal year (story: falls to ~66 % in FY26).
TARGET_DELIVERY = {2022: 0.72, 2023: 0.71, 2024: 0.70, 2025: 0.68, 2026: 0.66, 2027: 0.60}
GROUP_DEMAND = {"FS": 1.0, "PRD": 1.0, "HPS": 1.0, "CMT": 1.0, "RES": 1.0, "XAI": 1.06}
ATTRITION = {2022: 0.18, 2023: 0.16, 2024: 0.15, 2025: 0.14, 2026: 0.13, 2027: 0.13}
AI_ADOPTION = {2022: 0.04, 2023: 0.14, 2024: 0.33, 2025: 0.52, 2026: 0.68, 2027: 0.70}   # S-curve, active share
HARVEST_P = {2022: 0.15, 2023: 0.22, 2024: 0.28, 2025: 0.34, 2026: 0.40, 2027: 0.40}
REUSE_P = {2022: 0.10, 2023: 0.18, 2024: 0.26, 2025: 0.34, 2026: 0.40, 2027: 0.40}

FIRST = {"F": ["Priya", "Mei", "Aisha", "Sofia", "Hannah", "Chloe", "Ananya", "Grace", "Yuki", "Elena", "Fatima",
               "Olivia", "Isabel", "Nadia", "Zara", "Leila", "Emma", "Sara", "Mia", "Ruth"],
         "M": ["Daniel", "Omar", "Rahul", "Lucas", "Ethan", "Kenji", "Arjun", "Mateo", "Samuel", "Wei", "Ahmed",
               "Noah", "Diego", "Ivan", "Liam", "Felix", "Hugo", "Tariq", "Ben", "Kwame"]}
LAST = ["Nair", "Okafor", "Rodriguez", "Tan", "Mehta", "Chen", "Smith", "Kim", "Garcia", "Silva", "Novak", "Singh",
        "Khan", "Müller", "Rossi", "Ito", "Haddad", "Johnson", "Patel", "Nguyen", "Owusu", "Kowalski", "Dubois",
        "Larsen", "Costa", "Ahmed", "Fischer", "Moreau", "Sato", "Reyes"]
CLIENT_WORDS = {"FS": (["Northbridge", "Harbour", "Meridian", "Sterling", "Pacific", "Summit", "Crown", "Atlas"],
                       ["Bank", "Insurance", "Capital", "Financial", "Mutual", "Securities"]),
                "PRD": (["Apex", "Vertex", "Orion", "Kestrel", "Nova", "Titan"], ["Industries", "Motors", "Foods", "Brands"]),
                "HPS": (["Unity", "Civic", "Evergreen", "Beacon", "Haven"], ["Health", "Hospital Group", "Agency", "Council"]),
                "CMT": (["Pulse", "Signal", "Lumen", "Echo", "Vista"], ["Telecom", "Media", "Networks", "Digital"]),
                "RES": (["Granite", "Solstice", "Delta", "Ridge", "Aurora"], ["Energy", "Utilities", "Mining", "Power"]),
                "XAI": (["Quantum", "Cognito", "Synapse", "Axiom", "Helix"], ["AI Labs", "Analytics", "Data Co", "Systems"])}
ROOT_CAUSES = ["late client data delivery", "scope change not re-priced", "key-person roll-off",
               "test environment instability", "integration defects", "under-estimated data volumes",
               "staffing gap at Consultant level", "dependency on third-party vendor"]


@dataclass
class Ctx:
    rng: np.random.Generator
    params: dict
    levels: pd.DataFrame
    targets: pd.DataFrame
    paygrade: pd.DataFrame
    sfcc: pd.DataFrame
    mdcc: pd.DataFrame
    activity_ce: dict
    gl: dict
    customers: list
    real_people: pd.DataFrame
    real_monthly: pd.DataFrame
    real_avail_week: pd.DataFrame
    assign_map: pd.DataFrame
    out: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------------------------- helpers
def level_rates(ctx, level, bill_code):
    r = ctx.levels.set_index("LEVEL").loc[level]
    bill = float(r.BILL_RATE_BASE) + float(r.BILL_RATE_STEP) * (bill_code - (int(r.BILL_CODE_LO) - 1))
    return float(r.COST_PER_DAY) / 8.0, bill / 8.0          # cost/h, bill/h


def month_iter(start, end):
    d = dt.date(start.year, start.month, 1)
    while d <= end:
        yield d
        d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def month_end(d):
    n = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return n - dt.timedelta(days=1)


# ----------------------------------------------------------------------------------------------- 1 people
def build_people(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng
    pg = ctx.paygrade.set_index("PAY_GRADE")
    sf = ctx.sfcc.set_index("SF_COST_CENTER")
    rp = ctx.real_people.copy()
    rp["pay_grade"] = rp["PAY_GRADE"].fillna(61).astype(int)
    rp["level"] = [pg.loc[g, "LEVEL"] for g in rp["pay_grade"]]
    rp["bill_code"] = [int(pg.loc[g, "BILL_CODE"]) for g in rp["pay_grade"]]
    rp["paygrade_imputed"] = rp["PAY_GRADE"].isna()
    rp["sf_cost_center"] = rp["COST_CENTER"].fillna("UNASSIGNED").astype(str)
    rp["md_group"] = [sf.loc[c, "MD_GROUP_ID"] for c in rp["sf_cost_center"]]
    rp["cost_center"] = [sf.loc[c, "COST_CENTER"] for c in rp["sf_cost_center"]]
    rp["hire_date"] = [min(h, f) if pd.notna(h) else f for h, f in zip(rp["TENURE_START"], rp["FIRST_START"])]
    rp["term_date"] = rp["TERM_DATE"]
    rp["term_reason"] = np.where(rp["TERM_DATE"].notna(), "OTHER", None)
    rp["source_system"] = "BDC_CLD"
    rp["gender"] = rp["GENDER"].where(rp["GENDER"].isin(["F", "M"]), pd.Series(
        rng.choice(["F", "M"], len(rp)), index=rp.index))
    rp["user_id"] = rp["USER_ID"].astype(str)
    rp["latent_risk"] = rng.lognormal(0, 0.35, len(rp))
    real = rp[["user_id", "source_system", "level", "bill_code", "pay_grade", "paygrade_imputed", "sf_cost_center",
               "md_group", "cost_center", "hire_date", "term_date", "term_reason", "gender", "latent_risk"]]

    # Simulated churn pool: keeps ~330 active, leavers replaced after ~2 months, monthly hazard calibrated so
    # firm voluntary attrition follows ATTRITION[fy] of total headcount.
    sim_levels = rng.choice(LEVELS[:4], p=[0.55, 0.30, 0.10, 0.05], size=20000)
    sf_by_group = {g: sorted(ctx.sfcc[ctx.sfcc.MD_GROUP_ID == g].SF_COST_CENTER) for g in GROUPS}
    rows, nxt = [], 1
    pool_target = 330
    real_hc = len(real)

    def new_sim(hire, lvl_i):
        nonlocal nxt
        lvl = sim_levels[lvl_i % len(sim_levels)]
        g = GROUPS[(nxt + int(rng.integers(0, 6))) % 6]
        lo, hi = {"Analyst": (61, 68), "Consultant": (69, 72), "Manager": (73, 76), "Senior Manager": (77, 81)}[lvl]
        p_g = int(rng.integers(lo, hi + 1))
        r = dict(user_id=f"S{90000 + nxt}", source_system="SIMULATED", level=lvl,
                 bill_code=int(pg.loc[p_g, "BILL_CODE"]), pay_grade=p_g, paygrade_imputed=False,
                 sf_cost_center=sf_by_group[g][int(rng.integers(0, len(sf_by_group[g])))], md_group=g,
                 hire_date=hire, term_date=None, term_reason=None, gender=rng.choice(["F", "M"]),
                 latent_risk=float(rng.lognormal(0.4, 0.45)))
        r["cost_center"] = sf.loc[r["sf_cost_center"], "COST_CENTER"]
        nxt += 1
        return r

    active = []
    for i in range(pool_target):
        hire = WINDOW_START - dt.timedelta(days=int(rng.integers(30, 900)))
        active.append(new_sim(hire, i))
    pending = []                                     # (hire_date) replacements
    for m in month_iter(WINDOW_START, WINDOW_END):
        fy = fiscal_year(m)
        for h in [p for p in pending if p <= m]:
            active.append(new_sim(h + dt.timedelta(days=int(rng.integers(0, 20))), nxt))
        pending = [p for p in pending if p > m]
        leavers_target = ATTRITION[fy] * (real_hc + pool_target) / 12.0
        risk = np.array([a["latent_risk"] for a in active])
        hazard = np.clip(leavers_target * risk / risk.sum(), 0, 0.9)
        leave = rng.random(len(active)) < hazard
        stay = []
        for a, lv in zip(active, leave):
            if lv:
                a["term_date"] = m + dt.timedelta(days=int(rng.integers(0, 27)))
                a["term_reason"] = rng.choice(["VOL_CAREER", "VOL_COMPENSATION", "VOL_WORKLOAD", "VOL_RELOCATION"],
                                              p=[0.4, 0.3, 0.2, 0.1])
                rows.append(a)
                pending.append(dt.date(m.year + (m.month > 10), (m.month + 1) % 12 + 1, 1))
            else:
                stay.append(a)
        active = stay
    rows.extend(active)
    sim = pd.DataFrame(rows)
    people = pd.concat([real, sim], ignore_index=True)
    people["hire_date"] = [d if pd.notna(d) else None for d in pd.to_datetime(people["hire_date"]).dt.date]
    people["term_date"] = [d if pd.notna(d) else None for d in pd.to_datetime(people["term_date"]).dt.date]
    people["term_date"] = people["term_date"].astype(object)
    people = people.sort_values("user_id", key=lambda s: s.str.zfill(8)).reset_index(drop=True)
    people["pidx"] = np.arange(len(people))
    return people


def build_names_and_mds(ctx: Ctx, people: pd.DataFrame):
    rng = ctx.rng
    first = [FIRST[g][int(rng.integers(0, 20))] for g in people["gender"]]
    last = [LAST[int(rng.integers(0, len(LAST)))] for _ in range(len(people))]
    names = pd.DataFrame({"USER_ID": people["user_id"], "FIRST_NAME": first, "LAST_NAME": last,
                          "SOURCE_SYSTEM": "SIMULATED"})
    # One MD per group: the real Principal (highest bill code, then longest tenure) in that group, active at as-of.
    act = people[(people.source_system == "BDC_CLD") & (people.level == "Principal")
                 & (people.term_date.isna() | (people.term_date > AS_OF))
                 & ~people.user_id.str.contains("ADMIN|TEST|SYS", case=False)]
    mds = []
    for g in GROUPS:
        c = act[act.md_group == g].sort_values(["bill_code", "hire_date", "user_id"], ascending=[False, True, True])
        if c.empty:
            raise RuntimeError(f"no Principal in group {g}")
        mds.append(dict(USER_ID=c.iloc[0].user_id, MD_GROUP_ID=g, ROLE="MANAGING_DIRECTOR",
                        VALID_FROM=WINDOW_START, SOURCE_SYSTEM="SIMULATED"))
    md = pd.DataFrame(mds)
    fs_md = md.loc[md.MD_GROUP_ID == "FS", "USER_ID"].iloc[0]
    names.loc[names.USER_ID == fs_md, ["FIRST_NAME", "LAST_NAME"]] = ["Priya", "Nair"]
    people["is_md"] = people["user_id"].isin(md.USER_ID)
    return names, md


# ----------------------------------------------------------------------------------------------- 3 skills
def build_skills(ctx: Ctx, people: pd.DataFrame):
    rng = ctx.rng
    catalogue = sorted({s for v in WT_SKILLS.values() for s in v} | set(AI_FAMILY)
                       | {s for v in INDUSTRY_SKILLS.values() for s in v})
    skill = pd.DataFrame({"SKILL_ID": catalogue,
                          "SKILL_NAME": [s.replace("_", " ").title() for s in catalogue],
                          "SKILL_FAMILY": ["AGENTIC_AI" if s in AI_FAMILY else
                                           "INDUSTRY" if any(s in v for v in INDUSTRY_SKILLS.values()) else
                                           "TECHNICAL" for s in catalogue]})
    tech = [s for s in catalogue if s not in AI_FAMILY]
    rows = []
    n = len(people)
    base_prof = rng.normal(2.8, 0.6, n) + people["level"].map(LEVEL_IDX).values * 0.25
    # AI aptitude: who becomes AI-skilled, and when (S-curve over fiscal years)
    ai_apt = rng.random(n)
    ai_level = np.zeros((n, 6))                              # FY22..FY27 -> AI skill 1..5
    for k, fy in enumerate(range(2022, 2028)):
        adopt = AI_ADOPTION[fy]
        ai_level[:, k] = np.where(ai_apt > 1 - adopt, np.clip(np.round(2 + 3 * (ai_apt - (1 - adopt)) / max(adopt, 1e-6)
                                                                       + rng.normal(0, 0.4, n)), 2, 5), 1)
        if k:
            ai_level[:, k] = np.maximum(ai_level[:, k], ai_level[:, k - 1])
    people["skill_index"] = np.clip(base_prof, 1.5, 4.8).round(2)
    for i, p in people.iterrows():
        k = int(rng.integers(8, 15))
        own = list(rng.choice(tech, size=min(k, len(tech)), replace=False))
        own += INDUSTRY_SKILLS[p.md_group][:1]
        for fy_i, fy in enumerate(range(2022, 2027)):
            assessed = dt.date(fy - 1, 11, 15)
            if p.hire_date and assessed < p.hire_date or (p.term_date and assessed > p.term_date):
                continue
            for s in sorted(set(own)):
                prof = int(np.clip(round(base_prof[i] + rng.normal(0, 0.5) + 0.1 * fy_i), 1, 5))
                rows.append((p.user_id, s, assessed, prof, "MANAGER"))
            ai = int(ai_level[i, fy_i])
            if ai >= 2:
                for s in AI_FAMILY[: max(1, ai - 1)]:
                    rows.append((p.user_id, s, assessed, int(np.clip(ai + rng.integers(-1, 1), 1, 5)), "INFERRED"))
    ps = pd.DataFrame(rows, columns=["USER_ID", "SKILL_ID", "ASSESSED_DATE", "PROFICIENCY", "ASSESSMENT_SOURCE"])
    return skill, ps, ai_level


# ----------------------------------------------------------------------------------------------- 4 learning
def build_learning_catalogue(ctx: Ctx, skill: pd.DataFrame):
    rng = ctx.rng
    items = []
    for i, s in enumerate(skill.SKILL_ID):
        for lvl in (2, 3, 4):
            ai = s in AI_FAMILY
            items.append(dict(LEARNING_ITEM_ID=f"LI-{len(items) + 1:04d}",
                              LEARNING_ITEM_TITLE=f"{s.replace('_', ' ').title()} - level {lvl}",
                              CURRICULUM="AGENTIC_AI" if ai else "CORE",
                              IS_AI_CURRICULUM=ai, TARGET_SKILL_ID=s, TARGET_PROFICIENCY_LEVEL=lvl,
                              LEARNING_HOURS=float(rng.choice([4, 8, 12, 16, 24]))))
    return pd.DataFrame(items)


# ----------------------------------------------------------------------------------------------- 5 HR extras
def build_hr_extras(ctx: Ctx, people: pd.DataFrame):
    rng = ctx.rng
    perf, comp = [], []
    for _, p in people.iterrows():
        for fy in range(2022, 2027):
            d = dt.date(fy, 9, 30)
            if (p.hire_date and p.hire_date > d) or (p.term_date and p.term_date < d):
                continue
            score = np.clip(3.2 - 0.6 * (p.latent_risk - 1) + rng.normal(0, 0.6), 1, 5)
            perf.append((p.user_id, fy, d, int(round(score))))
        compa = float(np.clip(1.0 - 0.08 * (p.latent_risk - 1) + rng.normal(0, 0.06), 0.75, 1.25))
        comp.append((p.user_id, p.level, ["B1", "B2", "B3", "B4", "B5"][LEVEL_IDX[p.level]], round(compa, 3)))
    perf = pd.DataFrame(perf, columns=["USER_ID", "FISCAL_YEAR", "RATING_DATE", "PERFORMANCE_RATING"])
    comp = pd.DataFrame(comp, columns=["USER_ID", "LEVEL", "PAY_BAND", "COMPA_RATIO"])
    return perf, comp


# ----------------------------------------------------------------------------------------------- availability
def weekly_availability(ctx: Ctx, people: pd.DataFrame, wk: pd.DataFrame):
    """Hours available per person-week: real Employee Availability where it exists (from 2024-07-08 weeks),
    otherwise 8 h per working day less simulated leave. 0 outside employment."""
    rng = ctx.rng
    P, W = len(people), len(wk)
    avail = np.zeros((P, W), dtype=np.float32)
    leave = np.zeros((P, W), dtype=np.float32)
    wstart = np.array(wk.week_start.values)
    work_h = wk.work_hours.values.astype(np.float32)
    hire = people.hire_date.values
    term = people.term_date.values
    for i in range(P):
        h = hire[i]
        t = term[i]
        emp = np.array([(h is None or ws + dt.timedelta(days=4) >= h) and (t is None or pd.isna(t) or ws <= t)
                        for ws in wstart])
        avail[i] = np.where(emp, work_h, 0)
        # ~25 leave days a year in 1-week and 2-day blocks
        n_blocks = int(rng.poisson(len(wk) / 52 * 4))
        for _ in range(n_blocks):
            w = int(rng.integers(0, W))
            leave[i, w] += min(avail[i, w], float(rng.choice([16, 40, 40])))
    real = ctx.real_avail_week
    if len(real):
        idx = people.set_index("user_id").pidx
        wkidx = pd.Series(wk.week_idx.values, index=wk.week_start.values)
        r = real[real.USER_ID.isin(idx.index) & real.WEEK_START.isin(wkidx.index)]
        pi = idx.loc[r.USER_ID].values
        wi = wkidx.loc[r.WEEK_START].values
        real_from = wkidx.loc[r.WEEK_START.min()]
        mask_people = np.unique(pi)
        leave[mask_people, real_from:] = 0
        avail[pi, wi] = r.AVAILABLE_HOURS.values
    avail = np.maximum(avail - leave, 0)
    return avail, leave


# ----------------------------------------------------------------------------------------------- 6/7 demand + staffing
class Staffing:
    def __init__(self, ctx, people, wk, avail, ai_level):
        self.ctx, self.people, self.wk, self.avail = ctx, people, wk, avail
        P, W = avail.shape
        self.deliv = np.zeros((P, W), dtype=np.float32)       # delivery hours
        self.bid = np.zeros((P, W), dtype=np.float32)
        self.learn = np.zeros((P, W), dtype=np.float32)
        self.frac = np.zeros((P, W), dtype=np.float32)        # committed delivery fraction
        self.ai_level = ai_level
        self.level_i = people.level.map(LEVEL_IDX).values
        self.group = people.md_group.values
        self.risk = people.latent_risk.values
        self.skill_index = people.skill_index.values
        lo = people.level.map({l: LEVEL_IDX[l] * 10 + 30 for l in LEVELS}).values
        self.bill_pos = np.clip((people.bill_code.values - lo) / 9.0, 0, 1)   # position of bill code within level
        # delivery ceiling per person: 1 - bid target (scaled by bill code) - learning - admin
        bid_t = ctx.targets.set_index("LEVEL").BID.astype(float).div(100)
        self.deliv_cap = (1.0 - people.level.map(bid_t).values * (0.75 + 0.5 * self.bill_pos)
                          - LEARNING_SHARE - 0.03).astype(np.float32)
        self.week_of = {d: i for d, i in zip(wk.week_start, wk.week_idx)}
        self.fy = wk.fiscal_year.values
        self.usage = self._usage_bands()
        self.assignments, self.ts_rows, self.bid_rows = [], [], []
        self.pursuits = []                               # (group, w0, w1, internal order, weight)

    def _usage_bands(self):
        """AI usage intensity per person-week (0..1). ~20 % of AI-skilled (>=3) people are inactive in FY26."""
        rng = self.ctx.rng
        P, W = self.avail.shape
        fy_i = np.clip(self.fy - 2022, 0, 5)
        lvl = self.ai_level[:, fy_i]                                 # P x W
        inactive = rng.random(P) < 0.22
        base = np.clip((lvl - 1) / 4.0 + rng.normal(0, 0.1, (P, 1)), 0, 1)
        use = np.where(lvl >= 2, np.clip(0.35 + 0.6 * base, 0, 1), 0.0)
        use[inactive, :] *= np.where(self.fy >= 2025, 0.0, 0.3)[None, :]
        self.inactive = inactive
        return use.astype(np.float32)

    def person_prod(self, pi, w):
        ai = self.ai_level[pi, min(max(self.fy[w] - 2022, 0), 5)]
        use = self.usage[pi, w]
        active = (ai >= 3) & (use >= 0.5)
        return 1 + 0.05 * (self.skill_index[pi] - 3) + np.where(active, 0.09, np.where(use > 0, 0.02, 0.0))

    def pick(self, level, group, w0, w1, alloc, n, skills, prefer_ai=False, exclude=()):
        rng = self.ctx.rng
        cand = np.where(self.level_i == LEVEL_IDX[level])[0]
        if not len(cand):
            return []
        win = slice(w0, w1)
        avail_ok = (self.avail[cand, win] > 0).mean(axis=1) >= 0.85
        # delivery may not stack beyond max(one assignment, person cap); bids only need free capacity
        ceiling = np.where(alloc <= 0.2, 1.0, np.maximum(self.deliv_cap[cand], alloc * 1.06))
        free_ok = (self.frac[cand, win] + alloc <= ceiling[:, None] + 1e-4).all(axis=1)
        ok = cand[avail_ok & free_ok]
        ok = np.array([c for c in ok if c not in exclude])
        if not len(ok):
            return []
        score = (np.where(self.group[ok] == group, 2.0, 0.0) + 0.4 * self.skill_index[ok]
                 - 0.6 * (self.risk[ok] - 1) + rng.normal(0, 0.8, len(ok)))
        if prefer_ai:
            score += 0.5 * (self.ai_level[ok, min(max(self.fy[w0] - 2022, 0), 5)] - 1)
        # higher bill code -> more likely on a bid than on delivery (within the level)
        score += np.where(alloc <= 0.2, 1.2, -0.4) * self.bill_pos[ok]
        order = ok[np.argsort(-score, kind="stable")]
        return list(order[:n])

    def alloc_for(self, pi, level):
        """Delivery allocation falls as the bill code rises within the level (+6 % lowest .. -6 % highest)."""
        return ALLOC[level] * (1.06 - 0.12 * float(self.bill_pos[pi]))

    def commit(self, pi, w0, w1, alloc, proj, wp, role):
        hrs = self.avail[pi, w0:w1] * alloc
        self.frac[pi, w0:w1] += alloc
        self.deliv[pi, w0:w1] += hrs
        self.assignments.append((pi, proj, wp, w0, w1, alloc, role))
        return hrs


def run_demand(ctx, people, wk, avail, ai_level, skill_df, learning, assets_state):
    """Month by month: open opportunities to fill each group's delivery gap two months ahead; won deals become
    projects that are staffed immediately. Pursuit teams book bid hours from free capacity."""
    rng = ctx.rng
    st = Staffing(ctx, people, wk, avail, ai_level)
    W = len(wk)
    month_weeks = wk.groupby("month_start").week_idx.agg(["min", "max"])
    opps, projects, wps, wp_skills, wp_plan, opp_team, opp_skills = [], [], [], [], [], [], []
    customers = ctx.customers
    accounts = {}
    for g in GROUPS:
        a_words, b_words = CLIENT_WORDS[g]
        for k in range(20):
            cid = customers[(GROUPS.index(g) * 20 + k) % len(customers)]
            accounts[cid] = dict(CUSTOMER=cid, ACCOUNT_NAME=f"{a_words[k % len(a_words)]} {b_words[(k // len(a_words)) % len(b_words)]}"
                                 + ("" if k < len(a_words) * len(b_words) else f" {k}"),
                                 MD_GROUP_ID=g, INDUSTRY=g, SOURCE_SYSTEM="SIMULATED")
    acct_by_group = {g: sorted(c for c, a in accounts.items() if a["MD_GROUP_ID"] == g) for g in GROUPS}
    sizes = list(SIZES)
    size_p = np.array([SIZES[s]["mix"] for s in sizes])
    seeded_loss = {"done": False}
    n_opp = 0
    as_of_w = st.week_of[AS_OF - dt.timedelta(days=AS_OF.weekday())]

    def group_people_hours(g, w0, w1):
        idx = np.where(st.group == g)[0]
        return st.avail[idx, w0:w1].sum(), st.deliv[idx, w0:w1].sum()

    months = list(month_iter(WINDOW_START, FORWARD_END))
    # Opening backlog: the first three months are filled as if their deals closed just before the window.
    schedule = [(0, 0), (0, 1)] + [(mi, mi + 2) for mi in range(len(months))]
    for mi, ti in schedule:
        m = months[mi]
        tgt_m = months[min(ti, len(months) - 1)]
        w0, w1 = int(month_weeks.loc[tgt_m, "min"]), int(month_weeks.loc[tgt_m, "max"]) + 1
        close_date = m + dt.timedelta(days=int(rng.integers(5, 25)))
        for g in GROUPS:
            fy = fiscal_year(tgt_m)
            # Only deals that close before the as-of date are known; after it, only the open pipeline exists.
            known = close_date < AS_OF
            av, dv = group_people_hours(g, w0, w1)
            target = TARGET_DELIVERY[fy] * GROUP_DEMAND[g] * av
            if g == "FS" and fy == 2026:
                target *= 0.95
            gap = target - dv
            tries = 0
            story_due = (g == "FS" and tgt_m == dt.date(2025, 12, 1) and not seeded_loss["done"])
            while (gap > 0.04 * av or story_due) and tries < 12:
                story_due = False
                tries += 1
                n_opp += 1
                size = sizes[int(rng.choice(len(sizes), p=size_p))]
                wt = WORK_TYPES[int(rng.integers(0, len(WORK_TYPES)))]
                fixed = rng.random() < 0.62
                force_story = (not seeded_loss["done"] and g == "FS" and tgt_m == dt.date(2025, 12, 1))
                if force_story:
                    size, wt, fixed = "Large", "Data Migration", True
                spec = SIZES[size]
                team = dict(spec["team"])
                req_skills = WT_SKILLS[wt][:3] + INDUSTRY_SKILLS[g][:1]
                weeks_n = 34 if force_story else int(rng.integers(spec["weeks"][0], spec["weeks"][1] + 1))
                cust = acct_by_group[g][int(rng.integers(0, 20))]
                req_ai = int(np.clip(round(2 + 2.2 * AI_ADOPTION[min(fy, 2027)] + rng.normal(0, 0.5)), 1, 5))
                planned_hours = {l: team[l] * ALLOC[l] * 38.0 * weeks_n for l in team}
                rates = {l: level_rates(ctx, l, ctx.levels.set_index("LEVEL").loc[l].BILL_CODE_LO + 4) for l in team}
                value = sum(planned_hours[l] * rates[l][1] for l in team) * float(rng.uniform(0.84, 0.90))
                # pursuit
                lead_level = "Principal" if size in ("Medium", "Large") or rng.random() < 0.3 else "Senior Manager"
                pw0 = st.week_of.get(close_date - dt.timedelta(days=close_date.weekday()), 0) - 10
                pw0 = max(pw0, 0)
                pw1 = min(pw0 + 10, W)
                principal = lead_level == "Principal" and rng.random() < 0.85
                members_n = {"XX-Small": 2, "X-Small": 3, "Small": 4, "Medium": 6, "Large": 8}[size]
                opp_id = f"OPP-{n_opp:05d}"
                io = f"IO{700000 + n_opp}"
                intensity = float(rng.lognormal(0, 0.55))
                lead = st.pick(lead_level, g, pw0, pw1, 0.15, 1, req_skills)
                mem = []
                for l in ["Manager", "Consultant", "Senior Manager", "Consultant", "Analyst", "Analyst", "Manager",
                          "Consultant"][: members_n]:
                    mem += st.pick(l, g, pw0, pw1, 0.15, 1, req_skills, exclude=set(lead + mem))
                team_p = (lead + mem)[: members_n + 1]
                hours_total = intensity * BID_HOURS[size]
                booked = 0.0
                for pi in team_p:
                    per_w = hours_total / max(len(team_p), 1) / max(pw1 - pw0, 1)
                    free = np.maximum(st.avail[pi, pw0:pw1] * (1 - st.frac[pi, pw0:pw1]) - st.bid[pi, pw0:pw1], 0)
                    h = np.minimum(free, per_w)
                    st.bid[pi, pw0:pw1] += h
                    for j, hj in enumerate(h):
                        if hj > 0.05:
                            st.bid_rows.append((pi, pw0 + j, io, float(hj)))
                    booked += float(h.sum())
                    role = "LEAD" if pi in lead else "MEMBER"
                    opp_team.append((opp_id, people.user_id.iloc[pi], role))
                fit = 0.0
                if team_p:
                    sk = ctx.out["_skill_sets"]
                    have = set().union(*[sk.get(people.user_id.iloc[pi], set()) for pi in team_p])
                    fit = len(set(req_skills) & have) / len(req_skills)
                logit = -0.6 + 1.3 * np.log(max(intensity, 0.05)) + 1.6 * (fit - 0.5) + 0.45 * principal
                p_win = 1 / (1 + np.exp(-logit))
                st.pursuits.append((g, pw0, pw1, io, intensity * BID_HOURS[size] / BID_HOURS["Small"]))
                if not known:
                    stage = "Proposal" if close_date < AS_OF + dt.timedelta(days=60) else "Qualify"
                    opps.append(dict(OPPORTUNITY_ID=opp_id, CUSTOMER=cust, MD_GROUP_ID=g, SIZE_CLASS=size,
                                     WORK_TYPE=wt, ESTIMATED_VALUE=round(value, 2), IS_FIXED_PRICE=fixed,
                                     CREATED_DATE=close_date - dt.timedelta(days=70), EXPECTED_CLOSE_DATE=close_date,
                                     CLOSED_DATE=None, STAGE=stage, PROBABILITY=round(float(p_win) * 100),
                                     OUTCOME=None, REQUIRED_AI_SKILL_LEVEL=req_ai, INTERNAL_ORDER=io,
                                     PRESALES_HOURS_PLANNED=round(hours_total, 1), PROJECT_ID=None,
                                     EXPECTED_START_DATE=tgt_m, SOURCE_SYSTEM="SIMULATED"))
                    for s in req_skills:
                        opp_skills.append((opp_id, s))
                    gap -= 0.5 * sum(planned_hours.values()) / max(weeks_n, 1) * (w1 - w0)
                    continue
                won = force_story or rng.random() < p_win
                opps.append(dict(OPPORTUNITY_ID=opp_id, CUSTOMER=cust, MD_GROUP_ID=g, SIZE_CLASS=size, WORK_TYPE=wt,
                                 ESTIMATED_VALUE=round(value, 2), IS_FIXED_PRICE=fixed,
                                 CREATED_DATE=close_date - dt.timedelta(days=70), EXPECTED_CLOSE_DATE=close_date,
                                 CLOSED_DATE=close_date, STAGE="Closed Won" if won else "Closed Lost",
                                 PROBABILITY=100 if won else 0, OUTCOME="WON" if won else "LOST",
                                 REQUIRED_AI_SKILL_LEVEL=req_ai, INTERNAL_ORDER=io,
                                 PRESALES_HOURS_PLANNED=round(hours_total, 1), PROJECT_ID=None,
                                 EXPECTED_START_DATE=tgt_m, SOURCE_SYSTEM="SIMULATED"))
                for s in req_skills:
                    opp_skills.append((opp_id, s))
                if not won:
                    continue
                # ---------- project
                pid = f"P-{len(projects) + 1:04d}"
                opps[-1]["PROJECT_ID"] = pid
                start_w = w0 + int(rng.integers(0, 2))
                seeded = force_story
                if seeded:
                    seeded_loss["done"] = True
                n_wp = int(rng.integers(spec["wps"][0], spec["wps"][1] + 1))
                ai_enabled = rng.random() < AI_ADOPTION[min(fy, 2027)] * 0.9
                delivery_model = ("AGENT_LED" if ai_enabled and rng.random() < 0.15 else
                                  "HUMAN_AGENT" if ai_enabled else "HUMAN")
                if seeded:
                    delivery_model = "HUMAN"
                ld_rate = round(float(rng.uniform(0.5, 1.0)), 2) if fixed else 0.0
                sold_cost = sum(planned_hours[l] * rates[l][0] for l in team) * 1.35
                proj = dict(PROJECT_ID=pid, OPPORTUNITY_ID=opp_id, CUSTOMER=cust, MD_GROUP_ID=g, SIZE_CLASS=size,
                            WORK_TYPE=wt, CONTRACT_TYPE="FIXED_PRICE" if fixed else "TIME_AND_MATERIALS",
                            CONTRACT_VALUE=round(value, 2), SOLD_COST=round(sold_cost, 2),
                            LD_RATE_PCT_PER_WEEK=ld_rate, DELIVERY_MODEL=delivery_model,
                            PLANNED_START=wk.week_start.iloc[start_w],
                            PLANNED_END=wk.week_start.iloc[min(start_w + weeks_n, W - 1)] + dt.timedelta(days=4),
                            SEEDED_STORY="FS_LOSS" if seeded else None, SOURCE_SYSTEM="SIMULATED")
                projects.append(proj)
                # ---------- work packages + staffing
                lead_pi = st.pick("Principal", g, start_w, min(start_w + weeks_n, W), ALLOC["Principal"], 1,
                                  req_skills) if "Principal" in team else []
                for pi in lead_pi:
                    st.commit(pi, start_w, min(start_w + weeks_n, W), st.alloc_for(pi, "Principal"), pid, None,
                              "PROJECT_LEAD")
                reuse_asset = assets_state.try_reuse(wt, fy, rng) if not seeded else None
                for k in range(n_wp):
                    wp_id = f"{pid}-WP{k + 1:02d}"
                    wp_team = {l: max(1, int(round(c / n_wp))) for l, c in team.items() if l != "Principal"}
                    members = []
                    for l, c in sorted(wp_team.items(), key=lambda x: -LEVEL_IDX[x[0]]):
                        got = st.pick(l, g, start_w, min(start_w + weeks_n, W), ALLOC[l], c, req_skills,
                                      prefer_ai=ai_enabled, exclude=set(members))
                        members += [(pi, l) for pi in got]
                    members_pi = [pi for pi, _ in members]
                    filled = len(members) / max(sum(wp_team.values()), 1)
                    plan_h = {l: c * ALLOC[l] * 38.0 * weeks_n for l, c in wp_team.items()}
                    plan_total = sum(plan_h.values())
                    if members_pi:
                        pp = np.mean([st.person_prod(pi, start_w) for pi in members_pi])
                    else:
                        pp = 0.9
                    asset_boost = 0.07 if reuse_asset else 0.0
                    wp_prod = pp * (1 + asset_boost) * (1 - 0.08 * (1 - filled)) * float(rng.normal(1.0, 0.05))
                    if delivery_model != "HUMAN":
                        wp_prod *= 1.03
                    if seeded:
                        wp_prod = 0.58 if k == 1 else 0.68
                    wp_prod = float(np.clip(wp_prod, 0.55, 1.35))
                    weekly_team_h = sum(ALLOC[l] * 38.0 for _, l in members) or 38.0
                    actual_hours = plan_total / wp_prod
                    act_weeks = int(np.ceil(actual_hours / weekly_team_h))
                    end_w = min(start_w + act_weeks, W)
                    owner = next((pi for pi, l in members if l in ("Senior Manager", "Manager")),
                                 members_pi[0] if members_pi else None)
                    wps.append(dict(WBS_ELEMENT=wp_id, PROJECT_ID=pid, WORK_PACKAGE_NAME=f"{wt} stream {k + 1}",
                                    WORK_TYPE=wt, OWNER_USER_ID=None if owner is None else people.user_id.iloc[owner],
                                    PLANNED_HOURS=round(plan_total, 1), PLANNED_START=wk.week_start.iloc[start_w],
                                    PLANNED_END=proj["PLANNED_END"], FORECAST_END=wk.week_start.iloc[min(end_w, W - 1)]
                                    + dt.timedelta(days=4), TEAM_PRODUCTIVITY=round(wp_prod, 3),
                                    REUSED_ASSET_ID=reuse_asset, IS_CRITICAL_PATH=bool(seeded and k == 1),
                                    SOURCE_SYSTEM="SIMULATED"))
                    for l, h in plan_h.items():
                        wp_plan.append((wp_id, l, round(h, 1)))
                    for s in req_skills:
                        wp_skills.append((wp_id, s, 3))
                    for pi, l in members:
                        a_pi = st.alloc_for(pi, l)
                        hrs = st.commit(pi, start_w, end_w, a_pi, pid, wp_id, "TEAM_MEMBER")
                        pprod = st.person_prod(pi, start_w)
                        st.ts_rows.append((pi, wp_id, start_w, end_w, a_pi, pprod * wp_prod / max(pp, 0.5),
                                           ai_enabled))
                    if reuse_asset:
                        assets_state.record_use(reuse_asset, pid, wp_id, wk.week_start.iloc[start_w],
                                                round(0.07 * plan_total, 1))
                # harvest at planned end
                if not seeded and proj["PLANNED_END"] < AS_OF and rng.random() < HARVEST_P[min(fy, 2027)]:
                    harvester = lead_pi[0] if lead_pi else (members_pi[0] if members_pi else None)
                    assets_state.harvest(pid, wt, proj["PLANNED_END"],
                                         None if harvester is None else people.user_id.iloc[harvester], rng)
                elif seeded:
                    assets_state.ensure_matching(wt, 3, dt.date(2025, 6, 30), rng)
                gap -= sum(planned_hours.values()) / max(weeks_n, 1) * (w1 - w0) / 1.0
    return st, opps, projects, wps, wp_skills, wp_plan, opp_team, opp_skills, list(accounts.values())


class Assets:
    def __init__(self):
        self.assets, self.harvests, self.uses = [], [], []

    def harvest(self, pid, wt, date, by, rng):
        aid = f"AS-{len(self.assets) + 1:04d}"
        typ = ["ACCELERATOR", "DATA_MODEL", "CODE_TEMPLATE", "TEST_PACK", "AI_AGENT", "PROPOSAL"][
            int(rng.integers(0, 6))]
        saving = float(rng.choice([80, 160, 240, 400]))
        self.assets.append(dict(ASSET_ID=aid, ASSET_TITLE=f"{wt} {typ.replace('_', ' ').title()} {len(self.assets) + 1}",
                                ASSET_TYPE=typ, WORK_TYPE=wt, SKILL_TAGS=",".join(WT_SKILLS[wt][:3]),
                                CATALOGUED_EFFORT_SAVING_HOURS=saving, HARVESTED_DATE=date,
                                DESCRIPTION=f"Reusable {typ.lower().replace('_', ' ')} for {wt.lower()} work: "
                                            f"covers {', '.join(s.lower().replace('_', ' ') for s in WT_SKILLS[wt][:3])}.",
                                SOURCE_SYSTEM="SIMULATED"))
        self.harvests.append(dict(ASSET_ID=aid, SOURCE_PROJECT_ID=pid, HARVEST_DATE=date, HARVESTED_BY_USER_ID=by,
                                  SOURCE_SYSTEM="SIMULATED"))
        return aid

    def ensure_matching(self, wt, n, date, rng):
        have = [a for a in self.assets if a["WORK_TYPE"] == wt and a["HARVESTED_DATE"] <= date]
        for _ in range(max(0, n - len(have))):
            self.harvest(None, wt, date, None, rng)

    def try_reuse(self, wt, fy, rng):
        cand = [a["ASSET_ID"] for a in self.assets if a["WORK_TYPE"] == wt]
        if cand and rng.random() < REUSE_P[min(fy, 2027)] * 1.8:
            return cand[int(rng.integers(0, len(cand)))]
        return None

    def record_use(self, aid, pid, wbs, date, hours):
        self.uses.append(dict(ASSET_ID=aid, PROJECT_ID=pid, WBS_ELEMENT=wbs, OPPORTUNITY_ID=None, USE_DATE=date,
                              HOURS_SAVED_ESTIMATED=hours, SOURCE_SYSTEM="SIMULATED"))


# ----------------------------------------------------------------------------------------------- 8 learning, timesheets
def allocate_bid_time(ctx, st, people, wk):
    """Every person spends part of the week on live pursuits in their group, up to the level Bid target
    (OPS.GEN_PARAMS_TIME_TARGET), limited by free capacity. Hours go to the pursuits active that week in proportion to
    their intensity weight, so high-intensity bids (higher win probability) receive more hours."""
    rng = ctx.rng
    target = ctx.targets.set_index("LEVEL").BID.astype(float).div(100).to_dict()
    lvl = people.level.values
    grp = people.group if hasattr(people, "group") else people.md_group.values
    W = st.avail.shape[1]
    by_gw = {}
    for (g, w0, w1, io, wt) in st.pursuits:
        for w in range(w0, min(w1, W)):
            by_gw.setdefault((g, w), []).append((io, wt))
    for g in GROUPS:
        idx = np.where(grp == g)[0]
        # higher bill code within the level -> larger share of the week on bids (x0.75 .. x1.25 of level target)
        frac_t = np.array([target[l] for l in lvl[idx]], dtype=np.float32) * (0.69 + 0.46 * st.bill_pos[idx]).astype(np.float32)
        for w in range(W):
            live = by_gw.get((g, w))
            if not live:
                continue
            ios = [x[0] for x in live]
            wts = np.array([x[1] for x in live], dtype=float)
            wts = wts / wts.sum()
            free = np.maximum(st.avail[idx, w] * (1 - st.frac[idx, w]) - st.bid[idx, w], 0)
            want = np.maximum(st.avail[idx, w] * frac_t * rng.uniform(0.85, 1.15, len(idx)) - st.bid[idx, w], 0)
            h = np.minimum(free, want)
            pick = rng.choice(len(ios), size=len(idx), p=wts)
            for k, pi in enumerate(idx):
                if h[k] > 0.5:
                    st.bid[pi, w] += h[k]
                    st.bid_rows.append((pi, w, ios[pick[k]], float(h[k])))


def schedule_learning(ctx, st, people, learning, ps, wk):
    """Per person and fiscal year, book learning items up to ~LEARNING_SHARE of available hours, in the weeks with
    the most free capacity. AI-curriculum share follows the adoption curve."""
    rng = ctx.rng
    li = learning.reset_index(drop=True)
    ai_items = li[li.IS_AI_CURRICULUM].reset_index(drop=True)
    core_items = li[~li.IS_AI_CURRICULUM].reset_index(drop=True)
    ai_share = {2022: 0.10, 2023: 0.20, 2024: 0.35, 2025: 0.45, 2026: 0.55, 2027: 0.55}
    comps = []
    uid = people.user_id.values
    for pi in range(len(people)):
        for fy in range(2022, 2028):
            ws = np.where(wk.fiscal_year.values == fy)[0]
            ws = ws[st.avail[pi, ws] > 0]
            if not len(ws):
                continue
            target = float(st.avail[pi, ws].sum()) * LEARNING_SHARE * float(np.clip(rng.normal(1.0, 0.2), 0.5, 1.5))
            booked = 0.0
            guard = 0
            while booked < target and guard < 40:
                guard += 1
                pool = ai_items if rng.random() < ai_share[fy] else core_items
                item = pool.iloc[int(rng.integers(0, len(pool)))]
                free = st.avail[pi, ws] * (1 - st.frac[pi, ws]) - st.bid[pi, ws] - st.learn[pi, ws]
                if free.max() <= 1:
                    break
                w = ws[int(np.argmax(free + rng.random(len(ws))))]
                h = float(min(item.LEARNING_HOURS, free.max(), target - booked + 4))
                if h <= 0.5:
                    break
                st.learn[pi, w] += h
                booked += h
                comps.append(dict(USER_ID=uid[pi], LEARNING_ITEM_ID=item.LEARNING_ITEM_ID,
                                  COMPLETION_DATE=wk.week_start.iloc[w] + dt.timedelta(days=4),
                                  COMPLETION_STATUS="COMPLETED", LEARNING_HOURS=round(h, 1), SOURCE_SYSTEM="SIMULATED"))
    return pd.DataFrame(comps)


def build_timesheets(ctx, st, people, wk):
    """Weekly rows per person x category x object. Bench = available - booked (no row)."""
    rng = ctx.rng
    rows = []
    uid = people.user_id.values
    cc = people.cost_center.values
    fy = wk.fiscal_year.values
    wstart = wk.week_start.values
    learn_boost = np.zeros_like(st.avail)
    for (pi, wp, w0, w1, alloc, eff, ai_proj) in st.ts_rows:
        for w in range(w0, w1):
            h = float(st.avail[pi, w] * alloc)
            if h <= 0:
                continue
            use = float(st.usage[pi, w])
            assisted = round(h * min(0.6, use * 0.5), 1) if use > 0 else 0.0
            rows.append((uid[pi], cc[pi], wstart[w], int(fy[w]), "DELIVERY", wp, None, round(h, 1),
                         round(h * eff, 1), assisted, round(assisted * float(rng.uniform(0.05, 0.2)), 1)))
    for (pi, proj, wp, w0, w1, alloc, role) in st.assignments:
        if role == "PROJECT_LEAD":
            for w in range(w0, w1):
                h = float(st.avail[pi, w] * alloc)
                if h > 0:
                    rows.append((uid[pi], cc[pi], wstart[w], int(fy[w]), "DELIVERY", f"{proj}-WP01", None,
                                 round(h, 1), round(h, 1), 0.0, 0.0))
    P, W = st.avail.shape
    for pi, w, io, h in st.bid_rows:
        rows.append((uid[pi], cc[pi], wstart[w], int(fy[w]), "BID", None, io, round(h, 1), None, 0.0, 0.0))
    l_i, l_w = np.nonzero(st.learn > 0.05)
    for pi, w in zip(l_i, l_w):
        rows.append((uid[pi], cc[pi], wstart[w], int(fy[w]), "LEARNING", None, "IO-LEARNING",
                     round(float(st.learn[pi, w]), 1), None, 0.0, 0.0))
    admin = np.round(st.avail * np.clip(rng.normal(0.025, 0.006, st.avail.shape), 0.01, 0.045), 1)
    admin = np.minimum(admin, np.maximum(st.avail - st.deliv - st.bid - st.learn, 0))
    a_i, a_w = np.nonzero(admin > 0.05)
    for pi, w in zip(a_i, a_w):
        rows.append((uid[pi], cc[pi], wstart[w], int(fy[w]), "ADMIN", None, "IO-ADMIN", float(admin[pi, w]), None,
                     0.0, 0.0))
    ts = pd.DataFrame(rows, columns=["USER_ID", "COST_CENTER", "WEEK_START", "FISCAL_YEAR", "CATEGORY",
                                     "WBS_ELEMENT", "INTERNAL_ORDER", "HOURS", "ZZ_EARNED_HOURS", "ZZ_AI_ASSISTED_HOURS",
                                     "ZZ_AI_HOURS_SAVED"])
    ts.insert(0, "TIMESHEET_RECORD", [f"TS{i + 1:09d}" for i in range(len(ts))])
    ts["BILLABLE_CONTROL"] = np.where(ts.CATEGORY == "DELIVERY", "BILLABLE", "NON_BILLABLE")
    ts["SOURCE_SYSTEM"] = "SIMULATED"
    return ts


# ----------------------------------------------------------------------------------------------- 9 finance
def build_finance(ctx, people, ts, projects, wps, opps, agt):
    """Universal Journal (operationalacctgdocitem shape, company code USC1), monthly per person x WBS for activity
    allocations, per WBS for overhead and revenue, per person x internal order for pre-sales; plan per WBS-period."""
    rng = ctx.rng
    lv = people.set_index("user_id")[["level", "bill_code", "cost_center"]]
    proj = pd.DataFrame(projects).set_index("PROJECT_ID")
    wpd = pd.DataFrame(wps).set_index("WBS_ELEMENT")
    pc_of_cc = ctx.mdcc.set_index("COST_CENTER").PROFIT_CENTER.to_dict()
    t = ts[ts.CATEGORY.isin(["DELIVERY", "BID"])].copy()
    t["MONTH"] = pd.to_datetime(t.WEEK_START).dt.to_period("M").dt.to_timestamp().dt.date
    t = t.join(lv, on="USER_ID", rsuffix="_P")
    cr = {(l, b): level_rates(ctx, l, b) for l, b in set(zip(t.level, t.bill_code))}
    t["COST"] = [h * cr[(l, b)][0] for h, l, b in zip(t.HOURS, t.level, t.bill_code)]
    t["BILL"] = [h * cr[(l, b)][1] for h, l, b in zip(t.HOURS, t.level, t.bill_code)]
    lines = []
    doc = [0]

    def post(fy_d, items, doc_type):
        doc[0] += 1
        d_id = f"{doc[0]:010d}"
        for j, it in enumerate(items):
            lines.append(dict(CompanyCode="USC1", FiscalYear=str(fiscal_year(fy_d)), AccountingDocument=d_id,
                              AccountingDocumentItem=f"{j + 1:06d}", LedgerGLLineItem=f"{j + 1:06d}",
                              FiscalPeriod=f"{fiscal_period(fy_d):03d}", PostingDate=fy_d, DocumentDate=fy_d,
                              AccountingDocumentType=doc_type, ControllingArea="A000", CompanyCodeCurrency="USD",
                              BaseUnit=it.get("unit"), **{k: it.get(k) for k in
                                                         ["GLAccount", "CostCenter", "ProfitCenter", "WBSElement",
                                                          "OrderID", "CostCtrActivityType", "PersonnelNumber",
                                                          "Customer", "AmountInCompanyCodeCurrency", "Quantity",
                                                          "DebitCreditCode", "ZZ_BILLABLE_CONTROL"]}))
        return d_id

    # (a) activity allocations: person x WBS / internal order x month
    agg = (t.groupby(["USER_ID", "CATEGORY", "WBS_ELEMENT", "INTERNAL_ORDER", "MONTH"], dropna=False)
           .agg(HOURS=("HOURS", "sum"), COST=("COST", "sum")).reset_index())
    for r in agg.itertuples(index=False):
        p = lv.loc[r.USER_ID]
        at = ACTIVITY_BY_LEVEL[p.level]
        d = month_end(r.MONTH)
        ce = ctx.activity_ce[at]
        target = dict(WBSElement=r.WBS_ELEMENT) if r.CATEGORY == "DELIVERY" else dict(OrderID=r.INTERNAL_ORDER)
        post(d, [dict(GLAccount=ce, ProfitCenter=pc_of_cc.get(p.cost_center), CostCtrActivityType=at,
                      PersonnelNumber=r.USER_ID, AmountInCompanyCodeCurrency=round(r.COST, 2), Quantity=r.HOURS,
                      unit="H", DebitCreditCode="S",
                      ZZ_BILLABLE_CONTROL="BILLABLE" if r.CATEGORY == "DELIVERY" else "NON_BILLABLE", **target),
                 dict(GLAccount=ce, CostCenter=p.cost_center, ProfitCenter=pc_of_cc.get(p.cost_center),
                      CostCtrActivityType=at, PersonnelNumber=r.USER_ID,
                      AmountInCompanyCodeCurrency=-round(r.COST, 2), Quantity=-r.HOURS, unit="H",
                      DebitCreditCode="H")], "RKL")
    # (b) overhead 35 % and (c) revenue per WBS x month
    deliv = t[t.CATEGORY == "DELIVERY"].groupby(["WBS_ELEMENT", "MONTH"]).agg(
        HOURS=("HOURS", "sum"), COST=("COST", "sum"), BILL=("BILL", "sum")).reset_index()
    deliv["PROJECT_ID"] = deliv.WBS_ELEMENT.str[:6]
    deliv = deliv.sort_values(["PROJECT_ID", "WBS_ELEMENT", "MONTH"])
    plan_by_wp = wpd.PLANNED_HOURS.to_dict()
    prod_by_wp = wpd.TEAM_PRODUCTIVITY.to_dict()
    proj_plan = wpd.groupby("PROJECT_ID").PLANNED_HOURS.sum().to_dict()
    cum_earned = {}
    for r in deliv.itertuples(index=False):
        pr = proj.loc[r.PROJECT_ID]
        d = month_end(r.MONTH)
        ohc = round(r.COST * ctx.params["overhead_pct"] / 100.0, 2)
        post(d, [dict(GLAccount=ctx.gl["overhead"], WBSElement=r.WBS_ELEMENT, AmountInCompanyCodeCurrency=ohc,
                      DebitCreditCode="S"),
                 dict(GLAccount=ctx.gl["overhead"], CostCenter="USC1_OH", AmountInCompanyCodeCurrency=-ohc,
                      DebitCreditCode="H")], "SA")
        if pr.CONTRACT_TYPE == "TIME_AND_MATERIALS":
            rev = r.BILL
        else:
            prev = cum_earned.get(r.WBS_ELEMENT, 0.0)
            earned = r.HOURS * prod_by_wp.get(r.WBS_ELEMENT, 1.0)
            pct_prev = min(prev / plan_by_wp[r.WBS_ELEMENT], 1.0)
            pct_now = min((prev + earned) / plan_by_wp[r.WBS_ELEMENT], 1.0)
            cum_earned[r.WBS_ELEMENT] = prev + earned
            wp_value = pr.CONTRACT_VALUE * plan_by_wp[r.WBS_ELEMENT] / proj_plan[r.PROJECT_ID]
            rev = wp_value * (pct_now - pct_prev)
        if rev > 0:
            post(d, [dict(GLAccount=ctx.gl["revenue"], WBSElement=r.WBS_ELEMENT, Customer=pr.CUSTOMER,
                          ProfitCenter="US10_PC10", AmountInCompanyCodeCurrency=-round(rev, 2), DebitCreditCode="H"),
                     dict(GLAccount=ctx.gl["receivable"], Customer=pr.CUSTOMER, ProfitCenter="US10_PC10",
                          AmountInCompanyCodeCurrency=round(rev, 2), DebitCreditCode="S")], "RV")
    agt_lines, doc[0] = agt_journal(ctx, agt, doc[0])
    je = pd.concat([pd.DataFrame(lines), agt_lines], ignore_index=True)
    # 0.5 % reversed documents (header flag) to exercise the exclusion logic
    docs = je[["CompanyCode", "FiscalYear", "AccountingDocument", "AccountingDocumentType", "PostingDate"]] \
        .drop_duplicates("AccountingDocument").reset_index(drop=True)
    rev_mask = rng.random(len(docs)) < 0.005
    docs["IsReversal"] = False
    docs["IsReversed"] = rev_mask
    docs["ReversalReferenceDocument"] = None
    reversals = docs[rev_mask].copy()
    if len(reversals):
        start = doc[0]
        reversals["ReversalReferenceDocument"] = reversals["AccountingDocument"]
        reversals["AccountingDocument"] = [f"{start + i + 1:010d}" for i in range(len(reversals))]
        reversals["IsReversal"] = True
        reversals["IsReversed"] = False
        rev_lines = je[je.AccountingDocument.isin(reversals.ReversalReferenceDocument)].copy()
        mp = dict(zip(reversals.ReversalReferenceDocument, reversals.AccountingDocument))
        rev_lines["AccountingDocument"] = rev_lines.AccountingDocument.map(mp)
        rev_lines["AmountInCompanyCodeCurrency"] = -rev_lines.AmountInCompanyCodeCurrency
        rev_lines["Quantity"] = -rev_lines.Quantity
        je = pd.concat([je, rev_lines], ignore_index=True)
        docs = pd.concat([docs, reversals], ignore_index=True)
    # plan (sold cost) per WBS x fiscal period, flat over planned duration
    plan_rows = []
    lo = ctx.levels.set_index("LEVEL").BILL_CODE_LO.to_dict()
    rate = {l: level_rates(ctx, l, int(lo[l]) + 4)[0] for l in LEVELS}
    wp_cost = {}
    for (w_id, l, h) in ctx.out["_wp_plan"]:
        wp_cost[w_id] = wp_cost.get(w_id, 0.0) + h * rate[l]
    for wp in wps:
        months = list(month_iter(wp["PLANNED_START"], wp["PLANNED_END"]))
        lvl_cost = wp_cost.get(wp["WBS_ELEMENT"], 0.0) * 1.35
        for mo in months:
            plan_rows.append(dict(PlanningCategory="PLN", CompanyCode="USC1", WBSElement=wp["WBS_ELEMENT"],
                                  FiscalYear=str(fiscal_year(mo)), FiscalPeriod=f"{fiscal_period(mo):03d}",
                                  GLAccount=ctx.gl["plan_cost"],
                                  AmountInCompanyCodeCurrency=round(lvl_cost / len(months), 2)))
    plan = pd.DataFrame(plan_rows)
    io = pd.DataFrame([dict(OrderID=o["INTERNAL_ORDER"], OrderType="PRESALES", OpportunityID=o["OPPORTUNITY_ID"],
                            CompanyCode="USC1", ControllingArea="A000",
                            ResponsibleCostCenter=ctx.mdcc[(ctx.mdcc.MD_GROUP_ID == o["MD_GROUP_ID"])
                                                           & (ctx.mdcc.CC_ROLE == "DELIVERY")].COST_CENTER.min(),
                            CreatedDate=o["CREATED_DATE"]) for o in opps]
                      + [dict(OrderID="IO-LEARNING", OrderType="LEARNING", OpportunityID=None, CompanyCode="USC1",
                              ControllingArea="A000", ResponsibleCostCenter="USC1_HR5", CreatedDate=WINDOW_START),
                         dict(OrderID="IO-ADMIN", OrderType="ADMIN", OpportunityID=None, CompanyCode="USC1",
                              ControllingArea="A000", ResponsibleCostCenter="USC1_M1", CreatedDate=WINDOW_START)])
    return je, docs, plan, io


def build_telemetry_and_agt(ctx, st, people, ts, wk, je_lines_fn=None):
    """Per person x vendor x active day usage; AGT_* allocations from AI cost centres to project WBS."""
    rng = ctx.rng
    rows = {v: [] for v in VENDORS}
    uid = people.user_id.values
    deliv = ts[ts.CATEGORY == "DELIVERY"][["USER_ID", "WEEK_START", "WBS_ELEMENT"]].drop_duplicates(
        ["USER_ID", "WEEK_START"])
    wbs_of = {(u, w): b for u, w, b in deliv.itertuples(index=False)}
    use_i, use_w = np.nonzero(st.usage > 0.05)
    vendor_pref = rng.choice(3, size=len(people), p=[0.4, 0.35, 0.25])
    for pi, w in zip(use_i, use_w):
        if st.avail[pi, w] <= 0:
            continue
        u = float(st.usage[pi, w])
        days = int(np.clip(round(u * 5 + rng.normal(0, 0.7)), 1, 5))
        ws = wk.week_start.iloc[w]
        for d in range(days):
            v = VENDORS[vendor_pref[pi] if rng.random() < 0.75 else int(rng.integers(0, 3))]
            day = ws + dt.timedelta(days=d)
            mapped = rng.random() < 0.92
            proj = wbs_of.get((uid[pi], ws)) if rng.random() < 0.93 else None
            sessions = int(rng.integers(1, 8))
            tokens = int(sessions * rng.integers(8_000, 60_000))
            cost = round(tokens / 1e6 * {"OPENAI": 6.0, "ANTHROPIC": 9.0, "CORTEX": 4.0}[v], 4)
            rows[v].append((day, uid[pi] if mapped else None, proj, sessions, tokens, cost))
    out = {}
    for v in VENDORS:
        df = pd.DataFrame(rows[v], columns=["USAGE_DATE", "USER_KEY", "PROJECT_KEY", "SESSIONS", "TOKENS", "COST_USD"])
        df["VENDOR"] = v
        df["SOURCE_SYSTEM"] = "SIMULATED"
        out[v] = df
    allu = pd.concat(out.values(), ignore_index=True)
    allu = allu[allu.PROJECT_KEY.notna()].copy()
    allu["MONTH"] = pd.to_datetime(allu.USAGE_DATE).dt.to_period("M").dt.to_timestamp().dt.date
    agt = allu.groupby(["VENDOR", "PROJECT_KEY", "MONTH"]).COST_USD.sum().reset_index()
    ident = pd.DataFrame({"USER_ID": uid, "OPENAI_USER_ID": ["user-" + hashlib.sha1(u.encode()).hexdigest()[:10]
                                                             for u in uid],
                          "ANTHROPIC_ACTOR_EMAIL": [f"{u.lower()}@acoco.example" for u in uid],
                          "SNOWFLAKE_USER_NAME": [f"ACOCO_{u}" for u in uid]})
    return out, agt, ident


def agt_journal(ctx, agt, start_doc):
    lines, doc = [], start_doc
    for r in agt.itertuples(index=False):
        doc += 1
        d = month_end(r.MONTH)
        amt = round(float(r.COST_USD) * 4.0, 2)            # loaded agent cost (platform + licences) per PRD R6
        qty = round(amt / AGT_PRICE[r.VENDOR], 2)
        base = dict(CompanyCode="USC1", FiscalYear=str(fiscal_year(d)), AccountingDocument=f"{doc:010d}",
                    FiscalPeriod=f"{fiscal_period(d):03d}", PostingDate=d, DocumentDate=d,
                    AccountingDocumentType="RKL", ControllingArea="A000", CompanyCodeCurrency="USD", BaseUnit="H",
                    GLAccount=ctx.gl["agent_cost"], CostCtrActivityType=f"AGT_{r.VENDOR}")
        lines.append(dict(base, AccountingDocumentItem="000001", LedgerGLLineItem="000001", WBSElement=r.PROJECT_KEY,
                          AmountInCompanyCodeCurrency=amt, Quantity=qty, DebitCreditCode="S"))
        lines.append(dict(base, AccountingDocumentItem="000002", LedgerGLLineItem="000002", CostCenter=AI_CC[r.VENDOR],
                          AmountInCompanyCodeCurrency=-amt, Quantity=-qty, DebitCreditCode="H"))
    return pd.DataFrame(lines), doc


def build_notes(ctx, projects, wps):
    rng = ctx.rng
    wpd = pd.DataFrame(wps)
    notes = []
    for p in projects:
        mine = wpd[wpd.PROJECT_ID == p["PROJECT_ID"]]
        late = mine[mine.FORECAST_END > mine.PLANNED_END]
        months = [m for m in month_iter(p["PLANNED_START"], min(p["PLANNED_END"], AS_OF)) if m < AS_OF]
        for i, m in enumerate(months):
            if p["SEEDED_STORY"] == "FS_LOSS":
                cause = ["late client data delivery", "under-estimated data volumes", "staffing gap at Consultant level"][i % 3]
                text = (f"{p['PROJECT_ID']} month {i + 1}: migration scripting work package behind plan; {cause}. "
                        f"Earned value trending below 0.8 of plan; critical path is WP02. Contingency exhausted.")
                rag = "RED" if i >= 2 else "AMBER"
            elif len(late) and i >= len(months) // 2:
                cause = ROOT_CAUSES[int(rng.integers(0, len(ROOT_CAUSES)))]
                text = f"{p['PROJECT_ID']} month {i + 1}: schedule slipping on {late.iloc[0].WBS_ELEMENT}; {cause}."
                rag = "AMBER"
            else:
                text = f"{p['PROJECT_ID']} month {i + 1}: delivery on track; milestones met."
                rag = "GREEN"
            notes.append(dict(NOTE_ID=f"N-{len(notes) + 1:06d}", PROJECT_ID=p["PROJECT_ID"], NOTE_DATE=month_end(m),
                              RAG_STATUS=rag, NOTE_TEXT=text, SOURCE_SYSTEM="SIMULATED"))
    return pd.DataFrame(notes)


# ----------------------------------------------------------------------------------------------- CLD-shaped HR rows
def core_workforce_rows(ctx, people, perf, comp):
    """Monthly Core Workforce rows (BDC column names) for: real users' back-history (window start .. their first
    CLD record) and Aug-Sep 2026 extension; simulated users for their whole employment."""
    rp = ctx.real_people
    first_real = dict(zip(rp.USER_ID.astype(str), rp.FIRST_START))
    last_real = dict(zip(rp.USER_ID.astype(str), rp.LAST_END))
    sal_mid = {"Analyst": 70000, "Consultant": 95000, "Manager": 130000, "Senior Manager": 170000,
               "Principal": 230000}
    compa = comp.set_index("USER_ID").COMPA_RATIO.to_dict()
    rows = []
    for p in people.itertuples(index=False):
        if p.source_system == "BDC_CLD":
            spans = [(WINDOW_START, first_real.get(p.user_id, WINDOW_START) - dt.timedelta(days=1))]
            le = last_real.get(p.user_id)
            if le is not None and le < WINDOW_END and (p.term_date is None or pd.isna(p.term_date)):
                spans.append((le + dt.timedelta(days=1), WINDOW_END))
        else:
            spans = [(WINDOW_START, WINDOW_END)]
        for s0, s1 in spans:
            for m in month_iter(s0, s1):
                me = month_end(m)
                if p.hire_date and me < p.hire_date:
                    continue
                if p.term_date is not None and not pd.isna(p.term_date) and m > p.term_date:
                    continue
                is_term = p.term_date is not None and not pd.isna(p.term_date) and m <= p.term_date <= me
                hired = p.hire_date and m <= p.hire_date <= me
                mid = sal_mid[p.level]
                tenure = max(0, (m.year - p.hire_date.year) * 12 + m.month - p.hire_date.month) if p.hire_date else 0
                rows.append({"userId": p.user_id, "startDate": max(m, p.hire_date) if hired else m,
                             "endDate": p.term_date if is_term else me,
                             "employmentStatus": "D" if is_term else "A",
                             "eventReasonCode": "TERM_VOL" if is_term else ("HIRNEW" if hired else "DATACHG"),
                             "moveOutReason": p.term_reason if is_term else None,
                             "terminations": 1 if is_term else None, "externalHires": 1 if hired else None,
                             "payGrade": int(p.pay_grade), "costCenter": p.sf_cost_center, "fte": 1.0,
                             "organizationalTenure": str(tenure), "tenureStartDate": p.hire_date,
                             "annualSalary": round(mid * compa.get(p.user_id, 1.0), 0), "midPoint": mid,
                             "gender": p.gender, "sopHeadcount": 0.0 if hired else 1.0,
                             "eopHeadcount": 0.0 if is_term else 1.0, "avgHeadcount": 1.0})
    return pd.DataFrame(rows)


def availability_rows(ctx, people, leave, wk):
    """Daily Employee Availability rows (BDC column names) where no real row exists: real users before the CLD
    starts (2024-07-08) and all simulated users. Weekdays only."""
    real = ctx.assign_map.set_index("USER_ID").ASSIGNMENT_ID.to_dict()
    real_from = ctx.real_avail_week.WEEK_START.min() if len(ctx.real_avail_week) else FORWARD_END
    wd = workdays()
    wd["week_start"] = [d - dt.timedelta(days=d.weekday()) for d in wd["date"]]
    week_idx = dict(zip(wk.week_start, wk.week_idx))
    out = []
    for p in people.itertuples(index=False):
        aid = real.get(p.user_id, f"SA-{p.user_id}")
        last = real_from - dt.timedelta(days=1) if p.source_system == "BDC_CLD" else FORWARD_END
        sel = wd[(wd.date >= max(WINDOW_START, p.hire_date or WINDOW_START)) & (wd.date <= last)]
        if p.term_date is not None and not pd.isna(p.term_date):
            sel = sel[sel.date <= p.term_date]
        if sel.empty:
            continue
        lv = leave[p.pidx]
        for d, hol, ws in zip(sel.date, sel.is_holiday, sel.week_start):
            lw = lv[week_idx[ws]]
            absent = 8.0 if (lw >= 40 or (lw > 0 and d.weekday() in (0, 1) and lw >= 16)) else 0.0
            out.append((aid, d, 0.0 if hol else 8.0, bool(hol), "LEAVE" if absent else None,
                        0.0 if hol else absent))
    ea = pd.DataFrame(out, columns=["assignmentId", "workDate", "plannedWorkHours", "isPublicHoliday",
                                    "absenceType", "dailyAbsenceHours"])
    ea["isWeeklyOff"] = False
    ea["availabilityStatus"] = np.where(ea.dailyAbsenceHours > 0, "ABSENT", "AVAILABLE")
    return ea
