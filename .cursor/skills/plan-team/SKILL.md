---
name: plan-team
description: PLAN phase with full role roundtable — pm, ceo, architect, designer, devex, engineer, qa, security, facilitator. Use for build/improve with meaningful scope.
---

# Plan Team

Orchestrate planning roundtable. **No role writes application code.**

## Read first

- `.planning/STATE.md` — `roundtable_depth`, `has_ui`, `has_devex`, `security_gate`
- Active change folder, especially `roles/pm.md`

## PM readiness gate

Before **ceo**, **architect**, **engineer**, or **qa**:

- If `roles/pm.md` has substantive **Demand evidence** and **Status quo** → PM step may be **skipped** or run as **delta** (confirm / update only).
- If missing or placeholder → launch `pm` subagent first; **STOP** until PM gate passes (same criteria as `/discover-team`).

Problem understanding is not re-derived from code alone.

## Default sequence

| Step | Subagent | Gate before next step |
|------|----------|------------------------|
| 1 | `pm` | **Demand evidence**, **Status quo**, **Assignment** filled (see `changes/_template/roles/pm.md`) |
| 2 | `ceo` | **Scope mode** + **Must-haves** (3) + ≥1 **Explicitly out** (skip if minimal / `roundtable_depth: minimal`) |
| 3 | `architect` | **Selected option** in `roles/architect.md` + human pick reflected in `design.md` |
| 4 | `designer` | **Interaction state table** for primary flows (if `has_ui: true`) |
| 5 | `devex` | **Friction trace** + persona **TTHW** (if `has_devex: true`) |
| 6 | `engineer` | **Repo touchpoints** in `roles/engineer.md` + ≥1 unchecked task in `tasks.md` |
| 7 | `qa` | ≥3 EARS criteria (build) or ≥1 + **Regression** (fix); each tagged `(wedge)`/`(edge)`/`(regression)` |
| 8 | `security` | No open **Critical/High** without human **Accept** in `roles/security.md` (if `security_gate: true`) |

9. **Facilitator** — merge into:
   - `proposal.md` (final; lead with problem/demand from `roles/pm.md`)
   - `design.md` (selected approach)
   - `tasks.md` (executable checklist + acceptance)
   - `specs/` deltas (ADDED/MODIFIED/REMOVED)

10. **Human gate**: approve all artifacts before `/execute`

## Chain (read order for subagents)

`pm` → `ceo` → `architect` reads pm+ceo → `designer`/`devex` read design+pm → `engineer` reads architect+design+optional designer/devex → `qa` reads pm wedge + architect matrix + tasks → `security` reads design+diff scope note.

## Modes

- `--minimal`: architect → engineer → qa only (**still** enforce PM gate unless `roles/pm.md` ready; skip ceo/designer/devex unless flags)
- `--roles architect,engineer,qa`: custom subset — enforce gates for included roles only
- `--auto`: run roles back-to-back but still stop at final human approve

## After approve

Tell human: switch to **Agent Mode** → `/execute`
