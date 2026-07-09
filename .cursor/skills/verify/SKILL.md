---
name: verify
description: VERIFY phase — tests, checker subagent in NEW chat, CI readiness. Evaluator role. Never same session as execute.
---

# Verify

**Maker-checker:** run in a **new chat**, not the execute session.

## Steps

1. Run test suite (project-specific — see AGENTS.md)
2. Run lint if configured
3. Launch `checker` subagent with:
   - `git diff` scope
   - `tasks.md` acceptance criteria
   - `design.md`
4. Optionally invoke `qa` subagent for acceptance mapping
5. Report Pass/Fail

## On pass

- Update `.planning/STATE.md` `last_verified: <date>`
- Recommend `/ship`

## On fail

- List failures → `/execute` for fixes → re-verify

## CI

Remind human: PR must pass `ci.yml` before merge
