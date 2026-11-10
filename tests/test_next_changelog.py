import subprocess
import tempfile
import unittest
from pathlib import Path

from semver_forge.cli import main


def git(root, *args):
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )


class NextChangelogTests(unittest.TestCase):
    def test_next_writes_release_notes_to_changelog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init")
            git(root, "config", "user.name", "Test User")
            git(root, "config", "user.email", "test@example.invalid")

            (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
            (root / ".semver-forge.toml").write_text(
                """[project]
name = "example"

[version]
initial = "1.0.0"
source = { type = "text", file = "VERSION" }

[git]
tag_prefix = "v"
baseline = ""
unknown_commit = "ignore"
merge_commits = "ignore"

[commits]
breaking_changes = true
ignored_types = ["docs", "style", "refactor", "test", "build", "ci", "chore"]
unknown = "ignore"

[commits.types]
feat = "minor"
fix = "patch"
perf = "patch"
revert = "patch"

[sync]
targets = []
""",
                encoding="utf-8",
            )
            git(root, "add", "VERSION", ".semver-forge.toml")
            git(root, "commit", "-m", "chore: initialize test project")
            baseline = git(root, "rev-parse", "HEAD").stdout.strip()

            config = (root / ".semver-forge.toml").read_text(encoding="utf-8")
            (root / ".semver-forge.toml").write_text(
                config.replace('baseline = ""', f'baseline = "{baseline}"'),
                encoding="utf-8",
            )
            git(root, "add", ".semver-forge.toml")
            git(root, "commit", "-m", "test: set version boundary")

            (root / "feature.txt").write_text("feature\n", encoding="utf-8")
            git(root, "add", "feature.txt")
            git(root, "commit", "-m", "feat: add feature")

            self.assertEqual(main(["--project", str(root), "next", "--yes"]), 0)
            self.assertEqual((root / "VERSION").read_text(encoding="utf-8").strip(), "1.1.0")
            changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("## [1.1.0]", changelog)
            self.assertIn("add feature", changelog)


if __name__ == "__main__":
    unittest.main()
