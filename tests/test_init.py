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
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=20,
        )

    def test_init_reuses_legacy_configuration_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            legacy = project / "semver-forge.toml"
            legacy.write_text('[version]\ninitial = "1.0.0"\n')
            result = self.run_cli(project, "init", "--yes")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(legacy.is_file())
            self.assertFalse((project / ".semver-forge.toml").exists())

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
            subprocess.run(
                ["git", "-C", str(project), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            (project / "VERSION").write_text("3.1.0\n")
            result = self.run_cli(project, "init", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((project / "VERSION").read_text(), "3.1.0\n")
            committed = subprocess.run(
                ["git", "-C", str(project), "show", "--pretty=format:", "--name-only", "HEAD"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.splitlines()
            self.assertEqual(set(committed), {".semver-forge.toml"})

    def test_init_derives_project_metadata_and_version(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pyproject.toml").write_text(
                (
                    '[project]\nname = "derived-name"\n'
                    'description = "Derived description"\nversion = "4.5.6"\n'
                ),
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

    def test_version_conflict_is_reported_before_overwrite_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pyproject.toml").write_text(
                '[project]\nname = "sample"\nversion = "1.2.3"\n',
                encoding="utf-8",
            )
            (project / "VERSION").write_text("1.2.4\n", encoding="utf-8")
            config = project / ".semver-forge.toml"
            config.write_text("preserve me", encoding="utf-8")
            result = self.run_cli(project, "init")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conflicting existing version sources", result.stderr)
            self.assertNotIn("Overwrite existing configuration", result.stdout)
            self.assertEqual(config.read_text(encoding="utf-8"), "preserve me")

    def test_existing_configuration_requires_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            config = project / ".semver-forge.toml"
            config.write_text("preserve me")
            result = self.run_cli(project, "init")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_text(), "preserve me")

    def test_git_init_preserves_unrelated_staged_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            subprocess.run(["git", "-C", str(project), "config", "user.name", "Test"], check=True)
            subprocess.run(
                ["git", "-C", str(project), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            unrelated = project / "unrelated.txt"
            unrelated.write_text("staged before init")
            subprocess.run(["git", "-C", str(project), "add", "unrelated.txt"], check=True)
            result = self.run_cli(project, "init", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            committed = subprocess.run(
                ["git", "-C", str(project), "show", "--pretty=format:", "--name-only", "HEAD"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.splitlines()
            self.assertEqual(set(committed), {".semver-forge.toml", "VERSION"})
            staged = subprocess.run(
                ["git", "-C", str(project), "diff", "--cached", "--name-only"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.splitlines()
            self.assertEqual(staged, ["unrelated.txt"])

    def test_git_init_reports_staging_failure_without_claiming_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            subprocess.run(["git", "-C", str(project), "config", "user.name", "Test"], check=True)
            subprocess.run(
                ["git", "-C", str(project), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            (project / ".gitignore").write_text("/.semver-forge.toml\n", encoding="utf-8")
            result = self.run_cli(project, "init", "--json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("staging failed", result.stdout)
            self.assertIn('"committed": false', result.stdout)
            self.assertIn('"staged_files"', result.stdout)
            head = subprocess.run(
                ["git", "-C", str(project), "rev-parse", "--verify", "HEAD"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(head.returncode, 0)


if __name__ == "__main__":
    unittest.main()
