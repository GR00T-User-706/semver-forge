import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = os.environ.copy()
ENV['PYTHONPATH'] = str(ROOT / 'src') + (os.pathsep + ENV['PYTHONPATH'] if ENV.get('PYTHONPATH') else '')

class CLIHelpTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'semver_forge', *args], cwd=ROOT, env=ENV,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)

    def test_no_arguments_shows_help_and_succeeds(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Typical workflow", result.stdout)
        self.assertNotIn("the following arguments are required", result.stderr)

    def test_root_help_has_examples_and_command_guidance(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Typical workflow', result.stdout)
        self.assertIn('Use', result.stdout)

    def test_every_subcommand_has_nonempty_description(self):
        commands = ['init', 'doctor', 'current', 'status', 'history', 'check', 'verify-tag',
                    'verify-release', 'validate', 'compare', 'bump', 'next', 'sync',
                    'release', 'changelog', 'install', 'uninstall']
        for command in commands:
            with self.subTest(command=command):
                result = self.run_cli(command, '--help')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertGreater(len(result.stdout.strip().splitlines()), 4)
                self.assertNotIn('usage: semver-forge ' + command + ' [-h]\n\noptions:', result.stdout)

    def test_manpage_exists_and_mentions_safety(self):
        manpage = ROOT / 'man' / 'semver-forge.1'
        self.assertTrue(manpage.is_file())
        text = manpage.read_text(encoding='utf-8')
        self.assertIn('.TH SEMVER-FORGE', text)
        self.assertIn('.SH SAFETY', text)
        self.assertIn('release --dry-run', text)

    def test_user_local_install_and_uninstall_include_manpage(self):
        with tempfile.TemporaryDirectory(prefix="semver forge install ") as directory:
            prefix = Path(directory) / "user prefix"
            installed = self.run_cli("install", "--prefix", str(prefix))
            self.assertEqual(installed.returncode, 0, installed.stderr)
            launcher = prefix / "bin" / "semver-forge"
            manpage = prefix / "share" / "man" / "man1" / "semver-forge.1"
            self.assertTrue(launcher.is_file())
            self.assertTrue(manpage.is_file())
            help_result = subprocess.run([str(launcher), "doctor", "--help"], text=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn("Inspect Git", help_result.stdout)
            root_help = subprocess.run([str(launcher)], text=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, timeout=10)
            self.assertEqual(root_help.returncode, 0, root_help.stderr)
            self.assertIn("Typical workflow", root_help.stdout)
            # Exercise init through the installed launcher, not the source checkout.
            repo = Path(directory) / "practice repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            initialized = subprocess.run([str(launcher), "--project", str(repo), "init"],
                                         text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            self.assertTrue((repo / ".semver-forge.toml").is_file())
            generated_config = (repo / ".semver-forge.toml").read_text(encoding="utf-8")
            self.assertIn('name = "practice repo"', generated_config)
            self.assertIn('initial = "0.1.0"', generated_config)
            self.assertIn('file = "VERSION"', generated_config)
            self.assertNotIn("example-project", generated_config)
            self.assertEqual((repo / "VERSION").read_text(encoding="utf-8"), "0.1.0\\n")
            removed = self.run_cli("uninstall", "--prefix", str(prefix))
            self.assertEqual(removed.returncode, 0, removed.stderr)
            self.assertFalse(launcher.exists())
            self.assertFalse(manpage.exists())

if __name__ == '__main__':
    unittest.main()
