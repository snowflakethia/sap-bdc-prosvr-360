"""Export definitions that a database clone does not carry, or that live outside the cloned databases.

CP-00 measured: clones carry tables, views, dynamic tables (cloned DTs start SUSPENDED) and Semantic Views, but not
Cortex Search services. Agents and the SPCS service are outside the data databases. This script writes, when the
objects exist: Semantic View DDL (GET_DDL), and DESCRIBE output for Cortex Search services, the agent and the service,
to backup/<cp>/. The SQL files in sql/ remain the primary rebuild source; these exports are the as-deployed record.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402


def exists_schema(db: str, schema: str) -> bool:
    try:
        return bool(sf.query(f"show schemas like '{schema}' in database {db}"))
    except sf.SqlError:
        return False


def main():
    cp = sys.argv[1]
    out = ROOT / "backup" / cp
    out.mkdir(parents=True, exist_ok=True)
    written = []

    if exists_schema("ACOCO_L2", "SEMANTIC"):
        for r in sf.query("show semantic views in schema ACOCO_L2.SEMANTIC"):
            ddl = sf.query(f"select get_ddl('semantic_view', 'ACOCO_L2.SEMANTIC.{r['name']}') as d")[0]["D"]
            p = out / f"semantic_view_{r['name']}.sql"
            p.write_text(ddl + ";\n")
            written.append(p.name)

    if exists_schema("ACOCO_L2", "REASONING"):
        for r in sf.query("show cortex search services in schema ACOCO_L2.REASONING"):
            desc = sf.query(f"describe cortex search service ACOCO_L2.REASONING.{r['name']}")
            p = out / f"cortex_search_{r['name']}.json"
            p.write_text(json.dumps(desc, indent=2, default=str))
            written.append(p.name)

    if exists_schema("ACOCO_DB", "AGENT"):
        for r in sf.query("show agents in schema ACOCO_DB.AGENT"):
            desc = sf.query(f"describe agent ACOCO_DB.AGENT.{r['name']}")
            p = out / f"agent_{r['name']}.json"
            p.write_text(json.dumps(desc, indent=2, default=str))
            written.append(p.name)

    if exists_schema("ACOCO_DB", "APP"):
        for r in sf.query("show services in schema ACOCO_DB.APP"):
            desc = sf.query(f"describe service ACOCO_DB.APP.{r['name']}")
            p = out / f"service_{r['name']}.json"
            p.write_text(json.dumps(desc, indent=2, default=str))
            written.append(p.name)

    (out / "export_manifest.json").write_text(json.dumps({"cp": cp, "files": written}, indent=2))
    print(f"exported {len(written)} definitions to backup/{cp}/")


if __name__ == "__main__":
    main()
