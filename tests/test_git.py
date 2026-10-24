import tempfile,subprocess,unittest
from pathlib import Path
from semver_forge import git
class GitTests(unittest.TestCase):
 def test_temp_repo_and_dirty(self):
  with tempfile.TemporaryDirectory(prefix='repo with spaces ') as d:
   subprocess.run(['git','init','-q',d],check=True); subprocess.run(['git','-C',d,'-c','user.name=Test','-c','user.email=test@example.invalid','commit','--allow-empty','-m','feat: initial'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   self.assertEqual(git.root(d),Path(d).resolve()); self.assertFalse(git.is_dirty(d)); (Path(d)/'new file').write_text('x'); self.assertTrue(git.is_dirty(d))
