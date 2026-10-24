import unittest
from semver_forge.semver import Version, SemVerError
class SemVerTests(unittest.TestCase):
 def test_parse_and_roundtrip(self):
  for x in ['0.1.0','1.4.2','2.0.0-rc.1','1.2.3-beta.4+build.19']: self.assertEqual(str(Version.parse(x)),x)
 def test_invalid(self):
  for x in ['01.2.3','1.2','1.2.3-01','v1.2.3','1.2.3-']: 
   with self.assertRaises(SemVerError): Version.parse(x)
 def test_bumps(self):
  v=Version.parse('1.2.3'); self.assertEqual(str(v.bump('major')),'2.0.0'); self.assertEqual(str(v.bump('minor')),'1.3.0'); self.assertEqual(str(v.bump('patch')),'1.2.4')
 def test_precedence(self):
  seq=['1.0.0-alpha','1.0.0-alpha.1','1.0.0-alpha.beta','1.0.0-beta','1.0.0-beta.2','1.0.0-beta.11','1.0.0-rc.1','1.0.0']
  for a,b in zip(seq,seq[1:]): self.assertLess(Version.parse(a).compare(Version.parse(b)),0)
 def test_build_ignored(self): self.assertEqual(Version.parse('1.2.3+a').compare(Version.parse('1.2.3+b')),0)
 def test_prerelease_next(self): self.assertEqual(str(Version.parse('1.2.3-beta.4').prerelease_next('beta')),'1.2.3-beta.5')
