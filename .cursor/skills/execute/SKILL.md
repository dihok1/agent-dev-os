---
name: execute
description: EXECUTE phase — implement ONE unchecked task per session in Agent Mode. Fresh context. Atomic commit per task.
---

# Execute

**Executor only.** Fresh session per task. Do not run checker in same chat.

## Before starting

- **Agent Mode** (not Plan/Ask)
- Read: one unchecked task from `tasks.md`, `design.md`, `constitution.md`
- Do NOT load full plan-team history

## Per task

1. Pick first `- [ ]` task (or user-specified task id)
2. Implement minimal change matching repo conventions
3. Run relevant tests
4. Atomic commit: `feat|fix|refactor(scope): <task summary>`
5. Mark task `[x]` in `tasks.md`
6. Stop — suggest new chat for next task or `/verify` when all done

## `/execute all`

Run tasks sequentially; **new chat per task** (tell human to open new chat each time).

## Boundaries

- Stay within active change scope (freeze rule)
- improve intent: no behavior change
- fix intent: minimal diff only
