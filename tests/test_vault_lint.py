from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'j-research'
LINT = SKILL / 'scripts' / 'vault_lint.py'

PAGE = '''---
type: {type}
reviewed: {reviewed}
volatility: {volatility}
sources: [[[raw/2026-11/2026-11-01 source]]]
---
# {title}
{body}
'''
RAW = '---\nurl: https://example.com\ncaptured: 2026-11-01\nkind: docs\n---\nExtract.\n'


class VaultLintTest(unittest.TestCase):
    def setUp(self):
        self.vault = Path(tempfile.mkdtemp()) / 'vault'
        shutil.copytree(SKILL / 'assets' / 'vault', self.vault)
        (self.vault / 'raw' / '2026-11').mkdir(parents=True)
        (self.vault / 'wiki').mkdir()
        (self.vault / 'raw' / '2026-11' / '2026-11-01 source.md').write_text(RAW)

    def tearDown(self):
        shutil.rmtree(self.vault.parent)

    def page(self, title, body='', type='topic', reviewed='2026-11-01', volatility='medium'):
        (self.vault / 'wiki' / f'{title}.md').write_text(PAGE.format(type=type, reviewed=reviewed, volatility=volatility, title=title, body=body))

    def index(self, *titles):
        (self.vault / 'index.md').write_text('# Index\n\n' + ''.join(f'- [[{t}]]: summary\n' for t in titles))

    def run_lint(self, today='2026-11-07'):
        result = subprocess.run([sys.executable, str(LINT), str(self.vault), '--today', today], capture_output=True, text=True)
        return result.returncode, result.stdout

    def test_template_is_clean(self):
        code, out = self.run_lint()
        self.assertEqual(code, 0, out)

    def test_clean_vault_passes(self):
        self.page('A', 'See [[B]].')
        self.page('B', 'See [[A]].', type='entity')
        self.index('A', 'B')
        code, out = self.run_lint()
        self.assertEqual(code, 0, out)
        self.assertIn('0 errors, 0 warnings', out)

    def test_errors(self):
        self.page('A', 'See [[Missing page]].', type='opinion')
        (self.vault / 'wiki' / 'B.md').write_text('# B\nNo frontmatter. [[A]]\n')
        (self.vault / 'raw' / '2026-11' / 'bad.md').write_text('---\nurl: x\n---\n')
        self.index('A', 'Gone')
        code, out = self.run_lint()
        self.assertEqual(code, 1)
        for expected in ['broken link [[Missing page]]', 'broken link [[Gone]]', 'type must be one of', 'wiki/B: missing frontmatter', 'wiki/B: not listed in index.md', 'raw/2026-11/bad: missing frontmatter captured, kind']:
            self.assertIn(expected, out)

    def test_stale_and_orphan_are_warnings(self):
        self.page('A', reviewed='2026-07-01', volatility='high')
        self.index('A')
        code, out = self.run_lint()
        self.assertEqual(code, 0, out)
        self.assertIn('wiki/A: stale', out)
        self.assertIn('wiki/A: orphan', out)

    def test_links_in_code_are_ignored(self):
        self.page('A', 'Example: `[[Not a link]]`\n```\n[[Also not]]\n```\n[[B]]')
        self.page('B', '[[A]]')
        self.index('A', 'B')
        code, out = self.run_lint()
        self.assertEqual(code, 0, out)


if __name__ == '__main__':
    unittest.main()
