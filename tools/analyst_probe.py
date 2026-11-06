"""Ask Cortex Analyst one question per Semantic View and execute the SQL it returns (gate CP-07).

  .venv/bin/python tools/analyst_probe.py          -> logs/analyst_probe.json

Uses the Python connector session token against the Cortex Analyst REST API (POST /api/v2/cortex/analyst/message).
"""
import json
import pathlib
import sys
import urllib.request

import snowflake.connector

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402

QUESTIONS = {
    "SV_WORKFORCE_PERFORMANCE": "What was the bench percentage by level for Financial Services in fiscal year 2026?",
    "SV_PROJECT_DELIVERY": "Which active projects have the lowest CPI?",
    "SV_PIPELINE_PRESALES": "What is the win rate by skill fit band?",
    "SV_AI_ADOPTION": "What was AI assistant spend by AI tool in fiscal year 2026?",
    "SV_PORTFOLIO_360": "What was the margin percentage by MD group in fiscal year 2026?",
    "SV_WORKFORCE_PRODUCTIVITY": "What was the average WPS by person level in fiscal year 2026?",
}


def ask(conn, sv, question):
    host = conn.host
    body = json.dumps({"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
                       "semantic_view": f"ACOCO_L2.SEMANTIC.{sv}"}).encode()
    req = urllib.request.Request(f"https://{host}/api/v2/cortex/analyst/message", data=body, method="POST",
                                 headers={"Authorization": f'Snowflake Token="{conn.rest.token}"',
                                          "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        msg = json.loads(r.read())
    sql = next((c.get("statement") for c in msg["message"]["content"] if c.get("type") == "sql"), None)
    text = " ".join(c.get("text", "") for c in msg["message"]["content"] if c.get("type") == "text")
    return sql, text


def main():
    conn = snowflake.connector.connect(connection_name=sf.CONNECTION)
    conn.cursor().execute("USE WAREHOUSE WH_ACOCO_BUILD")
    out = []
    for sv, question in QUESTIONS.items():
        rec = dict(semantic_view=sv, question=question)
        try:
            sql, text = ask(conn, sv, question)
            rec.update(sql=sql, interpretation=text[:300])
            if sql:
                cur = conn.cursor()
                cur.execute(sql)
                rows = cur.fetchmany(5)
                rec.update(executed=True, rows_returned=cur.rowcount, sample=[list(map(str, r)) for r in rows])
            else:
                rec.update(executed=False, error="no SQL returned")
        except Exception as e:  # report, do not hide
            rec.update(executed=False, error=str(e)[:400])
        out.append(rec)
        print(f"{'PASS' if rec.get('executed') else 'FAIL'}  {sv}: {question}  ->  rows {rec.get('rows_returned')} "
              f"{rec.get('error', '')}")
    (ROOT / "logs" / "analyst_probe.json").write_text(json.dumps(out, indent=1, default=str))
    sys.exit(0 if all(r.get("executed") for r in out) else 1)


if __name__ == "__main__":
    main()
