"""Snapshot data-quality evidence into ACOCO_L2.QUALITY (PRD 7.2) so the app never reads L0 / L1.

  .venv/bin/python tools/snapshot_quality.py

Writes Q_LINEAGE_COUNTS (L0 / L1 / L2 row counts), Q_FRESHNESS (date coverage of key facts by source),
Q_COMPLETENESS (null rate of conformed keys) and Q_ACCESS_SNAPSHOT (no writes to CLDs). Each run appends a snapshot.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402
import gen_l1  # noqa: E402

FRESHNESS = [("TIME.TIMESHEET_RECORD", "WEEK_START"), ("TIME.EMPLOYEE_AVAILABILITY", "WORK_DATE"),
             ("FINANCE.JOURNAL_ENTRY_ITEM", "POSTING_DATE"), ("WORKFORCE.WORKFORCE_JOB", "VALID_FROM"),
             ("SALES.OPPORTUNITY", "CREATED_DATE"), ("AI_TELEMETRY.AI_USAGE_EVENT", "USAGE_DATE"),
             ("TALENT.PERSON_SKILL", "ASSESSED_DATE"), ("TALENT.LEARNING_COMPLETION", "COMPLETION_DATE")]
KEYS = {"PERSON_ID", "COST_CENTER_ID", "PROJECT_ID", "WBS_ID", "OPPORTUNITY_ID", "CUSTOMER_ID", "SKILL_ID",
        "LEARNING_ITEM_ID", "ASSET_ID", "ORDER_ID", "MD_GROUP_ID", "LEVEL"}


def lit(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def insert(table, cols, rows):
    if not rows:
        return
    vals = ",\n".join("(CURRENT_TIMESTAMP(), " + ", ".join(lit(r[c]) for c in cols) + ")" for r in rows)
    sf.query(f"INSERT INTO ACOCO_L2.QUALITY.{table} VALUES {vals}")


def main():
    lineage = []
    # L0: every table the L1 map reads (FROM + JOIN), counted once
    seen = set()
    for _, _, o, _ in gen_l1.objects():
        for s in o["sources"]:
            tbl = s["from"].rsplit(" ", 1)[0]
            if tbl.startswith("ACOCO_DB.") or tbl in seen:
                continue
            seen.add(tbl)
            n = list(sf.query(f"SELECT COUNT(*) n FROM {tbl}")[0].values())[0]
            lineage.append(dict(layer="L0", object_name=tbl, object_kind="CLD" if "_V1." in tbl else "ACOCO_SIM",
                                source_system="BDC_CLD" if "_V1." in tbl else "SIMULATED", row_count=n))
    for d, n, _, _ in gen_l1.objects():
        for r in sf.query(f"SELECT SOURCE_SYSTEM s, COUNT(*) n FROM ACOCO_L1.{d}.{n} GROUP BY 1"):
            lineage.append(dict(layer="L1", object_name=f"ACOCO_L1.{d}.{n}", object_kind="VIEW", source_system=r["S"],
                                row_count=r["N"]))
    for r in sf.query("""SELECT table_schema s, table_name t, IFF(is_dynamic = 'YES', 'DYNAMIC_TABLE', table_type) k, row_count n
                         FROM ACOCO_L2.INFORMATION_SCHEMA.TABLES
                         WHERE table_schema NOT IN ('INFORMATION_SCHEMA', 'QUALITY') AND table_type <> 'VIEW'"""):
        lineage.append(dict(layer="L2", object_name=f"ACOCO_L2.{r['S']}.{r['T']}", object_kind=r["K"], source_system=None,
                            row_count=r["N"]))
    insert("Q_LINEAGE_COUNTS", ["layer", "object_name", "object_kind", "source_system", "row_count"], lineage)

    fresh = []
    for obj, col in FRESHNESS:
        for r in sf.query(f"SELECT SOURCE_SYSTEM s, MIN({col})::DATE a, MAX({col})::DATE b FROM ACOCO_L1.{obj} GROUP BY 1"):
            fresh.append(dict(object_name=f"ACOCO_L1.{obj}", date_column=col, min_date=r["A"], max_date=r["B"], source_system=r["S"]))
    insert("Q_FRESHNESS", ["object_name", "date_column", "min_date", "max_date", "source_system"], fresh)

    comp = []
    for d, n, o, _ in gen_l1.objects():
        keys = [c for c in o["columns"] if c in KEYS]
        if not keys:
            continue
        sel = ", ".join(f"COUNT_IF({c} IS NULL) {c}" for c in keys)
        r = sf.query(f"SELECT COUNT(*) N__, {sel} FROM ACOCO_L1.{d}.{n}")[0]
        for c in keys:
            comp.append(dict(object_name=f"ACOCO_L1.{d}.{n}", column_name=c, row_count=r["N__"], null_count=r[c],
                             null_pct=round(100 * r[c] / r["N__"], 3) if r["N__"] else None))
    insert("Q_COMPLETENESS", ["object_name", "column_name", "row_count", "null_count", "null_pct"], comp)

    gate = json.loads((ROOT / "logs" / "gate_cp02.json").read_text())
    w = next((c for c in gate["checks"] if c["check_id"] == "CP02-08"), None)
    insert("Q_ACCESS_SNAPSHOT", ["check_name", "value"],
           [dict(check_name="writes_by_build_user_to_CLDs_or_connector", value=w["actual"] if w else "not measured")])
    print(f"quality snapshot: lineage {len(lineage)}, freshness {len(fresh)}, completeness {len(comp)}")


if __name__ == "__main__":
    main()
