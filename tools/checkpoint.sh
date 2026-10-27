#!/usr/bin/env bash
# Checkpoint backup: gate -> zero-copy clones -> DDL export -> git commit + tag + push.
#
#   tools/checkpoint.sh <nn> "<title>" [DB ...]     e.g. tools/checkpoint.sh 02 "L0 gap-fill" ACOCO_SIM
#   tools/checkpoint.sh --prune [--dry-run]         drop CP clones older than the last three checkpoints
#
# Only databases named exactly ACOCO_DB / ACOCO_SIM / ACOCO_L1 / ACOCO_L2 may be cloned. CLDs (*_V1) and the
# connector are never cloned, altered or dropped (PRD 4.2).
set -euo pipefail
cd "$(dirname "$0")/.."
CONN="${ACOCO_CONNECTION:-sfseapac_kp}"
ALLOWED="ACOCO_DB ACOCO_SIM ACOCO_L1 ACOCO_L2"
sql() { snow sql -c "$CONN" -q "$1" >/dev/null; }

if [[ "${1:-}" == "--prune" ]]; then
  DRY="${2:-}"
  keep=$(git tag -l 'cp-*' | sort | tail -3 | sed 's/cp-/CP/' | tr '\n' '|' | sed 's/|$//')
  dbs=$(snow sql -c "$CONN" --format json -q "show databases like 'ACOCO_BKP_CP%'" | python3 -c 'import json,sys;[print(r["name"]) for r in json.load(sys.stdin)]')
  for db in $dbs; do
    if [[ -n "$keep" && "$db" =~ ACOCO_BKP_($keep)_ ]]; then echo "keep  $db"; continue; fi
    if [[ "$DRY" == "--dry-run" ]]; then echo "would drop $db"; else sql "drop database $db"; echo "dropped $db"; fi
  done
  exit 0
fi

NN="${1:?checkpoint number, e.g. 02}"; TITLE="${2:?title}"; shift 2
CP="cp${NN}"; TAG="cp-${NN}"

echo "== gate $CP"; python3 tools/gate.py "$CP"

mkdir -p "backup/$CP"
: > "backup/$CP/clones.txt"            # re-running a checkpoint starts a fresh list
for db in "$@"; do
  [[ " $ALLOWED " == *" $db "* ]] || { echo "refusing to clone $db (not in: $ALLOWED)"; exit 2; }
  bkp="ACOCO_BKP_CP${NN}_${db}"
  echo "== clone $db -> $bkp"
  sql "create or replace database $bkp clone $db comment = 'checkpoint $TAG backup of $db'"
  echo "$bkp" >> "backup/$CP/clones.txt"
done

# Objects a clone does not carry (Cortex Search, measured in CP-00) or that live outside the cloned databases
# (agent, service) are exported as DDL when they exist.
python3 tools/export_ddl.py "$CP" || { echo "DDL export failed"; exit 3; }

echo "== git"
git add -A
git commit -q -m "CP-${NN}: ${TITLE}

Generated with [Snowflake CoCo](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)

Co-authored-by: Snowflake CoCo <noreply@snowflake.com>" || echo "(nothing new to commit)"
git tag -f "$TAG"
git push -q && git push -q -f origin "$TAG"
echo "== $TAG pushed: $(git rev-parse --short HEAD)"
