#!/usr/bin/env bash
# status.sh — Show current Agent Dev OS state
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE="$ROOT/.planning/STATE.md"

echo "=== Agent Dev OS Status ==="
echo ""

if [[ ! -f "$STATE" ]]; then
  echo "Not initialized. Run: ./scripts/bootstrap.sh --name \"Your Project\""
  exit 0
fi

grep -E '^(product_stage|active_change|last_verified|roundtable_depth|has_ui|security_gate):' "$STATE" || true
echo ""

ACTIVE="$(grep '^active_change:' "$STATE" | awk '{print $2}')"
if [[ -n "$ACTIVE" && "$ACTIVE" != "none" && -f "$ROOT/$ACTIVE/tasks.md" ]]; then
  echo "Tasks ($(basename "$ACTIVE")):"
  grep -E '^\- \[[ x]\]' "$ROOT/$ACTIVE/tasks.md" || echo "  (no tasks yet)"
  echo ""
  DONE=$(grep -cE '^\- \[x\]' "$ROOT/$ACTIVE/tasks.md" 2>/dev/null || echo 0)
  TOTAL=$(grep -cE '^\- \[[ x]\]' "$ROOT/$ACTIVE/tasks.md" 2>/dev/null || echo 0)
  echo "Progress: $DONE / $TOTAL tasks"
else
  echo "No active change. Run: ./scripts/new-change.sh <intent> <slug>"
fi
