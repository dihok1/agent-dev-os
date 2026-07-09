<div align="center">

# Agent Dev OS

### Операционная система для AI-разработки в Cursor

**Синтез современных подходов** — GSD, OpenSpec, Spec Kit, BMAD, gstack и Planner–Executor–Evaluator — **нативно в Cursor**, без лишних CLI.

[English README](README.md) · [Полный разбор синтеза](docs/SYNTHESIS.md)

</div>

---

## Объединение всех современных подходов

Ни один фреймворк не закрывает всё. К 2025–2026 команды сошлись на **комбинации паттернов**. Agent Dev OS упаковывает эту комбинацию в один copy-paste шаблон.

| Подход | Что взяли | Что не взяли |
|--------|-----------|--------------|
| **[GSD](https://github.com/gsd-build/get-shit-done)** | Loop, fresh executor на каждый task, `STATE.md` | Vendor lock-in, 50+ команд |
| **[OpenSpec](https://github.com/Fission-AI/OpenSpec)** | Change как единица работы, spec deltas, brownfield | Обязательный CLI |
| **[Spec Kit](https://github.com/github/spec-kit)** | `constitution.md`, human gates | Жёсткие фазы |
| **[BMAD](https://github.com/bmad-code-org/BMAD-METHOD)** | Ролевое планирование (PM, Architect, QA) | Тяжёлая установка |
| **[gstack](https://github.com/garrytan/gstack)** | Office-hours PM, scope modes CEO, iron law debug, checker | Все 23 skills как обязательные |
| **P–E–E** | Planner ≠ Executor ≠ Evaluator — разные сессии | LangGraph runtime |
| **Context engineering** | Память на диске, не в чате | — |

**Один loop, разная глубина:**

```
EXPLORE → PLAN → EXECUTE → VERIFY → SHIP → ARCHIVE → REFLECT
```

| Фаза | Откуда паттерн |
|------|----------------|
| EXPLORE | gstack Think + BMAD discovery |
| PLAN | gstack + BMAD roles + Spec Kit gates |
| EXECUTE | GSD fresh executor |
| VERIFY | P–E–E + gstack Review/QA + CI |
| ARCHIVE | OpenSpec deltas + gstack Retro |

> *Не выбирай религию. Выбери пересечение — и шипай.*

📖 Подробно: [docs/SYNTHESIS.md](docs/SYNTHESIS.md)

---

## Быстрый старт

```bash
git clone https://github.com/dihok1/agent-dev-os.git my-app && cd my-app
./scripts/bootstrap.sh --name "Мой проект" --stage build
./scripts/new-change.sh build auth
# В Cursor: /plan-team → /execute → /verify → /ship
```

Полная документация — в [README.md](README.md).
