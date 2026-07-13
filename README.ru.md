<div align="center">

# Agent Dev OS

**Шаблон для AI-разработки в Cursor** — скопируй в свой проект и запусти.

[English README](README.md)

</div>

---

## Быстрый старт

```bash
git clone https://github.com/dihok1/agent-dev-os.git my-app && cd my-app
./scripts/bootstrap.sh --name "Мой проект"
./scripts/new-change.sh build auth
```

**В Cursor:**

```
/plan-team    → роли планируют (proposal, design, tasks)
/execute      → одна задача, потом НОВЫЙ чат
/verify       → проверка в НОВОМ чате
/ship → /archive
```

## Суть

- **Память на диске** — `.planning/`, `changes/`, `specs/` (не в истории чата)
- **Роли планируют, один агент пишет код, другой проверяет**
- **Один task = один чат** в фазе execute

## Документация

| Тема | Файл |
|------|------|
| Полный гайд | [README.md](README.md) |
| Методология | [docs/SYNTHESIS.md](docs/SYNTHESIS.md) |
| Автоматизация задач (опционально) | [docs/execute-next.md](docs/execute-next.md) |

## Лицензия

MIT
