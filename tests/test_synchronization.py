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
