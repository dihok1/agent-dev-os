---
name: plan
description: Solo PLAN without roundtable. Quick design.md + tasks.md for small clear scope. Use when roundtable_depth is minimal.
---

# Plan (Solo)

For small, well-scoped changes. No subagent roundtable unless user asks.

## Steps

1. Read `.planning/STATE.md`, active change, relevant `specs/`, similar code in repo
2. Use **Plan Mode** (read-only exploration)
3. Write/update:
   - `design.md` — approach, key decisions, test strategy
   - `tasks.md` — 2–7 tasks, one per execute session
   - `specs/` delta if behavior changes
4. Present summary to human → **approve gate**
5. On approve: recommend Agent Mode + `/execute`

## When to escalate

If scope grows (>7 tasks, architecture fork, new domain): stop and suggest `/plan-team`
