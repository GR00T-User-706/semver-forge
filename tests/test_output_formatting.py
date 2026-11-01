import unittest

from semver_forge.cli import _format_output


class OutputFormattingTests(unittest.TestCase):
    def test_formats_list_of_result_dictionaries(self):
        result = [
            {
                "file": "VERSION",
                "old_version": "3.2.1",
                "new_version": "3.2.2",
                "changed": True,
            }
        ]

        self.assertEqual(
            _format_output(result),
            "-\n  file: VERSION\n  old_version: 3.2.1\n  new_version: 3.2.2\n  changed: True",
        )

    def test_formats_nested_lists_without_python_repr(self):
        result = {
            "latest_tag": "v3.2.0",
            "commits": [{"hash": "abc123", "subject": "fix: example"}],
        }

        self.assertEqual(
            _format_output(result),
            "latest_tag: v3.2.0\ncommits:\n  -\n    hash: abc123\n    subject: fix: example",
        )

    def test_formats_empty_collections(self):
        self.assertEqual(_format_output({"items": [], "metadata": {}}), "items: []\nmetadata: {}")


if __name__ == "__main__":
    unittest.main()
