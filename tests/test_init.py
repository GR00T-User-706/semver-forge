import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InitTests(unittest.TestCase):
    def run_cli(self, project, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        env["XDG_STATE_HOME"] = str(Path(project) / ".state")
        return subprocess.run(
            [sys.executable, "-m", "semver_forge", "--project", str(project), *args],
            cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=20,
        )

    def test_init_works_without_git(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "plain"
            project.mkdir()
            result = self.run_cli(project, "init", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / ".semver-forge.toml").is_file())
            self.assertEqual((project / "VERSION").read_text(), "0.1.0\n")

    def test_git_init_commits_only_generated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            subprocess.run(["git", "-C", str(project), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(project), "config", "user.email", "test@example.invalid"], check=True)
            (project / "VERSION").write_text("3.1.0\n")
            result = self.run_cli(project, "init", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((project / "VERSION").read_text(), "3.1.0\n")
            committed = subprocess.run(
                ["git", "-C", str(project), "show", "--pretty=format:", "--name-only", "HEAD"],
                check=True, text=True, stdout=subprocess.PIPE,
            ).stdout.splitlines()
            self.assertEqual(set(committed), {".semver-forge.toml"})

    def test_init_derives_project_metadata_and_version(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pyproject.toml").write_text(
                '[project]\nname = "derived-name"\ndescription = "Derived description"\nversion = "4.5.6"\n',
                encoding="utf-8",
            )
            result = self.run_cli(project, "init", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            config = (project / ".semver-forge.toml").read_text(encoding="utf-8")
            self.assertIn('name = "derived-name"', config)
            self.assertIn('description = "Derived description"', config)
            self.assertIn('initial = "4.5.6"', config)
            self.assertIn('file = "pyproject.toml"', config)
            self.assertFalse((project / "VERSION").exists())

    def test_init_refuses_conflicting_version_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pyproject.toml").write_text(
                '[project]\nname = "derived-name"\nversion = "1.2.3"\n',
                encoding="utf-8",
            )
            (project / "VERSION").write_text("1.2.4\n", encoding="utf-8")
            result = self.run_cli(project, "init", "--json")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conflicting existing version sources", result.stderr)
            self.assertFalse((project / ".semver-forge.toml").exists())

    def test_existing_configuration_requires_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            config = project / ".semver-forge.toml"
            config.write_text("preserve me")
            result = self.run_cli(project, "init")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_text(), "preserve me")


if __name__ == "__main__":
    unittest.main()
