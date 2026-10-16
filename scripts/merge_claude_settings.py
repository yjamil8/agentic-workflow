#!/usr/bin/env python3
"""Merge the toolkit's cost settings into a Claude Code settings.json.

Only the keys in the profile (and optional model pins) are set; every other
setting is preserved. An existing file that would change is backed up as
<file>.bak-<timestamp>. An unreadable or invalid file is left untouched.

Usage:
  merge_claude_settings.py --settings ~/.claude/settings.json \
      --profile config/claude-cost-settings.json \
      [--pin-models OPUS_ID,SONNET_ID,HAIKU_ID] [--dry-run]
"""
import argparse
import json
import os
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
    """Return (merged settings, list of (key, old, new) changes) without mutating inputs."""
    merged = json.loads(json.dumps(current))
    wanted = dict(profile.get('env', {}))
    wanted.update(pins or {})
    env = merged.get('env')
    if env is None:
        env = merged['env'] = {}
    elif not isinstance(env, dict):
        raise ValueError('settings "env" is not an object; fix it by hand first')
    changes = []
    for key, value in wanted.items():
        if env.get(key) != value:
            changes.append((key, env.get(key), value))
            env[key] = value
    return merged, changes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--settings', required=True)
    ap.add_argument('--profile', required=True)
    ap.add_argument('--pin-models')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)
    try:
        pins = parse_pins(a.pin_models) if a.pin_models else None
        with open(a.profile) as f:
            profile = json.load(f)
        current = {}
        if os.path.exists(a.settings):
            with open(a.settings) as f:
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
        print(f'  {"would set" if a.dry_run else "set"} {key}: {old if old is not None else "(unset)"} -> {new}')
    if a.dry_run:
        return 0
    folder = os.path.dirname(os.path.abspath(a.settings))
    os.makedirs(folder, exist_ok=True)
    if os.path.exists(a.settings):
        backup = f'{a.settings}.bak-{time.strftime("%Y%m%d-%H%M%S")}'
        with open(a.settings, 'rb') as src, open(backup, 'wb') as dst:
            dst.write(src.read())
        print(f'  backed up: {a.settings} -> {backup}')
    fd, tmp = tempfile.mkstemp(dir=folder, prefix='.settings-', suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(merged, f, indent=2)
        f.write('\n')
    if os.path.exists(a.settings):
        os.chmod(tmp, os.stat(a.settings).st_mode & 0o777)
    os.replace(tmp, a.settings)
    print(f'✓ installed: {a.settings}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
