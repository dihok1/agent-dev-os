---
name: discover-team
description: EXPLORE phase with role roundtable — pm, ceo (optional), architect lite, facilitator synthesis. Use for new products and big unknowns. intent=explore.
---

# Discover Team

Orchestrate discovery roundtable. **Roles never write code.**

## Sequence

1. Confirm active change exists (`changes/<slug>/`, intent=explore). If not: tell human to run `./scripts/new-change.sh explore <slug>`

2. **PM (office-hours)** — launch `pm` subagent (fresh session, Ask mode)
   - Full Startup or Builder session per `.cursor/agents/pm.md`
   - **One forcing question per turn**; facilitator must not answer for the human
   - Wait until human has answered the active question batch (or explicit escape hatch in pm.md)
   - Output: `roles/pm.md` with sections filled per template

3. **PM gate (mandatory)** — before CEO or architect, verify `roles/pm.md` contains:
   - **Demand evidence** and **Status quo** (non-empty, specific — not placeholders)
   - **Assignment** (one concrete next action)
   - If missing: stop roundtable; resume `pm` subagent only

4. **CEO** (if `roundtable_depth: full` in STATE.md) — launch `ceo` subagent
   - Human picks scope mode
   - Output: `roles/ceo.md`

4b. **CEO gate** — before architect, verify `roles/ceo.md` contains:
   - **Scope mode** (one of four enum values)
   - **Must-haves** (3 items)
   - **Explicitly out** (≥1 item)
   - If missing: stop; resume `ceo` only

5. **Architect (lite)** — launch `architect` subagent
   - Read `roles/pm.md` first; 2–3 options aligned with wedge — no deep implementation
   - Human picks option
   - Output: `roles/architect.md`

5b. **Architect gate** — verify **Selected option** filled (or human recorded choice in session → facilitator writes it)
   - Options must reference PM **Target user and narrowest wedge**

6. **Facilitator** (you) — synthesize:
   - Update `proposal.md` with problem, demand, status quo, wedge from `roles/pm.md`
   - GO / NO-GO recommendation
   - If GO: suggest `./scripts/new-change.sh build <slug>` + `/plan-team`
   - If NO-GO: suggest `/archive` to record decision

## Flags

- `--full`: include CEO step
- `--auto`: skip human gates only if user explicitly requested (default: always gate)

## Human gates (mandatory)

- After each PM question (or batch if human requests escape hatch per pm.md)
- After PM artifact gate (sections above)
- After architect option selected
- Final GO / NO-GO approval
