import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(ROOT / "src") + (
    os.pathsep + ENV["PYTHONPATH"] if ENV.get("PYTHONPATH") else ""
)


class CLIHelpTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "semver_forge", *args],
            cwd=ROOT,
            env=ENV,
            text=True,
            capture_output=True,
            timeout=10,
        )

    def test_no_arguments_shows_help_and_succeeds(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("{init,next,changelog,commit,sync,config,check}", result.stdout)
        self.assertIn("usage: svf", result.stdout)
        self.assertNotIn("the following arguments are required", result.stderr)

    def test_root_help_has_examples_and_command_guidance(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("{init,next,changelog,commit,sync,config,check}", result.stdout)
        self.assertIn("synchronize metadata", result.stdout)

    def test_every_subcommand_has_nonempty_description(self):
        commands = ["init", "next", "sync", "config", "check"]
        for command in commands:
            with self.subTest(command=command):
                result = self.run_cli(command, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertGreater(len(result.stdout.strip().splitlines()), 4)
                self.assertIn("usage: svf " + command, result.stdout)

    def test_both_manual_pages_exist_and_cross_reference(self):
        cli_page = ROOT / "man" / "svf.1"
        config_page = ROOT / "man" / "svf-config.5"
        self.assertTrue(cli_page.is_file())
        self.assertTrue(config_page.is_file())
        cli_text = cli_page.read_text(encoding="utf-8")
        config_text = config_page.read_text(encoding="utf-8")
        self.assertIn(".TH SVF", cli_text)
        self.assertIn(".SH COMMANDS", cli_text)
        self.assertIn("--discover", cli_text)
        self.assertIn("svf-config (5)", cli_text)
        self.assertIn(".SH TOML SYNTAX", config_text)
        self.assertIn(".SH CONFIGURATION SCHEMA", config_text)
        self.assertIn("TOML v1.0.0", config_text)

    def test_version_option_reports_installed_version(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^svf \d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
