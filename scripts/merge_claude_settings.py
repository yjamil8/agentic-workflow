#!/usr/bin/env python3
"""Merge a toolkit settings profile into a Claude Code settings.json.

Only the keys in the profile (and optional model pins) are set, and list
entries are added, never removed; every other setting is preserved. An existing file that would change is backed up as
<file>.bak-<timestamp>. An unreadable or invalid file is left untouched.

Usage:
  merge_claude_settings.py --settings ~/.claude/settings.json \
      --profile config/claude-cost-settings.json \
      [--pin-models OPUS_ID,SONNET_ID,HAIKU_ID] [--toolkit-root PATH] [--add-dir DIR ...] [--dry-run]
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time

PIN_KEYS = ('ANTHROPIC_DEFAULT_OPUS_MODEL', 'ANTHROPIC_DEFAULT_SONNET_MODEL', 'ANTHROPIC_DEFAULT_HAIKU_MODEL')


def parse_pins(value):
    parts = [p.strip() for p in value.split(',')]
    if len(parts) != 3 or not all(parts):
        raise ValueError('--pin-models needs exactly three model IDs: OPUS,SONNET,HAIKU')
    return dict(zip(PIN_KEYS, parts))


def merge(current, profile, pins=None):
    """Return (merged settings, list of (key, old, new) changes) without mutating inputs.

    Objects merge key by key, lists gain the profile's missing entries (existing
    entries and their order are kept), and other values are replaced.
    """
    merged = json.loads(json.dumps(current))
    wanted = json.loads(json.dumps(profile))
    if pins:
        wanted.setdefault('env', {}).update(pins)
    changes = []
    _merge_into(merged, wanted, '', changes)
    return merged, changes


def _merge_into(target, source, prefix, changes):
    for key, value in source.items():
        label = prefix + key
        if isinstance(value, dict):
            if key not in target:
                target[key] = {}
            elif not isinstance(target[key], dict):
                raise ValueError(f'settings "{label}" is not an object; fix it by hand first')
            _merge_into(target[key], value, label + '.', changes)
        elif isinstance(value, list):
            if key not in target:
                target[key] = []
            elif not isinstance(target[key], list):
                raise ValueError(f'settings "{label}" is not a list; fix it by hand first')
            for item in value:
                if item not in target[key]:
                    target[key].append(item)
                    changes.append((label, None, item))
        elif target.get(key) != value:
            changes.append((label, target.get(key), value))
            target[key] = value


def substitute(value, root):
    """Replace the <agentic-workflow-root> placeholder in every string."""
    if isinstance(value, dict):
        return {k: substitute(v, root) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(v, root) for v in value]
    if isinstance(value, str) and root:
        return value.replace('<agentic-workflow-root>', root)
    return value


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')  # an ASCII-only console must not crash after the write
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--settings', required=True)
    ap.add_argument('--profile', required=True)
    ap.add_argument('--pin-models')
    ap.add_argument('--toolkit-root', help='replaces <agentic-workflow-root> in the profile')
    ap.add_argument('--add-dir', action='append', default=[],
                    help='also add this directory to permissions.additionalDirectories (repeatable)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)
    try:
        pins = parse_pins(a.pin_models) if a.pin_models else None
        with open(a.profile, encoding='utf-8') as f:
            profile = substitute(json.load(f), a.toolkit_root)
        for folder in a.add_dir:
            folder = os.path.abspath(os.path.expanduser(folder))
            if not os.path.isdir(folder):
                raise ValueError(f'--add-dir {folder} is not a directory')
            profile.setdefault('permissions', {}).setdefault('additionalDirectories', []).append(folder)
        current = {}
        if os.path.exists(a.settings):
            with open(a.settings, encoding='utf-8') as f:
                current = json.load(f)
            if not isinstance(current, dict):
                raise ValueError(f'{a.settings} is not a JSON object')
        merged, changes = merge(current, profile, pins)
    except (OSError, ValueError) as e:  # json.JSONDecodeError is a ValueError
        print(f'  not changed: {a.settings}: {e}', file=sys.stderr)
        return 1
    if not changes:
        print(f'  up to date: {a.settings}')
        return 0
    for key, old, new in changes:
        verb = 'would' if a.dry_run else ''
        if isinstance(new, str) and old is None and '.' in key and key.rsplit('.', 1)[1] in ('allow', 'ask', 'deny', 'environment', 'soft_deny', 'hard_deny', 'additionalDirectories'):
            print(f'  {verb + " add" if verb else "add"} {key}: {new[:100]}')
        else:
            print(f'  {verb + " set" if verb else "set"} {key}: {old if old is not None else "(unset)"} -> {new}')
    if a.dry_run:
        return 0
    # Write through a symlink (for example into a dotfiles checkout) instead of replacing it.
    target = os.path.realpath(a.settings)
    folder = os.path.dirname(target)
    os.makedirs(folder, exist_ok=True)
    if os.path.exists(target):
        backup = unique_backup(a.settings)
        shutil.copy2(target, backup)  # keeps the original's permissions: the file may hold secrets
        print(f'  backed up: {a.settings} -> {backup}')
    fd, tmp = tempfile.mkstemp(dir=folder, prefix='.settings-', suffix='.json')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write('\n')
    if os.path.exists(target):
        os.chmod(tmp, os.stat(target).st_mode & 0o777)
    os.replace(tmp, target)
    print(f'\u2713 installed: {a.settings}')
    return 0


def unique_backup(path):
    """<file>.bak-<timestamp>, with a counter when a backup from the same second exists."""
    base = f'{path}.bak-{time.strftime("%Y%m%d-%H%M%S")}'
    candidate, n = base, 1
    while os.path.lexists(candidate):
        candidate, n = f'{base}-{n}', n + 1
    return candidate

if __name__ == '__main__':
    sys.exit(main())
