#!/usr/bin/env bash
# new-change.sh — Scaffold a new Change work unit
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

INTENT="${1:-}"
SLUG="${2:-}"

usage() {
  cat <<'EOF'
Usage: ./scripts/new-change.sh <intent> <slug>

Intents: explore | build | fix | improve

Examples:
  ./scripts/new-change.sh build add-oauth
  ./scripts/new-change.sh fix session-timeout
  ./scripts/new-change.sh explore websocket-vs-polling
EOF
}

if [[ -z "$INTENT" || -z "$SLUG" ]]; then
  usage
  exit 1
fi

if [[ ! "$INTENT" =~ ^(explore|build|fix|improve)$ ]]; then
  echo "Error: intent must be explore, build, fix, or improve" >&2
  exit 1
fi

if [[ ! "$SLUG" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "Error: slug must be lowercase alphanumeric with hyphens" >&2
  exit 1
fi

DEST="$ROOT/changes/$SLUG"
if [[ -d "$DEST" ]]; then
  echo "Error: changes/$SLUG already exists" >&2
  exit 1
fi

cp -R "$ROOT/changes/_template" "$DEST"

# Substitute placeholders in scaffolded markdown files
substitute_placeholders() {
  local f="$1"
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' \
      -e "s/{{CHANGE_SLUG}}/$SLUG/g" \
      -e "s/{{INTENT}}/$INTENT/g" "$f"
  else
    sed -i \
      -e "s/{{CHANGE_SLUG}}/$SLUG/g" \
      -e "s/{{INTENT}}/$INTENT/g" "$f"
  fi
}

while IFS= read -r -d '' f; do
  substitute_placeholders "$f"
done < <(find "$DEST" -type f -name '*.md' -print0 2>/dev/null || true)

# Fallback if find fails (sandbox / restricted environments)
if ! grep -q "$SLUG" "$DEST/proposal.md" 2>/dev/null; then
  for f in "$DEST"/*.md "$DEST"/roles/*.md; do
    [[ -f "$f" ]] && substitute_placeholders "$f"
  done
fi

# Update STATE.md
STATE="$ROOT/.planning/STATE.md"
if [[ ! -f "$STATE" ]]; then
  echo "Warning: .planning/STATE.md missing — run ./scripts/bootstrap.sh first" >&2
  mkdir -p "$ROOT/.planning"
  cp "$ROOT/.planning/STATE.md.template" "$STATE"
  sed -i.bak "s/{{PRODUCT_STAGE}}/build/g" "$STATE" 2>/dev/null || true
  rm -f "$STATE.bak"
fi

DATE="$(date +%Y-%m-%d)"
if [[ "$(uname)" == "Darwin" ]]; then
  sed -i '' \
    -e "s/^active_change:.*/active_change: changes\/$SLUG/" \
    -e "s/^last_verified:.*/last_verified: $DATE/" \
    "$STATE"
else
  sed -i \
    -e "s/^active_change:.*/active_change: changes\/$SLUG/" \
    -e "s/^last_verified:.*/last_verified: $DATE/" \
    "$STATE"
fi

echo "✓ Created changes/$SLUG (intent: $INTENT)"
echo "  Active change updated in .planning/STATE.md"
echo ""
case "$INTENT" in
  explore) echo "  Suggested: /discover-team or /explore" ;;
  build|improve) echo "  Suggested: /plan-team or /plan" ;;
  fix) echo "  Suggested: /investigate" ;;
esac
