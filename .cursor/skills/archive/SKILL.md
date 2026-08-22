---
name: archive
description: ARCHIVE phase — merge spec deltas to specs/, update ROADMAP, move change to archive, clear active_change.
---

# Archive

Run after PR is merged.

## Steps

1. Merge `changes/<slug>/specs/` deltas into `specs/<domain>/spec.md`
   - Use ADDED / MODIFIED / REMOVED sections
2. Add entry to `.planning/ROADMAP.md` under Completed
3. Record Product Contract outcome status: observed, proxy/manual check pending, or follow-up date + owner; do not claim impact from delivery alone
4. Record key decisions in `.planning/STATE.md` if not already
5. Run `./scripts/archive-change.sh <slug>` or move to `changes/archive/YYYY-MM-DD-<slug>/`
6. Set `active_change: none` in STATE.md
7. Recommend `/reflect` for retro snippet

## Spec delta format

```markdown
## ADDED
### Requirement: ...
...

## MODIFIED
...

## REMOVED
...
```
