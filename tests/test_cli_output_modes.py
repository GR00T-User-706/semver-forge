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
            '# generated config\n'
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
            "Project: sample\nVersion: 2.3.4\n\nSynchronized files\n"
            "VERSION\npyproject.toml\n",
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

    def test_config_list_prints_recognized_keys(self):
        result = self.run_cli("config", "--list", "--project", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("version.source", result.stdout)
        self.assertIn("sync.targets", result.stdout)
        self.assertNotIn("sample", result.stdout)

    def test_verbose_and_debug_are_global_options(self):
        before = self.run_cli("--verbose", "check", "--project", str(self.project))
        after = self.run_cli("check", "--verbose", "--project", str(self.project))
        debug = self.run_cli("check", "--debug", "--project", str(self.project))
        for result in (before, after, debug):
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("canonical:", result.stdout)


if __name__ == "__main__":
    unittest.main()
