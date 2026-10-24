import tempfile
import subprocess
import unittest
from pathlib import Path

from semver_forge.vcs import backend_for


class VCSTests(unittest.TestCase):
    def test_selects_git_backend_for_git_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(["git", "init", "-q", directory], check=True)
            backend = backend_for(directory)
            self.assertEqual(backend.name, "git")
            self.assertEqual(backend.root(directory), Path(directory).resolve())

    def test_rejects_directory_without_supported_vcs(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                backend_for(directory)


if __name__ == "__main__":
    unittest.main()
