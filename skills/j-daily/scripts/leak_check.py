#!/usr/bin/env python3
"""Flag anything in a draft post that may be private, as a Markdown checklist for the PR body.

It never blocks or edits the draft: the owner reviews each hit before merging.

Checks: secrets (gitleaks, if installed), email addresses, absolute home paths, repo names
from the day's collected data, and every line of the owner's deny list (case-insensitive).

Usage: leak_check.py DRAFT [--day DAY.json] [--denylist FILE]
  --denylist  default: daily.denylist in ~/.config/jstack/config.json, if set
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

CONFIG = Path(os.environ.get('JSTACK_CONFIG', '~/.config/jstack/config.json')).expanduser()
EMAIL = re.compile(r'\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b')
HOME_PATH = re.compile(r'(?:/Users/|/home/|~/)[^\s)`\'"]+')


def secrets(text):
    if not shutil.which('gitleaks'):
        return ['gitleaks is not installed, so secrets were not checked']
    done = subprocess.run(['gitleaks', 'stdin', '--no-banner', '--redact', '-f', 'json', '-r', '-', '-l', 'error'],
                          input=text, capture_output=True, text=True)
    if done.returncode == 0:
        return []
    try:
        findings = json.loads(done.stdout or '[]')
    except ValueError:
        findings = []
    if not findings:  # a nonzero exit with no report means gitleaks itself failed
        error = re.sub(r'\x1b\[[0-9;]*m', '', done.stderr).strip()[:200]  # drop terminal colours
        return [f'gitleaks failed, so secrets were not checked: {error}']
    return [f"possible secret ({f.get('RuleID')}) on line {f.get('StartLine')}" for f in findings]


def repo_names(day):
    names = set()
    for key in ('opened', 'merged'):
        names.update(pr['repo'] for pr in day.get('prs', {}).get(key, []))
    names.update(repo['repo'] for repo in day.get('commits', {}).get('repos', []))
    return sorted(names)


def check(text, day=None, deny=()):
    hits = secrets(text)
    hits += [f'email address: {match}' for match in sorted(set(EMAIL.findall(text)))]
    hits += [f'local path: {match}' for match in sorted(set(HOME_PATH.findall(text)))]
    lowered = text.lower()
    for name in repo_names(day or {}):  # report only what the draft already says, never the full name
        found = next((term for term in (name, name.split('/')[-1]) if term.lower() in lowered), None)
        if found:
            hits.append(f'repo name: {found} (fine if the repo is public)')
    hits += [f'deny list: {term}' for term in deny if term.lower() in lowered]
    return hits


def read_deny(path):
    if not path or not Path(path).expanduser().is_file():
        return []
    lines = Path(path).expanduser().read_text().splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith('#')]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('draft', type=Path)
    parser.add_argument('--day', type=Path)
    parser.add_argument('--denylist')
    args = parser.parse_args()
    cfg = json.loads(CONFIG.read_text()) if CONFIG.is_file() else {}
    deny = read_deny(args.denylist or cfg.get('daily', {}).get('denylist'))
    day = json.loads(args.day.read_text()) if args.day else None
    hits = check(args.draft.read_text(), day, deny)
    if hits:
        print('Possible private details. Check each before merging:\n')
        print('\n'.join(f'- [ ] {hit}' for hit in hits))
    else:
        print('Leak check: nothing flagged.')


if __name__ == '__main__':
    main()
