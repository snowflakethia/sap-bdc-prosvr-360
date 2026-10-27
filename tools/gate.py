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


GATES = {"cp00": gate_cp00}


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
