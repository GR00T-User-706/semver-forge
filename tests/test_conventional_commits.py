import unittest
from semver_forge.conventional_commits import parse_message,classify
class ConventionalTests(unittest.TestCase):
 def test_feature(self): self.assertEqual(classify('feat(cli): add mode'),'minor')
 def test_fix(self): self.assertEqual(classify('fix: handle null'),'patch')
 def test_breaking_bang(self): self.assertEqual(classify('feat!: remove old API'),'major')
 def test_breaking_footer(self): self.assertEqual(classify('fix: change API\n\nBREAKING CHANGE: caller changes'),'major')
 def test_docs_ignored(self): self.assertIsNone(classify('docs: spelling'))
 def test_malformed(self): self.assertIsNone(classify('made a change'))
