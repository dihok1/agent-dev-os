---
name: explore
description: Solo EXPLORE — research findings only, no plan. Ask/Debug mode. Use for quick technical or market questions; deep product discovery uses /discover-team.
---

# Explore (Solo)

**Research only.** Output is one Markdown findings document. Do **not** write a development plan.

For deep product discovery (office-hours) use `/discover-team`. For design/tasks use `/plan` or `/plan-team` in a **separate** session after the human decides to plan.

## Hard boundaries

| Do | Do not |
|----|--------|
| Clarify the question | Write `design.md`, `tasks.md`, or `specs/` |
| Gather evidence (repo, specs, web) | Lock architecture or stack choices |
| Write **`research.md`** | Populate plan-team `roles/*` (pm, architect, …) |
| Point to a next **skill** (one line) | Draft implementation steps, waves, or acceptance criteria |
| Stop when the findings doc is done | Start `/plan` / `/plan-team` / `/execute` in this session |

## Steps

1. Confirm or create active change (`./scripts/new-change.sh explore <slug>` if needed).
2. Clarify the research question in one sentence (confirm with human if fuzzy).
3. Optionally launch `researcher` subagent (fresh context) — or answer yourself if tiny.
4. Read only what you need: `specs/`, codebase, docs, web.
5. Write **`changes/<active>/research.md`** using `changes/_template/research.md` (all sections; use `_(n/a)_` where irrelevant).
6. Show the human the path to the doc and a **single** suggested next skill — then **STOP**.

## Deliverable

Path: `changes/<active>/research.md`

That file is the whole Explore outcome. Planning is a different command.

## Suggested next skill (pointer only — do not run it)

| If findings say… | Suggest |
|------------------|---------|
| Need product validation | `/discover-team` |
| Ready to design/build | `/plan` or `/plan-team` (new session) |
| Looks like a bug | `/investigate` |
| Dead end | `/archive` |

Do not flesh out proposal/design/tasks here — the next skill owns that.

## Modes

- Prefer **Ask** or **Debug** (read-only posture). Never Agent implement.
- fix-shaped questions: capture symptoms and hypotheses **inside `research.md`**; do not write `design.md`. Hand off to `/investigate` for iron-law debug.
