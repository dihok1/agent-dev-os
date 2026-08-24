#!/usr/bin/env python3
"""Independent Telegram task worker.

Reads raw updates from the Tasks inbox SQLite database, extracts structured
tasks from text and supported media, syncs them to a Notion database, and
never sends Telegram messages or marks chats as read.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from notifier import (
    DATA_DIR,
    TASK_INBOX_DB_PATH,
    Config,
    TaskInboxStore,
    display_name,
    load_env,
    message_link,
    message_text,
    urgency,
)


MEDIA_DIR = DATA_DIR / "task_media"
SUPPORTED_MEDIA_FIELDS = ("voice", "photo", "document")
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
NOTION_RICH_TEXT_LIMIT = 1900
PROJECT_HINT = re.compile(
    r"(?:проект(?:у|е|а)?|project)\s*[:\-]?\s*"
    r"([A-Za-zА-Яа-яёЁ0-9_./-]{2,40})",
    re.IGNORECASE,
)
DEADLINE_HINT = re.compile(
    r"(?:до|к|deadline|срок(?:ом)?)\s+([^\n,.]{2,40})",
    re.IGNORECASE,
)


@dataclass
class ExtractedTask:
    title: str
    status: str
    project: str
    priority: str
    deadline: str | None
    author: str
    source_link: str | None
    body: str
    attachments: list[dict[str, Any]]
    update_id: int
    source: str | None
    chat_id: int | None
    message_id: int | None


class TelegramFileClient:
    """Passive file client: getFile + HTTPS download only."""

    ALLOWED_METHODS = {"getFile", "getMe"}

    def __init__(self, token: str) -> None:
        self._token = token
        self._base = f"https://api.telegram.org/bot{token}/"
        self._file_base = f"https://api.telegram.org/file/bot{token}/"

    def call(self, method: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
        if method not in self.ALLOWED_METHODS:
            raise RuntimeError(
                f"Telegram API method is blocked by task-worker policy: {method}"
            )
        body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self._base + method,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (OSError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Telegram API request failed for {method}: {type(exc).__name__}"
            ) from None
        if not result.get("ok"):
            raise RuntimeError(
                f"Telegram API rejected {method}: {result.get('description', 'unknown error')}"
            )
        return result.get("result")

    def download_file(self, file_id: str, dest: Path, timeout: int = 60) -> dict[str, Any]:
        info = self.call("getFile", {"file_id": file_id})
        remote_path = str(info.get("file_path") or "")
        if not remote_path:
            raise RuntimeError("getFile returned empty file_path")
        dest.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(self._file_base + remote_path, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                dest.write_bytes(response.read())
        except (OSError, TimeoutError) as exc:
            raise RuntimeError(
                f"Telegram file download failed: {type(exc).__name__}"
            ) from None
        return {
            "file_id": file_id,
            "file_unique_id": info.get("file_unique_id"),
            "file_path": remote_path,
            "local_path": str(dest),
            "file_size": info.get("file_size"),
        }


def task_source_key(task: ExtractedTask) -> str | None:
    if task.source is None or task.chat_id is None or task.message_id is None:
        return None
    return f"{task.source}:{task.chat_id}:{task.message_id}"


def _rich_text(value: str | None) -> list[dict[str, Any]]:
    text = (value or "")[:NOTION_RICH_TEXT_LIMIT]
    if not text:
        return []
    return [{"type": "text", "text": {"content": text}}]


def format_attachments_for_notion(attachments: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in attachments:
        kind = str(item.get("kind") or "file")
        name = str(item.get("file_name") or item.get("file_id") or kind)
        local = item.get("local_path")
        if local:
            lines.append(f"{kind}: {name} → {local}")
        else:
            lines.append(f"{kind}: {name}")
    return "\n".join(lines)[:NOTION_RICH_TEXT_LIMIT]


class NotionSync(Protocol):
    def upsert_task(self, task: ExtractedTask, page_id: str | None = None) -> str: ...


class NotionTaskClient:
    """Headless Notion API client for create/update of task pages."""

    def __init__(self, token: str, database_id: str) -> None:
        self._token = token.strip()
        self._database_id = database_id.strip()
        if not self._token or not self._database_id:
            raise ValueError("NOTION_TOKEN and NOTION_DATABASE_ID are required")

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode(
            "utf-8"
        )
        request = urllib.request.Request(
            NOTION_API_BASE + path,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(
                f"Notion API {method} {path} failed: HTTP {exc.code}: {detail}"
            ) from None
        except (OSError, TimeoutError) as exc:
            raise RuntimeError(
                f"Notion API {method} {path} failed: {type(exc).__name__}"
            ) from None
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Notion API {method} {path} returned invalid JSON"
            ) from exc

    def properties_for_task(self, task: ExtractedTask) -> dict[str, Any]:
        source_key = task_source_key(task) or f"update:{task.update_id}"
        props: dict[str, Any] = {
            "Name": {"title": _rich_text(task.title) or _rich_text("Без названия")},
            "Status": {"rich_text": _rich_text(task.status)},
            "Project": {"rich_text": _rich_text(task.project)},
            "Priority": {"rich_text": _rich_text(task.priority)},
            "Deadline": {"rich_text": _rich_text(task.deadline)},
            "Author": {"rich_text": _rich_text(task.author)},
            "Source Key": {"rich_text": _rich_text(source_key)},
            "Body": {"rich_text": _rich_text(task.body)},
            "Attachments": {
                "rich_text": _rich_text(format_attachments_for_notion(task.attachments))
            },
        }
        if task.source_link:
            props["Source"] = {"url": task.source_link}
        else:
            props["Source"] = {"url": None}
        return props

    def find_page_id_by_source_key(self, source_key: str) -> str | None:
        result = self._request(
            "POST",
            f"/databases/{self._database_id}/query",
            {
                "page_size": 1,
                "filter": {
                    "property": "Source Key",
                    "rich_text": {"equals": source_key},
                },
            },
        )
        results = result.get("results") or []
        if not results:
            return None
        page_id = results[0].get("id")
        return str(page_id) if page_id else None

    def create_page(self, task: ExtractedTask) -> str:
        result = self._request(
            "POST",
            "/pages",
            {
                "parent": {"database_id": self._database_id},
                "properties": self.properties_for_task(task),
            },
        )
        page_id = result.get("id")
        if not page_id:
            raise RuntimeError("Notion create page returned no id")
        return str(page_id)

    def update_page(self, page_id: str, task: ExtractedTask) -> str:
        self._request(
            "PATCH",
            f"/pages/{page_id}",
            {"properties": self.properties_for_task(task)},
        )
        return page_id

    def upsert_task(self, task: ExtractedTask, page_id: str | None = None) -> str:
        source_key = task_source_key(task)
        if page_id:
            try:
                return self.update_page(page_id, task)
            except RuntimeError as exc:
                # Page may have been deleted or archived in Notion — recreate.
                if "HTTP 404" not in str(exc) and "archived" not in str(exc).lower():
                    raise
        if source_key:
            existing = self.find_page_id_by_source_key(source_key)
            if existing:
                return self.update_page(existing, task)
        return self.create_page(task)

    def archive_page(self, page_id: str) -> None:
        self._request("PATCH", f"/pages/{page_id}", {"archived": True})


class ExtractedTaskStore:
    """Local structured tasks produced by the worker, with Notion page ids."""

    def __init__(self, path: Path = TASK_INBOX_DB_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS extracted_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_id INTEGER NOT NULL,
                source TEXT,
                chat_id INTEGER,
                message_id INTEGER,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                project TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'normal',
                deadline TEXT,
                author TEXT NOT NULL DEFAULT '',
                source_link TEXT,
                body TEXT NOT NULL DEFAULT '',
                attachments_json TEXT NOT NULL DEFAULT '[]',
                notion_page_id TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_extracted_tasks_source_chat_message
                ON extracted_tasks(source, chat_id, message_id)
                WHERE source IS NOT NULL
                  AND chat_id IS NOT NULL
                  AND message_id IS NOT NULL;
            """
        )
        columns = {
            str(row[1])
            for row in self.db.execute("PRAGMA table_info(extracted_tasks)").fetchall()
        }
        if "notion_page_id" not in columns:
            self.db.execute(
                "ALTER TABLE extracted_tasks ADD COLUMN notion_page_id TEXT"
            )
        self.db.commit()

    def upsert_task(self, task: ExtractedTask) -> dict[str, Any]:
        now = int(time.time())
        attachments_json = json.dumps(task.attachments, ensure_ascii=False)
        if task.source is not None and task.chat_id is not None and task.message_id is not None:
            existing = self.db.execute(
                """
                SELECT id, notion_page_id FROM extracted_tasks
                WHERE source=? AND chat_id=? AND message_id=?
                """,
                (task.source, task.chat_id, task.message_id),
            ).fetchone()
            if existing:
                self.db.execute(
                    """
                    UPDATE extracted_tasks SET
                        update_id=?, title=?, status=?, project=?, priority=?,
                        deadline=?, author=?, source_link=?, body=?,
                        attachments_json=?, updated_at=?
                    WHERE id=?
                    """,
                    (
                        task.update_id,
                        task.title,
                        task.status,
                        task.project,
                        task.priority,
                        task.deadline,
                        task.author,
                        task.source_link,
                        task.body,
                        attachments_json,
                        now,
                        int(existing[0]),
                    ),
                )
                self.db.commit()
                return {
                    "id": int(existing[0]),
                    "notion_page_id": existing[1],
                }

        cursor = self.db.execute(
            """
            INSERT INTO extracted_tasks(
                update_id, source, chat_id, message_id, title, status, project,
                priority, deadline, author, source_link, body, attachments_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.update_id,
                task.source,
                task.chat_id,
                task.message_id,
                task.title,
                task.status,
                task.project,
                task.priority,
                task.deadline,
                task.author,
                task.source_link,
                task.body,
                attachments_json,
                now,
                now,
            ),
        )
        self.db.commit()
        return {"id": int(cursor.lastrowid), "notion_page_id": None}

    def set_notion_page_id(
        self, source: str, chat_id: int, message_id: int, page_id: str
    ) -> None:
        self.db.execute(
            """
            UPDATE extracted_tasks
            SET notion_page_id=?, updated_at=?
            WHERE source=? AND chat_id=? AND message_id=?
            """,
            (page_id, int(time.time()), source, chat_id, message_id),
        )
        self.db.commit()

    def get_by_message(
        self, source: str, chat_id: int, message_id: int
    ) -> dict[str, Any] | None:
        row = self.db.execute(
            """
            SELECT update_id, title, status, project, priority, deadline, author,
                   source_link, body, attachments_json, notion_page_id
            FROM extracted_tasks
            WHERE source=? AND chat_id=? AND message_id=?
            """,
            (source, chat_id, message_id),
        ).fetchone()
        if not row:
            return None
        return {
            "update_id": row[0],
            "title": row[1],
            "status": row[2],
            "project": row[3],
            "priority": row[4],
            "deadline": row[5],
            "author": row[6],
            "source_link": row[7],
            "body": row[8],
            "attachments": json.loads(row[9] or "[]"),
            "notion_page_id": row[10],
        }

    def count_tasks(self) -> int:
        return int(self.db.execute("SELECT COUNT(*) FROM extracted_tasks").fetchone()[0])


def primary_message(update: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    for source in (
        "business_message",
        "edited_business_message",
        "message",
        "edited_message",
    ):
        payload = update.get(source)
        if isinstance(payload, dict):
            canonical = {
                "edited_business_message": "business_message",
                "edited_message": "message",
            }.get(source, source)
            return canonical, payload
    return None, None


def infer_priority(text: str) -> str:
    score, _ = urgency(text)
    if score >= 3:
        return "high"
    if score >= 2:
        return "medium"
    return "normal"


def infer_project(text: str) -> str:
    match = PROJECT_HINT.search(text)
    return match.group(1).strip() if match else ""


def infer_deadline(text: str) -> str | None:
    match = DEADLINE_HINT.search(text)
    if not match:
        return None
    return match.group(1).strip()[:80] or None


def build_title(text: str, media_kind: str | None) -> tuple[str, str]:
    cleaned = " ".join(text.split())
    if cleaned and not cleaned.startswith("["):
        title = cleaned[:120]
        status = "Новая"
        return title, status
    labels = {
        "voice": "Голосовое сообщение",
        "photo": "Фото",
        "document": "Документ",
    }
    if media_kind:
        return labels.get(media_kind, "Медиа сообщение"), "Уточнить"
    return "Сообщение без текста", "Уточнить"


def media_file_id(message: dict[str, Any], field: str) -> str | None:
    payload = message.get(field)
    if field == "photo" and isinstance(payload, list) and payload:
        largest = max(payload, key=lambda item: int(item.get("file_size") or 0))
        return str(largest.get("file_id") or "") or None
    if isinstance(payload, dict):
        return str(payload.get("file_id") or "") or None
    return None


def detect_media_kind(message: dict[str, Any]) -> str | None:
    for field in SUPPORTED_MEDIA_FIELDS:
        if message.get(field):
            return field
    return None


class TaskWorker:
    def __init__(
        self,
        inbox: TaskInboxStore,
        tasks: ExtractedTaskStore,
        files: TelegramFileClient | None = None,
        notion: NotionSync | None = None,
        media_dir: Path = MEDIA_DIR,
    ) -> None:
        self.inbox = inbox
        self.tasks = tasks
        self.files = files
        self.notion = notion
        self.media_dir = media_dir

    def collect_attachments(self, message: dict[str, Any], update_id: int) -> list[dict[str, Any]]:
        attachments: list[dict[str, Any]] = []
        for field in SUPPORTED_MEDIA_FIELDS:
            file_id = media_file_id(message, field)
            if not file_id:
                continue
            meta: dict[str, Any] = {
                "kind": field,
                "file_id": file_id,
            }
            if field == "document" and isinstance(message.get("document"), dict):
                doc = message["document"]
                meta["file_name"] = doc.get("file_name")
                meta["mime_type"] = doc.get("mime_type")
            if self.files is not None:
                suffix = Path(str(meta.get("file_name") or file_id)).suffix or {
                    "voice": ".ogg",
                    "photo": ".jpg",
                    "document": "",
                }.get(field, "")
                dest = self.media_dir / f"{update_id}_{field}{suffix}"
                downloaded = self.files.download_file(file_id, dest)
                meta.update(downloaded)
            attachments.append(meta)
        return attachments

    def extract_task(self, update: dict[str, Any]) -> ExtractedTask | None:
        source, message = primary_message(update)
        if message is None:
            return None
        update_id = int(update["update_id"])
        chat = message.get("chat") or {}
        chat_id = int(chat["id"]) if chat.get("id") is not None else None
        message_id = int(message["message_id"]) if message.get("message_id") is not None else None
        text = message_text(message)
        media_kind = detect_media_kind(message)
        title, status = build_title(text, media_kind)
        raw_text = (message.get("text") or message.get("caption") or "").strip()
        author = display_name(message.get("from") or {})
        attachments = self.collect_attachments(message, update_id)
        return ExtractedTask(
            title=title,
            status=status,
            project=infer_project(raw_text),
            priority=infer_priority(raw_text or text),
            deadline=infer_deadline(raw_text),
            author=author,
            source_link=message_link(message),
            body=raw_text or text,
            attachments=attachments,
            update_id=update_id,
            source=source,
            chat_id=chat_id,
            message_id=message_id,
        )

    def sync_to_notion(self, task: ExtractedTask, page_id: str | None) -> str | None:
        if self.notion is None:
            return None
        new_page_id = self.notion.upsert_task(task, page_id=page_id)
        if (
            task.source is not None
            and task.chat_id is not None
            and task.message_id is not None
        ):
            self.tasks.set_notion_page_id(
                task.source, task.chat_id, task.message_id, new_page_id
            )
        return new_page_id

    def process_row(self, row: dict[str, Any]) -> None:
        update_id = int(row["update_id"])
        try:
            update = json.loads(row["raw_json"])
            task = self.extract_task(update)
            if task is not None:
                stored = self.tasks.upsert_task(task)
                self.sync_to_notion(task, stored.get("notion_page_id"))
            self.inbox.mark_processed(update_id)
        except Exception as exc:
            self.inbox.mark_error(update_id, str(exc))
            raise

    def process_once(self, limit: int = 20) -> int:
        rows = self.inbox.claim_pending(limit=limit)
        processed = 0
        for row in rows:
            try:
                self.process_row(row)
                processed += 1
            except Exception as exc:
                print(
                    f"task worker error update_id={row['update_id']}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
        return processed

    def run(self, once: bool = False, poll_interval: float = 2.0) -> None:
        while True:
            self.process_once()
            if once:
                return
            time.sleep(poll_interval)


def notion_client_from_env() -> NotionTaskClient:
    token = os.getenv("NOTION_TOKEN", "").strip()
    database_id = os.getenv("NOTION_DATABASE_ID", "").strip()
    if not token or not database_id:
        raise SystemExit(
            "NOTION_TOKEN and NOTION_DATABASE_ID are required in .env for Notion sync"
        )
    return NotionTaskClient(token, database_id)


def build_worker_from_env(
    inbox_path: Path = TASK_INBOX_DB_PATH,
    media_dir: Path = MEDIA_DIR,
    with_files: bool = True,
    with_notion: bool = True,
) -> TaskWorker:
    load_env(Path(__file__).resolve().parent / ".env")
    inbox = TaskInboxStore(inbox_path)
    tasks = ExtractedTaskStore(inbox_path)
    files = None
    if with_files:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise SystemExit("TELEGRAM_BOT_TOKEN is missing in .env")
        files = TelegramFileClient(token)
    notion = notion_client_from_env() if with_notion else None
    return TaskWorker(
        inbox, tasks, files=files, notion=notion, media_dir=media_dir
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram task inbox worker")
    parser.add_argument("--once", action="store_true", help="Process pending rows once and exit")
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Seconds between polls when running continuously",
    )
    args = parser.parse_args()
    # Config.from_env validates token the same way ASAP does when files are needed.
    Config.from_env()
    worker = build_worker_from_env()
    worker.run(once=args.once, poll_interval=args.interval)


if __name__ == "__main__":
    main()