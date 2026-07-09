---
name: discover-team
description: EXPLORE phase with role roundtable — pm, ceo (optional), architect lite, facilitator synthesis. Use for new products and big unknowns. intent=explore.
---

# Discover Team

Orchestrate discovery roundtable. **Roles never write code.**

## Sequence

1. Confirm active change exists (`changes/<slug>/`, intent=explore). If not: tell human to run `./scripts/new-change.sh explore <slug>`

2. **PM** — launch `pm` subagent (fresh session, Ask mode)
   - Wait for human answers to 6 questions
   - Output: `roles/pm.md`

3. **CEO** (if `roundtable_depth: full` in STATE.md) — launch `ceo` subagent
   - Human picks scope mode
   - Output: `roles/ceo.md`

4. **Architect (lite)** — launch `architect` subagent
   - 2–3 options, no deep implementation
   - Human picks option
   - Output: `roles/architect.md`

5. **Facilitator** (you) — synthesize:
   - Update `proposal.md` with GO / NO-GO recommendation
   - If GO: suggest `./scripts/new-change.sh build <slug>` + `/plan-team`
   - If NO-GO: suggest `/archive` to record decision

## Flags

- `--full`: include CEO step
- `--auto`: skip human gates only if user explicitly requested (default: always gate)

## Human gates (mandatory)

- After PM questions answered
- After architect option selected
- Final GO / NO-GO approval
