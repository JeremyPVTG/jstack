#!/usr/bin/env python3
"""Collect one day's work as JSON for the j-daily skill. It changes no files or branches;
the only write is a `git fetch` of the vault's remote-tracking refs.

Sources:
  vault    entries appended to the research vault's log.md, placed by commit time
  prs      pull requests you opened or merged on GitHub (gh search prs)
  commits  your commits in local repos that had no pull request that day
  t3       messages you typed in T3 Code and your answers to its questions

A source that fails is reported under its "error" key; the others still run.

Usage: collect_day.py [--date YYYY-MM-DD] [--tz ZONE] [--out FILE]
  --date  the day to collect (default: today in --tz)
  --tz    IANA time zone that bounds the day (default: this machine's zone)

Config: ~/.config/jstack/config.json (or $JSTACK_CONFIG)
  research_vault     local clone of the research vault, shared with j-research
  daily.repo_roots   folders whose child git repos are scanned for commits (default: home)
  daily.author_emails  extra commit emails that are yours (the global git email and your
                     GitHub noreply address are always included)
  daily.t3_state     T3 Code state database (default: ~/.t3/userdata/statev2.sqlite)
"""
import argparse
from datetime import date, datetime, time, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from zoneinfo import ZoneInfo

CONFIG = Path(os.environ.get('JSTACK_CONFIG', '~/.config/jstack/config.json')).expanduser()
LOG_LINE = re.compile(r'^## \[(\d{4}-\d{2}-\d{2})\] (\w+) \| (.*)$')
COMMIT_MARK = 'COMMIT\x1f'
MAX_TEXT = 4000
T3_COLUMNS = {
    'orchestration_v2_projection_messages': {'thread_id', 'role', 'created_at', 'payload_json'},
    'orchestration_v2_projection_turn_items': {'thread_id', 'type', 'updated_at', 'payload_json'},
    'orchestration_v2_projection_threads': {'thread_id', 'title'},
}


def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout


def local_zone():
    try:
        return ZoneInfo(os.path.realpath('/etc/localtime').split('zoneinfo/', 1)[1])
    except (IndexError, KeyError, ValueError, OSError):
        return datetime.now().astimezone().tzinfo


def day_window(day, tz):
    """Start and end of the calendar day in tz, so a daylight-saving day is 23 or 25 hours."""
    return datetime.combine(day, time(), tzinfo=tz), datetime.combine(day + timedelta(days=1), time(), tzinfo=tz)


def utc_text(moment):
    return moment.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_time(text):
    return datetime.fromisoformat(text.replace('Z', '+00:00'))


def clip(text):
    text = (text or '').strip()
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + ' [cut]'


def vault_entries(vault, start, end):
    """Log lines added by commits inside the window. Commit time is exact; the bracketed date
    in a log line is UTC in older entries and the owner's zone in newer ones."""
    vault = Path(vault).expanduser() if vault else None
    if not vault or not vault.is_dir():
        return {'error': 'research_vault is not set or not a folder'}
    refs = ['HEAD']  # local commits not yet pushed
    try:  # vault writes often land on the remote first; fetch updates only remote-tracking refs
        run(['git', 'fetch', '-q', 'origin'], cwd=vault)
        run(['git', 'rev-parse', '--verify', '-q', 'origin/HEAD'], cwd=vault)
        refs.append('origin/HEAD')
    except subprocess.CalledProcessError:
        pass
    since = (start - timedelta(days=1)).isoformat()
    out = run(['git', 'log', *refs, '--reverse', '-p', f'--since={since}',
               f'--format={COMMIT_MARK}%cI', '--', 'log.md'], cwd=vault)
    entries, moment = [], None
    for line in out.splitlines():
        if line.startswith(COMMIT_MARK):
            moment = parse_time(line[len(COMMIT_MARK):])
            continue
        match = LOG_LINE.match(line[1:]) if line.startswith('+') else None
        if not match or moment is None or not start <= moment < end:
            continue
        parts = match.group(3).split(' | ')
        entry = {'time': moment.isoformat(), 'kind': match.group(2), 'summary': parts[0], 'pages': []}
        for part in parts[1:]:
            if part.startswith('pages:'):
                entry['pages'] = re.findall(r'\[\[([^\]]+)\]\]', part)
            elif part.startswith('spend:'):
                entry['spend'] = part[len('spend:'):].strip()
        entries.append(entry)
    return {'entries': entries}


def pull_requests(start, end):
    """PRs you opened or merged in the window, across every repo gh can see."""
    span = f'{utc_text(start)}..{utc_text(end - timedelta(seconds=1))}'
    fields = 'repository,number,title,url,state,isDraft,createdAt,closedAt'
    result = {}
    for key, flag in (('opened', '--created'), ('merged', '--merged-at')):
        rows = json.loads(run(['gh', 'search', 'prs', '--author', '@me', flag, span,
                               '--limit', '100', '--json', fields]))
        result[key] = [{'repo': row['repository']['nameWithOwner'], 'number': row['number'],
                        'title': row['title'], 'url': row['url'], 'state': row['state'],
                        'draft': row['isDraft']} for row in rows]
        if len(rows) == 100:
            result.setdefault('warnings', []).append(f'{key}: stopped at 100 results')
    return result


def remote_name(repo):
    """owner/name from the origin remote, or None."""
    try:
        url = run(['git', 'remote', 'get-url', 'origin'], cwd=repo).strip()
    except subprocess.CalledProcessError:
        return None
    match = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$', url)
    return match.group(1) if match else None


def local_repos(roots):
    """Child folders of each root that are git checkouts, one per repository."""
    seen, repos = set(), []
    for root in roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.name.startswith('.') or not (child / '.git').exists():
                continue
            try:
                common = Path(child, run(['git', 'rev-parse', '--git-common-dir'], cwd=child).strip()).resolve()
            except subprocess.CalledProcessError:
                continue
            if common not in seen:
                seen.add(common)
                repos.append(child)
    return repos


def author_emails(extra):
    """Your commit identities: the global git email, your GitHub noreply address, and any extras."""
    emails = set(extra)
    for source in (['git', 'config', '--global', 'user.email'],
                   ['gh', 'api', 'user', '--jq', '"\\(.id)+\\(.login)@users.noreply.github.com"']):
        try:
            emails.add(run(source).strip())
        except (subprocess.CalledProcessError, OSError):
            pass
    return sorted(email for email in emails if email)


def commits(roots, start, end, pr_repos, emails):
    """Your commit subjects per repo, skipping repos whose work is already in a PR that day."""
    if not emails:
        return {'error': 'no author email found; set daily.author_emails'}
    authors = ['--fixed-strings', *(f'--author={email}' for email in emails)]
    found = []
    for repo in local_repos(roots):
        name = remote_name(repo)
        if name and name in pr_repos:
            continue
        try:
            out = run(['git', 'log', '--all', '--no-merges', f'--since={start.isoformat()}',
                       *authors, '--format=%H%x1f%cI%x1f%s'], cwd=repo)
        except subprocess.CalledProcessError:
            continue
        subjects, shas = [], set()
        for line in out.splitlines():
            sha, when, subject = line.split('\x1f', 2)
            if sha not in shas and start <= parse_time(when) < end:
                shas.add(sha)
                subjects.append(subject)
        if subjects:
            found.append({'repo': name or repo.name, 'count': len(subjects), 'subjects': subjects[:50]})
    return {'repos': found}


def t3_activity(db, start, end):
    """Messages the person typed (createdBy "user") and their answers to question prompts.
    The database is T3's internal store, so check the columns before trusting it."""
    db = Path(db).expanduser()
    if not db.is_file():
        return {'error': f'no T3 database at {db}'}
    con = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True)
    try:
        for table, needed in T3_COLUMNS.items():
            have = {row[1] for row in con.execute(f'pragma table_info({table})')}
            if not needed <= have:
                return {'error': f'T3 schema changed: {table} lacks {sorted(needed - have)}'}
        titles = dict(con.execute('select thread_id, title from orchestration_v2_projection_threads'))
        low, high = utc_text(start - timedelta(days=1)), utc_text(end + timedelta(days=1))
        threads = {}
        for thread, created, payload in con.execute(
                'select thread_id, created_at, payload_json from orchestration_v2_projection_messages '
                "where role = 'user' and created_at between ? and ? order by created_at", (low, high)):
            data = json.loads(payload)
            if data.get('createdBy') != 'user' or not start <= parse_time(created) < end:
                continue
            threads.setdefault(thread, {'title': titles.get(thread), 'messages': []})['messages'].append(
                {'time': created, 'text': clip(data.get('text'))})
        answers = []
        for thread, updated, payload in con.execute(
                'select thread_id, updated_at, payload_json from orchestration_v2_projection_turn_items '
                "where type = 'user_input_request' and updated_at between ? and ? order by updated_at", (low, high)):
            if not start <= parse_time(updated) < end:
                continue
            data = json.loads(payload)
            given = (data.get('questionAnswer') or {}).get('answers') or {}
            for question in data.get('questions') or []:
                text = question.get('question')
                key = text if text in given else question.get('id')  # some hosts key answers by id
                if key in given:
                    answers.append({'time': updated, 'thread': titles.get(thread), 'header': question.get('header'),
                                    'question': clip(text), 'answer': clip(str(given[key]))})
        return {'threads': list(threads.values()), 'answers': answers}
    finally:
        con.close()


def guarded(source):
    try:
        return source()
    except (subprocess.CalledProcessError, OSError, sqlite3.Error, ValueError, KeyError) as error:
        detail = getattr(error, 'stderr', '') or str(error)
        return {'error': f'{type(error).__name__}: {detail.strip()[:300]}'}


def collect(day, tz, cfg):
    start, end = day_window(day, tz)
    daily = cfg.get('daily', {})
    result = {'day': day.isoformat(), 'timezone': str(tz), 'start': start.isoformat(), 'end': end.isoformat()}
    result['vault'] = guarded(lambda: vault_entries(cfg.get('research_vault'), start, end))
    result['prs'] = guarded(lambda: pull_requests(start, end))
    pr_repos = {pr['repo'] for key in ('opened', 'merged') for pr in result['prs'].get(key, [])}
    roots = daily.get('repo_roots') or [str(Path.home())]
    emails = author_emails(daily.get('author_emails', []))
    result['commits'] = guarded(lambda: commits(roots, start, end, pr_repos, emails))
    t3 = daily.get('t3_state') or str(Path.home() / '.t3' / 'userdata' / 'statev2.sqlite')
    result['t3'] = guarded(lambda: t3_activity(t3, start, end))
    return result


def summary(result):
    def part(name, text):
        error = result[name].get('error')
        return f'{name}: ERROR {error}' if error else f'{name}: {text}'
    prs, t3 = result['prs'], result['t3']
    return '; '.join([
        part('vault', f"{len(result['vault'].get('entries', []))} entries"),
        part('prs', f"{len(prs.get('merged', []))} merged, {len(prs.get('opened', []))} opened"),
        part('commits', f"{sum(r['count'] for r in result['commits'].get('repos', []))} in "
                        f"{len(result['commits'].get('repos', []))} repos without a PR"),
        part('t3', f"{sum(len(t['messages']) for t in t3.get('threads', []))} messages in "
                   f"{len(t3.get('threads', []))} threads, {len(t3.get('answers', []))} answers"),
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--date', type=date.fromisoformat)
    parser.add_argument('--tz', type=ZoneInfo)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    tz = args.tz or local_zone()
    day = args.date or datetime.now(tz).date()
    cfg = json.loads(CONFIG.read_text()) if CONFIG.is_file() else {}
    result = collect(day, tz, cfg)
    text = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.out:
        args.out.write_text(text)
    else:
        sys.stdout.write(text)
    print(f"{result['day']} ({result['timezone']}): {summary(result)}", file=sys.stderr)


if __name__ == '__main__':
    main()
