# Contributing to Agent Dev OS

Thanks for helping improve the template!

## What we welcome

- Clearer skill prompts (tested in real projects)
- Additional language/stack CI snippets
- Docs and examples
- Bug fixes in scripts

## What we avoid

- Domain-specific trading/finance logic — this stays universal
- Heavy external CLI dependencies (GSD, OpenSpec, BMAD installers)
- Breaking changes to folder layout without discussion

## Development

1. Fork and clone
2. Copy template to a test project: `cp -r . ../my-test && cd ../my-test`
3. `./scripts/bootstrap.sh --name "Test"`
4. Walk through one full loop: explore → build → verify → archive
5. Open PR with description of scenario tested

## Skill authoring

Follow [Cursor Skills docs](https://cursor.com/docs/skills):

- One `SKILL.md` per skill in `.cursor/skills/<name>/`
- YAML frontmatter: `name`, `description`
- Keep skills focused — orchestration in skills, detail in subagents

## Code of conduct

Be constructive. We're building tooling for humans and agents to collaborate better.
