import subprocess
import tempfile
import unittest
from pathlib import Path

from semver_forge.release import plan


class ReleaseTests(unittest.TestCase):
    def test_plan_from_history(self):
        with tempfile.TemporaryDirectory() as d:

            def run(*a):
                return subprocess.run(
                    a, cwd=d, check=True, capture_output=True
                )

            run("git", "init", "-q")
            run("git", "config", "user.name", "Test")
            run("git", "config", "user.email", "test@example.invalid")
            (Path(d) / "VERSION").write_text("1.0.0\n")
            run("git", "add", "VERSION")
            run("git", "commit", "-m", "chore: initial")
            run("git", "tag", "v1.0.0")
            (Path(d) / "a").write_text("x")
            run("git", "add", "a")
            run("git", "commit", "-m", "feat: new thing")
            cfg = {
                "version": {"source": {"type": "text", "file": "VERSION"}},
                "git": {"tag_prefix": "v", "baseline": None, "unknown_commit": "ignore"},
                "commits": {
                    "breaking_changes": True,
                    "ignored_types": ["docs", "chore"],
                    "types": {"feat": "minor", "fix": "patch"},
                    "unknown": "ignore",
                },
            }
            p = plan(Path(d), cfg)
            self.assertEqual(str(p["next"]), "1.1.0")
