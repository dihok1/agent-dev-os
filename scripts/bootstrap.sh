#!/usr/bin/env bash
# bootstrap.sh — Initialize Agent Dev OS in a new or existing repo
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

NAME=""
STAGE="build"
WITH_GSTACK=false

usage() {
  cat <<'EOF'
Usage: ./scripts/bootstrap.sh --name "Project Name" [--stage explore|build|operate] [--with-gstack]

Initializes .planning/ from templates and prepares the repo for Agent Dev OS.

  --name          Project display name (required)
  --stage         Product stage: explore | build | operate (default: build)
  --with-gstack   Print optional gstack extension pack instructions
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; shift 2 ;;
    --stage) STAGE="$2"; shift 2 ;;
    --with-gstack) WITH_GSTACK=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$NAME" ]]; then
  echo "Error: --name is required" >&2
  usage
  exit 1
fi

if [[ ! "$STAGE" =~ ^(explore|build|operate)$ ]]; then
  echo "Error: --stage must be explore, build, or operate" >&2
  exit 1
fi

PLANNING="$ROOT/.planning"
mkdir -p "$PLANNING"

render_template() {
  local src="$1" dst="$2"
  sed -e "s/{{PROJECT_NAME}}/$NAME/g" \
      -e "s/{{PRODUCT_STAGE}}/$STAGE/g" \
      "$src" > "$dst"
}

if [[ -f "$PLANNING/PROJECT.md" ]]; then
  echo "Warning: .planning/PROJECT.md exists — skipping (delete to re-bootstrap)"
else
  render_template "$PLANNING/PROJECT.md.template" "$PLANNING/PROJECT.md"
fi

for f in STATE ROADMAP constitution; do
  if [[ ! -f "$PLANNING/${f}.md" ]]; then
    render_template "$PLANNING/${f}.md.template" "$PLANNING/${f}.md"
  fi
done

mkdir -p "$ROOT/specs" "$ROOT/changes/archive"
chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/hooks/"*.sh 2>/dev/null || true

echo ""
echo "✓ Agent Dev OS initialized"
echo "  Project:  $NAME"
echo "  Stage:    $STAGE"
echo "  Planning: .planning/"
echo ""
echo "Next steps:"
echo "  1. Edit .planning/PROJECT.md and constitution.md"
echo "  2. ./scripts/new-change.sh explore my-first-change   # or build/fix/improve"
echo "  3. In Cursor: /route-intent or /discover-team"
echo ""

if $WITH_GSTACK; then
  cat <<'EOF'
Optional — gstack extension pack:
  git clone --depth 1 https://github.com/garrytan/gstack.git ~/gstack
  cd ~/gstack && ./setup --host cursor
  See docs/gstack-mapping.md for skill mapping.

EOF
fi
