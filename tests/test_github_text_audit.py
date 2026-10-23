"""Offline regression tests for secure GitHub text-surface audit outputs."""
import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit-github-text-surfaces.py"
spec = importlib.util.spec_from_file_location("genesis_gh_text_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class GithubTextAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="genesis-gh-surface-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = self.root / "case"
        audit.private_dir(self.case)
        self.corpus = self.case / "records"
        audit.private_dir(self.corpus)
        audit.private_write(self.corpus / "content.txt", "SYNTHETIC_TEST_ONLY")

    def test_private_write_creates_0600(self):
        file = self.case / "created.private"
        audit.private_write(file, "SYNTHETIC")
        self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)
        with self.assertRaises(FileExistsError):
            audit.private_write(file, "SHOULD_NOT_OVERWRITE")
        self.assertEqual(file.read_text(), "SYNTHETIC")

    def test_report_replacement_is_normalized_and_no_outputs_relaxed(self):
        # Simulate a scanner that unlinks/recreates the report with 0666,
        # despite the initial private file precreation. The parent remains 0700.
        fake = self.root / "fake-scanner"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys, json\n"
            "path = sys.argv[sys.argv.index('--report-path') + 1]\n"
            "os.unlink(path)\n"
            "fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)\n"
            "with os.fdopen(fd, 'w') as out: json.dump([], out)\n"
        )
        fake.chmod(0o700)
        old = audit.SCANNER
        audit.SCANNER = fake
        self.addCleanup(setattr, audit, "SCANNER", old)
        state, count, findings = audit.scan_records(
            self.case, self.corpus, "test", {"PATH": os.environ["PATH"]}
        )
        self.assertEqual((state, count, findings), ("PASS", 0, []))
        for suffix in ("ignore.private", "report.private.json", "stdout.private", "stderr.private"):
            file = self.case / ("test." + suffix)
            self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600, file.name)

    def test_nonprivate_parent_is_rejected(self):
        self.case.chmod(0o755)
        old = audit.SCANNER
        fake = self.root / "fake"
        fake.write_text("#!/bin/sh\nexit 0\n")
        fake.chmod(0o700)
        audit.SCANNER = fake
        self.addCleanup(setattr, audit, "SCANNER", old)
        with self.assertRaisesRegex(audit.AuditError, "directory permissions invalid"):
            audit.scan_records(self.case, self.corpus, "negative", {"PATH": os.environ["PATH"]})


if __name__ == "__main__":
    unittest.main()
