from pathlib import Path
import importlib.util
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills' / 'j-daily' / 'scripts' / 'leak_check.py'
spec = importlib.util.spec_from_file_location('leak_check', SCRIPT)
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)

DAY = {'prs': {'merged': [{'repo': 'acme/secret-app'}], 'opened': []}, 'commits': {'repos': [{'repo': 'me/tools'}]}}


class LeakCheckTest(unittest.TestCase):
    def test_flags_emails_paths_repo_names_and_deny_terms(self):
        text = 'Mailed bob@example.com about /Users/me/notes.md and the Secret-App PR at Hillside Farm.'
        hits = lc.check(text, DAY, ['hillside farm'])
        joined = '\n'.join(hits)
        self.assertIn('email address: bob@example.com', joined)
        self.assertIn('local path: /Users/me/notes.md', joined)
        self.assertIn('repo name: secret-app', joined)
        self.assertNotIn('acme', joined)
        self.assertIn('deny list: hillside farm', joined)
        self.assertNotIn('me/tools', joined)

    def test_a_clean_draft_has_no_hits(self):
        hits = lc.check('I measured how many visits came from link scanners.', DAY, ['hillside farm'])
        self.assertEqual([h for h in hits if 'gitleaks' not in h], [])

    @unittest.skipUnless(shutil.which('gitleaks'), 'gitleaks not installed')
    def test_flags_a_token_through_gitleaks(self):
        token = 'ghp_' + 'a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8'
        self.assertTrue(any('possible secret' in hit for hit in lc.check(f'key = "{token}"')))


if __name__ == '__main__':
    unittest.main()
