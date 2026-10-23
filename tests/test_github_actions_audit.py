"""Offline safety checks for Actions inventory pagination (no GitHub calls)."""
import importlib.util
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location(
    "genesis_actions_audit_test", ROOT / "audit-github-actions-surfaces.py"
)
actions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(actions)


class ActionsAuditTests(TestCase):
    def test_one_page_matches_total(self):
        batch = {"total_count": 2, "workflow_runs": [{"id": 1}, {"id": 2}]}
        with patch.object(actions.base, "gh_get", return_value=batch):
            self.assertEqual(
                len(actions.safe_counted_pages("repos/Gyliardson/genesis/actions/runs", "workflow_runs", {})), 2
            )

    def test_incomplete_run_inventory_fails_closed(self):
        batch = {"total_count": 3, "workflow_runs": [{"id": 1}, {"id": 2}]}
        with (
            patch.object(actions.base, "gh_get", return_value=batch),
            self.assertRaises(actions.base.AuditError),
        ):
            actions.safe_counted_pages("repos/Gyliardson/genesis/actions/runs", "workflow_runs", {})

    def test_invalid_batch_fails_closed(self):
        batch = {"total_count": 1, "workflow_runs": "untrusted"}
        with (
            patch.object(actions.base, "gh_get", return_value=batch),
            self.assertRaises(actions.base.AuditError),
        ):
            actions.safe_counted_pages("repos/Gyliardson/genesis/actions/runs", "workflow_runs", {})


if __name__ == "__main__":
    main()
