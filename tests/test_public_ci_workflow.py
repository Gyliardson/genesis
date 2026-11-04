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


    def test_ci_uses_hashes_and_offline_build(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("--require-hashes", workflow)
        self.assertIn("--only-binary=:all:", workflow)
        self.assertIn("run: |\n          python -m pip --isolated install", workflow)
        self.assertIn("--no-build-isolation", workflow)
        self.assertIn("--no-index --no-deps", workflow)
        self.assertNotIn('pip install -e ".[dev]"', workflow)

    def test_ci_lock_contains_ten_exact_hashes(self):
        import re
        lock = WORKFLOW.parents[2] / "requirements/ci-py311-ubuntu24.04-x86_64.txt"
        lines = [x for x in lock.read_text(encoding="utf-8").splitlines()
                 if x.strip() and not x.startswith("#")]
        self.assertEqual(len(lines), 10)
        self.assertTrue(all(re.fullmatch(
            r"[A-Za-z0-9_.-]+==[0-9][A-Za-z0-9_.-]* --hash=sha256:[0-9a-f]{64}", x
        ) for x in lines))
        self.assertTrue(any(x.startswith("hatchling==") for x in lines))


if __name__ == "__main__":
    unittest.main()
