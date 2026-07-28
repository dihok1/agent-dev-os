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
| `/office-hours` | `/discover-team` + `pm` subagent | Adapted Q1–Q6, Startup/Builder, `roles/pm.md`; not full gstack runtime |
| `/plan-ceo-review` | ceo subagent | Four scope modes + must-haves/outs; no 11-section interactive CEO plan file |
| `/plan-eng-review` | architect subagent | Options, 4-path data flow, test matrix, rollback; no 11-pass AskUserQuestion loop |
| `/plan-design-review` | designer subagent | 0–10 passes + interaction state table; no live `/design-review` browser audit |
| `/plan-devex-review` | devex subagent | Personas, TTHW, friction trace, DX modes; no gbrain DX trend / hall-of-fame files |
| `/investigate` | `/investigate` | Iron law + phases 1–3 in skill; no gstack learnings.jsonl / freeze hooks |
| `/review` | checker subagent + `/verify` | Two-pass CRITICAL checklist + `roles/checker.md`; no Review Army specialists / Greptile |
| `/qa` | qa subagent + `/verify` | Plan EARS + verify mapping; gstack `/qa` also fixes bugs in browser loop |
| `/cso` | security subagent | Change-scoped STRIDE/OWASP; not full CSO phases 2–11 infra archaeology |
| `/ship` | `/ship` | PR hygiene + tasks.md completion audit; no VERSION bot |
| `/retro` | `/reflect` | ROADMAP retro + shipped slice; no git analytics |
| `/autoplan` | `/plan-team --auto` | Full plan, human approve at end |
| `/careful`, `/freeze`, `/guard` | hooks + AGENTS.md boundaries | Safety |
| `/context-save` | STATE.md WIP checkpoint | Session continuity |

## Role artifacts (`changes/_template/roles/`)

| Role | Template | When skipped |
|------|----------|--------------|
| pm | yes | Never on build without prior discover |
| ceo | yes | minimal roundtable |
| architect | yes | — |
| engineer | yes | — |
| qa | yes | — |
| designer | yes | `has_ui: false` |
| devex | yes | `has_devex: false` |
| security | yes | `security_gate: false` until ship |
| checker | yes | Written at `/verify` (new chat) |
| research | yes (optional) | Solo `/explore` only; not plan-team chain |

## Recommendation

- **Core**: use Agent Dev OS skills (lean, repo-portable)
- **gstack**: when you want Garry Tan's full 23-skill sprint workflow alongside

Do not mix both on the same step without mapping — pick one orchestrator per phase.
