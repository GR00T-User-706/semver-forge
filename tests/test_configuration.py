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

    def test_bad_toml(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x"
            p.write_text("[")
            with self.assertRaises(ConfigError):
                load(p)
