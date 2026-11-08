import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(ROOT / "src") + (
    os.pathsep + ENV["PYTHONPATH"] if ENV.get("PYTHONPATH") else ""
)


class CLIOutputModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        (self.project / "VERSION").write_text("2.3.4\n", encoding="utf-8")
        (self.project / "pyproject.toml").write_text(
            '[project]\nname = "sample"\nversion = "2.3.4"\n',
            encoding="utf-8",
        )
        self.config = (
            "# generated config\n"
            '[project]\nname = "sample"\n\n'
            '[version]\ninitial = "2.3.4"\n'
            'source = { type = "text", file = "VERSION" }\n\n'
            '[sync]\ntargets = [{ type = "toml", file = "pyproject.toml", '
            'key = "project.version" }]\n'
        )
        (self.project / ".semver-forge.toml").write_text(self.config, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "semver_forge", *args],
            cwd=ROOT,
            env=ENV,
            text=True,
            capture_output=True,
            timeout=10,
        )

    def test_check_default_is_minimal(self):
        result = self.run_cli("check", "--project", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "Project: sample\nVersion: 2.3.4\n\nSynchronized files\nVERSION\npyproject.toml\n",
        )

    def test_check_verbose_keeps_full_report(self):
        result = self.run_cli("check", "--verbose", "--project", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("canonical:", result.stdout)
        self.assertIn("configuration:", result.stdout)

    def test_config_prints_project_file_verbatim(self):
        result = self.run_cli("config", "--project", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, self.config)

    def test_config_list_groups_settings_by_toml_table(self):
        result = self.run_cli("config", "--list", "--project", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[project]", result.stdout)
        self.assertIn("[version]", result.stdout)
        self.assertIn("[commits.types]", result.stdout)
        self.assertIn("source", result.stdout)
        self.assertIn("inline table", result.stdout)
        self.assertIn("  type", result.stdout)
        self.assertIn("targets", result.stdout)
        self.assertIn("Optional project name", result.stdout)
        self.assertIn("default:", result.stdout)
        self.assertNotIn("project.name", result.stdout)
        self.assertNotIn("version.source.type", result.stdout)
        self.assertNotIn("sample", result.stdout)

    def test_verbose_and_debug_are_global_options_for_check(self):
        before = self.run_cli("--verbose", "check", "--project", str(self.project))
        after = self.run_cli("check", "--verbose", "--project", str(self.project))
        debug = self.run_cli("check", "--debug", "--project", str(self.project))
        for result in (before, after, debug):
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("canonical:", result.stdout)

    def init_git(self):
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.project,
            check=True,
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.project, check=True)
        subprocess.run(["git", "add", "."], cwd=self.project, check=True)
        subprocess.run(["git", "commit", "-qm", "chore: baseline"], cwd=self.project, check=True)

    def test_sync_output_is_unchanged_by_verbose_and_debug(self):
        self.init_git()
        normal = self.run_cli("sync", "--project", str(self.project))
        verbose = self.run_cli("sync", "--verbose", "--project", str(self.project))
        debug = self.run_cli("sync", "--debug", "--project", str(self.project))
        for result in (normal, verbose, debug):
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(normal.stdout, verbose.stdout)
        self.assertEqual(normal.stdout, debug.stdout)
        self.assertIn("file:", normal.stdout)

    def test_next_output_is_unchanged_by_verbose_and_debug(self):
        self.init_git()
        normal = self.run_cli("next", "--project", str(self.project))
        verbose = self.run_cli("next", "--verbose", "--project", str(self.project))
        debug = self.run_cli("next", "--debug", "--project", str(self.project))
        for result in (normal, verbose, debug):
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(normal.stdout, verbose.stdout)
        self.assertEqual(normal.stdout, debug.stdout)
        self.assertIn("current:", normal.stdout)


if __name__ == "__main__":
    unittest.main()
