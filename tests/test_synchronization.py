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
