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
6. **Stop** — open a **new chat** for the next task, or `/verify` when all tasks are done

## `/execute all`

Run tasks sequentially; **new chat per task**.

## Optional: cloud automation

If execute-next webhook chain is configured (see [docs/execute-next.md](../../docs/execute-next.md)):

- After step 5, run `./scripts/finish-execute-task.sh` instead of stopping
- Never call `trigger-execute-next.sh` before the task PR is merged to `main`

## Boundaries

- Stay within active change scope (freeze rule)
- improve intent: no behavior change
- fix intent: minimal diff only
