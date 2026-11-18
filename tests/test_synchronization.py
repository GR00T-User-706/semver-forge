import tempfile
import unittest
from pathlib import Path

from semver_forge.errors import ConfigError
from semver_forge.synchronization import sync


class SyncTests(unittest.TestCase):
    def test_dry_run_immutable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "VERSION"
            path.write_text("1.0.0\n", encoding="utf-8")
            cfg = {
                "version": {"source": {"type": "text", "file": "VERSION"}},
                "sync": {"targets": []},
            }
            sync(directory, cfg, "1.1.0", True)
            self.assertEqual(path.read_text(encoding="utf-8"), "1.0.0\n")

    def test_sync(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "VERSION"
            path.write_text("1.0.0\n", encoding="utf-8")
            cfg = {
                "version": {"source": {"type": "text", "file": "VERSION"}},
                "sync": {"targets": []},
            }
            sync(directory, cfg, "1.1.0")
            self.assertEqual(path.read_text(encoding="utf-8"), "1.1.0\n")

    def test_duplicate_canonical_target_is_synchronized_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "VERSION"
            path.write_text("1.0.0\n", encoding="utf-8")
            source = {"type": "text", "file": "VERSION"}
            cfg = {
                "version": {"source": source},
                "sync": {"targets": [source]},
            }

            result = sync(directory, cfg, "1.1.0")

            self.assertEqual(len(result), 1)
            self.assertEqual(path.read_text(encoding="utf-8"), "1.1.0\n")

    def test_conflicting_definitions_for_same_file_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "VERSION"
            path.write_text("1.0.0\n", encoding="utf-8")
            cfg = {
                "version": {"source": {"type": "text", "file": "VERSION"}},
                "sync": {"targets": [{"type": "yaml", "file": "VERSION", "key": "version"}]},
            }

            with self.assertRaisesRegex(ConfigError, "conflicting synchronization definitions"):
                sync(directory, cfg, "1.1.0")

            self.assertEqual(path.read_text(encoding="utf-8"), "1.0.0\n")

    def test_text_pattern_updates_embedded_version_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            path = root / "README.md"
            path.write_text(
                "Current release: 1.2.3\nDownload: sample-1.2.3.tar.gz\n",
                encoding="utf-8",
            )
            cfg = {
                "version": {"source": {"type": "text", "file": "VERSION"}},
                "sync": {
                    "targets": [
                        {
                            "type": "text-pattern",
                            "file": "README.md",
                            "pattern": "Current release: {version}",
                        },
                        {
                            "type": "text-pattern",
                            "file": "README.md",
                            "pattern": "sample-{version}.tar.gz",
                        },
                    ]
                },
            }

            result = sync(directory, cfg, "1.2.4")

            self.assertEqual(len(result), 3)
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "Current release: 1.2.4\nDownload: sample-1.2.4.tar.gz\n",
            )

    def test_text_pattern_updates_all_matching_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            path = root / "man.1"
            path.write_text(
                '.TH SAMPLE 1 "2026-11-18" "sample 1.2.3" "User Commands"\n'
                ".SH NAME\nsample 1.2.3\n",
                encoding="utf-8",
            )
            cfg = {
                "version": {"source": {"type": "text", "file": "VERSION"}},
                "sync": {
                    "targets": [
                        {
                            "type": "text-pattern",
                            "file": "man.1",
                            "pattern": "sample {version}",
                        },
                    ]
                },
            }

            sync(directory, cfg, "1.2.4")

            self.assertEqual(
                path.read_text(encoding="utf-8"),
                '.TH SAMPLE 1 "2026-11-18" "sample 1.2.4" "User Commands"\n'
                ".SH NAME\nsample 1.2.4\n",
            )

    def test_text_pattern_rejects_mixed_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            path = root / "README.md"
            path.write_text(
                "Current release: 1.2.3\nCurrent release: 1.2.2\n",
                encoding="utf-8",
            )
            cfg = {
                "version": {"source": {"type": "text", "file": "VERSION"}},
                "sync": {
                    "targets": [
                        {
                            "type": "text-pattern",
                            "file": "README.md",
                            "pattern": "Current release: {version}",
                        },
                    ]
                },
            }

            with self.assertRaisesRegex(ConfigError, "multiple different version values"):
                sync(directory, cfg, "1.2.4")

            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "Current release: 1.2.3\nCurrent release: 1.2.2\n",
            )

    def test_rejects_invalid_version_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "VERSION"
            path.write_text("1.2.3\n", encoding="utf-8")
            cfg = {
                "version": {"source": {"type": "text", "file": "VERSION"}},
                "sync": {"targets": []},
            }
            with self.assertRaises(ConfigError):
                sync(directory, cfg, "not-a-version")
            self.assertEqual(path.read_text(encoding="utf-8"), "1.2.3\n")


if __name__ == "__main__":
    unittest.main()
