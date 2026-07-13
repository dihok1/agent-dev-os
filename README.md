<div align="center">

# Agent Dev OS

**Copy-paste template for AI-assisted development in Cursor**

Planner → Executor → Evaluator · Change-based work · Role planning · CI verification

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Cursor](https://img.shields.io/badge/Cursor-native-000000?logo=cursor&logoColor=white)](https://cursor.com)

[Русский](README.ru.md) · [How it works](#how-it-works) · [Commands](#commands) · [Docs](docs/SYNTHESIS.md)

</div>

---

## What is this?

A **ready-to-use folder structure** for Cursor: skills, subagents, hooks, and scripts so agents don't mix planning with coding in one chat.

**You get:**
- Persistent memory on disk (`.planning/`, `specs/`, `changes/`)
- 12 Cursor skills (`/plan-team`, `/execute`, `/verify`, …)
- 10 planning roles (PM, Architect, QA, …) that never write code
- One executor per task, one checker in a fresh chat

No extra CLI. Copy into your repo and run bootstrap.

---

## Quick start

```bash
# 1. Copy template into your project
git clone https://github.com/dihok1/agent-dev-os.git my-app
cd my-app

# 2. Initialize (creates .planning/ from templates)
./scripts/bootstrap.sh --name "My App"

# 3. Open in Cursor, create first work unit
./scripts/new-change.sh build user-auth
```

**In Cursor chat:**

```
/route-intent     # not sure where to start
/plan-team        # roles debate → proposal, design, tasks
/execute          # ONE task — then open a NEW chat for the next
/verify           # NEW chat — checker reviews everything
/ship → /archive
```

**Requirements:** [Cursor](https://cursor.com) · bash · git

---

## How it works

### The loop

```
EXPLORE → PLAN → EXECUTE → VERIFY → SHIP → ARCHIVE
```

| You want to… | Start with |
|--------------|------------|
| Research, compare options | `/discover-team` |
| Build a feature | `/plan-team` |
| Fix a bug | `/investigate` (reproduce first) |
| Refactor without behavior change | `/plan-team` (minimal) |

### Golden rule: fresh chat per phase

| Phase | Who | Writes code? |
|-------|-----|--------------|
| Plan | Role roundtable | No |
| Execute | One agent, **one task** | Yes |
| Verify | Checker, **new chat** | No |

Memory lives in files (`STATE.md`, `tasks.md`), not in chat history.

### Folder layout

```
my-app/
├── .planning/       # PROJECT, STATE, roadmap, constitution
├── changes/         # Active work: proposal, design, tasks, roles/
│   └── _template/   # Copied by new-change.sh
├── specs/           # Living specs (merged on archive)
├── .cursor/
│   ├── skills/      # /plan-team, /execute, /verify, …
│   ├── agents/      # pm, architect, checker, …
│   └── rules/       # Planning & implementation guardrails
├── scripts/         # bootstrap, new-change, status, archive
└── AGENTS.md        # Short guide for agents (read this in Cursor)
```

---

## Commands

### Shell

| Command | What it does |
|---------|--------------|
| `./scripts/bootstrap.sh --name "App"` | First-time setup |
| `./scripts/new-change.sh build my-feature` | Start a Change |
| `./scripts/status.sh` | Show active change & progress |
| `./scripts/archive-change.sh my-feature` | Archive after merge |

### Cursor skills

| Skill | When |
|-------|------|
| `/route-intent` | Unsure what to do |
| `/plan-team` | Full planning with roles |
| `/execute` | Implement one task |
| `/verify` | Pre-ship review (new chat) |
| `/ship` | Prepare PR |
| `/archive` | Merge specs, close change |

Full list: `.cursor/skills/`

---

## Optional

| Topic | Doc |
|-------|-----|
| Methodology (GSD, OpenSpec, BMAD, …) | [docs/SYNTHESIS.md](docs/SYNTHESIS.md) |
| Cloud task automation (webhook chain) | [docs/execute-next.md](docs/execute-next.md) |
| gstack extension pack | [docs/gstack-mapping.md](docs/gstack-mapping.md) |

---

## Safety

- Hooks block dangerous git commands (force-push, etc.)
- Checker never runs in the same chat as the executor
- Constitution + human gates before large scope changes

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep the template **universal** — no domain-specific app code.

## License

MIT
