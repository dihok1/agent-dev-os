import json
import unittest
import tempfile
from pathlib import Path

from notifier import (
    BotApi,
    Config,
    LlmDecision,
    Notifier,
    PolzaClassifier,
    Store,
    TaskInboxStore,
    is_addressed,
    is_reply_to_owner,
    message_link,
    message_text,
    redact_for_llm,
    urgency,
)


class FakeApi:
    def __init__(self, fail_first=False):
        self.fail_first = fail_first
        self.calls = []

    def call(self, method, payload=None, timeout=30):
        self.calls.append((method, payload))
        if method == "sendMessage" and self.fail_first:
            self.fail_first = False
            raise RuntimeError("temporary send failure")
        return {"message_id": 1}


class FakeLlm:
    def __init__(self, decision):
        self.decision = decision
        self.calls = []

    def classify(
        self,
        text,
        context,
        sent_at,
        addressed_to_owner=False,
        reply_to_owner=False,
        chat_type="private",
    ):
        self.calls.append(
            (text, context, sent_at, addressed_to_owner, reply_to_owner, chat_type)
        )
        return self.decision


class UrgencyTests(unittest.TestCase):
    def test_explicit_urgent(self):
        score, reasons = urgency("Даня, срочно ответь до 15:00 — клиент ждёт")
        self.assertGreaterEqual(score, 3)
        self.assertTrue(reasons)

    def test_no_rush_suppresses_alert(self):
        score, _ = urgency("Даня, не срочно, можно завтра")
        self.assertEqual(score, 0)

    def test_now_is_explicitly_urgent(self):
        score, reasons = urgency("Можешь посмотреть сейчас?")
        self.assertGreaterEqual(score, 3)
        self.assertIn("явная срочность", reasons)

    def test_not_now_is_not_explicitly_urgent(self):
        score, reasons = urgency("Можно посмотреть не сейчас")
        self.assertEqual(score, 0)
        self.assertNotIn("явная срочность", reasons)

    def test_help_with_account_access_is_urgent(self):
        score, reasons = urgency("У меня вылетел общедзеновский аккаунт для AM. Помоги, пожалуйста, снова зайти")
        self.assertGreaterEqual(score, 3)
        self.assertIn("просят помочь", reasons)
        self.assertIn("проблема с доступом", reasons)

    def test_personalized_task_plus_deadline(self):
        score, _ = urgency("Добавь это сегодня")
        self.assertGreaterEqual(score, 3)

    def test_plain_task_is_not_automatically_urgent(self):
        score, _ = urgency("Посмотри документ")
        self.assertLess(score, 3)

    def test_short_call_question_is_urgent(self):
        score, _ = urgency("Наберу на 5 минут? Есть вопрос")
        self.assertGreaterEqual(score, 3)

    def test_accountability_escalation_is_urgent(self):
        score, _ = urgency("Дань, тут не отвечено")
        self.assertGreaterEqual(score, 3)

    def test_real_access_recovery_followup_is_urgent(self):
        score, _ = urgency("Пока не понятно как доступ восстановить?")
        self.assertGreaterEqual(score, 3)

    def test_name_variants(self):
        names = ("Данила", "Даня", "Данечка", "Данек", "Данил", "Даниил")
        for name in names:
            with self.subTest(name=name):
                self.assertTrue(is_addressed(f"{name}, посмотри", [], None, "", names))

    def test_username(self):
        self.assertTrue(is_addressed("Пинг @danila_work!", [], None, "danila_work", ()))

    def test_reply_to_owner(self):
        message = {"reply_to_message": {"from": {"id": 777}}}
        self.assertTrue(is_reply_to_owner(message, 777))
        self.assertFalse(is_reply_to_owner(message, 778))

    def test_unrelated_name_fragment(self):
        self.assertFalse(is_addressed("Обсуждаем компанию Данилов", [], None, "", ("Данил",)))

    def test_public_group_message_link(self):
        message = {"message_id": 42, "chat": {"id": -100123, "type": "supergroup", "username": "team_chat"}}
        self.assertEqual(message_link(message), "https://t.me/team_chat/42")

    def test_private_supergroup_message_link(self):
        message = {"message_id": 42, "chat": {"id": -1001234567890, "type": "supergroup"}}
        self.assertEqual(message_link(message), "https://t.me/c/1234567890/42")

    def test_private_chat_link(self):
        message = {"message_id": 42, "chat": {"id": 7, "type": "private"}, "from": {"id": 7, "username": "alex"}}
        self.assertEqual(message_link(message), "https://t.me/alex")

    def test_media_without_caption_is_still_processed(self):
        self.assertEqual(message_text({"voice": {"file_id": "x"}}), "[голосовое сообщение]")

    def test_llm_redaction_removes_credentials_and_contacts(self):
        raw = "https://example.com x@y.ru +7 999 123-45-67 TOKEN_abcdefghijklmnopqrstuvwxyz"
        redacted = redact_for_llm(raw)
        self.assertNotIn("example.com", redacted)
        self.assertNotIn("x@y.ru", redacted)
        self.assertNotIn("999 123", redacted)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", redacted)

    def test_fenced_llm_json_is_parsed(self):
        parsed = PolzaClassifier._parse_json(
            '```json\n{"urgency":2,"reply_expected":true,"deadline":null,"confidence":0.9,"reason":"Нужен ответ"}\n```'
        )
        self.assertEqual(parsed["urgency"], 2)

    def test_level_two_alert_is_not_asap(self):
        decision = LlmDecision(2, True, 0.9, None, "Нужен ответ")
        self.assertTrue(decision.should_alert)
        self.assertFalse(decision.is_urgent)

    def test_level_three_alert_is_asap(self):
        decision = LlmDecision(3, True, 0.9, None, "Срочно")
        self.assertTrue(decision.should_alert)
        self.assertTrue(decision.is_urgent)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tempdir.name) / "messages.sqlite3")
        self.config = Config(
            token="test-token",
            alert_chat_id=999,
            owner_username="danila_voloschenko",
            name_variants=("Данила", "Даня", "Дань"),
        )
        self.message = {
            "message_id": 10,
            "date": 1_800_000_000,
            "chat": {"id": 123, "type": "private", "username": "alex"},
            "from": {"id": 123, "first_name": "Alex", "username": "alex"},
            "text": "Срочно ответь сейчас",
        }

    def tearDown(self):
        self.store.db.close()
        self.tempdir.cleanup()

    def test_failed_alert_remains_pending_and_retries(self):
        api = FakeApi(fail_first=True)
        notifier = Notifier(self.config, api, self.store)
        with self.assertRaises(RuntimeError):
            notifier.process_message("business_message", self.message)
        self.assertTrue(self.store.alert_is_pending("business_message", 123, 10))
        notifier.process_message("business_message", self.message)
        self.assertFalse(self.store.alert_is_pending("business_message", 123, 10))
        self.assertEqual([method for method, _ in api.calls], ["sendMessage", "sendMessage"])

    def test_notification_goes_only_to_owner_without_business_connection(self):
        api = FakeApi()
        notifier = Notifier(self.config, api, self.store)
        notifier.process_message("business_message", self.message)
        method, payload = api.calls[0]
        self.assertEqual(method, "sendMessage")
        self.assertEqual(payload["chat_id"], 999)
        self.assertNotIn("business_connection_id", payload)

    def test_deleted_business_message_is_redacted_locally(self):
        api = FakeApi()
        notifier = Notifier(self.config, api, self.store)
        neutral = dict(self.message, text="Обычное сообщение")
        notifier.process_message("business_message", neutral)
        self.store.mark_deleted("business_message", 123, [10])
        row = self.store.db.execute(
            "SELECT text, deleted FROM messages WHERE source='business_message' AND chat_id=123 AND message_id=10"
        ).fetchone()
        self.assertEqual(row, ("[сообщение удалено]", 1))

    def test_owner_group_message_is_ignored(self):
        self.store.set("owner_id", 777)
        api = FakeApi()
        notifier = Notifier(self.config, api, self.store)
        own_message = {
            "message_id": 11,
            "date": 1_800_000_000,
            "chat": {"id": -100123, "type": "supergroup", "title": "Team"},
            "from": {"id": 777, "first_name": "Данила"},
            "text": "@danila_voloschenko тест",
        }
        notifier.process_message("message", own_message)
        count = self.store.db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        self.assertEqual(count, 0)

    def test_passive_policy_blocks_business_sending(self):
        api = BotApi("test-token")
        with self.assertRaisesRegex(RuntimeError, "passive-mode policy"):
            api.call("sendMessage", {"chat_id": 123, "business_connection_id": "secret"})

    def test_passive_policy_blocks_destructive_methods(self):
        api = BotApi("test-token")
        for method in ("deleteMessage", "readBusinessMessage", "editMessageText"):
            with self.subTest(method=method):
                with self.assertRaisesRegex(RuntimeError, "passive-mode policy"):
                    api.call(method, {})

    def test_llm_can_escalate_borderline_private_message(self):
        api = FakeApi()
        llm = FakeLlm(LlmDecision(2, True, 0.9, None, "Запрашивается срок"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        borderline = dict(self.message, text="Надо добавить в отчет. Когда сможешь?")
        notifier.process_message("business_message", borderline)
        self.assertEqual(len(llm.calls), 1)
        self.assertEqual(api.calls[0][0], "sendMessage")
        self.assertIn("Нужен твой ответ", api.calls[0][1]["text"])
        self.assertNotIn("ASAP", api.calls[0][1]["text"])
        row = self.store.db.execute(
            "SELECT urgency_score, alert_sent, urgency_reasons FROM messages WHERE message_id=10"
        ).fetchone()
        self.assertEqual(row[0:2], (3, 1))
        self.assertIn("LLM", row[2])

    def test_explicit_non_urgent_message_is_checked_by_llm(self):
        api = FakeApi()
        llm = FakeLlm(LlmDecision(0, False, 1.0, None, "Можно позже"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        neutral = dict(self.message, text="Не срочно, можно завтра")
        notifier.process_message("business_message", neutral)
        self.assertEqual(len(llm.calls), 1)
        self.assertEqual(api.calls, [])

    def test_explicitly_urgent_private_message_skips_llm(self):
        api = FakeApi()
        llm = FakeLlm(LlmDecision(0, False, 1.0, None, "ignore"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        notifier.process_message("business_message", self.message)
        self.assertEqual(llm.calls, [])
        self.assertEqual(api.calls[0][0], "sendMessage")

    def test_rule_score_without_explicit_urgency_goes_to_llm(self):
        api = FakeApi()
        llm = FakeLlm(LlmDecision(1, False, 0.9, None, "Можно позже"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        task = dict(self.message, text="Добавь это сегодня")
        notifier.process_message("business_message", task)
        self.assertEqual(len(llm.calls), 1)
        self.assertEqual(api.calls, [])

    def test_unaddressed_group_message_is_checked_by_llm(self):
        api = FakeApi()
        llm = FakeLlm(LlmDecision(1, False, 0.9, None, "Общее обсуждение"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        group_message = {
            "message_id": 12,
            "date": 1_800_000_000,
            "chat": {"id": -100123, "type": "supergroup", "title": "Team"},
            "from": {"id": 123, "first_name": "Alex"},
            "text": "Коллеги, отчёт будет завтра",
        }
        notifier.process_message("message", group_message)
        self.assertEqual(len(llm.calls), 1)
        self.assertEqual(api.calls, [])

    def test_addressed_group_message_alerts_without_llm(self):
        api = FakeApi()
        llm = FakeLlm(LlmDecision(1, False, 0.9, None, "Обычное обращение"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        group_message = {
            "message_id": 13,
            "date": 1_800_000_000,
            "chat": {"id": -100123, "type": "supergroup", "title": "Team"},
            "from": {"id": 123, "first_name": "Alex"},
            "text": "Данила, привет",
        }
        notifier.process_message("message", group_message)
        self.assertEqual(llm.calls, [])
        self.assertEqual(api.calls[0][0], "sendMessage")
        self.assertIn("Тебя упомянули", api.calls[0][1]["text"])
        self.assertNotIn("ASAP", api.calls[0][1]["text"])

    def test_group_reply_to_owner_is_classified_by_llm(self):
        self.store.set("owner_id", 777)
        api = FakeApi()
        llm = FakeLlm(LlmDecision(1, False, 0.9, None, "Обычный ответ"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        group_message = {
            "message_id": 14,
            "date": 1_800_000_000,
            "chat": {"id": -100123, "type": "supergroup", "title": "Team"},
            "from": {"id": 123, "first_name": "Alex"},
            "reply_to_message": {"message_id": 9, "from": {"id": 777, "first_name": "Данила"}},
            "text": "Сделал",
        }
        notifier.process_message("message", group_message)
        self.assertEqual(len(llm.calls), 1)
        self.assertTrue(llm.calls[0][3])
        self.assertTrue(llm.calls[0][4])
        self.assertEqual(api.calls, [])
        row = self.store.db.execute(
            "SELECT addressed, alert_sent FROM messages WHERE message_id=14"
        ).fetchone()
        self.assertEqual(row, (1, 0))

    def test_group_reply_level_two_is_neutral_not_asap(self):
        self.store.set("owner_id", 777)
        api = FakeApi()
        llm = FakeLlm(LlmDecision(2, True, 0.9, None, "Ждут объяснения"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        group_message = {
            "message_id": 16,
            "date": 1_800_000_000,
            "chat": {"id": -100123, "type": "supergroup", "title": "Team"},
            "from": {"id": 123, "first_name": "Alex"},
            "reply_to_message": {
                "message_id": 9,
                "from": {"id": 777, "first_name": "Данила"},
            },
            "text": "зачем? не поняла",
        }
        notifier.process_message("message", group_message)
        self.assertIn("Нужен твой ответ", api.calls[0][1]["text"])
        self.assertNotIn("ASAP", api.calls[0][1]["text"])

    def test_private_trivial_reply_does_not_trigger_asap(self):
        self.store.set("owner_id", 777)
        api = FakeApi()
        llm = FakeLlm(LlmDecision(0, False, 0.95, None, "Подтверждение"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        reply = dict(
            self.message,
            text="Добро",
            reply_to_message={
                "message_id": 9,
                "from": {"id": 777, "first_name": "Данила"},
            },
        )
        notifier.process_message("business_message", reply)
        self.assertEqual(len(llm.calls), 1)
        self.assertEqual(api.calls, [])

    def test_strong_group_mention_keeps_asap_label(self):
        api = FakeApi()
        llm = FakeLlm(LlmDecision(0, False, 0.9, None, "ignore"))
        notifier = Notifier(self.config, api, self.store, llm=llm)
        group_message = {
            "message_id": 15,
            "date": 1_800_000_000,
            "chat": {"id": -100123, "type": "supergroup", "title": "Team"},
            "from": {"id": 123, "first_name": "Alex"},
            "text": "Данила, срочно проверь",
        }
        notifier.process_message("message", group_message)
        self.assertEqual(llm.calls, [])
        self.assertIn("ASAP", api.calls[0][1]["text"])

    def test_group_alert_contains_exact_message_link(self):
        api = FakeApi()
        notifier = Notifier(self.config, api, self.store)
        group_message = {
            "message_id": 42,
            "chat": {
                "id": -1001234567890,
                "type": "supergroup",
                "title": "Team",
            },
            "from": {"id": 123, "first_name": "Alex"},
        }
        notifier.send_alert(group_message)
        payload = api.calls[0][1]
        expected = "https://t.me/c/1234567890/42"
        self.assertIn(expected, payload["text"])
        self.assertEqual(payload["reply_markup"]["inline_keyboard"][0][0]["url"], expected)
        self.assertEqual(
            payload["reply_markup"]["inline_keyboard"][0][0]["text"],
            "Открыть сообщение ↗",
        )

    def test_time_policy_is_explicit_in_llm_prompt(self):
        prompt = PolzaClassifier.SYSTEM_PROMPT
        self.assertIn("Europe/Moscow", prompt)
        self.assertIn("ближайшие 30 минут", prompt)
        self.assertIn("31–120 минут", prompt)


class TaskInboxTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tempdir.name) / "messages.sqlite3")
        self.task_inbox = TaskInboxStore(Path(self.tempdir.name) / "task_inbox.sqlite3")
        self.config = Config(
            token="test-token",
            alert_chat_id=999,
            owner_username="danila_voloschenko",
            name_variants=("Данила", "Даня", "Дань"),
        )
        self.message = {
            "message_id": 10,
            "date": 1_800_000_000,
            "chat": {"id": 123, "type": "private", "username": "alex"},
            "from": {"id": 123, "first_name": "Alex", "username": "alex"},
            "text": "Срочно ответь сейчас",
        }

    def tearDown(self):
        self.store.db.close()
        self.task_inbox.db.close()
        self.tempdir.cleanup()

    def test_process_update_copies_raw_update_to_task_inbox(self):
        api = FakeApi()
        notifier = Notifier(
            self.config, api, self.store, task_inbox=self.task_inbox
        )
        update = {"update_id": 501, "business_message": self.message}
        notifier.process_update(update)
        row = self.task_inbox.db.execute(
            "SELECT update_id, source, chat_id, message_id, status, raw_json "
            "FROM updates WHERE update_id=501"
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0:5], (501, "business_message", 123, 10, "pending"))
        copied = json.loads(row[5])
        self.assertEqual(copied["update_id"], 501)
        self.assertEqual(copied["business_message"]["text"], "Срочно ответь сейчас")
        self.assertEqual(api.calls[0][0], "sendMessage")

    def test_task_inbox_copy_failure_does_not_block_asap(self):
        class BrokenInbox:
            def save_raw_update(self, update):
                raise RuntimeError("disk full")

            def record_copy_error(self, update, error):
                raise RuntimeError("also broken")

        api = FakeApi()
        notifier = Notifier(
            self.config, api, self.store, task_inbox=BrokenInbox()
        )
        notifier.process_update(
            {"update_id": 777, "business_message": self.message}
        )
        self.assertEqual(api.calls[0][0], "sendMessage")
        self.assertFalse(self.store.alert_is_pending("business_message", 123, 10))


if __name__ == "__main__":
    unittest.main()
