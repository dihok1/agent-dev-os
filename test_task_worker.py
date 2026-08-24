#!/usr/bin/env python3
"""Tests for the independent Telegram task worker."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from notifier import TaskInboxStore, load_env
from task_worker import (
    ExtractedTask,
    ExtractedTaskStore,
    NotionTaskClient,
    TaskWorker,
    TelegramFileClient,
    format_attachments_for_notion,
    task_source_key,
)


class FakeFileClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict | None]] = []
        self.downloads: list[str] = []

    def call(self, method, payload=None, timeout=30):
        self.calls.append((method, payload))
        if method == "getFile":
            file_id = (payload or {}).get("file_id", "x")
            return {
                "file_id": file_id,
                "file_unique_id": f"u-{file_id}",
                "file_path": f"voice/{file_id}.ogg",
                "file_size": 12,
            }
        raise RuntimeError(f"unexpected method {method}")

    def download_file(self, file_id: str, dest: Path, timeout: int = 60) -> dict:
        self.downloads.append(file_id)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"media-bytes")
        return {
            "file_id": file_id,
            "file_unique_id": f"u-{file_id}",
            "file_path": f"files/{file_id}",
            "local_path": str(dest),
            "file_size": 11,
        }


class BrokenFileClient(FakeFileClient):
    def download_file(self, file_id: str, dest: Path, timeout: int = 60) -> dict:
        raise RuntimeError("download failed")


class FakeNotionClient:
    def __init__(self) -> None:
        self.pages: dict[str, ExtractedTask] = {}
        self.by_source_key: dict[str, str] = {}
        self.calls: list[tuple[str, str | None]] = []
        self._seq = 0
        self.fail_next = False

    def upsert_task(self, task: ExtractedTask, page_id: str | None = None) -> str:
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("Notion unavailable")
        key = task_source_key(task) or f"update:{task.update_id}"
        if page_id and page_id in self.pages:
            self.pages[page_id] = task
            self.by_source_key[key] = page_id
            self.calls.append(("update", page_id))
            return page_id
        existing = self.by_source_key.get(key)
        if existing:
            self.pages[existing] = task
            self.calls.append(("update", existing))
            return existing
        self._seq += 1
        new_id = f"page-{self._seq}"
        self.pages[new_id] = task
        self.by_source_key[key] = new_id
        self.calls.append(("create", new_id))
        return new_id


def base_message(**overrides):
    message = {
        "message_id": 10,
        "date": 1_800_000_000,
        "chat": {"id": 123, "type": "private", "username": "alex"},
        "from": {"id": 123, "first_name": "Alex", "username": "alex"},
    }
    message.update(overrides)
    return message


def sample_task(**overrides) -> ExtractedTask:
    task = ExtractedTask(
        title="Срочно проверь отчёт по проекту Alpha до пятницы",
        status="Новая",
        project="Alpha",
        priority="high",
        deadline="пятницы",
        author="Alex",
        source_link="https://t.me/alex",
        body="Срочно проверь отчёт по проекту Alpha до пятницы",
        attachments=[
            {"kind": "document", "file_id": "doc-1", "file_name": "brief.pdf"}
        ],
        update_id=1,
        source="business_message",
        chat_id=123,
        message_id=10,
    )
    for key, value in overrides.items():
        setattr(task, key, value)
    return task


class TaskWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.inbox = TaskInboxStore(root / "task_inbox.sqlite3")
        self.tasks = ExtractedTaskStore(root / "task_inbox.sqlite3")
        self.media_dir = root / "media"
        self.files = FakeFileClient()
        self.notion = FakeNotionClient()
        self.worker = TaskWorker(
            self.inbox,
            self.tasks,
            files=self.files,
            notion=self.notion,
            media_dir=self.media_dir,
        )

    def tearDown(self):
        self.inbox.db.close()
        self.tasks.db.close()
        self.tempdir.cleanup()

    def _enqueue(self, update_id: int, message: dict, source: str = "business_message"):
        update = {"update_id": update_id, source: message}
        self.inbox.save_raw_update(update)
        return update

    def test_text_message_creates_structured_task(self):
        self._enqueue(
            1,
            base_message(text="Срочно проверь отчёт по проекту Alpha до пятницы"),
        )
        self.assertEqual(self.worker.process_once(), 1)
        task = self.tasks.get_by_message("business_message", 123, 10)
        self.assertIsNotNone(task)
        assert task is not None
        self.assertEqual(
            task["title"], "Срочно проверь отчёт по проекту Alpha до пятницы"
        )
        self.assertEqual(task["status"], "Новая")
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["project"], "Alpha")
        self.assertEqual(task["deadline"], "пятницы")
        self.assertEqual(task["author"], "Alex")
        self.assertEqual(task["source_link"], "https://t.me/alex")
        self.assertEqual(task["notion_page_id"], "page-1")
        status = self.inbox.db.execute(
            "SELECT status FROM updates WHERE update_id=1"
        ).fetchone()[0]
        self.assertEqual(status, "processed")

    def test_voice_message_downloads_and_marks_clarify(self):
        self._enqueue(2, base_message(voice={"file_id": "voice-1", "duration": 3}))
        self.assertEqual(self.worker.process_once(), 1)
        task = self.tasks.get_by_message("business_message", 123, 10)
        self.assertIsNotNone(task)
        assert task is not None
        self.assertEqual(task["title"], "Голосовое сообщение")
        self.assertEqual(task["status"], "Уточнить")
        self.assertEqual(len(task["attachments"]), 1)
        self.assertEqual(task["attachments"][0]["kind"], "voice")
        self.assertEqual(task["attachments"][0]["file_id"], "voice-1")
        self.assertTrue(Path(task["attachments"][0]["local_path"]).exists())
        self.assertEqual(self.files.downloads, ["voice-1"])

    def test_photo_with_caption_keeps_text_and_attachment(self):
        self._enqueue(
            3,
            base_message(
                caption="Добавь это в бэклог",
                photo=[
                    {"file_id": "ph-small", "file_size": 10},
                    {"file_id": "ph-large", "file_size": 99},
                ],
            ),
        )
        self.assertEqual(self.worker.process_once(), 1)
        task = self.tasks.get_by_message("business_message", 123, 10)
        assert task is not None
        self.assertEqual(task["title"], "Добавь это в бэклог")
        self.assertEqual(task["status"], "Новая")
        self.assertEqual(task["attachments"][0]["file_id"], "ph-large")

    def test_document_attachment_metadata(self):
        self._enqueue(
            4,
            base_message(
                document={
                    "file_id": "doc-1",
                    "file_name": "brief.pdf",
                    "mime_type": "application/pdf",
                },
                caption="Документ для проекта Beta",
            ),
        )
        self.assertEqual(self.worker.process_once(), 1)
        task = self.tasks.get_by_message("business_message", 123, 10)
        assert task is not None
        self.assertEqual(task["project"], "Beta")
        attachment = task["attachments"][0]
        self.assertEqual(attachment["kind"], "document")
        self.assertEqual(attachment["file_name"], "brief.pdf")
        self.assertTrue(attachment["local_path"].endswith(".pdf"))

    def test_retry_after_transient_failure(self):
        self._enqueue(5, base_message(voice={"file_id": "voice-retry"}))
        broken = TaskWorker(
            self.inbox,
            self.tasks,
            files=BrokenFileClient(),
            notion=self.notion,
            media_dir=self.media_dir,
        )
        self.assertEqual(broken.process_once(), 0)
        status, err = self.inbox.db.execute(
            "SELECT status, last_error FROM updates WHERE update_id=5"
        ).fetchone()
        self.assertEqual(status, "error")
        self.assertIn("download failed", err)

        recovered = TaskWorker(
            self.inbox,
            self.tasks,
            files=self.files,
            notion=self.notion,
            media_dir=self.media_dir,
        )
        self.assertEqual(recovered.process_once(), 1)
        task = self.tasks.get_by_message("business_message", 123, 10)
        self.assertIsNotNone(task)
        status = self.inbox.db.execute(
            "SELECT status FROM updates WHERE update_id=5"
        ).fetchone()[0]
        self.assertEqual(status, "processed")

    def test_dedupe_same_chat_message_upserts_single_task(self):
        first = base_message(text="Сделай первую версию")
        self._enqueue(10, first)
        self.assertEqual(self.worker.process_once(), 1)

        edited = base_message(text="Сделай финальную версию срочно")
        # Edited delivery: new update_id, same chat/message → inbox upsert + reprocess.
        self.inbox.save_raw_update(
            {"update_id": 11, "edited_business_message": edited}
        )
        self.assertEqual(self.worker.process_once(), 1)

        self.assertEqual(self.tasks.count_tasks(), 1)
        task = self.tasks.get_by_message("business_message", 123, 10)
        assert task is not None
        self.assertEqual(task["title"], "Сделай финальную версию срочно")
        self.assertEqual(task["update_id"], 11)
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["notion_page_id"], "page-1")
        self.assertEqual(len(self.notion.pages), 1)
        self.assertEqual(
            [kind for kind, _ in self.notion.calls],
            ["create", "update"],
        )

    def test_notion_failure_keeps_row_retryable(self):
        self._enqueue(20, base_message(text="Синхронизируй с Notion"))
        self.notion.fail_next = True
        self.assertEqual(self.worker.process_once(), 0)
        status, err = self.inbox.db.execute(
            "SELECT status, last_error FROM updates WHERE update_id=20"
        ).fetchone()
        self.assertEqual(status, "error")
        self.assertIn("Notion unavailable", err)
        # Local task may already be stored; retry must still sync Notion.
        self.assertEqual(self.worker.process_once(), 1)
        task = self.tasks.get_by_message("business_message", 123, 10)
        assert task is not None
        self.assertEqual(task["notion_page_id"], "page-1")

    def test_file_client_blocks_outbound_methods(self):
        client = TelegramFileClient("test-token")
        with self.assertRaisesRegex(RuntimeError, "blocked by task-worker policy"):
            client.call("sendMessage", {"chat_id": 1, "text": "hi"})
        with self.assertRaisesRegex(RuntimeError, "blocked by task-worker policy"):
            client.call("getUpdates")

    def test_non_message_update_is_marked_processed_without_task(self):
        self.inbox.save_raw_update(
            {"update_id": 99, "business_connection": {"id": "bc-1"}}
        )
        self.assertEqual(self.worker.process_once(), 1)
        self.assertEqual(self.tasks.count_tasks(), 0)
        status = self.inbox.db.execute(
            "SELECT status FROM updates WHERE update_id=99"
        ).fetchone()[0]
        self.assertEqual(status, "processed")
        self.assertEqual(self.notion.calls, [])


class NotionClientUnitTests(unittest.TestCase):
    def test_properties_include_project_priority_deadline_source_attachments(self):
        client = NotionTaskClient("secret", "db-1")
        task = sample_task()
        props = client.properties_for_task(task)
        self.assertEqual(props["Name"]["title"][0]["text"]["content"], task.title)
        self.assertEqual(props["Project"]["rich_text"][0]["text"]["content"], "Alpha")
        self.assertEqual(props["Priority"]["rich_text"][0]["text"]["content"], "high")
        self.assertEqual(props["Deadline"]["rich_text"][0]["text"]["content"], "пятницы")
        self.assertEqual(props["Source"]["url"], "https://t.me/alex")
        self.assertEqual(
            props["Source Key"]["rich_text"][0]["text"]["content"],
            "business_message:123:10",
        )
        self.assertIn(
            "brief.pdf", props["Attachments"]["rich_text"][0]["text"]["content"]
        )

    def test_format_attachments_includes_local_path(self):
        text = format_attachments_for_notion(
            [{"kind": "voice", "file_id": "v1", "local_path": "/tmp/v1.ogg"}]
        )
        self.assertIn("voice: v1", text)
        self.assertIn("/tmp/v1.ogg", text)

    def test_upsert_queries_then_creates_and_updates(self):
        client = NotionTaskClient("secret", "db-1")
        task = sample_task()
        responses = [
            {"results": []},
            {"id": "page-abc"},
            {},
        ]

        def fake_request(method, path, payload=None, timeout=30):
            fake_request.calls.append((method, path, payload))
            return responses.pop(0)

        fake_request.calls = []
        with mock.patch.object(client, "_request", side_effect=fake_request):
            created = client.upsert_task(task)
            self.assertEqual(created, "page-abc")
            updated = client.upsert_task(task, page_id="page-abc")
            self.assertEqual(updated, "page-abc")

        methods = [call[0] for call in fake_request.calls]
        self.assertEqual(methods, ["POST", "POST", "PATCH"])
        self.assertEqual(fake_request.calls[0][1], "/databases/db-1/query")
        self.assertEqual(fake_request.calls[1][1], "/pages")
        self.assertEqual(fake_request.calls[2][1], "/pages/page-abc")

    def test_upsert_updates_existing_by_source_key(self):
        client = NotionTaskClient("secret", "db-1")
        task = sample_task(title="Обновлённый заголовок")
        responses = [
            {"results": [{"id": "existing-1"}]},
            {},
        ]

        def fake_request(method, path, payload=None, timeout=30):
            fake_request.calls.append((method, path, payload))
            return responses.pop(0)

        fake_request.calls = []
        with mock.patch.object(client, "_request", side_effect=fake_request):
            page_id = client.upsert_task(task)
        self.assertEqual(page_id, "existing-1")
        self.assertEqual(fake_request.calls[1][0], "PATCH")
        patch_payload = fake_request.calls[1][2]
        assert patch_payload is not None
        self.assertEqual(
            patch_payload["properties"]["Name"]["title"][0]["text"]["content"],
            "Обновлённый заголовок",
        )

    def test_http_error_is_wrapped(self):
        client = NotionTaskClient("secret", "db-1")

        def raise_http(*_args, **_kwargs):
            raise urllib.error.HTTPError(
                url="https://api.notion.com/v1/pages",
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=mock.Mock(read=mock.Mock(return_value=b'{"message":"invalid token"}')),
            )

        with mock.patch("urllib.request.urlopen", side_effect=raise_http):
            with self.assertRaisesRegex(RuntimeError, "HTTP 401"):
                client.create_page(sample_task())


@unittest.skipUnless(
    os.getenv("NOTION_TOKEN", "").strip()
    and os.getenv("NOTION_DATABASE_ID", "").strip(),
    "NOTION_TOKEN and NOTION_DATABASE_ID required for live smoke",
)
class NotionSmokeTests(unittest.TestCase):
    """Live smoke against the configured Notion tasks database."""

    def test_create_update_and_dedupe_by_source_key(self):
        load_env(Path(__file__).resolve().parent / ".env")
        # Re-check after loading .env so local credentials are picked up.
        token = os.getenv("NOTION_TOKEN", "").strip()
        database_id = os.getenv("NOTION_DATABASE_ID", "").strip()
        if not token or not database_id:
            self.skipTest("NOTION_TOKEN and NOTION_DATABASE_ID required for live smoke")
        client = NotionTaskClient(token, database_id)
        marker = f"smoke-{os.getpid()}-{int(time.time())}"
        task = sample_task(
            title=f"[smoke] Notion sync {marker}",
            body=f"smoke body {marker}",
            source="business_message",
            chat_id=9_001_001,
            message_id=int(time.time()) % 1_000_000,
            update_id=42,
        )
        page_id = client.upsert_task(task)
        self.assertTrue(page_id)

        task.title = f"[smoke] Notion sync updated {marker}"
        updated_id = client.upsert_task(task)
        self.assertEqual(updated_id, page_id)

        found = client.find_page_id_by_source_key(task_source_key(task) or "")
        self.assertEqual(found, page_id)

        client.archive_page(page_id)


if __name__ == "__main__":
    unittest.main()
