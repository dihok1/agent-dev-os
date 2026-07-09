# gstack Extension Pack Mapping

[garrytan/gstack](https://github.com/garrytan/gstack) is an optional extension — **not required** for Agent Dev OS.

## Install

```bash
git clone --depth 1 https://github.com/garrytan/gstack.git ~/gstack
cd ~/gstack && ./setup --host cursor
```

Or during bootstrap:

```bash
./scripts/bootstrap.sh --name "My App" --with-gstack
```

## Skill mapping

| gstack | Agent Dev OS | Notes |
|--------|--------------|-------|
| `/office-hours` | `/discover-team` (pm role) | Same forcing-questions pattern |
| `/plan-ceo-review` | ceo subagent | Scope modes |
| `/plan-eng-review` | architect subagent | Diagrams, test matrix |
| `/plan-design-review` | designer subagent | UI dimensions |
| `/plan-devex-review` | devex subagent | API/CLI friction |
| `/investigate` | `/investigate` | Iron law: reproduce first |
| `/review` | checker subagent | VERIFY phase |
| `/qa` | qa subagent + `/verify` | Browser if MCP available |
| `/cso` | security subagent | Pre-ship gate |
| `/ship` | `/ship` | PR hygiene |
| `/retro` | `/reflect` | Post-archive retro |
| `/autoplan` | `/plan-team --auto` | Full plan, human approve at end |
| `/careful`, `/freeze`, `/guard` | hooks + AGENTS.md boundaries | Safety |
| `/context-save` | STATE.md WIP checkpoint | Session continuity |

## Recommendation

- **Core**: use Agent Dev OS skills (lean, repo-portable)
- **gstack**: when you want Garry Tan's full 23-skill sprint workflow alongside

Do not mix both on the same step without mapping — pick one orchestrator per phase.
