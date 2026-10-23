"""Static regression checks for the staged public CI workflow contract."""

import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


class PublicCIWorkflowContractTests(unittest.TestCase):
    def test_public_manual_dispatch_preserves_unprivileged_paths(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "on:\n"
            "  # Allows a first trusted CI run after authorized private-to-public conversion.\n"
            "  # Visibility conversion alone does not emit push/pull_request events.\n"
            "  workflow_dispatch:\n"
            "  push:\n"
            "    branches: [main]\n"
            "  pull_request:\n",
            workflow,
        )
        self.assertNotIn("pull_request_target:", workflow)
        self.assertIn("permissions:\n  contents: read\n", workflow)
        self.assertIn("runs-on: ubuntu-24.04", workflow)
        self.assertIn('python-version: "3.11"', workflow)
        self.assertIn("timeout-minutes: 15", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("run: ruff check .", workflow)
        self.assertIn("run: pytest -q", workflow)


if __name__ == "__main__":
    unittest.main()
