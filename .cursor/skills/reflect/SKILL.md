---
name: reflect
description: Post-archive retrospective. Writes short retro snippet to ROADMAP. gstack /retro pattern.
---

# Reflect

Lightweight retro after `/archive`. Optional — **does not** change loop or constitution by itself.

## Steps

1. Read archived change: `changes/archive/<slug>/` — `proposal.md`, `tasks.md`, `roles/` (what was planned vs shipped)
2. **Shipped slice** (one paragraph): what actually merged vs original PM wedge / CEO scope
3. Ask human (or infer from artifacts):
   - What went well?
   - What slowed us down? (gates, verify fails, scope drift)
   - One process tweak for next change?
4. **Signals** (optional, from git if easy):
   - Approx commit count on the change branch
   - Any verify/checker re-runs noted in `roles/checker.md` history in archive
5. Append to `.planning/ROADMAP.md`:

```markdown
### Retro: <slug> (YYYY-MM-DD)
- **Shipped:** ...
- **Well:** ...
- **Slow:** ...
- **Try next:** ...
```

6. If the same **Slow** pattern appears 3× in ROADMAP → suggest updating a **rule** or `constitution.md` (human approval required — never auto-edit constitution)

## Not in scope (use gstack `/retro` optionally)

Team-wide analytics, per-author breakdown, cross-project timeline — stay in gstack if installed.
