import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from semver_forge.cli import main
from semver_forge.errors import ConfigError
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

            targets = discover_sync_targets(root, {"type": "text", "file": "VERSION"})

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

    def test_yaml_invalid_document_and_missing_key_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "manifest.yaml"
            source = {
                "type": "yaml",
                "file": "manifest.yaml",
                "key": "control.Version",
            }
            path.write_text("control: [", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "invalid YAML"):
                read_version(root, source)

            path.write_text("control:\n  Package: sample\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "key path does not exist"):
                render_version(root, source, "1.2.4")

            path.write_text("control: scalar\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "key path is not a mapping"):
                render_version(root, source, "1.2.4")

    def test_yaml_read_errors_abort_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.yaml").write_text("version: 1.2.3\n", encoding="utf-8")

            with patch.object(
                Path,
                "read_text",
                side_effect=PermissionError("permission denied"),
            ):
                with self.assertRaisesRegex(PermissionError, "permission denied"):
                    discover_sync_targets(root)

    def test_yaml_sync_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "manifest.yaml"
            path.write_text(
                "control:\n  Version: 1.2.3 # retain comment\n",
                encoding="utf-8",
            )
            source = {
                "type": "yaml",
                "file": "manifest.yaml",
                "key": "control.Version",
            }

            first = render_version(root, source, "1.2.4")
            path.write_text(first, encoding="utf-8")
            second = render_version(root, source, "1.2.4")

            self.assertEqual(first, second)

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

    def test_sync_discover_merges_configured_and_discovered_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            configured = root / "packaging" / "configured-version.txt"
            configured.parent.mkdir(parents=True)
            configured.write_text("1.2.2\n", encoding="utf-8")
            (root / ".semver-forge.toml").write_text(
                '[version]\ninitial = "1.2.3"\n'
                'source = { type = "text", file = "VERSION" }\n\n'
                "[sync]\n"
                'targets = [{ type = "text", file = '
                '"packaging/configured-version.txt" }]\n',
                encoding="utf-8",
            )
            manifest = root / "packaging" / "termux" / "manifest.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                "control:\n  Package: sample\n  Version: 1.2.2\n",
                encoding="utf-8",
            )

            dry_output = io.StringIO()
            with contextlib.redirect_stdout(dry_output):
                dry_status = main(
                    ["--project", str(root), "--json", "sync", "--discover", "--dry-run"]
                )

            preview = json.loads(dry_output.getvalue())
            self.assertEqual(dry_status, 0)
            expected_target = {
                "type": "yaml",
                "file": "packaging/termux/manifest.yaml",
                "key": "control.Version",
            }
            self.assertEqual(preview["discovered_targets"], [expected_target])
            self.assertTrue(preview["configuration"]["changed"])
            self.assertIn(expected_target, preview["configuration"]["proposed_targets"])
            sync_files = {
                Path(item["file"]).relative_to(root).as_posix()
                for item in preview["synchronization"]
            }
            self.assertEqual(
                sync_files,
                {"VERSION", "packaging/configured-version.txt", "packaging/termux/manifest.yaml"},
            )
            self.assertEqual(sum(item["changed"] for item in preview["synchronization"]), 2)
            self.assertEqual(configured.read_text(encoding="utf-8"), "1.2.2\n")
            self.assertIn("Version: 1.2.2", manifest.read_text(encoding="utf-8"))
            self.assertNotIn(
                "packaging/termux/manifest.yaml",
                (root / ".semver-forge.toml").read_text(encoding="utf-8"),
            )

            run_output = io.StringIO()
            with contextlib.redirect_stdout(run_output):
                run_status = main(["--project", str(root), "--json", "sync", "--discover"])

            self.assertEqual(run_status, 0)
            self.assertEqual(configured.read_text(encoding="utf-8"), "1.2.3\n")
            self.assertIn("Version: 1.2.3", manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                (root / ".semver-forge.toml").read_text(encoding="utf-8").count("targets ="),
                1,
            )
            self.assertIn(
                "packaging/termux/manifest.yaml",
                (root / ".semver-forge.toml").read_text(encoding="utf-8"),
            )

    def test_custom_key_discovers_arbitrary_text_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            path = root / "src" / "version.py"
            path.parent.mkdir()
            path.write_text('__version__ = "1.2.2"\n', encoding="utf-8")

            targets = discover_sync_targets(
                root,
                {"type": "text", "file": "VERSION"},
                custom_keys=["__version__"],
            )

            self.assertEqual(
                [item for item in targets if item["file"] == "src/version.py"],
                [{"type": "shell", "file": "src/version.py", "key": "__version__"}],
            )

    def test_custom_key_ignores_ambiguous_assignments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            path = root / "version.py"
            path.write_text(
                '__version__ = "1.2.2"\n__version__ = "1.2.3"\n',
                encoding="utf-8",
            )

            targets = discover_sync_targets(
                root,
                {"type": "text", "file": "VERSION"},
                custom_keys=["__version__"],
            )

            self.assertEqual(targets, [])

    def test_sync_discover_uses_configured_custom_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            custom = root / "src" / "version.py"
            custom.parent.mkdir()
            custom.write_text('SME_VERSION = "1.2.2"\n', encoding="utf-8")
            (root / ".semver-forge.toml").write_text(
                '[version]\ninitial = "1.2.3"\n'
                'source = { type = "text", file = "VERSION" }\n\n'
                '[sync]\n'
                'targets = []\n'
                'discovery_keys = ["SME_VERSION"]\n',
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["--project", str(root), "--json", "sync", "--discover"])

            self.assertEqual(status, 0)
            self.assertIn(
                "src/version.py",
                (root / ".semver-forge.toml").read_text(encoding="utf-8"),
            )
            self.assertIn(
                'SME_VERSION = "1.2.3"',
                custom.read_text(encoding="utf-8"),
            )

    def test_discovers_nested_debian_control_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "packaging" / "debian").mkdir(parents=True)
            (root / "packaging" / "debian" / "control").write_text(
                "Source: sample\nVersion: 1.2.3\nSection: utils\n",
                encoding="utf-8",
            )

            targets = discover_sync_targets(root)

            self.assertEqual(
                targets,
                [{"type": "debian", "file": "packaging/debian/control"}],
            )

    def test_unreadable_directory_aborts_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def fail_walk(_root, *, followlinks, onerror):
                onerror(PermissionError("permission denied"))
                return iter(())

            with patch("semver_forge.metadata_discovery.os.walk", side_effect=fail_walk):
                with self.assertRaisesRegex(PermissionError, "permission denied"):
                    discover_sync_targets(root)

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
