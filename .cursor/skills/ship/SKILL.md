---
name: ship
description: SHIP phase — commit hygiene, open PR, security gate if enabled. After verify pass.
---

# Ship

## Preconditions

- `/verify` passed
- All tasks `[x]` in `tasks.md`
- If `security_gate: true` in STATE.md → run `security` subagent first

## Steps

1. Ensure branch is pushed
2. Create PR with summary:
   - What / Why (from `proposal.md`)
   - How (from `design.md`)
   - Test plan (from `tasks.md` acceptance)
3. Link active change slug in PR body
4. Wait for CI green + human review
5. Do NOT merge unless human explicitly asks
6. After merge → recommend `/archive`

## PR template snippet

```markdown
## Change
<slug>

## Summary
...

## Test plan
- [ ] ...
```
