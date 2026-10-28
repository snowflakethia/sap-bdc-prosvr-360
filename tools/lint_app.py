"""CP-09 app lint (PRD 8.2 / plan CP-09).

  python tools/lint_app.py          # static rules over service/ -> "lint: 0 violations"
  python tools/lint_app.py --run    # also run every registry statement with default binds, report rows / ms

Rules
  R1  no ACOCO_SIM. / ACOCO_L1. / *_V1 object and no ACOCO_L2 schema other than SERVING, SEMANTIC, ONTOLOGY
      anywhere in service/ (the two Cortex Search services in ACOCO_L2.REASONING are the named PRD 8.3 exceptions);
      no leftover Supply Chain 360 objects (APP_DATA, SAP_SUPPLY_CHAIN, APP_REF).
  R2  server/src/registry.sql is byte-identical to tools/demo_queries.sql.
  R3  bind variables only: each registry statement's '?' count equals its declared binds; no ${...} in any
      server SQL template; runQuery is only called by the registry runner and with registry text.
"""
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / "service" / "app"
REGISTRY = APP / "server" / "src" / "registry.sql"
COPY = ROOT / "tools" / "demo_queries.sql"
SKIP_DIRS = {"node_modules", "dist", ".vite"}
TEXT_EXT = {".ts", ".tsx", ".js", ".mjs", ".json", ".sql", ".yaml", ".yml", ".html", ".css", ".md", ""}
ALLOWED_SCHEMAS = {"SERVING", "SEMANTIC", "ONTOLOGY"}
ALLOWED_EXCEPTIONS = {"ACOCO_L2.REASONING.CSS_PROJECT_COMMENTARY", "ACOCO_L2.REASONING.CSS_ASSET_LIBRARY"}
RUNNER_FILES = {"registry.ts"}

# Default binds = the demo's opening state (FS, FY22-FY26, story project).
DEFAULTS = {"prompt": "Reply with the single word OK.", "g": "FS", "gf": "FS", "fy0": 2022, "fy1": 2026, "s": "ALL", "p": "P-0615",
            "q": '{"query": "why is the project over budget", "columns": ["NOTE_DATE", "RAG_STATUS", "SEARCH_TEXT"], '
                 '"filter": {"@eq": {"PROJECT_ID": "P-0615"}}, "limit": 3}'}
AS_SEARCH_Q = '{"query": "data migration accelerator", "columns": ["ASSET_ID", "ASSET_TITLE", "ASSET_TYPE", "WORK_TYPE", ' \
              '"EFFORT_SAVING_HOURS", "SOURCE_PROJECT_ID"], "limit": 5}'


def parse_registry(text):
    """-> [(name, [bind names], sql)] from '-- name:' / '-- binds:' headers."""
    out = []
    for block in re.split(r"(?m)^-- name: ", text)[1:]:
        lines = block.split("\n")
        name = lines[0].strip()
        assert lines[1].startswith("-- binds:"), f"{name}: missing '-- binds:' line"
        binds = [b.strip() for b in lines[1][len("-- binds:"):].split(",") if b.strip()]
        sql = "\n".join(lines[2:]).strip()
        out.append((name, binds, sql.rstrip(";").strip()))
    return out


def files():
    for f in APP.rglob("*"):
        if f.is_file() and not (set(f.relative_to(APP).parts) & SKIP_DIRS) and f.suffix in TEXT_EXT \
                and f.name not in {"package-lock.json"}:
            yield f


def lint():
    v = []
    for f in files():
        rel = f.relative_to(ROOT)
        for i, line in enumerate(f.read_text(errors="ignore").split("\n"), 1):
            for m in re.finditer(r"\bACOCO_(SIM|L1)\.", line):
                v.append(f"R1 {rel}:{i} reads {m.group(0)}")
            for m in re.finditer(r"\b[A-Z][A-Z0-9_]*_V1\b", line):
                v.append(f"R1 {rel}:{i} references {m.group(0)}")
            for m in re.finditer(r"\bACOCO_L2\.([A-Z_]+)(\.[A-Z0-9_]+)?", line):
                if m.group(1) not in ALLOWED_SCHEMAS and m.group(0) not in ALLOWED_EXCEPTIONS:
                    v.append(f"R1 {rel}:{i} reads ACOCO_L2.{m.group(1)}")
            for m in re.finditer(r"\b(APP_DATA|SAP_SUPPLY_CHAIN|APP_REF)\b", line):
                if f.name != "VENDORED.md":
                    v.append(f"R1 {rel}:{i} leftover SC360 object {m.group(0)}")
    if not COPY.exists() or REGISTRY.read_bytes() != COPY.read_bytes():
        v.append("R2 server/src/registry.sql differs from tools/demo_queries.sql")
    stmts = parse_registry(REGISTRY.read_text())
    names = [s[0] for s in stmts]
    for d in {n for n in names if names.count(n) > 1}:
        v.append(f"R3 duplicate registry name {d}")
    for name, binds, sql in stmts:
        body = re.sub(r"'[^']*'", "''", sql)
        if body.count("?") != len(binds):
            v.append(f"R3 {name}: {body.count('?')} '?' but {len(binds)} binds declared")
        if "${" in sql or "{{" in sql:
            v.append(f"R3 {name}: template interpolation in SQL")
        unknown = [b for b in binds if b not in DEFAULTS]
        if unknown:
            v.append(f"R3 {name}: unknown bind names {unknown}")
    for f in (APP / "server" / "src").rglob("*.ts"):
        src = f.read_text()
        for m in re.finditer(r"`([^`]*)`", src, re.S):
            if "${" in m.group(1) and re.search(r"\b(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|MERGE|CALL)\b", m.group(1)):
                v.append(f"R3 {f.relative_to(ROOT)}: SQL template with interpolation")
        if "runQuery(" in src and f.name not in RUNNER_FILES and f.name != "snowflake.ts":
            v.append(f"R3 {f.relative_to(ROOT)}: calls runQuery outside the registry runner")
    return v, stmts


def run(stmts):
    import snowflake.connector
    con = snowflake.connector.connect(connection_name="sfseapac_kp", paramstyle="qmark",
                                      session_parameters={"QUERY_TAG": "ACOCO_APP_LINT"})
    cur = con.cursor()
    cur.execute("USE WAREHOUSE WH_ACOCO_APP")
    bad = 0
    for name, binds, sql in stmts:
        vals = [AS_SEARCH_Q if (name == "as_search" and b == "q") else DEFAULTS[b] for b in binds]
        t = time.time()
        try:
            cur.execute(sql, vals)
            n = len(cur.fetchall())
            ms = int(1000 * (time.time() - t))
            flag = "" if n else "  <- 0 rows"
            bad += 0 if n else 1
            print(f"  {name:22s} {n:6d} rows {ms:6d} ms{flag}")
        except Exception as e:
            bad += 1
            print(f"  {name:22s} ERROR {str(e)[:160]}")
    print(f"run: {len(stmts) - bad}/{len(stmts)} statements return rows")
    return bad


if __name__ == "__main__":
    violations, statements = lint()
    for x in violations:
        print(x)
    print(f"lint: {len(violations)} violations ({len(statements)} registry statements)")
    rc = 1 if violations else 0
    if "--run" in sys.argv:
        rc |= 1 if run(statements) else 0
    sys.exit(rc)
