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
        os.chmod(self.settings, 0o640)  # not the temp-file default, so a missing chmod fails
        self.run_merge()
        self.assertEqual(os.stat(self.settings).st_mode & 0o777, 0o640)

    def test_backup_keeps_content_and_restrictive_mode(self):
        original = json.dumps({'env': {'ANTHROPIC_API_KEY': 'secret'}})
        self.settings.write_text(original)
        os.chmod(self.settings, 0o600)
        old_umask = os.umask(0o022)
        try:
            self.run_merge()
        finally:
            os.umask(old_umask)
        (backup,) = self.backups()
        self.assertEqual(backup.read_text(), original)
        self.assertEqual(os.stat(backup).st_mode & 0o777, 0o600)

    def test_top_level_array_is_refused(self):
        self.settings.write_text('[1]')
        rc, _, err = self.run_merge()
        self.assertEqual(rc, 1)
        self.assertIn('not a JSON object', err)
        self.assertEqual(self.settings.read_text(), '[1]')

    def test_two_changes_in_one_second_keep_both_backups(self):
        self.settings.write_text(json.dumps({'env': {'A': '1'}}))
        self.run_merge()
        self.settings.write_text(json.dumps({'env': {'A': '2'}}))
        self.run_merge()
        contents = sorted(b.read_text() for b in self.backups())
        self.assertEqual(len(contents), 2)
        self.assertIn(json.dumps({'env': {'A': '1'}}), contents)

    def test_symlinked_settings_stay_a_symlink(self):
        real = Path(self.dir.name) / 'dotfiles-settings.json'
        real.write_text('{}')
        self.settings.symlink_to(real)
        self.run_merge()
        self.assertTrue(self.settings.is_symlink())
        self.assertIn('CLAUDE_CODE_PROMPT_CACHE_TTL', real.read_text())

    def test_non_ascii_text_is_preserved(self):
        self.settings.write_text(json.dumps({'statusLine': 'caf\u00e9 \u2713'}, ensure_ascii=False), encoding='utf-8')
        self.run_merge()
        self.assertIn('caf\u00e9 \u2713', self.settings.read_text(encoding='utf-8'))


PERMS = ROOT / 'config' / 'claude-permissions.json'


class PermissionsProfileTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.settings = Path(self.dir.name) / 'settings.json'

    def run_merge(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = m.main(['--settings', str(self.settings), '--profile', str(PERMS), '--toolkit-root', '/opt/aw', *extra])
        return rc, out.getvalue(), err.getvalue()

    def test_lists_are_unioned_and_existing_rules_kept_in_order(self):
        self.settings.write_text(json.dumps({'permissions': {'allow': ['Bash(make *)', 'Bash(rg *)'], 'deny': ['Read(./.env)']}}))
        rc, out, _ = self.run_merge()
        self.assertEqual(rc, 0)
        perms = json.loads(self.settings.read_text())['permissions']
        self.assertEqual(perms['allow'][:2], ['Bash(make *)', 'Bash(rg *)'])
        self.assertEqual(perms['allow'].count('Bash(rg *)'), 1)
        self.assertEqual(perms['deny'], ['Read(./.env)'])
        self.assertIn('Bash(git reset --hard *)', perms['ask'])
        self.assertEqual(perms['defaultMode'], 'auto')

    def test_toolkit_root_is_substituted_everywhere(self):
        self.run_merge()
        text = self.settings.read_text()
        self.assertNotIn('<agentic-workflow-root>', text)
        perms = json.loads(text)['permissions']
        self.assertIn('/opt/aw', perms['additionalDirectories'])
        self.assertIn('Bash(python3 /opt/aw/claude_skills/agent-table/scripts/agent_table_claude.py *)', perms['allow'])

    def test_add_dir_is_added_once(self):
        work = Path(self.dir.name) / 'work'
        work.mkdir()
        self.run_merge('--add-dir', str(work))
        rc, out, _ = self.run_merge('--add-dir', str(work))
        self.assertIn('up to date', out)
        dirs = json.loads(self.settings.read_text())['permissions']['additionalDirectories']
        self.assertEqual(dirs.count(str(work)), 1)

    def test_missing_add_dir_changes_nothing(self):
        rc, _, err = self.run_merge('--add-dir', str(Path(self.dir.name) / 'nope'))
        self.assertEqual(rc, 1)
        self.assertIn('is not a directory', err)
        self.assertFalse(self.settings.exists())

    def test_non_list_rule_field_is_refused(self):
        self.settings.write_text(json.dumps({'permissions': {'allow': 'Bash(*)'}}))
        rc, _, err = self.run_merge()
        self.assertEqual(rc, 1)
        self.assertIn('"permissions.allow" is not a list', err)

    def test_destructive_commands_ask_and_routine_ones_are_allowed(self):
        perms = json.loads(PERMS.read_text())['permissions']
        for rule in ('Bash(rm -rf *)', 'Bash(git push --force *)', 'Bash(git clean *)', 'Bash(git worktree remove *)'):
            self.assertIn(rule, perms['ask'])
        self.assertIn('Bash(rg *)', perms['allow'])
        self.assertFalse(set(perms['allow']) & set(perms['ask']))
        self.assertNotIn('Bash(*)', perms['allow'])


class InstallerFlagTests(unittest.TestCase):
    """Run the real installer against a disposable HOME."""

    def run_installer(self, *args):
        import subprocess
        home = tempfile.mkdtemp()
        self.addCleanup(__import__('shutil').rmtree, home, True)
        p = subprocess.run(['bash', str(ROOT / 'scripts' / 'install-local.sh'), *args],
                           env=dict(os.environ, HOME=home), capture_output=True, text=True)
        return p, Path(home)

    def test_bad_pins_install_nothing(self):
        p, home = self.run_installer('--cost-settings', '--pin-models', 'a,b')
        self.assertEqual(p.returncode, 1)
        self.assertFalse((home / '.claude').exists())

    def test_pins_require_cost_settings(self):
        p, _ = self.run_installer('--pin-models', 'a,b,c')
        self.assertEqual(p.returncode, 2)

    def test_unknown_option_is_rejected(self):
        p, _ = self.run_installer('--bogus')
        self.assertEqual(p.returncode, 2)

    def test_cost_settings_written_with_pins(self):
        p, home = self.run_installer('--cost-settings', '--pin-models=o,s,h')
        self.assertEqual(p.returncode, 0, p.stderr)
        env = json.loads((home / '.claude' / 'settings.json').read_text())['env']
        self.assertEqual((env['CLAUDE_CODE_AUTO_COMPACT_WINDOW'], env['ANTHROPIC_DEFAULT_HAIKU_MODEL']), ('200000', 'h'))

    def test_permissions_with_work_root(self):
        work = tempfile.mkdtemp()
        self.addCleanup(__import__('shutil').rmtree, work, True)
        p, home = self.run_installer('--permissions', '--work-root', work)
        self.assertEqual(p.returncode, 0, p.stderr)
        perms = json.loads((home / '.claude' / 'settings.json').read_text())['permissions']
        self.assertEqual(perms['additionalDirectories'], [str(ROOT), work])

    def test_work_root_requires_permissions(self):
        p, _ = self.run_installer('--work-root', '/tmp')
        self.assertEqual(p.returncode, 2)

    def test_missing_work_root_installs_nothing(self):
        p, home = self.run_installer('--permissions', '--work-root', '/nonexistent/dir')
        self.assertEqual(p.returncode, 1)
        self.assertFalse((home / '.claude').exists())

    def test_without_flag_settings_are_untouched(self):
        p, home = self.run_installer()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse((home / '.claude' / 'settings.json').exists())


if __name__ == '__main__':
    unittest.main()
