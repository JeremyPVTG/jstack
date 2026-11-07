#!/usr/bin/env python3
"""Check a j-research vault for the problems a model misses as the vault grows.

Errors (exit 1): missing or invalid frontmatter, broken wikilinks, wiki pages
missing from index.md, index entries pointing nowhere.
Warnings (exit 0): pages past their volatility window, orphan wiki pages.

Usage: vault_lint.py VAULT [--today YYYY-MM-DD]
"""
from datetime import date
from pathlib import Path
import re
import sys

WINDOWS = {'high': 30, 'medium': 90, 'low': 365}
TYPES = {'topic', 'entity', 'comparison', 'decision'}
WIKI_FIELDS = ('type', 'reviewed', 'volatility', 'sources')
RAW_FIELDS = ('url', 'captured', 'kind')
CODE = re.compile(r'```.*?```|`[^`\n]*`', re.S)
LINK = re.compile(r'\[\[([^\[\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]')


def frontmatter(text):
    if not text.startswith('---\n'):
        return None
    end = text.find('\n---', 4)
    if end < 0:
        return None
    fields = {}
    for line in text[4:end].splitlines():
        match = re.match(r'([A-Za-z_]+):\s*(.*?)\s*(?:#.*)?$', line)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def parse_date(value):
    try:
        return date.fromisoformat(value.strip('"\''))
    except ValueError:
        return None


def lint(vault, today):
    errors, warnings = [], []
    notes = [p for p in vault.rglob('*.md') if not any(part.startswith('.') for part in p.relative_to(vault).parts)]
    by_name, by_path = {}, {}
    for path in notes:
        rel = path.relative_to(vault).with_suffix('').as_posix()
        by_path[rel.lower()] = rel
        by_name.setdefault(path.stem.lower(), rel)

    def resolve(target):
        target = target.strip().removesuffix('.md').lower()
        return by_path.get(target) or by_name.get(target.rsplit('/', 1)[-1] if '/' not in target else '')

    inbound = {}
    for path in notes:
        rel = path.relative_to(vault).with_suffix('').as_posix()
        text = path.read_text(errors='replace')
        for target in LINK.findall(CODE.sub('', text)):
            found = resolve(target)
            if found is None:
                errors.append(f'{rel}: broken link [[{target}]]')
            elif found != rel:
                inbound.setdefault(found, set()).add(rel)
        if rel.startswith('wiki/'):
            fields = frontmatter(text)
            missing = [f for f in WIKI_FIELDS if not fields or f not in fields]
            if missing:
                errors.append(f'{rel}: missing frontmatter {", ".join(missing)}')
                continue
            if fields['type'] not in TYPES:
                errors.append(f'{rel}: type must be one of {", ".join(sorted(TYPES))}')
            reviewed = parse_date(fields['reviewed'])
            if reviewed is None:
                errors.append(f'{rel}: reviewed must be YYYY-MM-DD')
            elif fields['volatility'] not in WINDOWS:
                errors.append(f'{rel}: volatility must be high, medium, or low')
            elif (today - reviewed).days > WINDOWS[fields['volatility']]:
                warnings.append(f'{rel}: stale, reviewed {reviewed} ({fields["volatility"]} volatility)')
        elif rel.startswith('raw/'):
            fields = frontmatter(text)
            missing = [f for f in RAW_FIELDS if not fields or not fields.get(f)]
            if missing:
                errors.append(f'{rel}: missing frontmatter {", ".join(missing)}')

    indexed = {target for target, sources in inbound.items() if 'index' in sources}
    for rel in sorted(r for r in by_path.values() if r.startswith('wiki/')):
        if rel not in indexed:
            errors.append(f'{rel}: not listed in index.md')
        if not (inbound.get(rel, set()) - {'index'}):
            warnings.append(f'{rel}: orphan, no other page links to it')
    return errors, warnings


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    vault = Path(argv[1]).expanduser()
    today = date.today()
    if '--today' in argv:
        today = date.fromisoformat(argv[argv.index('--today') + 1])
    if not (vault / 'index.md').exists():
        print(f'Not a vault (no index.md): {vault}')
        return 2
    errors, warnings = lint(vault, today)
    for line in errors:
        print('ERROR', line)
    for line in warnings:
        print('WARN ', line)
    print(f'{len(errors)} errors, {len(warnings)} warnings')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
