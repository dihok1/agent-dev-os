---
name: investigate
description: FIX intent debug phase. Iron law — reproduce before fix. Debug mode. Produces root cause + minimal tasks.md.
---

# Investigate

**Iron law:** no `/execute` without reproduction and confirmed root cause (gstack investigate Phases 1–3 before implementation).

## Steps

1. Switch to **Debug Mode**
2. **Phase 1 — Investigate:** symptoms, code trace, `git log` on affected files, **reproduce deterministically**
3. **Phase 2 — Patterns:** match race/nil/config/cache signatures; note recurring area = smell
4. **Phase 3 — Hypothesis:** testable root-cause claim; **3-strike rule** → stop and escalate human
5. Document in `design.md` (required sections):
   - **Steps to reproduce**
   - **Root cause (confirmed)** — testable statement
   - **Minimal fix approach**
6. Update `tasks.md` — 1–3 tasks only; include **regression test** task
7. **Human gate**: confirm root cause
8. Recommend **new Agent chat** → `/execute`

## Investigate gate (blocks `/execute`)

Facilitator/human confirms `design.md` has both:

- **Steps to reproduce** (specific, re-run by executor)
- **Root cause (confirmed)** (not symptom)

`/verify` checker **Fails** if fix ships without these.

## Escalation

- 3 failed hypotheses → stop, escalate to human
- Touching >3 files or architecture → suggest `new-change build` + `/plan-team`

## Rules

- No drive-by refactors
- No fix before Phase 3 confirmed — symptom patches forbidden
- Optional: note debug scope directory in `design.md` (ADOS substitute for gstack `/freeze` during debug)

## Debug report (optional, end of investigate)

```
Symptom / Root cause / Fix approach / Regression test plan / Status
```
