---
name: plan-team
description: PLAN phase with full role roundtable — pm, ceo, architect, designer, devex, engineer, qa, security, facilitator. Use for build/improve with meaningful scope.
---

# Plan Team

Orchestrate planning roundtable. **No role writes application code.**

## Read first

- `.planning/STATE.md` — `roundtable_depth`, `has_ui`, `has_devex`, `security_gate`
- `.planning/PROJECT.md` — durable users, decisions, outcomes, product principles
- Active change folder, especially `roles/pm.md`

## PM readiness gate

Before **ceo**, **architect**, **engineer**, or **qa**:

- If `roles/pm.md` and the `proposal.md` **Product Contract** are substantive → PM step may be **skipped** or run as **delta** (confirm / update only).
- If missing or placeholder → launch `pm` subagent first; **STOP** until PM gate passes (same criteria as `/discover-team`).

Problem understanding is not re-derived from code alone.

The Product Contract gate requires: specific user/decision maker, job, current workflow, pain/risk, why now, desired behavior, evidence confidence, baseline/target/window (or explicit unavailability), guardrails, and non-goals. Never invent evidence or metrics to pass the gate.

## Default sequence

| Step | Subagent | Gate before next step |
|------|----------|------------------------|
| 1 | `pm` | PM artifact complete + `proposal.md` Product Contract passes specificity gate |
| 2 | `ceo` | **Scope mode** + **Must-haves** (3) + ≥1 **Explicitly out** (skip if minimal / `roundtable_depth: minimal`) |
| 3 | `architect` | Risk tier + **Selected option** + product trade-offs; human pick reflected in `design.md` |
| 3b | `pm` delta / facilitator | **PM alignment check: pass** after selected architecture; revise if product outcome drifted |
| 4 | `designer` | **Interaction state table** for primary flows (if `has_ui: true`) |
| 5 | `devex` | **Friction trace** + persona **TTHW** (if `has_devex: true`) |
| 6 | `engineer` | **Repo touchpoints** + task-to-outcome **Product trace** + ≥1 unchecked task |
| 7 | `qa` | Outcome + behavioral acceptance and ≥3 EARS criteria (build), or ≥1 + **Regression** (fix) |
| 8 | `security` | No open **Critical/High** without human **Accept** in `roles/security.md` (if `security_gate: true`) |

9. **Facilitator** — merge into:
   - `proposal.md` (final Product Contract; concise durable source for every later phase)
   - `design.md` (selected approach)
   - `tasks.md` (executable checklist + acceptance)
   - `specs/` deltas (ADDED/MODIFIED/REMOVED)

10. **Human gate**: approve all artifacts before `/execute`

## Chain (read order for subagents)

`pm` → `ceo` → `architect` reads product contract+pm+ceo → **PM alignment** → `designer`/`devex` read design+pm → `engineer` reads product contract+pm+architect+design+optional designer/devex → `qa` traces all acceptance layers to the contract → `security` reads design+diff scope note.

## Modes

- `--minimal`: architect → engineer → qa only (**still** enforce PM gate unless `roles/pm.md` ready; skip ceo/designer/devex unless flags)
- `--roles architect,engineer,qa`: custom subset — enforce gates for included roles only
- `--auto`: run roles back-to-back but still stop at final human approve

## After approve

Tell human: switch to **Agent Mode** → `/execute`
