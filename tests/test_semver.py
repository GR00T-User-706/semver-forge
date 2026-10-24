import unittest

from semver_forge.semver import SemVerError, Version


class SemVerTests(unittest.TestCase):
    def test_parse_and_roundtrip(self):
        versions = [
            "0.1.0",
            "1.4.2",
            "2.0.0-rc.1",
            "1.2.3-beta.4+build.19",
        ]
        for version in versions:
            self.assertEqual(str(Version.parse(version)), version)

    def test_invalid(self):
        versions = ["01.2.3", "1.2", "1.2.3-01", "v1.2.3", "1.2.3-"]
        for version in versions:
            with self.assertRaises(SemVerError):
                Version.parse(version)

    def test_bumps(self):
        version = Version.parse("1.2.3")
        self.assertEqual(str(version.bump("major")), "2.0.0")
        self.assertEqual(str(version.bump("minor")), "1.3.0")
        self.assertEqual(str(version.bump("patch")), "1.2.4")

    def test_precedence(self):
        sequence = [
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-alpha.beta",
            "1.0.0-beta",
            "1.0.0-beta.2",
            "1.0.0-beta.11",
            "1.0.0-rc.1",
            "1.0.0",
        ]
        for left, right in zip(sequence, sequence[1:], strict=True):
            self.assertLess(
                Version.parse(left).compare(Version.parse(right)),
                0,
            )

    def test_build_ignored(self):
        self.assertEqual(
            Version.parse("1.2.3+a").compare(Version.parse("1.2.3+b")),
            0,
        )

    def test_prerelease_next(self):
        self.assertEqual(
            str(Version.parse("1.2.3-beta.4").prerelease_next("beta")),
            "1.2.3-beta.5",
        )
