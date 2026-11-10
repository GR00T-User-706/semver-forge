import subprocess
import tempfile
import unittest
from pathlib import Path

from semver_forge import git
from semver_forge.commit import format_message, generate_summary, infer_scope, infer_type


class CommitSuggestionTests(unittest.TestCase):
    def test_fix_is_inferred_from_bug_language(self):
        commit_type, confidence = infer_type(
            ["src/example.py"],
            (
                "diff --git a/src/example.py b/src/example.py\n"
                "+raise RuntimeError('fix broken state')\n"
            ),
        )
        self.assertEqual(commit_type, "fix")
        self.assertEqual(confidence, "medium")

    def test_docs_are_high_confidence(self):
        commit_type, confidence = infer_type(["README.md"], "+document the workflow")
        self.assertEqual(commit_type, "docs")
        self.assertEqual(confidence, "high")

    def test_scope_and_message(self):
        self.assertEqual(infer_scope(["src/semver_forge/changelog.py"]), "changelog")
        self.assertEqual(
            format_message("feat", "changelog", "add synchronization"),
            "feat(changelog): add synchronization",
        )
        self.assertEqual(generate_summary("fix", "changelog"), "fix changelog behavior")


class CommitGitTests(unittest.TestCase):
    def test_history_and_diff_helpers(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subprocess.run(["git", "init", "-q", d], check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=d, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=d,
                check=True,
            )
            (root / "a.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=d, check=True)
            subprocess.run(["git", "commit", "-m", "chore: initial"], cwd=d, check=True)
            (root / "a.txt").write_text("two\n", encoding="utf-8")
            self.assertTrue(git.is_dirty(root))
            self.assertEqual(git.status_paths(root), ["a.txt"])
            self.assertIn("-one", git.diff_head(root))


if __name__ == "__main__":
    unittest.main()
