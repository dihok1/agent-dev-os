#!/usr/bin/env bash
# load-state.sh — sessionStart hook: inject planning context
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE="$ROOT/.planning/STATE.md"

if [[ ! -f "$STATE" ]]; then
  exit 0
fi

ACTIVE="$(grep '^active_change:' "$STATE" | awk '{print $2}' || echo none)"
STAGE="$(grep '^product_stage:' "$STATE" | awk '{print $2}' || echo unknown)"

cat <<EOF
[Agent Dev OS]
product_stage: $STAGE
active_change: $ACTIVE
→ Read: .planning/STATE.md, .planning/constitution.md
EOF

if [[ -n "$ACTIVE" && "$ACTIVE" != "none" && -f "$ROOT/$ACTIVE/tasks.md" ]]; then
  echo "→ Active tasks: $ACTIVE/tasks.md"
fi
