import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from semver_forge.check import inspect_project
from semver_forge.config_scopes import (
    config_get,
    config_report,
    config_write,
    effective_config,
)
from semver_forge.errors import ConfigError


class ConfigScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        self.home = Path(self.temp.name) / "home"
        self.prefix = Path(self.temp.name) / "prefix"
        self.home.mkdir()
        self.prefix.mkdir()
        self.environment = patch.dict(os.environ, {"PREFIX": str(self.prefix)})
        self.environment.start()
        self.home_patch = patch("pathlib.Path.home", return_value=self.home)
        self.home_patch.start()

    def tearDown(self):
        self.home_patch.stop()
        self.environment.stop()
        self.temp.cleanup()

    def test_precedence_and_source_reporting(self):
        config_write(self.root, "system", "git.tag_prefix", '"sys"')
        config_write(self.root, "global", "git.tag_prefix", '"user"')
        config_write(self.root, "project", "git.tag_prefix", '"project"')
        cfg, _paths, _unknown = effective_config(self.root)
        self.assertEqual(cfg["git"]["tag_prefix"], "project")
        self.assertEqual(config_get(self.root, "git.tag_prefix")["source"], "project")
        global_value = config_get(self.root, "git.tag_prefix", "global")
        self.assertEqual(global_value["value"], "user")
        self.assertEqual(global_value["source"], "global")
        report = config_report(self.root)
        self.assertEqual(report["precedence"], ["system", "global", "project"])
        self.assertEqual(report["sources"]["git.tag_prefix"], "project")

    def test_set_preserves_unrelated_comments_and_values(self):
        project = self.root / ".semver-forge.toml"
        project.write_text(
            '# keep this comment\n[git]\ntag_prefix = "v"\nrequire_clean = true\n',
            encoding="utf-8",
        )
        config_write(self.root, "project", "git.tag_prefix", '""')
        text = project.read_text(encoding="utf-8")
        self.assertIn("# keep this comment", text)
        self.assertIn("require_clean = true", text)
        self.assertIn('tag_prefix = ""', text)

    def test_invalid_effective_version_setting_rolls_back(self):
        project = self.root / ".semver-forge.toml"
        project.write_text(
            '[version]\ninitial = "1.2.3"\nsource = { type = "text", file = "VERSION" }\n',
            encoding="utf-8",
        )
        original = project.read_text(encoding="utf-8")
        with self.assertRaises(ConfigError):
            config_write(self.root, "project", "version.initial", '"not-a-version"')
        self.assertEqual(project.read_text(encoding="utf-8"), original)

    def test_check_reports_drift_and_does_not_write(self):
        (self.root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        (self.root / "config.zsh").write_text(
            'SME_VERSION="1.2.2"\n',
            encoding="utf-8",
        )
        project = self.root / ".semver-forge.toml"
        project.write_text(
            '[project]\nname = "sample"\n'
            '[version]\ninitial = "1.2.3"\n'
            'source = { type = "text", file = "VERSION" }\n'
            '[sync]\ntargets = [{ type = "shell", file = "config.zsh", '
            'key = "SME_VERSION" }]\n',
            encoding="utf-8",
        )
        before = {path.name: path.read_bytes() for path in self.root.iterdir() if path.is_file()}
        result = inspect_project(self.root)
        after = {path.name: path.read_bytes() for path in self.root.iterdir() if path.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(result["canonical"]["version"], "1.2.3")
        self.assertEqual(result["synchronization"][1]["status"], "drift")


if __name__ == "__main__":
    unittest.main()
