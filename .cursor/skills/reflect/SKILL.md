---
name: reflect
description: Post-archive retrospective. Writes short retro snippet to ROADMAP. gstack /retro pattern.
---

# Reflect

Lightweight retro after `/archive`. Optional but recommended.

## Steps

1. Read completed change in `changes/archive/`
2. Ask human (or infer):
   - What went well?
   - What slowed us down?
   - One process tweak for next change?
3. Append to `.planning/ROADMAP.md`:

```markdown
### Retro: <slug> (YYYY-MM-DD)
- **Well:** ...
- **Slow:** ...
- **Try next:** ...
```

4. If pattern repeats 3× → suggest updating `constitution.md` or a rule (human approval required)
