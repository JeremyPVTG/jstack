from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills' / 'j-bookmarks' / 'scripts' / 'x_bookmarks.py'
spec = importlib.util.spec_from_file_location('x_bookmarks', SCRIPT)
xb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xb)

AREAS = {'tooling': {'about': 'Agent tools'}, 'work': {'about': 'The company', 'repo': 'org/repo'}}
TWEETS = {'tweets': [
    {'id': '111111', 'author': {'username': 'dev'}, 'createdAt': 'x', 'text': 'A tool | worth [trying]'},
    {'id': '222222', 'author': {'username': 'spam'}, 'createdAt': 'x', 'text': 'adult text', 'media': [1]},
    {'id': '333333', 'author': {'username': 'co'}, 'createdAt': 'x', 'text': 'Funding advice'},
]}


class XBookmarksTest(unittest.TestCase):
    def setUp(self):
        self.vault = Path(tempfile.mkdtemp())
        self.cfg = {'areas': AREAS}

    def test_ignored_rows_keep_only_the_id_and_the_ledger_round_trips(self):
        rows = {}
        xb.apply(rows, [
            {'id': '111111', 'state': 'to-research', 'area': 'tooling', 'author': 'dev', 'title': 'Try [it] | now', 'note': 'Could speed up CI'},
            {'id': '222222', 'state': 'ignored', 'author': 'spam', 'title': 'should vanish', 'note': 'should vanish'},
        ], AREAS, '2026-11-07')
        xb.save(self.vault, self.cfg, rows, '2026-11-07')
        text = (self.vault / 'triage' / 'x-bookmarks.md').read_text()
        self.assertNotIn('vanish', text)
        self.assertNotIn('spam', text)
        self.assertIn('222222', text)
        parsed, last = xb.parse(text)
        self.assertEqual(last, '2026-11-07')
        self.assertEqual(parsed['222222'], {'state': 'ignored'})
        self.assertEqual(parsed['111111']['title'], 'Try (it) / now')
        self.assertEqual(xb.parse(xb.render(parsed, last))[0], parsed)

    def test_unseen_skips_listed_posts(self):
        rows = {'222222': {'state': 'ignored'}}
        xb.save(self.vault, self.cfg, rows, None)
        source = self.vault / 'b.json'
        source.write_text(json.dumps(TWEETS))
        self.assertEqual([i['id'] for i in xb.unseen(self.vault, self.cfg, str(source))], ['111111', '333333'])

    def test_rejects_bad_decisions(self):
        for decision in (
            {'id': '111111', 'state': 'to-research', 'area': 'nope', 'author': 'dev', 'title': 't'},
            {'id': '111111', 'state': 'researched', 'area': 'tooling', 'author': 'dev', 'title': 't'},
            {'id': 'abc', 'state': 'ignored'},
            {'id': '111111', 'state': 'to-research', 'area': 'tooling', 'author': 'bad handle!', 'title': 't'},
        ):
            with self.assertRaises(ValueError, msg=decision):
                xb.apply({}, [decision], AREAS, '2026-11-07')

    def test_researched_keeps_post_details_and_records_the_outcome(self):
        rows = {}
        xb.apply(rows, [{'id': '111111', 'state': 'to-research', 'area': 'tooling', 'author': 'dev', 'title': 'Try it', 'note': 'why'}], AREAS, '2026-11-01')
        xb.apply(rows, [{'id': '111111', 'state': 'researched', 'note': 'Adopted for CI', 'outcome': '[[CI caching]]'}], AREAS, '2026-11-07')
        self.assertEqual(rows['111111'] | {}, {'state': 'researched', 'author': 'dev', 'title': 'Try it', 'area': 'tooling', 'note': 'Adopted for CI', 'outcome': '[[CI caching]]', 'date': '2026-11-07'})

    def test_sync_opens_issues_for_issue_areas_and_closes_finished_ones(self):
        rows = {}
        xb.apply(rows, [
            {'id': '333333', 'state': 'to-research', 'area': 'work', 'author': 'co', 'title': 'Funding', 'note': 'why'},
            {'id': '111111', 'state': 'to-research', 'area': 'tooling', 'author': 'dev', 'title': 'Tool', 'note': 'why'},
        ], AREAS, '2026-11-01')
        with mock.patch.object(xb, 'gh', return_value='https://github.com/org/repo/issues/7') as gh, mock.patch.object(xb.subprocess, 'run'):
            opened, _ = xb.sync(self.cfg, rows, '2026-11-01')
        self.assertEqual(opened, ['https://github.com/org/repo/issues/7'])
        self.assertEqual(gh.call_args.args[:4], ('issue', 'create', '-R', 'org/repo'))
        self.assertEqual(rows['111111']['outcome'], '')
        closed_issue = json.dumps({'state': 'CLOSED', 'stateReason': 'COMPLETED', 'closedAt': '2026-11-05T10:00:00Z'})
        with mock.patch.object(xb, 'gh', return_value=closed_issue):
            _, closed = xb.sync(self.cfg, rows, '2026-11-07')
        self.assertEqual(closed, ['https://github.com/org/repo/issues/7'])
        self.assertEqual((rows['333333']['state'], rows['333333']['date']), ('researched', '2026-11-05'))

    def test_reassign_clears_the_issue_link_and_closes_the_issue(self):
        rows = {}
        xb.apply(rows, [{'id': '333333', 'state': 'to-research', 'area': 'work', 'author': 'co', 'title': 'Funding', 'note': 'why', 'outcome': 'https://github.com/org/repo/issues/7'}], AREAS, '2026-11-01')
        xb.save(self.vault, self.cfg, rows, None)
        calls = []
        with mock.patch.object(xb, 'gh', side_effect=lambda *a: calls.append(a) or ''):
            xb.record(self.vault, self.cfg, [{'id': '333333', 'state': 'to-research', 'area': 'tooling', 'outcome': ''}], '2026-11-07')
        self.assertEqual(calls[0][:3], ('issue', 'close', 'https://github.com/org/repo/issues/7'))
        row = xb.load(self.vault, self.cfg)[0]['333333']
        self.assertEqual((row['area'], row['outcome'], row['date']), ('tooling', '', '2026-11-07'))

    def test_classifier_prompt_carries_owner_corrections(self):
        cfg = {'areas': AREAS, 'calibration': ['Founder reading goes to tooling, not work.'], 'classifier': ['fake']}
        out = json.dumps({'structured_output': {'decisions': [{'id': '111111', 'state': 'ignored'}]}})
        with mock.patch.object(xb.subprocess, 'run', return_value=mock.Mock(returncode=0, stdout=out)) as run:
            xb.classify(cfg, [{'id': '111111', 'author': 'dev', 'text': 'x'}])
        self.assertIn('Founder reading goes to tooling, not work.', run.call_args.kwargs['input'])

    def test_flags_queue_items_older_than_thirty_days(self):
        rows = {}
        xb.apply(rows, [{'id': '111111', 'state': 'to-research', 'area': 'tooling', 'author': 'dev', 'title': 'Old tool', 'note': 'why'}], AREAS, '2026-09-01')
        xb.apply(rows, [{'id': '222222', 'state': 'to-research', 'area': 'tooling', 'author': 'dev', 'title': 'New tool', 'note': 'why'}], AREAS, '2026-11-01')
        self.assertEqual(list(xb.stale(rows, '2026-11-07')), ['111111'])
        xb.save(self.vault, self.cfg, rows, None)
        self.assertIn('1 queued over 30 days, keep or ignore: Old tool', xb.record(self.vault, self.cfg, [], '2026-11-07'))


if __name__ == '__main__':
    unittest.main()
