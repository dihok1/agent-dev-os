---
name: status
description: Show Agent Dev OS state — active change, phase hint, task progress. Reads STATE.md and tasks.md.
---

# Status

1. Run `./scripts/status.sh` or read `.planning/STATE.md`
2. Report:
   - product_stage, active_change, flags
   - Task progress (checked / total)
3. Suggest next skill by phase:

| Condition | Next |
|-----------|------|
| No active change | `/route-intent` + `new-change.sh` |
| explore, no `research.md` yet | `/explore` (findings only) |
| explore, research done / product ambiguity | `/discover-team` or `/plan-team` (separate) |
| plan artifacts incomplete | `/plan-team` or `/plan` |
| unchecked tasks | `/execute` (Agent Mode, new chat) |
| all tasks done | `/verify` (new chat) |
| verify passed | `/ship` |
| PR merged | `/archive` |
