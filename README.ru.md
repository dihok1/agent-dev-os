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
- **Product Contract** — пользователь, задача, ожидаемое поведение и измеримый результат сохраняются от discovery до execute и verify
- **Роли планируют, один агент пишет код, другой проверяет**
- **Один task = один чат** в фазе execute

PM адаптируется к типу работы: Startup, Operator, Decision Support, Platform или Builder. Каждая задача связана с продуктовым результатом либо явно помечена как технический enabler. `/verify` сначала проверяет product fit, затем техническую корректность. Глубина архитектурного разбора зависит от риска: Low, Medium или High.

## Документация

| Тема | Файл |
|------|------|
| Полный гайд | [README.md](README.md) |
| Методология | [docs/SYNTHESIS.md](docs/SYNTHESIS.md) |
| Автоматизация задач (опционально) | [docs/execute-next.md](docs/execute-next.md) |

## Лицензия

MIT
