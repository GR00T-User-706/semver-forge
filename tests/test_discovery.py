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
                '[project]\nname = "sample-app"\ndescription = "A sample application"\nversion = "2.4.1"\n\n'
                '[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n',
                encoding="utf-8",
            )
            (root / "VERSION").write_text("2.4.1\n", encoding="utf-8")
            (root / "tests").mkdir()
            result = discover(root)
            self.assertEqual(result["project"]["name"], "sample-app")
            self.assertEqual(result["project"]["description"], "A sample application")
            self.assertEqual(result["version"]["initial"], "2.4.1")
            self.assertEqual(result["version"]["source"], {
                "type": "toml", "file": "pyproject.toml", "key": "project.version"
            })
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
            self.assertIn('# keep this comment', updated)
            self.assertIn('description = "unchanged"', updated)


if __name__ == "__main__":
    unittest.main()
