#!/usr/bin/env bash
# run-tests.sh — stop hook: run test suite if configured
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Customize: uncomment your test runner
# npm test --if-present 2>/dev/null && exit 0
# pytest -q 2>/dev/null && exit 0
# go test ./... 2>/dev/null && exit 0

exit 0
