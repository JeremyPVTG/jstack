from datetime import date, timezone
from pathlib import Path
import importlib.util
import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills' / 'j-daily' / 'scripts' / 'collect_day.py'
spec = importlib.util.spec_from_file_location('collect_day', SCRIPT)
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

TZ = ZoneInfo('America/Los_Angeles')
DAY = date(2026, 11, 7)
START, END = cd.day_window(DAY, TZ)


def git(repo, *args, when=None, email='me@example.com'):
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'Me', 'GIT_AUTHOR_EMAIL': email,
           'GIT_COMMITTER_NAME': 'Me', 'GIT_COMMITTER_EMAIL': email}
    if when:
        env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = when
    subprocess.run(['git', *args], cwd=repo, env=env, check=True, capture_output=True)


def new_repo():
    repo = Path(tempfile.mkdtemp())
    git(repo, 'init', '-q', '-b', 'main')
    return repo


class WindowTest(unittest.TestCase):
    def test_a_daylight_saving_day_lasts_25_hours(self):
        start, end = cd.day_window(date(2026, 11, 1), TZ)
        self.assertEqual((end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds(), 25 * 3600)
        self.assertEqual(start.isoformat(), '2026-11-01T00:00:00-07:00')


class VaultTest(unittest.TestCase):
    def test_entries_are_placed_by_commit_time_not_their_bracketed_date(self):
        vault = new_repo()
        log = vault / 'log.md'
        lines = ['# Log\n']
        for when, line in [
            ('2026-11-06T23:30:00-08:00', '## [2026-11-07] research | Before the day | pages: [[A]]'),
            ('2026-11-07T21:00:00-08:00', '## [2026-11-08] research | Evening, dated in UTC | pages: [[B]], [[C]] | spend: ~$1'),
            ('2026-11-08T00:30:00-08:00', '## [2026-11-08] lint | After the day'),
        ]:
            lines.append(line + '\n')
            log.write_text(''.join(lines))
            git(vault, 'add', 'log.md')
            git(vault, 'commit', '-q', '-m', 'log', when=when)
        entries = cd.vault_entries(str(vault), START, END)['entries']
        self.assertEqual([e['summary'] for e in entries], ['Evening, dated in UTC'])
        self.assertEqual(entries[0]['pages'], ['B', 'C'])
        self.assertEqual(entries[0]['spend'], '~$1')

    def test_reads_entries_that_exist_only_on_the_remote_without_origin_head(self):
        remote = Path(tempfile.mkdtemp())
        git(remote, 'init', '-q', '--bare', '-b', 'main')
        writer = new_repo()
        (writer / 'log.md').write_text('# Log\n')
        git(writer, 'add', 'log.md')
        git(writer, 'commit', '-q', '-m', 'start', when='2026-11-06T09:00:00-08:00')
        git(writer, 'remote', 'add', 'origin', str(remote))
        git(writer, 'push', '-q', 'origin', 'main')
        vault = Path(tempfile.mkdtemp())
        git(vault, 'init', '-q', '-b', 'main')
        git(vault, 'remote', 'add', 'origin', str(remote))
        git(vault, 'config', 'remote.origin.followRemoteHEAD', 'never')  # git < 2.48 never sets origin/HEAD
        git(vault, 'pull', '-q', 'origin', 'main')
        (writer / 'log.md').write_text('# Log\n## [2026-11-07] research | Written by the server\n')
        git(writer, 'commit', '-q', '-am', 'log', when='2026-11-07T10:00:00-08:00')
        git(writer, 'push', '-q', 'origin', 'main')
        entries = cd.vault_entries(str(vault), START, END)['entries']
        self.assertEqual([e['summary'] for e in entries], ['Written by the server'])

    def test_a_missing_vault_is_an_error_not_a_crash(self):
        self.assertIn('error', cd.vault_entries(None, START, END))


class CommitsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def repo(self, name, remote):
        repo = self.root / name
        repo.mkdir()
        git(repo, 'init', '-q', '-b', 'main')
        git(repo, 'remote', 'add', 'origin', f'https://github.com/{remote}.git')
        return repo

    def commit(self, repo, subject, email, when='2026-11-07T12:00:00-08:00'):
        (repo / 'f').write_text(subject)
        git(repo, 'add', 'f')
        git(repo, 'commit', '-q', '-m', subject, when=when, email=email)

    def test_keeps_direct_noreply_commits_and_leaves_pr_work_out(self):
        noreply = '123+me@users.noreply.github.com'
        tools = self.repo('tools', 'me/tools')
        self.commit(tools, 'Yesterday', noreply, when='2026-11-06T12:00:00-08:00')
        self.commit(tools, 'Pushed straight to main', noreply)
        self.commit(tools, 'Someone else', 'other@example.com')
        self.commit(tools, 'Add the thing (#12)', noreply)
        git(tools, 'switch', '-q', '-c', 'feature')
        self.commit(tools, 'Work in progress on a PR branch', noreply)
        git(tools, 'switch', '-q', 'main')
        repos = cd.commits([str(self.root)], START, END, [noreply])['repos']
        self.assertEqual(repos, [{'repo': 'me/tools', 'count': 1, 'subjects': ['Pushed straight to main']}])


class T3Test(unittest.TestCase):
    def setUp(self):
        self.db = Path(tempfile.mkdtemp()) / 'state.sqlite'
        con = sqlite3.connect(self.db)
        con.execute('create table orchestration_v2_projection_threads (thread_id text, title text)')
        con.execute('create table orchestration_v2_projection_messages '
                    '(thread_id text, role text, created_at text, payload_json text)')
        con.execute('create table orchestration_v2_projection_turn_items '
                    '(thread_id text, type text, updated_at text, payload_json text)')
        con.execute("insert into orchestration_v2_projection_threads values ('t1', 'Blog plan')")
        for created, by, text in [('2026-11-07T20:00:00.000Z', 'user', 'Typed by me'),
                                  ('2026-11-07T20:01:00.000Z', 'agent', 'Monitor prompt'),
                                  ('2026-11-08T09:00:00.000Z', 'user', 'Next day')]:
            con.execute("insert into orchestration_v2_projection_messages values ('t1', 'user', ?, ?)",
                        (created, json.dumps({'createdBy': by, 'text': text})))
        questions = [{'id': '0', 'header': 'Scope', 'question': 'Which first?'},
                     {'id': '1', 'header': 'Deploy', 'question': 'Git deploys?'},
                     {'id': '2', 'header': 'Skip', 'question': 'Unanswered?'}]
        answer = {'answers': {'Which first?': 'The script', '1': 'Yes'}}
        con.execute("insert into orchestration_v2_projection_turn_items values ('t1', 'user_input_request', ?, ?)",
                    ('2026-11-07T21:00:00.000Z', json.dumps({'questions': questions, 'questionAnswer': answer})))
        con.commit()
        con.close()

    def test_keeps_only_typed_messages_and_answers_keyed_by_text_or_id(self):
        result = cd.t3_activity(self.db, START, END)
        self.assertEqual(result['threads'], [{'title': 'Blog plan', 'messages': [
            {'time': '2026-11-07T20:00:00.000Z', 'text': 'Typed by me'}]}])
        self.assertEqual([(a['header'], a['answer']) for a in result['answers']],
                         [('Scope', 'The script'), ('Deploy', 'Yes')])

    def test_a_changed_schema_is_reported(self):
        con = sqlite3.connect(self.db)
        con.execute('alter table orchestration_v2_projection_threads rename column title to name')
        con.commit()
        con.close()
        self.assertIn('schema changed', cd.t3_activity(self.db, START, END)['error'])


if __name__ == '__main__':
    unittest.main()
