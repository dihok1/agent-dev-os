---
name: verify
description: VERIFY phase — tests, checker subagent in NEW chat, CI readiness. Evaluator role. Never same session as execute.
---

# Verify

**Maker-checker:** run in a **new chat**, not the execute session.

## Preconditions

- All `tasks.md` items marked `[x]` (or human confirms intentional deferral)
- For **fix** intent: `design.md` contains **Steps to reproduce** and **Root cause (confirmed)** — else **Fail** before checker

## Steps

1. Run test suite (project-specific — see AGENTS.md)
2. Run lint if configured
3. Launch `checker` subagent (**new chat**) with:
   - `git diff` scope vs base branch
   - `tasks.md` acceptance criteria
   - `design.md`, `roles/engineer.md` touchpoints
   - Write **`roles/checker.md`** per `changes/_template/roles/checker.md`
4. **Checker gate** — Pass only if:
   - `roles/checker.md` **Verdict: Pass**
   - Pass 1 checklist categories reviewed (see template)
   - No open **Critical** items
5. Optionally invoke `qa` subagent — pick **Verify tier** (Quick/Standard/Exhaustive); map EARS → tests in `roles/qa.md`
6. Report Pass/Fail to human

## On pass

- Update `.planning/STATE.md` `last_verified: <date>`
- Recommend `/ship`

## On fail

- List failures → `/execute` for fixes → re-verify (new chat again)

## CI

Remind human: PR must pass `ci.yml` before merge
