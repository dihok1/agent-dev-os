---
name: plan-team
description: PLAN phase with full role roundtable — pm, ceo, architect, designer, devex, engineer, qa, security, facilitator. Use for build/improve with meaningful scope.
---

# Plan Team

Orchestrate planning roundtable. **No role writes application code.**

## Read first

- `.planning/STATE.md` — `roundtable_depth`, `has_ui`, `has_devex`, `security_gate`
- Active change folder

## Default sequence

| Step | Subagent | Gate |
|------|----------|------|
| 1 | `pm` | Human answers questions |
| 2 | `ceo` | Human picks scope mode (skip if minimal) |
| 3 | `architect` | Human picks option |
| 4 | `designer` | if `has_ui: true` |
| 5 | `devex` | if `has_devex: true` |
| 6 | `engineer` | — |
| 7 | `qa` | — |
| 8 | `security` | if `security_gate: true` (pre-ship note) |

9. **Facilitator** — merge into:
   - `proposal.md` (final)
   - `design.md` (selected approach)
   - `tasks.md` (executable checklist)
   - `specs/` deltas (ADDED/MODIFIED/REMOVED)

10. **Human gate**: approve all artifacts before `/execute`

## Modes

- `--minimal`: architect → engineer → qa only
- `--roles architect,engineer,qa`: custom subset
- `--auto`: run roles back-to-back but still stop at final human approve

## After approve

Tell human: switch to **Agent Mode** → `/execute`
