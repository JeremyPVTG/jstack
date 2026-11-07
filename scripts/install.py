#!/usr/bin/env python3
"""Link owned skills into explicit target directories; preserve replaced entries."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def present(path):
    return path.exists() or path.is_symlink()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.receipt-')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def install(args):
    packs = json.loads((ROOT / 'packs.json').read_text())
    names = args.skill or packs[args.pack]
    sources = []
    for name in dict.fromkeys(names):
        if '/' in name or name in ('.', '..'):
            raise ValueError('Invalid skill name')
        source = ROOT / 'skills' / name
        if not (source / 'SKILL.md').is_file():
            raise ValueError('Unknown skill: ' + name)
        sources.append(source)
    target = Path(args.target).expanduser().absolute()
    if target.resolve() == ROOT / 'skills' or ROOT in target.resolve().parents:
        raise ValueError('Target must be outside jstack')
    state = Path(args.state_dir).expanduser().absolute()
    plans = []
    for source in sources:
        dest = target / source.name
        if dest.is_symlink() and dest.resolve() == source.resolve():
            print('unchanged:', dest)
            continue
        print(('replace with backup:' if present(dest) else 'link:'), dest, '->', source)
        plans.append((source, dest))
    if args.dry_run or not plans:
        return
    run = state / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    receipt = {'version': 1, 'root': str(ROOT), 'entries': []}
    target.mkdir(parents=True, exist_ok=True)
    for source, dest in plans:
        backup = run / 'backup' / dest.name
        entry = {'destination': str(dest), 'source': str(source), 'backup': str(backup) if present(dest) else None, 'status': 'planned'}
        receipt['entries'].append(entry)
        save(run / 'receipt.json', receipt)
        if entry['backup']:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dest), str(backup))
        entry['status'] = 'backed-up'
        save(run / 'receipt.json', receipt)
        dest.symlink_to(source, target_is_directory=True)
        entry['status'] = 'linked'
        save(run / 'receipt.json', receipt)
    print('receipt:', run / 'receipt.json')


def rollback(args):
    path = Path(args.receipt).expanduser().resolve()
    receipt = json.loads(path.read_text())
    # Receipts are local trusted state, not files to accept from other people.
    actions = []
    for entry in reversed(receipt['entries']):
        dest = Path(entry['destination'])
        source = Path(entry['source'])
        backup = Path(entry['backup']) if entry['backup'] else None
        if entry['status'] == 'restored':
            continue
        if present(dest) and not (dest.is_symlink() and os.readlink(dest) == str(source)):
            raise ValueError('Refusing to replace a changed destination: ' + str(dest))
        if backup and not present(backup):
            if entry['status'] == 'planned' and present(dest):
                continue
            raise ValueError('Missing backup: ' + str(backup))
        actions.append((entry, dest, backup))
    for entry, dest, backup in actions:
        print('restore:', dest)
        if args.dry_run:
            continue
        if dest.is_symlink():
            dest.unlink()
        if backup:
            shutil.move(str(backup), str(dest))
        entry['status'] = 'restored'
        save(path, receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('install')
    add.add_argument('--target', required=True, help='Explicit agent skills directory')
    add.add_argument('--pack', choices=sorted(json.loads((ROOT / 'packs.json').read_text())), default='core')
    add.add_argument('--skill', action='append', help='Select an owned skill; repeatable')
    add.add_argument('--state-dir', default='~/.local/state/jstack')
    add.add_argument('--dry-run', action='store_true')
    undo = sub.add_parser('rollback')
    undo.add_argument('receipt')
    undo.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        (install if args.command == 'install' else rollback)(args)
    except (OSError, ValueError, KeyError) as error:
        print('jstack:', error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
