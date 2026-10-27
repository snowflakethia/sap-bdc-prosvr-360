"""Rebuild ACOCO_L2 from sql/03_l2/*.sql in file order.

Run after any ACOCO_SIM reload (gen/run.py --load replaces tables, which resets change tracking and fails every
dynamic table built on them - D-05-3).

  .venv/bin/python tools/build_l2.py            all files
  .venv/bin/python tools/build_l2.py 10 11      only files whose name starts with these prefixes
"""
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sf  # noqa: E402


def main():
    prefixes = sys.argv[1:]
    files = sorted((ROOT / "sql" / "03_l2").glob("*.sql"))
    if prefixes:
        files = [f for f in files if any(f.name.startswith(p) for p in prefixes)]
    for f in files:
        t = time.time()
        sf.run_file(str(f))
        print(f"built {f.name} ({time.time() - t:.0f}s)")


if __name__ == "__main__":
    main()
