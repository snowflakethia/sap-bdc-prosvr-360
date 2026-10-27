"""Ontology tooling for ACOCO_L2.ONTOLOGY (PRD 5.3).

  .venv/bin/python tools/gen_ontology.py --check-refs   no L2 object definition references L0 (*_V1 CLDs, ACOCO_SIM)
  .venv/bin/python tools/gen_ontology.py --report       entity integrity: key unique / not null, count = distinct L1 keys

The ONT_* registry (generated from the Semantic Views) is added in CP-06.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402

AS_OF = "(SELECT AS_OF_DATE FROM ACOCO_L2.CORE.VW_AS_OF)"
# entity -> (key columns, distinct-key count of the owning L1 source)
ENTITIES = {
    "ENT_PERSON": (["PERSON_ID"], f"SELECT COUNT(DISTINCT PERSON_ID) FROM ACOCO_L1.WORKFORCE.WORKFORCE_JOB WHERE VALID_FROM <= {AS_OF}"),
    "ENT_LEVEL": (["LEVEL"], "SELECT COUNT(DISTINCT LEVEL) FROM ACOCO_L1.ORGANISATION.LEVEL"),
    "ENT_MD_GROUP": (["MD_GROUP_ID"], "SELECT COUNT(DISTINCT MD_GROUP_ID) FROM ACOCO_L1.ORGANISATION.MD_GROUP"),
    "ENT_CUSTOMER": (["CUSTOMER_ID"], "SELECT COUNT(DISTINCT CUSTOMER_ID) FROM ACOCO_L1.SALES.CUSTOMER"),
    "ENT_PROJECT": (["PROJECT_ID"], "SELECT COUNT(DISTINCT PROJECT_ID) FROM ACOCO_L1.PROJECTS.PROJECT"),
    "ENT_WORK_PACKAGE": (["WBS_ID"], "SELECT COUNT(DISTINCT WBS_ID) FROM ACOCO_L1.PROJECTS.WBS_ELEMENT"),
    "ENT_OPPORTUNITY": (["OPPORTUNITY_ID"], "SELECT COUNT(DISTINCT OPPORTUNITY_ID) FROM ACOCO_L1.SALES.OPPORTUNITY"),
    "ENT_SKILL": (["SKILL_ID"], "SELECT COUNT(DISTINCT SKILL_ID) FROM ACOCO_L1.TALENT.SKILL"),
    "ENT_LEARNING_ITEM": (["LEARNING_ITEM_ID"], "SELECT COUNT(DISTINCT LEARNING_ITEM_ID) FROM ACOCO_L1.TALENT.LEARNING_ITEM"),
    "ENT_ASSET": (["ASSET_ID"], "SELECT COUNT(DISTINCT ASSET_ID) FROM ACOCO_L1.ASSETS.ASSET"),
    "ENT_AI_TOOL": (["AI_TOOL_ID"], "SELECT (SELECT COUNT(DISTINCT AI_TOOL_ID) FROM ACOCO_L1.AI_TELEMETRY.AI_USAGE_EVENT)"
                                    " + (SELECT COUNT(*) FROM ACOCO_L1.ORGANISATION.ACTIVITY_TYPE WHERE IS_AI_AGENT)"),
    "ENT_TIME_CATEGORY": (["TIME_CATEGORY"], "SELECT COUNT(DISTINCT TIME_CATEGORY) FROM ACOCO_L2.CORE.DT_TIME_TARGET"),
}
RELATIONSHIPS = {
    "REL_PERSON_SKILL": ["PERSON_ID", "SKILL_ID"], "REL_PERSON_ASSIGNMENT": ["ASSIGNMENT_ID"],
    "REL_PURSUIT_TEAM": ["OPPORTUNITY_ID", "PERSON_ID"], "REL_WP_SKILL": ["WBS_ID", "SKILL_ID"],
    "REL_OPPORTUNITY_SKILL": ["OPPORTUNITY_ID", "SKILL_ID"], "REL_ASSET_SKILL": ["ASSET_ID", "SKILL_ID"],
    "REL_ASSET_USE": ["ASSET_USE_ID"],
}
L0_REF = re.compile(r"\b[A-Z][A-Z0-9_]*_V1\s*\.|\bACOCO_SIM\b", re.I)


def l2_objects():
    """(kind, fqn) for every view / dynamic table / table in ACOCO_L2 (excluding INFORMATION_SCHEMA)."""
    rows = sf.query("""SELECT table_schema s, table_name t, table_type k, is_dynamic d FROM ACOCO_L2.INFORMATION_SCHEMA.TABLES
                       WHERE table_schema <> 'INFORMATION_SCHEMA'""")
    out = []
    for r in rows:
        kind = "VIEW" if r["K"] == "VIEW" else ("DYNAMIC_TABLE" if r["D"] == "YES" else "TABLE")
        out.append((kind, f"ACOCO_L2.{r['S']}.{r['T']}"))
    return out


def check_refs():
    bad = []
    objs = l2_objects()
    for kind, fqn in objs:
        if kind == "TABLE":
            continue
        ddl = sf.query(f"SELECT GET_DDL('{'VIEW' if kind == 'VIEW' else 'TABLE'}', '{fqn}') d")[0]["D"]
        if L0_REF.search(ddl):
            bad.append(fqn)
    return len(objs), bad


def keys_report(table, key):
    k = ", ".join(key)
    nulls = " OR ".join(f"{c} IS NULL" for c in key)
    r = sf.query(f"""SELECT COUNT(*) n,
                            (SELECT COUNT(*) FROM (SELECT {k} FROM ACOCO_L2.ONTOLOGY.{table} GROUP BY {k} HAVING COUNT(*) > 1)) dup,
                            COUNT_IF({nulls}) nul
                     FROM ACOCO_L2.ONTOLOGY.{table}""")[0]
    return r["N"], r["DUP"], r["NUL"]


def report():
    rows = []
    for t, (key, src) in ENTITIES.items():
        n, dup, nul = keys_report(t, key)
        expected = list(sf.query(src)[0].values())[0]
        rows.append(dict(object=t, rows=n, l1_distinct_keys=expected, duplicate_keys=dup, null_keys=nul,
                         ok=(n == expected and dup == 0 and nul == 0 and n > 0)))
    for t, key in RELATIONSHIPS.items():
        n, dup, nul = keys_report(t, key)
        rows.append(dict(object=t, rows=n, l1_distinct_keys=None, duplicate_keys=dup, null_keys=nul,
                         ok=(dup == 0 and nul == 0 and n > 0)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-refs", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    rc = 0
    if a.check_refs:
        n, bad = check_refs()
        print(f"check-refs: {n} L2 objects scanned, {len(bad)} reference L0 {bad}")
        rc |= bool(bad)
    if a.report:
        rows = report()
        (ROOT / "logs" / "ontology_report.json").write_text(json.dumps(rows, indent=1))
        for r in rows:
            print(f"{'PASS' if r['ok'] else 'FAIL'}  {r['object']:<24} rows {r['rows']:>7,}  L1 keys {r['l1_distinct_keys']}  "
                  f"dup {r['duplicate_keys']}  null {r['null_keys']}")
        bad = [r for r in rows if not r["ok"]]
        print(f"ontology: {len(rows) - len(bad)}/{len(rows)} PASS")
        rc |= bool(bad)
    sys.exit(rc)


if __name__ == "__main__":
    main()
