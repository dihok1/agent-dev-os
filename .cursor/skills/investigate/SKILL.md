---
name: investigate
description: FIX intent debug phase. Iron law — reproduce before fix. Debug mode. Produces root cause + minimal tasks.md.
---

# Investigate

**Iron law:** no `/execute` without reproduction and confirmed root cause.

## Steps

1. Switch to **Debug Mode**
2. **Reproduce** — runtime evidence required (stack trace, failing test, logs)
3. Document in `design.md`:
   - Steps to reproduce
   - Root cause hypothesis (confirmed)
   - Minimal fix approach
4. Update `tasks.md` — 1–3 tasks only
5. **Human gate**: confirm root cause
6. Recommend **new Agent chat** → `/execute`

## Escalation

- 3 failed fix attempts → stop, escalate to human
- Touching >3 files or architecture → suggest `new-change build` + `/plan-team`

## Rules

- No drive-by refactors
- Add regression test to task list
