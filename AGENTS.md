# AGENTS.md

Agent Dev OS runtime guide for Cursor agents. Details live in `.cursor/skills/`.

## Quick commands

| Shell | Cursor skill |
|-------|--------------|
| `./scripts/bootstrap.sh --name "App"` | first-time setup |
| `./scripts/new-change.sh build my-feature` | start a Change |
| `./scripts/status.sh` | `/status` |
| `./scripts/archive-change.sh my-feature` | `/archive` (partial) |

## Loop (one process, variable depth)

```
EXPLORE → PLAN → EXECUTE → VERIFY → SHIP → ARCHIVE → REFLECT
```

| Intent | Entry skill |
|--------|-------------|
| explore | `/discover-team` or `/explore` |
| build / improve | `/plan-team` or `/plan` |
| fix | `/investigate` |
| unsure | `/route-intent` |

## Modes

| Phase | Cursor mode |
|-------|-------------|
| Explore / Plan | Ask or Plan |
| Execute | Agent |
| Investigate | Debug |
| Verify (checker) | Ask — **new chat** |

## Tests & lint

<!-- Customize after bootstrap -->

```bash
# npm test
# pytest
# go test ./...
```

## Definition of Done

1. All `tasks.md` items checked
2. Tests + lint pass locally
3. `/verify` + checker pass (new chat)
4. CI green on PR
5. Human merges → `/archive`

## Boundaries

| Tier | Rule |
|------|------|
| **Always** | Read STATE.md + constitution; one task per execute session |
| **Ask first** | Schema changes, new dependencies, files outside change scope |
| **Never** | Force-push main, skip CI, merge PR, change constitution without human |

## Memory

- `.planning/` — vision, state, roadmap, constitution
- `specs/` — living truth (merged on archive)
- `changes/<slug>/` — active work unit

## Role roundtable

Planning roles (`pm`, `ceo`, `architect`, …) **never write code**. Only `/execute` implements.

## Optional

- [gstack extension pack](docs/gstack-mapping.md) — `./scripts/bootstrap.sh --with-gstack`
