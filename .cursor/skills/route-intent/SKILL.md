---
name: route-intent
description: Classify user goal into explore|build|fix|improve and suggest next skill + new-change command. Use when unsure where to start.
---

# Route Intent

Classify the user's request and recommend the next step.

## Steps

1. Read `.planning/STATE.md` (product_stage, active_change, flags)
2. Classify intent:

| Signal | Intent |
|--------|--------|
| Unclear what/how, research, build vs buy, compare options | `explore` |
| New capability, feature (ready to design) | `build` |
| Broken, bug, crash, error | `fix` |
| Works but refactor, perf, cleanup | `improve` |

3. Recommend roundtable depth / next skill:

| Situation | Depth | Next skill |
|-----------|-------|------------|
| Quick research / compare (findings only) | none | `/explore` → `research.md` — **no plan** |
| New product, large product ambiguity | `full` | `/discover-team` then later `/plan-team` |
| Medium feature, ready to plan | `standard` | `/plan-team` |
| Clear small scope | `minimal` | `/plan` |
| Bug | none | `/investigate` |

Do not suggest writing `design.md` / `tasks.md` from `/explore`. Planning is always a separate skill.

4. Output:

```
Intent: <explore|build|fix|improve>
Suggested: ./scripts/new-change.sh <intent> <slug>
Next skill: /<skill>
Roundtable: <full|standard|minimal|none>
```

5. If `active_change` is set, mention it — may continue existing change instead of new one.
