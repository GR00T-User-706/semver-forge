import tempfile
import unittest
from pathlib import Path

from semver_forge.config import find_config, load
from semver_forge.errors import ConfigError


class ConfigTests(unittest.TestCase):
    def test_load(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.toml"
            p.write_text('[version]\ninitial="1.2.3"\nsource={type="text",file="VERSION"}\n')
            cfg, unknown = load(p)
            self.assertEqual(cfg["version"]["initial"], "1.2.3")
            self.assertFalse(unknown)

    def test_duplicate_config_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".semver-forge.toml").write_text("[version]\ninitial='1.0.0'\n")
            (root / "semver-forge.toml").write_text("[version]\ninitial='1.0.0'\n")
            with self.assertRaisesRegex(ConfigError, "multiple SemVer Forge configuration files"):
                find_config(root)

    def test_bad_toml(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x"
            p.write_text("[")
            with self.assertRaises(ConfigError):
                load(p)
