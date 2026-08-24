# Design: telegram-task-inbox

## Approach

ASAP-бот остаётся единственным процессом, который получает Telegram updates.
Добавляется одна небольшая операция: перед текущей обработкой он сохраняет копию
исходного update в отдельную SQLite-базу Tasks. Самостоятельный task worker читает
только эту базу, распознаёт содержимое и синхронизирует задачи с Notion.

## Product alignment

Это минимальное изменение существующей службы: правила срочности, уведомления,
основная база и Telegram offset не меняются. Если task worker или Notion не
работают, ASAP продолжает работать, а события ждут обработки в отдельной базе.

**Risk tier:** Low

## Architecture

```text
Telegram
   |
ASAP-бот (как сейчас)
   | \
   |  \-- копия raw update --> task_inbox.sqlite
   |                              |
ASAP-уведомления              task worker
                                  |
                                Notion
                                  ^
                                  |
                              Notion MCP
```

## Key decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Telegram polling | Остаётся внутри ASAP | Нет конкуренции за token и миграции работающего polling |
| Передача Tasks | Одна отдельная SQLite-база с raw JSON | Проще очередей и достаточно надёжно для одного Mac |
| Task processing | Отдельный worker/process | Сбой анализа или Notion не блокирует ASAP |
| User-facing store | Notion database | Бесплатный task UI и официальный read/write MCP |
| Headless writes | Notion API integration | Фоновая запись без интерактивного OAuth MCP |
| Media | Worker скачивает по `file_id` из сохранённого raw update | ASAP не занимается распознаванием и вложениями |
| Retry/dedupe | Статус строки и уникальный Telegram update/message ID | Повторный запуск не создаёт дубли |

## Failure modes

| Failure | Mitigation |
|---------|------------|
| Не удалось записать копию update | Записать ошибку; не останавливать ASAP |
| Task worker/Notion недоступны | Оставить строку pending и повторить позже |
| Worker падает на одном файле | Пометить ошибку конкретной строки и продолжить остальные |
| Повторное или изменённое сообщение | Upsert по chat/message ID |
| Неуверенное распознавание | Создать задачу со статусом `Уточнить` и исходником |
| Утечка секретов | Отдельный `.env`, права `0600`, редактирование логов |

## Test strategy

- Проверить, что raw update копируется в отдельную базу и не меняет результат ASAP.
- Проверить, что ошибка task-базы не ломает уведомление ASAP.
- Проверить worker на тексте, голосовом, фото, документе, retry и duplicate.
- Прогнать существующий `test_notifier.py` без изменения ожидаемого поведения.
