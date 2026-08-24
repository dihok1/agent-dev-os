#!/usr/bin/env python3
"""Independent Telegram task worker.

Reads raw updates from the Tasks inbox SQLite database, extracts structured
tasks from text and supported media, and never sends Telegram messages or
marks chats as read. Notion sync is out of scope for this module (T3).
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
from typing import Any

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


class ExtractedTaskStore:
    """Local structured tasks produced by the worker (Notion sync is T3)."""

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
        self.db.commit()

    def upsert_task(self, task: ExtractedTask) -> None:
        now = int(time.time())
        attachments_json = json.dumps(task.attachments, ensure_ascii=False)
        if task.source is not None and task.chat_id is not None and task.message_id is not None:
            existing = self.db.execute(
                """
                SELECT id FROM extracted_tasks
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
                return

        self.db.execute(
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

    def get_by_message(
        self, source: str, chat_id: int, message_id: int
    ) -> dict[str, Any] | None:
        row = self.db.execute(
            """
            SELECT update_id, title, status, project, priority, deadline, author,
                   source_link, body, attachments_json
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
        media_dir: Path = MEDIA_DIR,
    ) -> None:
        self.inbox = inbox
        self.tasks = tasks
        self.files = files
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

    def process_row(self, row: dict[str, Any]) -> None:
        update_id = int(row["update_id"])
        try:
            update = json.loads(row["raw_json"])
            task = self.extract_task(update)
            if task is not None:
                self.tasks.upsert_task(task)
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


def build_worker_from_env(
    inbox_path: Path = TASK_INBOX_DB_PATH,
    media_dir: Path = MEDIA_DIR,
    with_files: bool = True,
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
    return TaskWorker(inbox, tasks, files=files, media_dir=media_dir)


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
