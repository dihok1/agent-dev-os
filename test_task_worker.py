#!/usr/bin/env python3
"""Tests for the independent Telegram task worker."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from notifier import TaskInboxStore
from task_worker import ExtractedTaskStore, TaskWorker, TelegramFileClient


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


def base_message(**overrides):
    message = {
        "message_id": 10,
        "date": 1_800_000_000,
        "chat": {"id": 123, "type": "private", "username": "alex"},
        "from": {"id": 123, "first_name": "Alex", "username": "alex"},
    }
    message.update(overrides)
    return message


class TaskWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.inbox = TaskInboxStore(root / "task_inbox.sqlite3")
        self.tasks = ExtractedTaskStore(root / "task_inbox.sqlite3")
        self.media_dir = root / "media"
        self.files = FakeFileClient()
        self.worker = TaskWorker(
            self.inbox, self.tasks, files=self.files, media_dir=self.media_dir
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
        self.assertEqual(task["title"], "Срочно проверь отчёт по проекту Alpha до пятницы")
        self.assertEqual(task["status"], "Новая")
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["project"], "Alpha")
        self.assertEqual(task["deadline"], "пятницы")
        self.assertEqual(task["author"], "Alex")
        self.assertEqual(task["source_link"], "https://t.me/alex")
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
            media_dir=self.media_dir,
        )
        self.assertEqual(broken.process_once(), 0)
        status, err = self.inbox.db.execute(
            "SELECT status, last_error FROM updates WHERE update_id=5"
        ).fetchone()
        self.assertEqual(status, "error")
        self.assertIn("download failed", err)

        recovered = TaskWorker(
            self.inbox, self.tasks, files=self.files, media_dir=self.media_dir
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


if __name__ == "__main__":
    unittest.main()
