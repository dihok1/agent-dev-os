"""Tests for scripts/next_task.py classification."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("next_task", ROOT / "scripts" / "next_task.py")
next_task = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(next_task)


class NextTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.tasks = Path(self.tempdir.name) / "tasks.md"

    def write_tasks(self, value: str) -> None:
        self.tasks.write_text(value, encoding="utf-8")

    def test_auto_task_any_id(self) -> None:
        self.write_tasks("- [x] **T1** — done\n- [ ] **Setup-env** — add config\n")
        result = next_task.classify(self.tasks)
        self.assertEqual(result["status"], "AUTO")
        self.assertEqual(result["task"], "Setup-env")

    def test_human_gate_by_comment_legacy(self) -> None:
        self.write_tasks("<!-- human-gate -->\n- [ ] **G1** — operator smoke\n")
        result = next_task.classify(self.tasks, auto_human_gates=False)
        self.assertEqual(result["status"], "HUMAN_GATE")

    def test_auto_gate_by_default(self) -> None:
        self.write_tasks("<!-- human-gate -->\n- [ ] **G1** — operator smoke\n")
        result = next_task.classify(self.tasks, auto_human_gates=True)
        self.assertEqual(result["status"], "AUTO_GATE")
        self.assertEqual(result["task"], "G1")

    def test_human_section_blocks_next_task_legacy(self) -> None:
        self.write_tasks("- [x] **T4** — done\n\n## ⛔ HUMAN GATE — Manual smoke\n\n**Do not start T5+ until signed off.**\n\n- [ ] **T5** — next work\n")
        result = next_task.classify(self.tasks, auto_human_gates=False)
        self.assertEqual(result["status"], "HUMAN_GATE")
        self.assertEqual(result["reason"], "unsigned_human_section")

    def test_human_section_auto_acks(self) -> None:
        self.write_tasks("- [x] **T4** — done\n\n## ⛔ HUMAN GATE — Manual smoke\n\n**Do not start T5+ until signed off.**\n\n- [ ] **T5** — next work\n")
        result = next_task.classify(self.tasks, auto_human_gates=True)
        self.assertEqual(result["status"], "AUTO_GATE")
        self.assertEqual(result["reason"], "auto_ack_unsigned_human_section")

    def test_verify_when_all_checked(self) -> None:
        self.write_tasks("- [x] **T1** — done\n")
        stamp = Path(self.tempdir.name) / ".verify-passed"
        with patch.object(next_task, "_active_change", return_value="changes/demo"), patch.object(next_task, "_verify_stamp", return_value=stamp):
            result = next_task.classify(self.tasks)
        self.assertEqual(result["status"], "VERIFY")

    def test_awaiting_human_after_verify(self) -> None:
        self.write_tasks("- [x] **T1** — done\n")
        stamp = Path(self.tempdir.name) / ".verify-passed"
        stamp.write_text("ok\n", encoding="utf-8")
        with patch.object(next_task, "_active_change", return_value="changes/demo"), patch.object(next_task, "_verify_stamp", return_value=stamp):
            result = next_task.classify(self.tasks)
        self.assertEqual(result["status"], "AWAITING_HUMAN")
        self.assertEqual(result["task"], "FINAL_MERGE")


if __name__ == "__main__":
    unittest.main()
