"""Ontology tooling for ACOCO_L2.ONTOLOGY (PRD 5.3).

  .venv/bin/python tools/gen_ontology.py --check-refs   no L2 object definition references L0 (*_V1 CLDs, ACOCO_SIM)
  .venv/bin/python tools/gen_ontology.py --report       entity integrity: key unique / not null, count = distinct L1 keys
  .venv/bin/python tools/gen_ontology.py --registry     (re)build ONT_ENTITY / ONT_RELATIONSHIP / ONT_METRIC from
                                                         DESCRIBE SEMANTIC VIEW + the hand-kept lists below
  .venv/bin/python tools/gen_ontology.py --check        PRD 7.2 rule 5: registry + keys + L0 refs; exit 1 on any error
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


# ---------------------------------------------------------------------------------------------- registry (CP-07)
# The 16 business relationships of PRD 5.3. Implemented in a Semantic View either directly (entity -> entity edge)
# or through a bridge fact that joins to both entities ("via").
BUSINESS_RELATIONSHIPS = [
    ("person", "has", "level", "many_to_one", None, "LEVEL"),
    ("person", "belongs to", "md_group", "many_to_one", None, "MD_GROUP_ID"),
    ("person", "holds", "skill", "many_to_many", "person_skill", "PERSON_ID, SKILL_ID (proficiency)"),
    ("person", "books time to", "time_category", "many_to_many", "time_booking", "PERSON_ID, TIME_CATEGORY"),
    ("person", "books time on", "project", "many_to_many", "project_team", "PERSON_ID, PROJECT_ID"),
    ("person", "pursues", "opportunity", "many_to_many", "pursuit_team", "PERSON_ID, OPPORTUNITY_ID"),
    ("person", "completes", "learning_item", "many_to_many", "learning_episode", "PERSON_ID, LEARNING_ITEM_ID"),
    ("learning_item", "targets", "skill", "many_to_one", None, "TARGET_SKILL_ID"),
    ("person", "uses", "ai_tool", "many_to_many", "ai_usage", "PERSON_ID, AI_TOOL_ID"),
    ("project", "is for", "customer", "many_to_one", None, "CUSTOMER_ID"),
    ("opportunity", "becomes", "project", "one_to_one", "bid", "OPPORTUNITY_ID, PROJECT_ID"),
    ("opportunity", "requires", "skill", "many_to_many", "bid_skill", "OPPORTUNITY_ID, SKILL_ID"),
    ("asset", "harvested from", "source_project", "many_to_one", None, "SOURCE_PROJECT_ID"),
    ("project", "reuses", "asset", "many_to_many", "asset_use", "PROJECT_ID, ASSET_ID"),
    ("asset", "embodies", "skill", "many_to_many", "asset_skill", "ASSET_ID, SKILL_ID"),
    ("work_package", "requires", "skill", "many_to_many", "wp_skill", "WBS_ID, SKILL_ID"),
    ("project", "consumes", "ai_tool", "many_to_many", "agent_on_project", "PROJECT_ID, AI_TOOL_ID (AGT_*)"),
    ("customer", "belongs to", "md_group", "many_to_one", None, "MD_GROUP_ID"),
]
# structural edges the views also use (not business relationships of their own)
STRUCTURAL_EDGES = {("work_package", "project"), ("project", "md_group")}


def describe_svs():
    svs = [r["name"] for r in sf.query("SHOW SEMANTIC VIEWS IN SCHEMA ACOCO_L2.SEMANTIC")]
    out = {}
    for sv in svs:
        rows = sf.query(f"DESCRIBE SEMANTIC VIEW ACOCO_L2.SEMANTIC.{sv}")
        tables, rels, metrics = {}, {}, []
        for r in rows:
            k, n, prop, val = r["object_kind"], r["object_name"], r["property"], r["property_value"]
            if k == "TABLE":
                tables.setdefault(n.lower(), {})[prop] = val
            elif k == "RELATIONSHIP":
                rels.setdefault(n, {})[prop] = val
            elif k == "METRIC":
                metrics.append((r["parent_entity"].lower(), n.lower(), prop, val))
        m = {}
        for t, n, prop, val in metrics:
            m.setdefault((t, n), {})[prop] = val
        out[sv] = dict(tables=tables, edges={(v["TABLE"].lower(), v["REF_TABLE"].lower()) for v in rels.values()}, metrics=m)
    return out


def registry():
    import gen_semantic as gs
    d = describe_svs()
    errors = []
    ent_names = set(gs.ENTITIES) | set(gs.ROLES)

    rel_rows = []
    for frm, verb, to, card, via, keys in BUSINESS_RELATIONSHIPS:
        impl = []
        for sv, x in d.items():
            if via is None and (frm, to) in x["edges"]:
                impl.append(sv)
            elif via and (via, frm) in x["edges"] and (via, to) in x["edges"]:
                impl.append(sv)
        if not impl:
            errors.append(f"relationship '{frm} {verb} {to}' is not implemented by any Semantic View")
        rel_rows.append(dict(FROM_ENTITY=frm, VERB=verb, TO_ENTITY=to, CARDINALITY=card,
                             IMPLEMENTED_BY="direct" if via is None else f"bridge {via}", JOIN_KEYS=keys,
                             SEMANTIC_VIEWS=", ".join(impl)))
    registered = {(f, t) for f, _, t, _, v, _ in BUSINESS_RELATIONSHIPS if v is None} | STRUCTURAL_EDGES
    for sv, x in d.items():
        for a, b in x["edges"]:
            if a in ent_names and b in ent_names and (a, b) not in registered:
                errors.append(f"{sv} joins entities {a} -> {b} with no registered relationship")
        for t, info in x["tables"].items():
            if t in ent_names:
                ent = gs.ROLES.get(t, t)
                want = gs.ENTITIES[ent][0].split(".")
                got = [info.get("BASE_TABLE_SCHEMA_NAME"), info.get("BASE_TABLE_NAME")]
                if got != want:
                    errors.append(f"{sv}.{t} uses {got}, not the shared entity {want}")

    share = {}
    for ent, (tbl, pk, _, owner) in gs.ENTITIES.items():
        r = sf.query(f"SELECT COUNT(*) n, COUNT_IF(SOURCE_SYSTEM = 'BDC_CLD') c FROM ACOCO_L2.{tbl}")[0]
        share[ent] = (r["N"], r["C"])
    defs = {"person": "A person employed by ACoCo at any time FY22-FY26", "md_group": "One of six industry groups led by a Managing Director",
            "level": "Career level with its bill-code band, cost and bill rates and time targets", "fiscal_month": "A V9 fiscal month (Oct-Sep year)",
            "project": "A customer project sold from a won bid", "customer": "A client account of one MD group",
            "work_package": "A WBS work package of a project", "opportunity": "A CRM bid for client work",
            "skill": "A skill in the People Intelligence catalogue (incl. the Agentic-AI family)",
            "learning_item": "A course in the AI or core curriculum", "asset": "A reusable delivery asset harvested from a project",
            "ai_tool": "An AI assistant people use, or an AI agent charged to projects", "time_category": "One of the five uses of time"}
    # entity -> L1 owning object (from its key-count query) and that object's L0 sources (l1_map.yml), for C4 lineage.
    import yaml
    l1map = yaml.safe_load((ROOT / "tools" / "l1_map.yml").read_text())["domains"]
    l0_of = {f"ACOCO_L1.{dom}.{obj}": "; ".join(f"{src['system']}: {src['from'].split()[0].replace(chr(34), '')}" for src in spec["sources"])
             for dom, x in l1map.items() for obj, spec in x["objects"].items()}
    l1_of = {"fiscal_month": "ACOCO_L1.ORGANISATION.FISCAL_PERIOD", "time_category": "ACOCO_L1.TIME.TIMESHEET_RECORD"}
    for t, (_, src) in ENTITIES.items():
        m = re.search(r"FROM (ACOCO_L1\.[A-Z_]+\.[A-Z_]+)", src)
        ent = next((e for e, v in gs.ENTITIES.items() if v[0].endswith("." + t)), None)
        if m and ent:
            l1_of[ent] = m.group(1)
    ent_rows = []
    for ent, (tbl, pk, _, owner) in gs.ENTITIES.items():
        n, c = share[ent]
        ent_rows.append(dict(ENTITY=ent, DEFINITION=defs[ent], OWNING_SYSTEM=owner, L2_TABLE=f"ACOCO_L2.{tbl}", PRIMARY_KEY=pk,
                             ROW_COUNT=n, BDC_CLD_SHARE_PCT=round(100 * c / n, 1) if n else 0.0,
                             SEMANTIC_VIEWS=", ".join(sv for sv, x in d.items() if ent in x["tables"]),
                             L1_SOURCE=l1_of.get(ent), L0_SOURCES=l0_of.get(l1_of.get(ent), "")))

    met_rows = []
    for sv, x in d.items():
        for (t, name), info in x["metrics"].items():
            base = name[6:] if name.startswith("total_") and name[6:] in gs.METRICS else name
            if base not in gs.METRICS:
                errors.append(f"{sv}.{t}.{name} has no registered definition / pillar")
                continue
            expr, desc, _, pillar = gs.METRICS[base]
            met_rows.append(dict(METRIC=name, DEFINITION=desc, PILLAR=pillar, SEMANTIC_VIEW=sv, LOGICAL_TABLE=t,
                                 EXPRESSION=info.get("EXPRESSION", "")))
    return ent_rows, rel_rows, met_rows, errors


def write_registry(ent_rows, rel_rows, met_rows):
    import build_reasoning as br
    for name, rows, comment in [
        ("ONT_ENTITY", ent_rows, "Ontology entities: definition, owning system, L2 table, key, BDC_CLD share, Semantic Views (gen_ontology.py)"),
        ("ONT_RELATIONSHIP", rel_rows, "Ontology relationships (PRD 5.3) and the Semantic Views that implement each (from DESCRIBE SEMANTIC VIEW)"),
        ("ONT_METRIC", met_rows, "Metrics defined once (PRD 2.7) with pillar, Semantic View and expression (from DESCRIBE SEMANTIC VIEW)")]:
        br.write_table(name, rows, comment, schema="ONTOLOGY")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-refs", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--registry", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rc = 0
    if a.registry or a.check:
        ent_rows, rel_rows, met_rows, errors = registry()
        if a.registry:
            write_registry(ent_rows, rel_rows, met_rows)
            print(f"registry: {len(ent_rows)} entities, {len(rel_rows)} relationships, {len(met_rows)} metrics written")
        if a.check:
            bad_keys = [r["object"] for r in report() if not r["ok"]]
            n, refs = check_refs()
            errors += [f"key check failed: {k}" for k in bad_keys] + [f"L0 reference: {x}" for x in refs]
            pillars = {}
            for m in met_rows:
                pillars[m["PILLAR"]] = pillars.get(m["PILLAR"], 0) + 1
            (ROOT / "logs" / "ontology_check.json").write_text(json.dumps(dict(
                entities=len(ent_rows), relationships=len(rel_rows), metrics=len(met_rows), metrics_by_pillar=pillars,
                errors=errors), indent=1))
            print(f"check: {len(ent_rows)} entities, {len(rel_rows)} relationships, {len(met_rows)} metrics {pillars}")
            print(f"check: {len(errors)} errors")
            for e in errors:
                print("  ", e)
            rc |= bool(errors)
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
