import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import merge_claude_settings as m

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'config' / 'claude-cost-settings.json'


class MergeSettingsTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.settings = Path(self.dir.name) / 'settings.json'

    def run_merge(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = m.main(['--settings', str(self.settings), '--profile', str(PROFILE), *extra])
        return rc, out.getvalue(), err.getvalue()

    def backups(self):
        return list(Path(self.dir.name).glob('settings.json.bak-*'))

    def test_creates_settings_when_missing(self):
        rc, out, _ = self.run_merge()
        self.assertEqual(rc, 0)
        env = json.loads(self.settings.read_text())['env']
        self.assertEqual(env['CLAUDE_CODE_AUTO_COMPACT_WINDOW'], '200000')
        self.assertEqual(env['CLAUDE_CODE_PROMPT_CACHE_TTL'], '1h')
        self.assertEqual(env['CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL'], '5m')
        self.assertEqual(self.backups(), [])

    def test_preserves_other_settings_and_backs_up(self):
        self.settings.write_text(json.dumps({'model': 'opus', 'hooks': {'x': 1}, 'env': {'KEEP': 'me', 'CLAUDE_CODE_AUTO_COMPACT_WINDOW': '500000'}}))
        rc, out, _ = self.run_merge()
        self.assertEqual(rc, 0)
        data = json.loads(self.settings.read_text())
        self.assertEqual((data['model'], data['hooks'], data['env']['KEEP']), ('opus', {'x': 1}, 'me'))
        self.assertEqual(data['env']['CLAUDE_CODE_AUTO_COMPACT_WINDOW'], '200000')
        self.assertIn('500000 -> 200000', out)
        self.assertEqual(len(self.backups()), 1)

    def test_rerun_is_a_no_op(self):
        self.run_merge()
        rc, out, _ = self.run_merge()
        self.assertEqual(rc, 0)
        self.assertIn('up to date', out)
        self.assertEqual(self.backups(), [])

    def test_dry_run_writes_nothing(self):
        rc, out, _ = self.run_merge('--dry-run')
        self.assertEqual(rc, 0)
        self.assertIn('would set', out)
        self.assertFalse(self.settings.exists())

    def test_pin_models(self):
        rc, _, _ = self.run_merge('--pin-models', 'claude-opus-5,claude-sonnet-5,claude-sonnet-5')
        env = json.loads(self.settings.read_text())['env']
        self.assertEqual(env['ANTHROPIC_DEFAULT_OPUS_MODEL'], 'claude-opus-5')
        self.assertEqual(env['ANTHROPIC_DEFAULT_HAIKU_MODEL'], 'claude-sonnet-5')

    def test_bad_pin_list_changes_nothing(self):
        rc, _, err = self.run_merge('--pin-models', 'only-one')
        self.assertEqual(rc, 1)
        self.assertIn('three model IDs', err)
        self.assertFalse(self.settings.exists())

    def test_invalid_json_is_left_untouched(self):
        self.settings.write_text('{not json')
        rc, _, err = self.run_merge()
        self.assertEqual(rc, 1)
        self.assertEqual(self.settings.read_text(), '{not json')
        self.assertEqual(self.backups(), [])

    def test_non_object_env_is_refused(self):
        self.settings.write_text(json.dumps({'env': ['x']}))
        rc, _, err = self.run_merge()
        self.assertEqual(rc, 1)
        self.assertIn('"env" is not an object', err)

    def test_file_mode_is_kept(self):
        self.settings.write_text('{}')
        os.chmod(self.settings, 0o600)
        self.run_merge()
        self.assertEqual(os.stat(self.settings).st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
