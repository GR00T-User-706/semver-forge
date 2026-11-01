import tempfile
import unittest
from pathlib import Path

from semver_forge.metadata_discovery import discover_sync_targets
from semver_forge.version_sources import read_version, render_version


class RecursiveMetadataDiscoveryTests(unittest.TestCase):
    def test_discovers_nested_supported_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            (root / "packaging" / "arch").mkdir(parents=True)
            (root / "packaging" / "arch" / "PKGBUILD").write_text(
                "pkgname=sample\npkgver=1.2.3\n", encoding="utf-8"
            )
            (root / "packaging" / "termux").mkdir(parents=True)
            (root / "packaging" / "termux" / "manifest.yaml").write_text(
                "control:\n  Package: sample\n  Version: 1.2.3\n",
                encoding="utf-8",
            )
            (root / "frontend").mkdir()
            (root / "frontend" / "package.json").write_text(
                '{"name":"frontend","version":"1.2.3"}\n', encoding="utf-8"
            )

            targets = discover_sync_targets(
                root, {"type": "text", "file": "VERSION"}
            )

            self.assertEqual(
                {(item["file"], item["type"], item.get("key")) for item in targets},
                {
                    ("packaging/arch/PKGBUILD", "shell", "pkgver"),
                    ("packaging/termux/manifest.yaml", "yaml", "control.Version"),
                    ("frontend/package.json", "json", "version"),
                },
            )

    def test_yaml_update_preserves_comments_and_unrelated_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "manifest.yaml"
            original = (
                "# package manifest\n"
                "control:\n"
                "  Package: sample\n"
                "  Version: 1.2.3 # version comment\n"
                "  Architecture: all\n"
            )
            path.write_text(original, encoding="utf-8")
            source = {
                "type": "yaml",
                "file": "manifest.yaml",
                "key": "control.Version",
            }

            updated = render_version(root, source, "1.2.4")
            path.write_text(updated, encoding="utf-8")

            self.assertEqual(read_version(root, source), "1.2.4")
            self.assertIn("# package manifest", updated)
            self.assertIn("# version comment", updated)
            self.assertIn("Architecture: all", updated)
            self.assertIn("Package: sample", updated)

    def test_ambiguous_yaml_version_fields_are_not_guessed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            (root / "manifest.yaml").write_text(
                "version: 1.2.3\ncontrol:\n  Version: 1.2.3\n",
                encoding="utf-8",
            )

            self.assertEqual(
                discover_sync_targets(root, {"type": "text", "file": "VERSION"}),
                [],
            )

    def test_dependency_and_build_directories_are_pruned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".venv" / "lib").mkdir(parents=True)
            (root / ".venv" / "lib" / "package.json").write_text(
                '{"version":"1.2.3"}\n', encoding="utf-8"
            )
            (root / "src").mkdir()
            (root / "src" / "VERSION").write_text("1.2.3\n", encoding="utf-8")

            targets = discover_sync_targets(root)

            self.assertEqual(
                [item["file"] for item in targets],
                ["src/VERSION"],
            )


if __name__ == "__main__":
    unittest.main()
