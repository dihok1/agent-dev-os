#!/usr/bin/env python3
"""Classify next unchecked task in active change: AUTO | AUTO_GATE | VERIFY | DONE."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".planning" / "STATE.md"
CONFIG = ROOT / ".cursor" / "automations" / "config.json"

CHECKBOX_RE = re.compile(r"^\- \[([ xX])\] (.*)$")
TASK_ID_RE = re.compile(r"\*\*([^*]+)\*\*")
SECTION_RE = re.compile(r"^(#{2,3})\s+(.+)$")

DEFAULT_HUMAN_ID_PATTERNS = [
    r"^G\d+$",
    r"^HG\d+$",
    r"^GATE\d+$",
    r"^H\d+$",
]

HUMAN_LINE_PHRASES = (
    "human gate",
    "operator:",
    "operator checklist",
    "manual smoke",
    "sign-off in chat",
    "manual verification",
    "blocking before",
    "do not start t",
    "do not start until",
)

HUMAN_SECTION_PHRASES = (
    "human gate",
    "⛔",
)


def _load_config() -> dict:
    if not CONFIG.is_file():
        return {}
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _human_id_patterns(cfg: dict) -> list[str]:
    patterns = cfg.get("humanGateIdPatterns")
    if patterns:
        return list(patterns)
    legacy = cfg.get("humanGatePattern")
    if legacy:
        return [legacy]
    return DEFAULT_HUMAN_ID_PATTERNS


def _auto_human_gates(cfg: dict) -> bool:
    """When true, G*/human gates are AUTO_GATE (agent auto-acks). Human only final stage merge."""
    if "autoHumanGates" in cfg:
        return bool(cfg["autoHumanGates"])
    # Default ON for execute-next chain — mid-stage gates must not stall automation.
    return True


def _active_change() -> str | None:
    if not STATE.is_file():
        return None
    for line in STATE.read_text(encoding="utf-8").splitlines():
        if line.startswith("active_change:"):
            value = line.split(":", 1)[1].strip()
            if value and value != "none":
                return value
    return None


def _extract_task_id(line: str) -> str | None:
    match = TASK_ID_RE.search(line)
    return match.group(1).strip() if match else None


def _section_is_human(title: str) -> bool:
    lower = title.lower()
    return any(p in lower or p in title for p in HUMAN_SECTION_PHRASES)


def _line_is_human(
    line: str,
    recent_lines: list[str],
    section_title: str | None,
    id_patterns: list[str],
) -> bool:
    if section_title and _section_is_human(section_title):
        blob = "\n".join(recent_lines).lower()
        if "human-gate" in blob or "<!-- human-gate" in blob:
            return True
        lower = line.lower()
        return any(phrase in lower for phrase in HUMAN_LINE_PHRASES)
    task_id = _extract_task_id(line)
    if task_id:
        for pattern in id_patterns:
            if re.match(pattern, task_id, re.IGNORECASE):
                return True
    lower = line.lower()
    return any(phrase in lower for phrase in HUMAN_LINE_PHRASES)


def _parse_sections(lines: list[str]) -> list[dict]:
    """Return ordered events: sections and checkbox tasks."""
    events: list[dict] = []
    current_section = ""
    recent: list[str] = []

    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        sec = SECTION_RE.match(line)
        if sec:
            current_section = sec.group(2).strip()
            events.append(
                {
                    "kind": "section",
                    "title": current_section,
                    "line_no": i + 1,
                    "human": _section_is_human(current_section),
                }
            )
            recent = []
            continue

        cb = CHECKBOX_RE.match(line)
        if cb:
            checked = cb.group(1).lower() == "x"
            body = cb.group(2).strip()
            events.append(
                {
                    "kind": "task",
                    "checked": checked,
                    "body": body,
                    "line": line,
                    "line_no": i + 1,
                    "section": current_section,
                    "task_id": _extract_task_id(body) or f"line-{i + 1}",
                }
            )
            recent.append(line)
            if len(recent) > 12:
                recent.pop(0)
            continue

        if line.strip().startswith("<!--"):
            recent.append(line)
            if len(recent) > 12:
                recent.pop(0)

    return events


def _blocking_human_section(events: list[dict], next_task_idx: int) -> dict | None:
    """Stage-1 style: ## HUMAN GATE section without completed checkbox before next task."""
    last_completed_idx = -1
    for idx, ev in enumerate(events):
        if ev["kind"] == "task" and ev["checked"]:
            last_completed_idx = idx

    for idx in range(last_completed_idx + 1, next_task_idx):
        ev = events[idx]
        if ev["kind"] != "section" or not ev.get("human"):
            continue
        # Section cleared if any checked task follows before next unchecked
        cleared = False
        for j in range(idx + 1, next_task_idx):
            follow = events[j]
            if follow["kind"] == "section":
                break
            if follow["kind"] == "task" and follow["checked"]:
                cleared = True
                break
        if not cleared:
            return ev
    return None


def _verify_stamp(change: str) -> Path:
    slug = Path(change).name
    return ROOT / "changes" / slug / ".verify-passed"


def classify(tasks_path: Path, *, auto_human_gates: bool | None = None) -> dict:
    cfg = _load_config()
    id_patterns = _human_id_patterns(cfg)
    if auto_human_gates is None:
        auto_human_gates = _auto_human_gates(cfg)
    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    events = _parse_sections(lines)

    current_section = ""

    for idx, ev in enumerate(events):
        if ev["kind"] == "section":
            current_section = ev["title"]
            continue
        if ev["checked"]:
            continue

        block = _blocking_human_section(events, idx)
        if block:
            if auto_human_gates:
                return {
                    "status": "AUTO_GATE",
                    "task": block["title"],
                    "line": f"(section) {block['title']}",
                    "reason": "auto_ack_unsigned_human_section",
                }
            return {
                "status": "HUMAN_GATE",
                "task": block["title"],
                "line": f"(section) {block['title']}",
                "reason": "unsigned_human_section",
            }

        # First unchecked task
        context_start = max(0, ev["line_no"] - 12)
        context = lines[context_start : ev["line_no"] - 1]

        if _line_is_human(ev["line"], context, ev.get("section") or current_section, id_patterns):
            if auto_human_gates:
                return {
                    "status": "AUTO_GATE",
                    "task": ev["task_id"],
                    "line": ev["line"],
                    "reason": "auto_ack_human_gate",
                }
            return {
                "status": "HUMAN_GATE",
                "task": ev["task_id"],
                "line": ev["line"],
                "reason": "task_marked_human",
            }

        return {
            "status": "AUTO",
            "task": ev["task_id"],
            "line": ev["line"],
            "reason": "executable_task",
        }

    # All checkboxes complete → VERIFY once, then AWAITING_HUMAN (final stage merge).
    change = _active_change() or ""
    stamp = _verify_stamp(change) if change else None
    if stamp is not None and not stamp.is_file():
        return {
            "status": "VERIFY",
            "task": "VERIFY",
            "line": "(all tasks checked — run /verify)",
            "reason": "ready_for_verify",
        }
    return {
        "status": "AWAITING_HUMAN",
        "task": "FINAL_MERGE",
        "line": "(verify passed — human final stage merge/archive)",
        "reason": "human_final_merge_only",
    }


def main() -> int:
    change = _active_change()
    if change is None:
        print("STATUS=NO_ACTIVE_CHANGE")
        return 0
    if not STATE.is_file():
        print("STATUS=NO_STATE")
        return 1

    tasks_path = ROOT / change / "tasks.md"
    slug = Path(change).name
    if not tasks_path.is_file():
        print("STATUS=NO_TASKS")
        print(f"CHANGE={slug}")
        return 1

    result = classify(tasks_path)
    print(f"STATUS={result['status']}")
    print(f"CHANGE={slug}")
    if result.get("task"):
        print(f"TASK={result['task']}")
    if result.get("line"):
        print(f"LINE={result['line']}")
    if result.get("reason"):
        print(f"REASON={result['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
