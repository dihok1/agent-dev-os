#!/usr/bin/env bash
# archive-change.sh — Move completed change to archive
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SLUG="${1:-}"

usage() {
  echo "Usage: ./scripts/archive-change.sh <slug>"
  echo "  Moves changes/<slug> → changes/archive/YYYY-MM-DD-<slug>"
  echo "  Clears active_change in STATE.md"
  echo "  Merge spec deltas into specs/ manually or via /archive skill"
}

if [[ -z "$SLUG" ]]; then
  usage
  exit 1
fi

SRC="$ROOT/changes/$SLUG"
if [[ ! -d "$SRC" ]]; then
  echo "Error: changes/$SLUG not found" >&2
  exit 1
fi

DATE="$(date +%Y-%m-%d)"
DEST="$ROOT/changes/archive/${DATE}-${SLUG}"
mkdir -p "$ROOT/changes/archive"
mv "$SRC" "$DEST"

STATE="$ROOT/.planning/STATE.md"
if [[ -f "$STATE" ]]; then
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "s/^active_change:.*/active_change: none/" "$STATE"
  else
    sed -i "s/^active_change:.*/active_change: none/" "$STATE"
  fi
fi

echo "✓ Archived to changes/archive/${DATE}-${SLUG}"
echo "  Next: merge changes/.../specs/ deltas into specs/ and update ROADMAP.md"
echo "  Or run /archive in Cursor for guided merge"
