---
name: ship
description: SHIP phase — commit hygiene, open PR, security gate if enabled. After verify pass.
---

# Ship

**Same OS loop:** SHIP only after VERIFY; human merges; then `/archive`. This skill adds a pre-PR checklist — it does not replace `/verify` or auto-merge.

## Preconditions (hard)

- `/verify` passed — `roles/checker.md` **Verdict: Pass**
- All `tasks.md` items `[x]` (or human documented deferral in PR)
- `security_gate: true` → `security` subagent done; no Critical/High without **Accept** in `roles/security.md`
- Branch pushed (or push as step 1)

## Pre-PR checklist (ADOS plan completion)

Cross-check **active change** artifacts (not external plan files):

| Check | Source |
|-------|--------|
| Every task in `tasks.md` addressed in branch diff | `tasks.md` + `git diff main...HEAD` |
| Acceptance / EARS criteria covered | `tasks.md` + `roles/qa.md` |
| Scope matches touchpoints | `roles/engineer.md` |
| fix intent: reproduction + root cause documented | `design.md` |
| Spec delta present if behavior changed | `changes/<slug>/specs/` |

If gaps: **do not open PR** — return to `/execute` or `/verify`.

Optional hygiene (project-specific — only if repo already uses these):

- Update CHANGELOG / version file **if** the project convention requires it on ship
- Rebase or merge `main` before PR if team policy says so (human decides)

## Steps

1. Run pre-PR checklist above; note result in PR body under **Plan completion**
2. Create PR:
   - **Change** slug
   - **Summary** — What / Why (`proposal.md`), How (`design.md`)
   - **Test plan** — from `tasks.md` acceptance + CI commands
   - **Verify** — link or note `roles/checker.md` Pass
   - **Security** — "N/A" or summary from `roles/security.md`
3. Wait for CI green + human review
4. **Do NOT merge** unless human explicitly asks
5. After merge → `/archive` → optional `/reflect`

## PR template snippet

```markdown
## Change
<slug>

## Summary
...

## Plan completion
- [ ] All tasks.md items shipped or deferred (named)
- [ ] Acceptance criteria met (qa)
- [ ] Checker verify pass

## Test plan
- [ ] ...
```
