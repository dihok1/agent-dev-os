"""Tests for scripts/next_task.py classification."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "next_task",
    ROOT / "scripts" / "next_task.py",
)
next_task = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(next_task)


def test_auto_task_any_id(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.md"
    tasks.write_text(
        "- [x] **T1** — done\n"
        "- [ ] **Setup-env** — add config\n",
        encoding="utf-8",
    )
    result = next_task.classify(tasks)
    assert result["status"] == "AUTO"
    assert result["task"] == "Setup-env"


def test_human_gate_by_comment_legacy(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.md"
    tasks.write_text(
        "<!-- human-gate -->\n"
        "- [ ] **G1** — operator smoke\n",
        encoding="utf-8",
    )
    result = next_task.classify(tasks, auto_human_gates=False)
    assert result["status"] == "HUMAN_GATE"


def test_auto_gate_by_default(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.md"
    tasks.write_text(
        "<!-- human-gate -->\n"
        "- [ ] **G1** — operator smoke\n",
        encoding="utf-8",
    )
    result = next_task.classify(tasks, auto_human_gates=True)
    assert result["status"] == "AUTO_GATE"
    assert result["task"] == "G1"


def test_human_section_blocks_next_task_legacy(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.md"
    tasks.write_text(
        "- [x] **T4** — done\n\n"
        "## ⛔ HUMAN GATE — Manual smoke\n\n"
        "**Do not start T5+ until signed off.**\n\n"
        "- [ ] **T5** — next work\n",
        encoding="utf-8",
    )
    result = next_task.classify(tasks, auto_human_gates=False)
    assert result["status"] == "HUMAN_GATE"
    assert result["reason"] == "unsigned_human_section"


def test_human_section_auto_acks(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.md"
    tasks.write_text(
        "- [x] **T4** — done\n\n"
        "## ⛔ HUMAN GATE — Manual smoke\n\n"
        "**Do not start T5+ until signed off.**\n\n"
        "- [ ] **T5** — next work\n",
        encoding="utf-8",
    )
    result = next_task.classify(tasks, auto_human_gates=True)
    assert result["status"] == "AUTO_GATE"
    assert result["reason"] == "auto_ack_unsigned_human_section"


def test_verify_when_all_checked(tmp_path: Path, monkeypatch) -> None:
    tasks = tmp_path / "tasks.md"
    tasks.write_text("- [x] **T1** — done\n", encoding="utf-8")
    monkeypatch.setattr(next_task, "_active_change", lambda: "changes/demo")
    stamp = tmp_path / ".verify-passed"
    monkeypatch.setattr(next_task, "_verify_stamp", lambda _c: stamp)
    result = next_task.classify(tasks)
    assert result["status"] == "VERIFY"


def test_awaiting_human_after_verify(tmp_path: Path, monkeypatch) -> None:
    tasks = tmp_path / "tasks.md"
    tasks.write_text("- [x] **T1** — done\n", encoding="utf-8")
    monkeypatch.setattr(next_task, "_active_change", lambda: "changes/demo")
    stamp = tmp_path / ".verify-passed"
    stamp.write_text("ok\n", encoding="utf-8")
    monkeypatch.setattr(next_task, "_verify_stamp", lambda _c: stamp)
    result = next_task.classify(tasks)
    assert result["status"] == "AWAITING_HUMAN"
    assert result["task"] == "FINAL_MERGE"
