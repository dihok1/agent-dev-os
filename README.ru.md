<div align="center">

# Agent Dev OS

### Операционная система для AI-разработки в Cursor

[English README](README.md)

</div>

Универсальный шаблон: **Planner → Executor → Evaluator**, единица работы **Change**, **Role Roundtable** на этапе планирования.

```bash
cp -r agent-dev-template/ my-app && cd my-app
./scripts/bootstrap.sh --name "Мой проект" --stage build
./scripts/new-change.sh build auth
# В Cursor: /plan-team → /execute → /verify → /ship
```

Подробности — в [README.md](README.md).
