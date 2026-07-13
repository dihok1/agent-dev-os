#!/usr/bin/env bash
# sync-execute-next.sh — stage planning + active change for cloud execute-next (GitHub)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GITIGNORE="$ROOT/.gitignore"
STATE="$ROOT/.planning/STATE.md"
MARKER_BEGIN="# execute-next:active-change BEGIN"
MARKER_END="# execute-next:active-change END"

usage() {
  cat <<'EOF'
Usage: ./scripts/sync-execute-next.sh [--commit] [--push]

Updates .gitignore for the current active_change and stages files cloud
automation needs on GitHub:
  .planning/STATE.md
  .planning/constitution.md
  changes/<active-slug>/

Options:
  --commit   Create git commit "chore: sync execute-next state"
  --push     Push to origin after commit (implies --commit)
EOF
}

DO_COMMIT=0
DO_PUSH=0
for arg in "$@"; do
  case "$arg" in
    --commit) DO_COMMIT=1 ;;
    --push) DO_COMMIT=1; DO_PUSH=1 ;;
    -h | --help) usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; usage; exit 1 ;;
  esac
done

if [[ ! -f "$STATE" ]]; then
  echo "Missing $STATE — run ./scripts/bootstrap.sh or ./scripts/new-change.sh first" >&2
  exit 1
fi

ACTIVE="$(grep '^active_change:' "$STATE" | awk '{print $2}' || true)"
if [[ -z "$ACTIVE" || "$ACTIVE" == "none" ]]; then
  echo "No active_change in STATE.md — run ./scripts/new-change.sh first" >&2
  exit 1
fi

SLUG="$(basename "$ACTIVE")"
CHANGE_DIR="$ROOT/changes/$SLUG"
if [[ ! -d "$CHANGE_DIR" ]]; then
  echo "Active change directory missing: changes/$SLUG" >&2
  exit 1
fi

python3 - <<PY
from pathlib import Path

gitignore = Path("$GITIGNORE")
begin = "$MARKER_BEGIN"
end = "$MARKER_END"
slug = "$SLUG"
block = f"""{begin} — updated by scripts/sync-execute-next.sh
!changes/{slug}/
!changes/{slug}/**
{end}"""

text = gitignore.read_text(encoding="utf-8")
if begin in text and end in text:
    pre, rest = text.split(begin, 1)
    _, post = rest.split(end, 1)
    text = pre.rstrip() + "\n\n" + block + post
else:
    anchor = "!changes/.gitkeep"
    if anchor not in text:
        raise SystemExit(f"Missing gitignore anchor: {anchor}")
    text = text.replace(
        anchor,
        anchor + "\n\n" + block,
        1,
    )
gitignore.write_text(text, encoding="utf-8")
print(f"Updated .gitignore for active change: {slug}")
PY

git add "$GITIGNORE"
git add -f "$STATE" "$ROOT/.planning/constitution.md" "$CHANGE_DIR"

echo "Staged execute-next sync:"
echo "  .planning/STATE.md"
echo "  .planning/constitution.md"
echo "  changes/$SLUG/"

if [[ "$DO_COMMIT" -eq 1 ]]; then
  if git diff --cached --quiet; then
    echo "Nothing to commit."
  else
    git commit -m "$(cat <<'EOF'
chore: sync execute-next state for cloud automation

Track active_change planning artifacts on GitHub so webhook-triggered
cloud agents can run next-task.sh and /execute.
EOF
)"
  fi
  if [[ "$DO_PUSH" -eq 1 ]]; then
    git push origin HEAD
    echo "Pushed to origin."
  fi
else
  echo ""
  echo "Next: git commit && git push, or re-run with --commit --push"
fi
