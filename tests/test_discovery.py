import tempfile
import unittest
from pathlib import Path

from semver_forge.discovery import discover, render_config
from semver_forge.version_sources import read_version, render_version


class DiscoveryTests(unittest.TestCase):
    def test_python_metadata_and_version_are_discovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text(
                (
                    '[project]\nname = "sample-app"\n'
                    'description = "A sample application"\nversion = "2.4.1"\n\n'
                    '[build-system]\nrequires = ["setuptools"]\n'
                    'build-backend = "setuptools.build_meta"\n'
                ),
                encoding="utf-8",
            )
            (root / "VERSION").write_text("2.4.1\n", encoding="utf-8")
            (root / "tests").mkdir()
            result = discover(root)
            self.assertEqual(result["project"]["name"], "sample-app")
            self.assertEqual(result["project"]["description"], "A sample application")
            self.assertEqual(result["version"]["initial"], "2.4.1")
            self.assertEqual(
                result["version"]["source"],
                {"type": "toml", "file": "pyproject.toml", "key": "project.version"},
            )
            self.assertEqual(result["sync_targets"], [{"type": "text", "file": "VERSION"}])
            self.assertEqual(result["test_commands"], ["python -m pytest"])
            self.assertEqual(result["build_commands"], ["python -m build"])
            self.assertEqual(result["artifact_paths"], ["dist/*"])
            self.assertIn('name = "sample-app"', render_config(result))

    def test_conflicting_versions_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text(
                '[project]\nname = "sample-app"\nversion = "2.4.1"\n',
                encoding="utf-8",
            )
            (root / "VERSION").write_text("2.4.2\n", encoding="utf-8")
            result = discover(root)
            self.assertEqual(result["version_status"], "conflict")
            self.assertEqual(
                {item["version"] for item in result["version_conflicts"]},
                {"2.4.1", "2.4.2"},
            )

    def test_empty_project_uses_safe_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = discover(root)
            self.assertEqual(result["project"]["name"], root.name)
            self.assertEqual(result["version"]["initial"], "0.1.0")
            self.assertEqual(result["version"]["source"], {"type": "text", "file": "VERSION"})
            self.assertEqual(result["sync_targets"], [])
            self.assertEqual(result["test_commands"], [])
            self.assertEqual(result["build_commands"], [])
            self.assertEqual(result["artifact_paths"], [])

    def test_toml_version_update_preserves_other_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "pyproject.toml"
            original = (
                '[project]\nname = "sample-app"\nversion = "1.2.3" # keep this comment\n'
                'description = "unchanged"\n'
            )
            path.write_text(original, encoding="utf-8")
            source = {"type": "toml", "file": "pyproject.toml", "key": "project.version"}
            updated = render_version(root, source, "1.2.4")
            path.write_text(updated, encoding="utf-8")
            self.assertEqual(read_version(root, source), "1.2.4")
            self.assertIn("# keep this comment", updated)
            self.assertIn('description = "unchanged"', updated)

    def test_later_manifest_fills_missing_python_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text(
                "[build-system]\nrequires = []\n", encoding="utf-8"
            )
            (root / "package.json").write_text(
                '{"name": "node-project", "description": "Node description"}',
                encoding="utf-8",
            )
            result = discover(root)
            self.assertEqual(result["project"]["name"], "node-project")
            self.assertEqual(result["project"]["description"], "Node description")

    def test_debian_changelog_version_is_discovered_and_synchronized(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            changelog = root / "debian" / "changelog"
            changelog.parent.mkdir()
            original = "sample-app (2.4.0-1) unstable; urgency=medium\n\n  * Initial release\n"
            changelog.write_text(original, encoding="utf-8")
            result = discover(root)
            self.assertEqual(result["version"]["initial"], "2.4.0-1")
            self.assertEqual(result["version"]["source"]["type"], "debian-changelog")
            updated = render_version(root, result["version"]["source"], "2.4.1-1")
            self.assertIn("sample-app (2.4.1-1) unstable; urgency=medium", updated)
            changelog.write_text(updated, encoding="utf-8")
            self.assertEqual(
                read_version(root, result["version"]["source"]),
                "2.4.1-1",
            )

    def test_toml_table_header_with_trailing_comment_is_updated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "pyproject.toml"
            original = (
                "[project] # project metadata\n"
                'name = "sample-app"\n'
                'version = "1.2.3" # keep version comment\n'
                "[tool.example] # unrelated table\n"
                "value = true\n"
            )
            path.write_text(original, encoding="utf-8")
            source = {"type": "toml", "file": "pyproject.toml", "key": "project.version"}
            updated = render_version(root, source, "1.2.4")
            path.write_text(updated, encoding="utf-8")
            self.assertEqual(read_version(root, source), "1.2.4")
            self.assertIn("[project] # project metadata", updated)
            self.assertIn('version = "1.2.4" # keep version comment', updated)
            self.assertIn("[tool.example] # unrelated table", updated)


if __name__ == "__main__":
    unittest.main()
