import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VersioningTests(unittest.TestCase):
    def test_version_files_match(self):
        v1 = (ROOT / "VERSION").read_text().strip()
        v2 = (ROOT / "VERSION.txt").read_text().strip()
        self.assertTrue(v1)
        self.assertEqual(v1, v2)

    def test_changelog_has_current_version_heading(self):
        version = (ROOT / "VERSION").read_text().strip()
        changelog = (ROOT / "CHANGELOG.md").read_text()

        # We accept either "## <ver>" or "## v<ver>" headings.
        self.assertTrue(
            (f"## {version}" in changelog) or (f"## v{version}" in changelog),
            f"CHANGELOG.md does not contain a heading for current version {version}",
        )


if __name__ == "__main__":
    unittest.main()
