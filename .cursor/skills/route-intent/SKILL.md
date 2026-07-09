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
| Unclear what/how, research, build vs buy | `explore` |
| New capability, feature | `build` |
| Broken, bug, crash, error | `fix` |
| Works but refactor, perf, cleanup | `improve` |

3. Recommend roundtable depth:

| Situation | Depth |
|-----------|-------|
| New product, large ambiguity | `full` — discover-team → plan-team |
| Medium feature | `standard` — plan-team |
| Clear small scope | `minimal` — /plan |
| Bug | none — /investigate |

4. Output:

```
Intent: <explore|build|fix|improve>
Suggested: ./scripts/new-change.sh <intent> <slug>
Next skill: /<skill>
Roundtable: <full|standard|minimal|none>
```

5. If `active_change` is set, mention it — may continue existing change instead of new one.
