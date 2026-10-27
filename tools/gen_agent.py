"""Build, deploy and regression-test the Cortex Agent ACOCO_DB.AGENT.ACOCO_ADVISOR (PRD 10).

  .venv/bin/python tools/gen_agent.py --render          write agent/acoco_advisor.agent.yaml (spec)
  .venv/bin/python tools/gen_agent.py --deploy          render + `cortex agent-studio agent-write` + `agent-deploy`
  .venv/bin/python tools/gen_agent.py --regress [N..]   run the 20 PRD-10 prompts (or the given numbers) through the
                                                        Agent REST API; routing / figure / latency assertions ->
                                                        logs/agent_regression.md + .json

Instructions carry the PRD-10 rules and the entity -> Semantic View map read from ACOCO_L2.ONTOLOGY.ONT_*.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402

AGENT_FQN = "ACOCO_DB.AGENT.ACOCO_ADVISOR"
SPEC_PATH = ROOT / "agent" / "acoco_advisor.agent.yaml"
MODEL = "claude-sonnet-4-5"
WAREHOUSE = "WH_ACOCO_APP"

TOOLS = [
    ("portfolio", "SV_PORTFOLIO_360",
     "ProServe360 overlay for the MD: MD-group revenue, margin, time mix by category vs target, bench, attrition, "
     "win-rate inputs and the cross-pillar risk register (top risks by USD at stake). Use first for scorecards, "
     "year-on-year comparisons and 'what are my biggest risks'."),
    ("project_delivery", "SV_PROJECT_DELIVERY",
     "Operational Excellence: project P&L, CPI / SPI / EAC, liquidated-damages exposure, forecast margin, project teams, "
     "delivery model (HUMAN / HUMAN_AGENT / AGENT_LED), asset reuse and MISSED reuse (assets that matched a work package but "
     "were not used, with ESTIMATED hours saved), work-package skill needs."),
    ("pipeline_presales", "SV_PIPELINE_PRESALES",
     "Value Creation: bids, win-rate, pursuit cost and intensity vs size-class median, pursuit-team skill fit bands, "
     "required skills, open pipeline value, and the bench-to-pipeline match (people rolling off in 90 days x open bids, "
     "match score, skill coverage, whether they meet the bid's AI-skill level)."),
    ("workforce", "SV_WORKFORCE_PERFORMANCE",
     "People Development (People Intelligence): person-month time mix (Delivery, Bid, Learning, Admin, Bench) vs level "
     "targets, productivity, headcount and voluntary attrition, roll-off in the next 90 days (and below the pipeline "
     "AI-skill level), skill proficiency, and modelled attrition risk (risk decile, top drivers)."),
    ("ai_adoption", "SV_AI_ADOPTION",
     "People Development (AI): AI assistant use and spend by tool, AI-agent cost charged to projects, AI-active vs other "
     "productivity, the stratified AI productivity test with 90 % confidence intervals (AI_ACTIVE and SKILLED_INACTIVE bands, "
     "SIGNIFICANT flag) and the learning payback test by curriculum."),
]
SEARCH = [
    ("project_commentary", "ACOCO_L2.REASONING.CSS_PROJECT_COMMENTARY", "NOTE_ID", "PROJECT_ID",
     "Project managers' monthly status notes (RAG, reasons for slippage, staffing gaps, client issues). Use for WHY a "
     "project is late / over budget; filter MD_GROUP_ID (e.g. FS) and RAG_STATUS (RED / AMBER) when the MD asks about her group."),
    ("asset_library", "ACOCO_L2.REASONING.CSS_ASSET_LIBRARY", "ASSET_ID", "ASSET_TITLE",
     "Reusable delivery assets (accelerators, templates, test packs) with work type and skill tags. Use to recommend "
     "assets for a project or bid by need."),
]


def entity_map():
    rels = sf.query("SELECT FROM_ENTITY, VERB, TO_ENTITY, SEMANTIC_VIEWS FROM ACOCO_L2.ONTOLOGY.ONT_RELATIONSHIP ORDER BY 1, 3")
    ents = sf.query("SELECT ENTITY, OWNING_SYSTEM, SEMANTIC_VIEWS FROM ACOCO_L2.ONTOLOGY.ONT_ENTITY ORDER BY 1")
    tool_of = {sv: t for t, sv, _ in TOOLS}
    conv = lambda svs: ", ".join(tool_of.get(x.strip(), x.strip()) for x in svs.split(",") if x.strip())
    lines = ["Entity -> tools (from ONT_ENTITY):"] + [f"- {e['ENTITY']} ({e['OWNING_SYSTEM']}): {conv(e['SEMANTIC_VIEWS'])}" for e in ents]
    lines += ["Relationships -> tools that can traverse them (from ONT_RELATIONSHIP):"]
    lines += [f"- {r['FROM_ENTITY']} {r['VERB']} {r['TO_ENTITY']}: {conv(r['SEMANTIC_VIEWS'])}" for r in rels]
    return "\n".join(lines)


def spec():
    response = """You are ACoCo Advisor for Priya Nair, Partner and Managing Director of the Financial Services (FS) group
of ACoCo, a professional-services firm. Answer for FS unless she asks firm-wide or about another group.
- Lead with the answer in one or two sentences, then a compact table. Use USD with thousands separators; percentages to one decimal.
- Frame every answer by pillar: Operational Excellence (delivery, margin, CPI/SPI), Value Creation (pipeline, win-rate,
  assets, AI agents as a costed resource), People Development (time mix, skills, learning, attrition, AI adoption).
  When a trade-off moves two pillars, say which.
- Name the tool / Semantic View each figure comes from in a short "Sources:" line.
- Honesty rules: (1) figures that include simulated rows (SOURCE_SYSTEM = SIMULATED) are demo data - say so once when
  relevant; (2) asset hours saved are ESTIMATED; (3) AI productivity results are ASSOCIATIONS within level x work type
  with a 90 % confidence interval - never say AI "causes" or "makes" people more productive, and when a band is not
  significant say "no significant effect"; (4) the attrition model is indicative (hold-out AUC 0.90 overall, 0.57 within
  the simulated pool) - present risk lists as a prompt for conversations, not a prediction about an individual;
  (5) never quote an individual's pay, salary or compa-ratio."""
    orchestration = f"""Today is 1 Oct 2026 (FY27 day 1). Fiscal years run October-September: FY26 = Oct 2025 - Sep 2026 and is the
last CLOSED year; "this year" / "last year" mean FY26 / FY25 unless the user says FY27. FY27 has no actuals yet.
Time targets by level (share of available hours, Delivery / Bid / Learning / Admin / Bench): Analyst 75/10/10/3/2,
Consultant 71/14/10/3/2, Manager 60/25/10/3/2, Senior Manager 45/40/10/3/2, Principal 35/50/10/3/2.
Judge Delivery first; judge Bid by win-rate and pursuit cost per won USD, never by hours alone; Admin must stay < 5 %;
Bench ~2 % is the transition allowance (above 3 % is a problem). Higher bill codes within a level carry more Bid.
Routing:
- Scorecards, FY26 vs FY25, group P&L, capacity mix, top risks -> portfolio (then drill down with the pillar tool).
- A project's margin, CPI/SPI, LDs, team, pyramid, delivery model, asset reuse / missed reuse -> project_delivery.
- WHY a project is late or over budget -> project_commentary (filter MD_GROUP_ID and RAG_STATUS), combined with project_delivery figures.
- Bids, win-rate, pursuit intensity, team skill fit, open pipeline, bench-to-pipeline matches -> pipeline_presales.
- Time mix per person / level, bench, roll-off, headcount, attrition, attrition risk, skills -> workforce.
- AI tool use, AI spend, AI-agent cost, AI productivity test, learning payback -> ai_adoption.
- Asset recommendations by need -> asset_library (plus project_delivery for missed reuse figures).
- Cross-pillar questions (e.g. bench people with AI skill 3+ who fit open bids) need two tools: use pipeline_presales for
  the bench-to-pipeline match and workforce for roll-off / skills, then join the answers by person.
- For the AI productivity test always use the productivity_test table with scope 'FS' (or 'FIRM'), stratum 'ALL LEVELS',
  fiscal year 2026, and report uplift with ci_low / ci_high and is_significant for both AI_ACTIVE and SKILLED_INACTIVE.
- Filter MD groups by name ('Financial Services') or id ('FS').
{entity_map()}"""
    tools, res = [], {}
    for name, sv, desc in TOOLS:
        tools.append(dict(tool_spec=dict(type="cortex_analyst_text_to_sql", name=name, description=desc)))
        res[name] = dict(execution_environment=dict(type="warehouse", warehouse=WAREHOUSE),
                         semantic_view=f"ACOCO_L2.SEMANTIC.{sv}")
    for name, svc, idc, title, desc in SEARCH:
        tools.append(dict(tool_spec=dict(type="cortex_search", name=name, description=desc)))
        res[name] = dict(search_service=svc, id_column=idc, title_column=title, max_results=5)
    return dict(models=dict(orchestration=MODEL),
                orchestration=dict(budget=dict(seconds=240, tokens=40000)),
                instructions=dict(response=response, orchestration=orchestration,
                                  sample_questions=[dict(question=q) for q in (
                                      "Give me my FY26 ProServe360 scorecard against FY25.",
                                      "Which bench consultants with AI skill 3+ fit my open bids above USD 5 M?",
                                      "Why is my at-risk fixed-price project behind schedule?")]),
                tools=tools, tool_resources=res)


def render():
    SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPEC_PATH.write_text(yaml.safe_dump(spec(), sort_keys=False, width=120))
    print(f"rendered {SPEC_PATH}")


def deploy():
    sf.query("CREATE SCHEMA IF NOT EXISTS ACOCO_DB.AGENT")
    content = SPEC_PATH.read_text()
    for cmd in (["cortex", "agent-studio", "agent-write", "-c", sf.CONNECTION, "--yaml-content", content,
                 "--source-object", AGENT_FQN],
                ["cortex", "agent-studio", "agent-deploy", "-c", sf.CONNECTION, "--yaml-content", content, "--fqn", AGENT_FQN]):
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        tail = (p.stdout + p.stderr).strip()[-500:]
        print(f"{cmd[2]}: rc {p.returncode} {tail[-200:]}")
        if p.returncode != 0:
            sys.exit(1)
    sf.query(f"ALTER AGENT {AGENT_FQN} SET COMMENT = 'ACoCo Advisor for the FS Partner MD (PRD 10); generated by tools/gen_agent.py'")


# ---------------------------------------------------------------------------------------------- regression
def anchors():
    return {a["id"]: a for a in json.loads((ROOT / "logs" / "validate_anchors.json").read_text())}


def num_in(text, lo, hi):
    """True if any number in the text falls in [lo, hi]."""
    for m in re.finditer(r"-?\d[\d,]*\.?\d*", text):
        try:
            v = float(m.group().replace(",", ""))
        except ValueError:
            continue
        if lo <= v <= hi:
            return True
    return False


def prompts():
    a = anchors()
    story = re.search(r"P-\d{4}", a["A1"]["measured"]).group()
    fs_bench = float(re.search(r"Bench ([\d.]+)", a["A9"]["measured"]).group(1))
    fs_deliv = float(re.search(r"Delivery ([\d.]+)", a["A9"]["measured"]).group(1))
    ro = int(re.search(r"(\d+) people", a["A3"]["measured"]).group(1))
    up = float(re.search(r"uplift ([+\-][\d.]+)", a["A10"]["measured"]).group(1))
    fit_hi = float(re.search(r"high ([\d.]+) %", a["A7"]["measured"]).group(1))
    # (id, story, prompt, expected tools (all must be used), [figure checks (lo, hi, label)], must-contain phrases)
    return [
        (1, "PMD-0", "Give me my FY26 ProServe360 scorecard against FY25.", {"portfolio"}, [], []),
        (2, "PMD-1", "Which of my FS projects drag margin the most in FY26?", {"project_delivery"}, [], []),
        (3, "PMD-2", f"What are the CPI and SPI of project {story} and its forecast margin?", {"project_delivery"},
         [(0.6, 0.8, "CPI")], [story]),
        (4, "PMD-3", "What was my FS time mix by level in FY26 against the level targets?", {"workforce|portfolio"},
         [(fs_bench - 0.6, fs_bench + 0.6, "bench %"), ], []),
        (5, "PMD-4", "How many FS people roll off before 30 December 2026, and how many are below the pipeline's AI-skill level?",
         {"workforce"}, [(ro - 3, ro + 3, "roll-offs")], []),
        (6, "PMD-5", "Who in FS has the highest attrition risk and what drives it?", {"workforce"}, [], []),
        (7, "PMD-6", "Does pursuit intensity improve our win-rate? Compare above- and below-median intensity bids within size class.",
         {"pipeline_presales"}, [], []),
        (8, "PMD-7", "Do People+Agents projects earn a better margin than People-only projects in FS in FY26?",
         {"project_delivery|ai_adoption"}, [], []),
        (9, "PMD-8", f"Why is project {story} behind schedule?", {"project_commentary"}, [], [story]),
        (10, "PMD-9", f"Which reusable assets did project {story} miss, and how many hours could they have saved?",
         {"project_delivery|asset_library"}, [], []),
        (11, "PMD-10", "What is our win-rate when the pursuit team's skill fit is at least 0.8 versus below 0.5?",
         {"pipeline_presales"}, [(fit_hi - 3, fit_hi + 3, "high-fit win-rate")], []),
        (12, "PMD-11", "If the bid that best fits my roll-off people slips 30 days, who stays on the bench and what does it cost?",
         {"pipeline_presales|workforce"}, [], []),
        (13, "PMD-12", "Does the agentic-AI curriculum pay back in later productivity?", {"ai_adoption"}, [], []),
        (14, "WHY-1", "Why are my red FS projects late?", {"project_commentary"}, [], []),
        (15, "WHY-2", "Why did FS margin change between FY25 and FY26?", {"portfolio|project_delivery"}, [], []),
        (16, "WHY-3", f"What do the project managers say is the main problem on {story}?", {"project_commentary"}, [], [story]),
        (17, "R1", "Which people rolling off in FS best match my open bids?", {"pipeline_presales"}, [], []),
        (18, "R2", "Which FS consultants are in the top attrition-risk decile?", {"workforce"}, [], []),
        (19, "R12", "Recommend assets for a data migration bid.", {"asset_library|project_delivery"}, [], []),
        (20, "R13", "Does AI make my skilled-but-inactive consultants more productive?", {"ai_adoption"},
         [], ["no significant", "associat"]),
    ], dict(story=story, fs_bench=fs_bench, fs_deliv=fs_deliv, roll_off=ro, uplift=up)


def run_agent(conn, question):
    db, sc, name = AGENT_FQN.split(".")
    body = json.dumps({"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}]}).encode()
    req = urllib.request.Request(f"https://{conn.host}/api/v2/databases/{db}/schemas/{sc}/agents/{name}:run", data=body,
                                 method="POST", headers={"Authorization": f'Snowflake Token="{conn.rest.token}"',
                                                         "Content-Type": "application/json", "Accept": "text/event-stream"})
    t0 = time.time()
    tools, text, sqls, event = [], [], [], None
    with urllib.request.urlopen(req, timeout=300) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").rstrip("\n")
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                try:
                    d = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue
                if event == "response.tool_use":
                    tools.append(d.get("name"))
                elif event == "response.text.delta":
                    text.append(d.get("text", ""))
                elif event == "response.tool_result":
                    for c in d.get("content", []):
                        s = (c.get("json") or {}).get("sql")
                        if s:
                            sqls.append(s)
                elif event == "error":
                    text.append(f"[ERROR {d}]")
    return dict(tools=tools, text="".join(text), sqls=sqls, seconds=round(time.time() - t0, 1))


def regress(only):
    import snowflake.connector
    conn = snowflake.connector.connect(connection_name=sf.CONNECTION)
    plist, ctx = prompts()
    results = []
    for pid, story, q, expect, figs, phrases in plist:
        if only and pid not in only:
            continue
        try:
            r = run_agent(conn, q)
        except Exception as e:
            r = dict(tools=[], text=f"[EXCEPTION {e}]", sqls=[], seconds=None)
        used = set(r["tools"])
        route_ok = all(any(alt in used for alt in group.split("|")) for group in expect)
        fig_ok = all(num_in(r["text"], lo, hi) for lo, hi, _ in figs)
        phrase_ok = all(p.lower() in r["text"].lower() for p in phrases)
        if pid == 20:   # R13 honesty: must not claim causation
            phrase_ok = phrase_ok and not re.search(r"\b(causes?|caused|makes? (them|people|consultants) more)\b", r["text"], re.I)
        res = dict(id=pid, story=story, prompt=q, expected=sorted(expect), used=r["tools"], routing=route_ok,
                   figures=fig_ok, phrases=phrase_ok, seconds=r["seconds"], answer=r["text"][:1500],
                   ok=route_ok and fig_ok and phrase_ok and "[ERROR" not in r["text"] and "[EXCEPTION" not in r["text"])
        results.append(res)
        print(f"{'PASS' if res['ok'] else 'FAIL'} {pid:>2} {story:<7} {r['seconds']}s tools={r['tools']} "
              f"route={route_ok} fig={fig_ok} phrase={phrase_ok}")
    (ROOT / "logs" / "agent_regression.json").write_text(json.dumps(dict(context=ctx, results=results), indent=1))
    write_md(results, ctx)
    return results


def write_md(results, ctx):
    secs = sorted(r["seconds"] for r in results if r["seconds"] is not None)
    p = lambda q: secs[min(len(secs) - 1, int(round(q * (len(secs) - 1))))] if secs else None
    ok = sum(r["ok"] for r in results)
    lines = [f"# ACOCO_ADVISOR regression ({time.strftime('%Y-%m-%d %H:%M')})", "",
             f"Agent `{AGENT_FQN}`, model `{MODEL}`, {len(results)} prompts (PRD 10): **{ok}/{len(results)} PASS**.",
             f"Figures checked against `plan/measured_anchors.md` (story project {ctx['story']}, FS bench {ctx['fs_bench']} %, "
             f"FS roll-offs {ctx['roll_off']}).", "",
             "| # | Story | Prompt | Expected tool | Tools used | Routing | Figures | Phrases | Seconds | Result |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['id']} | {r['story']} | {r['prompt']} | {', '.join(r['expected'])} | {', '.join(r['used']) or '-'} | "
                     f"{'ok' if r['routing'] else 'MISS'} | {'ok' if r['figures'] else 'MISS'} | {'ok' if r['phrases'] else 'MISS'} | "
                     f"{r['seconds']} | **{'PASS' if r['ok'] else 'FAIL'}** |")
    lines += ["", "## Latency", "", "| p50 | p90 | max |", "|---|---|---|", f"| {p(0.5)} s | {p(0.9)} s | {secs[-1] if secs else None} s |",
              "", "## Answers", ""]
    for r in results:
        lines += [f"### {r['id']}. {r['story']} - {r['prompt']}", "", r["answer"].replace("\n", "\n> ").join(["> ", ""]), ""]
    (ROOT / "logs" / "agent_regression.md").write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--regress", nargs="*", type=int)
    a = ap.parse_args()
    if a.render or a.deploy:
        render()
    if a.deploy:
        deploy()
    if a.regress is not None:
        res = regress(set(a.regress))
        sys.exit(0 if all(r["ok"] for r in res) else 1)


if __name__ == "__main__":
    main()
