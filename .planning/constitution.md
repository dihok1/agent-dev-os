# Constitution

Immutable principles for this project. Changes require explicit human approval.

## Core principles

1. **Security first** — no secrets in code; validate all external input.
2. **Tests are spec** — behavior changes need tests; refactors must not change behavior.
3. **Small changes** — one Change = one logical unit; atomic commits per task.
4. **Fresh context** — planner plans, executor executes, checker verifies (never same session).
5. **Human gates** — scope, architecture options, and merge require human approval.

## Non-negotiables

- No force-push to main
- No skipping CI on merge
- No fix without reproduction (fix intent)

## Quality bar

- Lint clean
- Tests pass locally and in CI
- Checker review completed before ship
