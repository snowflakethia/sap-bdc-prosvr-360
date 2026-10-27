"""Minimal Snowflake helper: runs SQL through the Snowflake CLI (`snow sql`) and returns rows as dicts.

Uses the existing CLI connection (default `sfseapac_kp`, override with env ACOCO_CONNECTION).
No Python connector dependency, so the tools run with the system python3.
"""
import json
import os
import subprocess

CONNECTION = os.environ.get("ACOCO_CONNECTION", "sfseapac_kp")


class SqlError(RuntimeError):
    pass


def query(sql: str) -> list[dict]:
    """Run one statement; return the rows of its result set."""
    proc = subprocess.run(
        ["snow", "sql", "-c", CONNECTION, "--format", "json", "-q", sql],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise SqlError((proc.stdout + proc.stderr).strip()[-2000:])
    out = proc.stdout.strip()
    if not out:
        return []
    data = json.loads(out)
    # Multi-statement input returns a list of result sets; single returns a list of rows.
    if data and isinstance(data[0], list):
        data = data[-1]
    return data


def run_file(path: str) -> None:
    proc = subprocess.run(["snow", "sql", "-c", CONNECTION, "-f", path], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SqlError((proc.stdout + proc.stderr).strip()[-2000:])
