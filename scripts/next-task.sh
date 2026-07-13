#!/usr/bin/env bash
# next-task.sh — Next unchecked task; AUTO vs HUMAN_GATE (any stage, any task id)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/next_task.py"
