#!/usr/bin/env bash
# trigger-execute-next.sh — POST webhook to start next execute-next run (new chat)
#
# Call ONLY after the previous task PR is squash-merged into main (see finish-execute-task.sh).
# Never chain on HUMAN_GATE stop (legacy) or AWAITING_HUMAN (final stage merge).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/.cursor/automations/config.json"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing $CONFIG" >&2
  exit 1
fi

{ read -r WEBHOOK_URL; read -r AUTH_ENV_VAR; } < <(python3 - <<PY
import json
c = json.load(open("$CONFIG"))
print(c["webhookUrl"])
print(c.get("webhookAuthEnvVar", "CURSOR_AUTOMATION_TOKEN"))
PY
)
AUTH_ENV_VAR="${AUTH_ENV_VAR:-CURSOR_AUTOMATION_TOKEN}"

TOKEN="${!AUTH_ENV_VAR:-}"
if [[ -z "$TOKEN" ]]; then
  cat >&2 <<EOF
Missing $AUTH_ENV_VAR.

Local trigger: add to .env (Generate auth header on saved webhook automation).
Cloud chain (optional): same value in cursor.com/dashboard/cloud-agents →
Environments → runtime secrets for this repo, then Update Existing Env.

If cloud chain fails, run ./scripts/trigger-execute-next.sh locally after each task.
See docs/execute-next.md
EOF
  exit 1
fi

# Prefer origin/main so we classify the post-merge truth, not a stale task branch.
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$ROOT" fetch origin main >/dev/null 2>&1 || true
fi

SLUG="$(grep '^active_change:' "$ROOT/.planning/STATE.md" 2>/dev/null | awk '{print $2}' | xargs basename 2>/dev/null || echo unknown)"
NEXT="$( "$ROOT/scripts/next-task.sh" 2>/dev/null || true )"
TASK="$(echo "$NEXT" | awk -F= '/^TASK=/{print $2}')"
STATUS="$(echo "$NEXT" | awk -F= '/^STATUS=/{print $2}')"

echo "$NEXT"

case "$STATUS" in
  HUMAN_GATE)
    echo "Blocked: next task is human gate $TASK — complete it manually, mark [x], then re-run this script." >&2
    exit 2
    ;;
  AWAITING_HUMAN|DONE)
    echo "Stage complete ($STATUS). Human does final merge/archive — not chaining." >&2
    exit 0
    ;;
  NO_ACTIVE_CHANGE)
    echo "No active change — not chaining." >&2
    exit 1
    ;;
  AUTO|AUTO_GATE|VERIFY)
    ;;
  *)
    echo "Unknown STATUS=$STATUS — not chaining." >&2
    exit 1
    ;;
esac

PAYLOAD="$(python3 - <<PY
import json, os
print(json.dumps({
    "source": "execute-next",
    "change": os.environ.get("CHANGE", "$SLUG"),
    "next_task": os.environ.get("TASK", "$TASK"),
    "status": os.environ.get("STATUS", "$STATUS"),
}))
PY
)"

echo "Triggering execute-next (change=$SLUG, status=$STATUS, next=${TASK:-auto})..."
HTTP_CODE="$(curl -sS -o /tmp/trigger-execute-next-body.txt -w '%{http_code}' \
  -X POST "$WEBHOOK_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")"

if [[ "$HTTP_CODE" =~ ^2 ]]; then
  echo "OK ($HTTP_CODE) — new agent run should start in a fresh chat."
  cat /tmp/trigger-execute-next-body.txt 2>/dev/null || true
else
  echo "Webhook failed HTTP $HTTP_CODE" >&2
  cat /tmp/trigger-execute-next-body.txt 2>/dev/null >&2 || true
  exit 1
fi
