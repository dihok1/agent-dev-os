"""Contract tests for product-context continuity across Agent Dev OS prompts."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class ProductContextTests(unittest.TestCase):
    def test_proposal_template_contains_measurable_product_contract(self) -> None:
        proposal = read("changes/_template/proposal.md")
        for field in ("User / decision maker", "Job to be done", "Current workflow", "Pain or decision risk", "Why now", "Desired behavior change", "Baseline", "Target", "Measurement window", "Guardrails"):
            self.assertIn(field, proposal)

    def test_execution_loads_and_traces_product_contract(self) -> None:
        execute = read(".cursor/skills/execute/SKILL.md")
        self.assertIn("Product Contract from `proposal.md`", execute)
        self.assertIn("Product preflight", execute)
        self.assertIn("enabler for Tn", execute)

    def test_engineer_and_tasks_require_product_trace(self) -> None:
        engineer = read(".cursor/agents/engineer.md")
        tasks = read("changes/_template/tasks.md")
        self.assertIn("Product trace", engineer)
        for field in ("Product outcome", "Evidence", "Trace"):
            self.assertIn(field, tasks)

    def test_checker_reviews_product_fit_before_technical_risk(self) -> None:
        checker = read(".cursor/agents/checker.md")
        self.assertLess(checker.index("PRODUCT FIT"), checker.index("TECHNICAL CRITICAL"))
        self.assertIn("proposal.md", checker)

    def test_pm_supports_non_startup_work(self) -> None:
        pm = read(".cursor/agents/pm.md")
        for context in ("Operator", "Decision Support", "Platform", "Builder"):
            self.assertIn(context, pm)
        self.assertIn("Do not manufacture revenue", pm)

    def test_architecture_depth_is_risk_proportional(self) -> None:
        architect = read(".cursor/agents/architect.md")
        for tier in ("Low", "Medium", "High"):
            self.assertIn(tier, architect)
        self.assertIn("Do not invent alternatives for Low-risk work", architect)


if __name__ == "__main__":
    unittest.main()
