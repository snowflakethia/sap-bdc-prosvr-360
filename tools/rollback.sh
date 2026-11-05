#!/usr/bin/env bash
# Roll back to checkpoint <nn>. Run only on the human's instruction.
#
#   tools/rollback.sh <nn> [--yes]
#
# 1. Creates branch rollback-cp<nn> at tag cp-<nn> (main is not rewritten).
# 2. Restores every database listed in backup/cp<nn>/clones.txt from its ACOCO_BKP_CP<nn>_<DB> clone.
# 3. Runs sql/rebuild_from_checkpoint.sql from that tag: resumes cloned dynamic tables (clones start SUSPENDED),
#    re-creates Cortex Search services (not carried by clones), the agent and the service where they existed.
set -euo pipefail
cd "$(dirname "$0")/.."
CONN="${ACOCO_CONNECTION:-<connection>}"
NN="${1:?checkpoint number}"; TAG="cp-${NN}"; CP="cp${NN}"

git rev-parse -q --verify "refs/tags/$TAG" >/dev/null || { echo "no tag $TAG"; exit 2; }
echo "Rollback target: $TAG ($(git rev-list -n1 --abbrev-commit "$TAG"))"
CLONES=$(git show "$TAG:backup/$CP/clones.txt" 2>/dev/null || true)
echo "Databases to restore: ${CLONES:-none}"
if [[ "${2:-}" != "--yes" ]]; then
  read -r -p "Type ROLLBACK to continue: " ok; [[ "$ok" == "ROLLBACK" ]] || { echo "aborted"; exit 1; }
fi

git switch -c "rollback-${CP}-$(date +%Y%m%d-%H%M)" "$TAG"

for bkp in $CLONES; do
  db="${bkp#ACOCO_BKP_CP${NN}_}"
  case "$db" in ACOCO_DB|ACOCO_SIM|ACOCO_L1|ACOCO_L2) ;; *) echo "refusing to restore $db"; exit 2;; esac
  echo "== restore $db from $bkp"
  snow sql -c "$CONN" -q "create or replace database $db clone $bkp" >/dev/null
done

if [[ -s sql/rebuild_from_checkpoint.sql ]]; then
  echo "== rebuild"; snow sql -c "$CONN" -f sql/rebuild_from_checkpoint.sql >/dev/null
fi
echo "== rolled back to $TAG on branch $(git branch --show-current)"
