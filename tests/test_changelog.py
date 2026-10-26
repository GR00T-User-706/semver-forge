import tempfile
import unittest
from pathlib import Path

from semver_forge.changelog import update_changelog


class ChangelogUpdateTests(unittest.TestCase):
    def test_update_prepends_version_and_preserves_existing_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            original = "# Changelog\n\n## [1.0.0]\n\n### Features\n\n- old feature\n"
            path.write_text(original, encoding="utf-8")

            result = update_changelog(path, "1.1.0", "### Fixes\n\n- corrected bug\n")

            self.assertIn("## [1.1.0]", result)
            self.assertIn("- corrected bug", result)
            self.assertIn("## [1.0.0]", result)
            self.assertEqual(path.read_text(encoding="utf-8"), result)
            self.assertLess(result.index("## [1.1.0]"), result.index("## [1.0.0]"))

    def test_dry_run_does_not_write_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            original = "# Changelog\n\n## [1.0.0]\n\n- old entry\n"
            path.write_text(original, encoding="utf-8")

            result = update_changelog(path, "1.1.0", "- new entry", dry_run=True)

            self.assertIn("## [1.1.0]", result)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_duplicate_version_is_rejected_without_modifying_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            original = "# Changelog\n\n## [1.1.0]\n\n- existing entry\n"
            path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "already contains version 1.1.0"):
                update_changelog(path, "1.1.0", "- duplicate entry")

            self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
