import subprocess
import tempfile
import unittest
from pathlib import Path

from semver_forge.errors import SafetyError
from semver_forge.safety import check_release_state


class SafetyTests(unittest.TestCase):
    def test_dirty_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    d,
                    "-c",
                    "user.name=T",
                    "-c",
                    "user.email=t@invalid",
                    "commit",
                    "--allow-empty",
                    "-m",
                    "init",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (Path(d) / "untracked").write_text("x")
            with self.assertRaises(SafetyError):
                check_release_state(Path(d), {"git": {"require_clean": True}})
