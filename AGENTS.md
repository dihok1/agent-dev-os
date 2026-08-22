# AGENTS.md

Runtime guide for Cursor agents. Skill details: `.cursor/skills/`.

## Quick start

```bash
./scripts/bootstrap.sh --name "My App"
./scripts/new-change.sh build my-feature
```

| Goal | Skill |
|------|-------|
| Unsure where to start | `/route-intent` |
| Research (findings only) | `/explore` → `research.md` |
| Product discovery | `/discover-team` |
| Plan a feature | `/plan-team` or `/plan` |
| Fix a bug | `/investigate` |
| Implement one task | `/execute` (new chat per task) |
| Review before ship | `/verify` (new chat) |
| Ship & archive | `/ship` → `/archive` |

## Loop

```
EXPLORE → PLAN → EXECUTE → VERIFY → SHIP → ARCHIVE
```

## Modes

| Phase | Cursor mode |
|-------|-------------|
| Explore / Plan | Ask or Plan |
| Execute | Agent |
| Investigate | Debug |
| Verify | Ask — **new chat** |

## Memory (read these, not chat history)

- `.planning/PROJECT.md` — durable users, decisions, outcomes, product principles
- `.planning/STATE.md` — active change, decisions
- `.planning/constitution.md` — project rules
- `changes/<slug>/proposal.md` — Product Contract: why, for whom, and measurable outcome
- `changes/<slug>/tasks.md` — what to do next
- `specs/` — living truth (updated on archive)

## Definition of Done

1. Product Contract remains satisfied and outcome evidence/check is recorded
2. All `tasks.md` items checked
3. Tests + lint pass
4. `/verify` product-fit + checker pass (new chat)
5. CI green on PR
6. Human merges → `/archive`

## Boundaries

| Tier | Rule |
|------|------|
| **Always** | Read PROJECT + Product Contract + STATE + constitution; one task per execute session |
| **Ask first** | Schema changes, new dependencies, scope outside active change |
| **Never** | Force-push main, skip CI, change constitution without human |

Planning roles (`pm`, `architect`, …) **never write code**. Only `/execute` implements.

## Optional

- [Cloud task chain](docs/execute-next.md) — webhook automation for hands-off execute
- [gstack extension](docs/gstack-mapping.md) — `./scripts/bootstrap.sh --with-gstack`
- [Methodology deep dive](docs/SYNTHESIS.md)
