# Publishing to GitHub

Checklist for publishing **Agent Dev OS** as a standalone repo.

## 1. Create repository

- Name suggestions: `agent-dev-os`, `cursor-agent-dev-os`, `agent-dev-template`
- Description (copy-paste):

  > Universal Cursor template: Planner→Executor→Evaluator loop, Change-based work units, Role Roundtable planning. No extra CLI.

- Topics: `cursor`, `ai-agents`, `developer-tools`, `template`, `spec-driven-development`, `ai-coding`, `llm`, `github-actions`

- Enable: Issues, Discussions (optional), Templates

## 2. Social preview

- **Image:** 1280×640 — loop diagram (EXPLORE→PLAN→EXECUTE→VERIFY) + "Agent Dev OS" title
- **Tagline:** *Roles plan. One agent builds. Another verifies.*

## 3. First release

```bash
git init
git add .
git commit -m "feat: initial Agent Dev OS template"
git tag v0.1.0
git push -u origin main --tags
```

Release notes highlight:
- 12 Cursor skills, 10 subagents
- bootstrap in 30 seconds
- MIT license

## 4. Pin for discovery

- Add "Use this template" button (GitHub repo Settings → Template repository)
- Star-worthy README already at `README.md`
- Russian audience: link `README.ru.md`

## 5. Optional launch posts

**Hacker News title:** *Show HN: Agent Dev OS – Cursor-native orchestration without another CLI*

**Reddit:** r/cursor, r/LocalLLaMA — focus on fresh-context executor + checker pattern

**Twitter/X:** *Stop letting one AI chat plan, code, and review itself. Agent Dev OS: Role Roundtable → fresh executor per task → checker in new chat. Copy-paste template for Cursor.*

## 6. Post-launch

- Watch Issues for skill prompt improvements
- Accept PRs that keep template universal (see CONTRIBUTING.md)
