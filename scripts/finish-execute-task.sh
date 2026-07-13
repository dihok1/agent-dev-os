#!/usr/bin/env bash
# finish-execute-task.sh — merge current task PR to main, then chain next agent.
#
# Prevents the execute-next loop: next webhook must see updated tasks.md on main.
# Usage (from agent branch after commit + push):
#   ./scripts/finish-execute-task.sh [--no-trigger] [--pr-url URL]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DO_TRIGGER=1
PR_URL=""
BASE_BRANCH="main"

for arg in "$@"; do
  case "$arg" in
    --no-trigger) DO_TRIGGER=0 ;;
    --pr-url=*) PR_URL="${arg#--pr-url=}" ;;
    --base=*) BASE_BRANCH="${arg#--base=}" ;;
    -h | --help)
      cat <<'EOF'
Usage: ./scripts/finish-execute-task.sh [--no-trigger] [--pr-url=URL] [--base=main]

1. Ensure current branch is pushed
2. Open or locate PR into base (default: main)
3. Mark ready + squash-merge into base
4. Verify next-task advances on base
5. Unless --no-trigger: call trigger-execute-next.sh
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" == "$BASE_BRANCH" || "$BRANCH" == "HEAD" ]]; then
  echo "Refuse to finish from $BRANCH — work must be on a task branch." >&2
  exit 1
fi

echo "Pushing $BRANCH..."
git push -u origin "$BRANCH"

if [[ -z "$PR_URL" ]]; then
  PR_URL="$(gh pr list --head "$BRANCH" --base "$BASE_BRANCH" --state open --json url --jq '.[0].url' 2>/dev/null || true)"
fi

if [[ -z "$PR_URL" || "$PR_URL" == "null" ]]; then
  SLUG="$(grep '^active_change:' "$ROOT/.planning/STATE.md" 2>/dev/null | awk '{print $2}' | xargs basename 2>/dev/null || echo change)"
  NEXT="$("$ROOT/scripts/next-task.sh" 2>/dev/null || true)"
  # After mark [x], next-task already points at the FOLLOWING task — use git log subject.
  TITLE="$(git log -1 --pretty=%s)"
  BODY="Automated execute-next task PR for \`$SLUG\`. Squash-merge into \`$BASE_BRANCH\` before chaining."
  echo "Creating PR: $TITLE"
  PR_URL="$(gh pr create --base "$BASE_BRANCH" --head "$BRANCH" --title "$TITLE" --body "$BODY")"
fi

echo "PR: $PR_URL"
gh pr ready "$PR_URL" 2>/dev/null || true

echo "Squash-merging into $BASE_BRANCH..."
if ! gh pr merge "$PR_URL" --squash --delete-branch; then
  echo "Merge failed — will not trigger next agent (avoids T* loop)." >&2
  exit 1
fi

echo "Refreshing local $BASE_BRANCH..."
git fetch origin "$BASE_BRANCH"
git checkout "$BASE_BRANCH"
git pull origin "$BASE_BRANCH"

NEXT="$("$ROOT/scripts/next-task.sh" || true)"
echo "$NEXT"
STATUS="$(echo "$NEXT" | awk -F= '/^STATUS=/{print $2}')"

if [[ "$DO_TRIGGER" -eq 0 ]]; then
  echo "Skipping trigger (--no-trigger)."
  exit 0
fi

if [[ "$STATUS" == "DONE" || "$STATUS" == "AWAITING_HUMAN" ]]; then
  echo "Stage complete ($STATUS) — human does final merge/archive. Not chaining."
  exit 0
fi

echo "Chaining next execute-next agent..."
exec "$ROOT/scripts/trigger-execute-next.sh"
