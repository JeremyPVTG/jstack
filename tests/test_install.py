import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'install.py'


class Installation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.target = self.root / 'skills with spaces'
        self.state = self.root / 'state'

    def run_install(self, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), 'install', '--target', str(self.target), '--state-dir', str(self.state), *extra], capture_output=True, text=True)

    def receipt(self):
        return next(self.state.glob('*/receipt.json'))

    def rollback(self):
        return subprocess.run([sys.executable, str(SCRIPT), 'rollback', str(self.receipt())], capture_output=True, text=True)

    def test_dry_run_creates_nothing(self):
        self.assertEqual(self.run_install('--dry-run').returncode, 0)
        self.assertFalse(self.target.exists())
        self.assertFalse(self.state.exists())

    def test_install_repeat_and_rollback(self):
        self.target.mkdir()
        original = self.target / 'j-review'
        original.mkdir()
        (original / 'personal.txt').write_text('keep me')
        self.assertEqual(self.run_install().returncode, 0)
        self.assertTrue(original.is_symlink())
        receipt = self.receipt()
        first = receipt.read_bytes()
        self.assertEqual(self.run_install().returncode, 0)
        self.assertEqual(receipt.read_bytes(), first)
        self.assertEqual(len(list(self.state.glob('*/receipt.json'))), 1)
        self.assertEqual(self.rollback().returncode, 0)
        self.assertFalse(original.is_symlink())
        self.assertEqual((original / 'personal.txt').read_text(), 'keep me')
        self.assertFalse((self.target / 'j-deliver').exists())
        self.assertEqual(self.rollback().returncode, 0)

    def test_preserves_broken_symlink(self):
        self.target.mkdir()
        old = self.target / 'j-review'
        old.symlink_to('missing-original')
        self.assertEqual(self.run_install('--skill', 'j-review').returncode, 0)
        self.assertEqual(self.rollback().returncode, 0)
        self.assertTrue(old.is_symlink())
        self.assertEqual(old.readlink(), Path('missing-original'))

    def test_rollback_refuses_changed_destination(self):
        self.assertEqual(self.run_install().returncode, 0)
        changed = self.target / 'j-review'
        changed.unlink()
        changed.mkdir()
        (changed / 'new.txt').write_text('later work')
        self.assertNotEqual(self.rollback().returncode, 0)
        self.assertEqual((changed / 'new.txt').read_text(), 'later work')
        self.assertTrue((self.target / 'j-deliver').is_symlink())

    def test_unknown_skill_does_not_mutate(self):
        self.assertNotEqual(self.run_install('--skill', '../escape').returncode, 0)
        self.assertFalse(self.target.exists())


if __name__ == '__main__':
    unittest.main()
