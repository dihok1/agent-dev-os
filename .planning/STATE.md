# State

product_stage: build
active_change: changes/telegram-task-inbox
last_verified: 2026-08-24

roundtable_depth: standard
has_ui: false
has_devex: false
security_gate: false

## Decisions

<!-- Format: YYYY-MM-DD: decision (rationale) -->
2026-08-24: Keep Telegram polling in ASAP and copy raw updates into a separate Tasks SQLite database read by an independent worker (simplest one-token design with minimal ASAP risk).

## Blockers

- none

## WIP checkpoint

<!-- Optional: context-save between sessions -->
