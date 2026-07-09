---
name: explore
description: Solo EXPLORE — quick research without full roundtable. Use for fix lite or fast technical questions. Ask/Debug mode.
---

# Explore (Solo)

Lightweight research. For deep product discovery use `/discover-team`.

## Steps

1. Clarify question in one sentence
2. Optionally launch `researcher` subagent for isolated context
3. Read `specs/`, codebase, docs as needed
4. Write findings to active change `proposal.md` or `design.md`
5. Recommend next step:
   - GO → `/plan` or `/plan-team`
   - NO-GO → `/archive`
   - fix path → `/investigate`

## fix intent (lite)

- Reproduce if possible (Debug mode)
- Document hypothesis in `design.md`
- Do NOT implement — hand off to `/investigate` or `/execute` after human confirms
