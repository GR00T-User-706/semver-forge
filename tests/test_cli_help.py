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
        self.assertIn("{init,next,sync,config,check}", result.stdout)
        self.assertNotIn("the following arguments are required", result.stderr)

    def test_root_help_has_examples_and_command_guidance(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("{init,next,sync,config,check}", result.stdout)
        self.assertIn("synchronize metadata", result.stdout)

    def test_every_subcommand_has_nonempty_description(self):
        commands = ["init", "next", "sync", "config", "check"]
        for command in commands:
            with self.subTest(command=command):
                result = self.run_cli(command, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertGreater(len(result.stdout.strip().splitlines()), 4)
                self.assertNotIn(
                    "usage: semver-forge " + command + " [-h]\n\noptions:", result.stdout
                )

    def test_manpage_exists_and_mentions_safety(self):
        manpage = ROOT / "man" / "semver-forge.1"
        self.assertTrue(manpage.is_file())
        text = manpage.read_text(encoding="utf-8")
        self.assertIn(".TH SEMVER-FORGE", text)
        self.assertIn(".SH COMMANDS", text)
        self.assertIn("--discover", text)

    def test_version_option_reports_installed_version(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^semver-forge \d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
