import json
import tempfile
import unittest
from pathlib import Path

from semver_forge.operation_log import record


class OperationLogTests(unittest.TestCase):
    def test_records_structured_event(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "semver-forge.log"
            record("info", "test.action", "completed", path=path)
            event = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(event["level"], "INFO")
            self.assertEqual(event["action"], "test.action")
            self.assertEqual(event["outcome"], "completed")

    def test_log_is_bounded_and_keeps_newest_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "semver-forge.log"
            record("info", "first", "completed", path=path, max_bytes=180)
            record("info", "second", "completed", path=path, max_bytes=180)
            record("info", "third", "completed", path=path, max_bytes=180)
            self.assertLessEqual(path.stat().st_size, 180)
            content = path.read_text(encoding="utf-8")
            self.assertIn('"action":"third"', content)


if __name__ == "__main__":
    unittest.main()
