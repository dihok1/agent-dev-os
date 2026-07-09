#!/usr/bin/env bash
# block-dangerous.sh — beforeShellExecution safety gate
# Reads JSON from stdin (Cursor hook protocol). Blocks destructive git ops.
set -euo pipefail

INPUT="$(cat)"
CMD="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null || echo "")"

BLOCK_PATTERNS=(
  'git push.*--force'
  'git push -f'
  'git reset --hard'
  'rm -rf /'
  'DROP DATABASE'
  'DROP TABLE'
)

for pat in "${BLOCK_PATTERNS[@]}"; do
  if echo "$CMD" | grep -qiE "$pat"; then
    echo '{"permission":"deny","userMessage":"Blocked by Agent Dev OS safety hook: destructive command"}' 
    exit 0
  fi
done

echo '{"permission":"allow"}'
