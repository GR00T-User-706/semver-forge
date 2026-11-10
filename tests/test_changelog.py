import tempfile
import unittest
from pathlib import Path

from semver_forge.changelog import sync_unreleased, update_changelog


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

    def test_existing_version_section_is_refreshed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_text(
                "# Changelog\n\n## [1.1.0]\n\n- old entry\n\n## [1.0.0]\n\n- prior release\n",
                encoding="utf-8",
            )
            result = update_changelog(path, "1.1.0", "- updated entry\n")
            self.assertIn("- updated entry", result)
            self.assertNotIn("- old entry", result)
            self.assertIn("- prior release", result)

    def test_duplicate_version_is_rejected_without_modifying_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            original = (
                "# Changelog\n\n## [1.1.0]\n\n- first entry\n\n## [1.1.0]\n\n- duplicate entry\n"
            )
            path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate headings"):
                update_changelog(path, "1.1.0", "- replacement")

            self.assertEqual(path.read_text(encoding="utf-8"), original)

    
    def test_sync_unreleased_detects_and_writes_missing_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_text(
                "# Changelog\\n\\n## [Unreleased]\\n\\n### Features\\n\\n"
                "- existing feature (abc1234)\\n",
                encoding="utf-8",
            )
            commits = [
                {
                    "hash": "abc123456789",
                    "message": "feat: existing feature",
                    "subject": "feat: existing feature",
                    "body": "",
                },
                {
                    "hash": "def567812345",
                    "message": "fix: correct broken behavior",
                    "subject": "fix: correct broken behavior",
                    "body": "",
                },
            ]
            result = sync_unreleased(path, commits)
            self.assertTrue(result["diverged"])
            self.assertTrue(result["changed"])
            self.assertEqual(result["missing_count"], 1)
            self.assertIn("correct broken behavior (def56781)", path.read_text(encoding="utf-8"))

    def test_sync_unreleased_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_text("# Changelog\\n", encoding="utf-8")
            commits = [
                {
                    "hash": "1234567890ab",
                    "message": "feat: add feature",
                    "subject": "feat: add feature",
                    "body": "",
                }
            ]
            result = sync_unreleased(path, commits, dry_run=True)
            self.assertTrue(result["diverged"])
            self.assertFalse(result["changed"])
            self.assertIn("add feature", result["notes"])
            self.assertEqual(path.read_text(encoding="utf-8"), "# Changelog\\n")


if __name__ == "__main__":
    unittest.main()
