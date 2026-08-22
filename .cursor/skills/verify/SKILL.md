---
name: verify
description: VERIFY phase — tests, checker subagent in NEW chat, CI readiness. Evaluator role. Never same session as execute.
---

# Verify

**Maker-checker:** run in a **new chat**, not the execute session.

## Preconditions

- All `tasks.md` items marked `[x]` (or human confirms intentional deferral)
- Product Contract is complete enough to evaluate; unavailable telemetry has an honest proxy/manual check and owner
- For **fix** intent: `design.md` contains **Steps to reproduce** and **Root cause (confirmed)** — else **Fail** before checker

## Steps

1. Run **product-fit pass** against `proposal.md`: target user, desired behavior, outcome evidence/check, approved trade-offs and guardrails
2. Run test suite (project-specific — see AGENTS.md)
3. Run lint if configured
4. Launch `checker` subagent (**new chat**) with:
   - `proposal.md` Product Contract and `roles/pm.md`
   - `git diff` scope vs base branch
   - `tasks.md` acceptance criteria
   - `design.md`, `roles/engineer.md` touchpoints
   - Write **`roles/checker.md`** per `changes/_template/roles/checker.md`
5. **Checker gate** — Pass only if:
   - Product fit verdict passes
   - `roles/checker.md` **Verdict: Pass**
   - Pass 1 checklist categories reviewed (see template)
   - No open **Critical** items
6. Optionally invoke `qa` subagent — map outcome → evidence/check, behavior → scenario, and EARS → tests
7. Report Pass/Fail to human, separating product-fit from technical results

## On pass

- Update `.planning/STATE.md` `last_verified: <date>`
- Recommend `/ship`

## On fail

- List failures → `/execute` for fixes → re-verify (new chat again)

## CI

Remind human: PR must pass `ci.yml` before merge
