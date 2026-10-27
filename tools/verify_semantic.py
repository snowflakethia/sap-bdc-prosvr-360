"""Verify every rendered Semantic View YAML with SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(..., TRUE) (no object created).

  .venv/bin/python tools/verify_semantic.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402


def main():
    bad = 0
    for p in sorted((ROOT / "sql" / "03_l2" / "semantic").glob("*.yaml")):
        try:
            sf.query(f"CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML('ACOCO_L2.SEMANTIC', $${p.read_text()}$$, TRUE)")
            print("OK  ", p.name)
        except sf.SqlError as e:
            bad += 1
            print("FAIL", p.name, str(e)[-300:].replace("\n", " "))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
