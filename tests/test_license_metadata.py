"""Minimal release-gate regressions for the Apache-2.0 code-license decision."""

import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LicenseMetadataTests(unittest.TestCase):
    def test_project_declares_approved_spdx_license(self):
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(metadata["project"]["license"], "Apache-2.0")

    def test_full_apache_v2_terms_and_appendix_present(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertGreater(len(license_text), 9500)
        for marker in (
            "Apache License",
            "Version 2.0, January 2004",
            "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION",
            "4. Redistribution.",
            "9. Accepting Warranty or Additional Liability.",
            "APPENDIX: How to apply the Apache License to your work",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, license_text)

    def test_contributor_and_readme_describe_code_license_and_limits(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        contribution = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        for document in (readme, contribution):
            with self.subTest(document=document[:30]):
                self.assertIn("Apache-2.0", document)
                self.assertIn("[LICENSE](LICENSE)", document)
                self.assertNotIn("LicenseRef-Proprietary", document)


if __name__ == "__main__":
    unittest.main()
