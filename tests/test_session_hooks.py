"""Hook setup operates only on temporary user configuration."""

import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

from scripts.models.target import Target
from scripts.hook_files import apply_hook_plan
from scripts.session_hooks import plan_hook

ROOT = Path(__file__).resolve().parents[1]


class SessionHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.canonical = self.root / 'collection with spaces'
        helper = self.canonical / 'skills/session-ledger/scripts/ledger.py'
        helper.parent.mkdir(parents=True)
        helper.write_text('# helper', encoding='utf-8')

    def target(self, host):
        return Target(host, host, self.root / host / 'skills', True)

    def plan(self, host='claude', action='install', system='Linux'):
        return plan_hook(self.target(host), self.canonical, Path(sys.executable), system, action)

    def test_preview_writes_nothing(self):
        plan = self.plan()
        self.assertEqual(plan.status, 'add')
        self.assertFalse((self.root / 'claude').exists())

    def test_merge_repeat_and_remove_preserve_other_settings(self):
        for host in ('claude', 'codex', 'cursor', 'antigravity'):
            with self.subTest(host=host):
                target = self.target(host)
                config = target.path.parent / ('settings.json' if host == 'claude' else 'hooks.json')
                config.parent.mkdir()
                original = {'personal': {'keep': True}}
                if host != 'antigravity':
                    original['hooks'] = {'Stop': [{'command': 'personal-command'}]}
                config.write_text(json.dumps(original), encoding='utf-8')
                plan = self.plan(host)
                apply_hook_plan(plan)
                installed = config.read_bytes()
                self.assertEqual(self.plan(host).status, 'unchanged')
                apply_hook_plan(self.plan(host))
                self.assertEqual(config.read_bytes(), installed)
                # Unrelated user edits after setup must survive removal.
                current = json.loads(config.read_text())
                current['later'] = 42
                config.write_text(json.dumps(current))
                apply_hook_plan(self.plan(host, 'remove'))
                result = json.loads(config.read_text())
                self.assertEqual(result['personal'], original['personal'])
                self.assertEqual(result['later'], 42)
                if host != 'antigravity':
                    self.assertEqual(result['hooks']['Stop'], original['hooks']['Stop'])
                self.assertEqual(self.plan(host, 'status').status, 'absent')
                self.assertTrue(list(config.parent.glob('.wonsky-state/hook-backups/*/*')))

    def test_modified_owned_hook_is_not_overwritten(self):
        plan = self.plan()
        apply_hook_plan(plan)
        config = plan.config
        doc = json.loads(config.read_text())
        doc['hooks']['SessionStart'][0]['hooks'][0]['timeout'] = 99
        config.write_text(json.dumps(doc))
        before = config.read_bytes()
        for action in ('install', 'remove', 'status'):
            self.assertEqual(self.plan(action=action).status, 'conflict')
        self.assertEqual(config.read_bytes(), before)

    def test_invalid_config_is_never_replaced(self):
        config = self.target('claude').path.parent / 'settings.json'
        config.parent.mkdir()
        config.write_text('{invalid')
        with self.assertRaises(ValueError):
            self.plan()
        self.assertEqual(config.read_text(), '{invalid')

    def test_stale_plan_rejected(self):
        plan = self.plan()
        plan.config.parent.mkdir()
        plan.config.write_text('{"new":"user edit"}')
        with self.assertRaises(ValueError):
            apply_hook_plan(plan)
        self.assertEqual(json.loads(plan.config.read_text()), {'new': 'user edit'})

    def test_state_symlink_rejected_without_touching_target(self):
        state = self.target('claude').path.parent / '.wonsky-state'
        state.parent.mkdir()
        outside = self.root / 'outside'
        outside.mkdir()
        try:
            state.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('symlink creation not available')
        with self.assertRaises(ValueError):
            self.plan()
        self.assertEqual(list(outside.iterdir()), [])

    def test_shared_agents_target_has_no_hook_runtime(self):
        self.assertEqual(self.plan('agents').status, 'unsupported')

    def test_claude_uses_direct_argument_vector(self):
        plan = self.plan()
        handler = plan.entry['hooks'][0]
        self.assertEqual(handler['command'], str(Path(sys.executable)))
        self.assertEqual(handler['args'], ['-B', str(self.canonical / 'skills/session-ledger/scripts/ledger.py'), 'hook', '--host', 'claude'])

    def test_windows_shell_command_contains_no_raw_user_path(self):
        for host in ('codex', 'cursor', 'antigravity'):
            plan = self.plan(host, system='Windows')
            self.assertIn('-EncodedCommand', json.dumps(plan.entry))
            self.assertNotIn(str(self.canonical), json.dumps(plan.entry))

    def test_state_failure_restores_previous_config(self):
        from scripts.hook_files import replace_file
        plan = self.plan()
        def fail_state(path, data):
            if path == plan.state:
                raise OSError('state write failed')
            replace_file(path, data)
        with mock.patch('scripts.hook_files.replace_file', side_effect=fail_state):
            with self.assertRaises(OSError):
                apply_hook_plan(plan)
        self.assertFalse(plan.config.exists())

    def test_duplicate_json_keys_are_preserved_as_conflict(self):
        config = self.target('claude').path.parent / 'settings.json'
        config.parent.mkdir()
        config.write_text('{"hooks":{},"hooks":{}}')
        with self.assertRaises(ValueError):
            self.plan()

    def test_cli_setup_does_not_sync_skills_or_print_unrelated_settings(self):
        config = self.target('codex').path.parent / 'hooks.json'
        config.parent.mkdir()
        config.write_text('{"personal":"DO_NOT_PRINT_THIS"}')
        env = dict(os.environ, HOME=str(self.root), USERPROFILE=str(self.root),
                   WONSKY_AGENTS_HOME=str(ROOT), CODEX_HOME=str(config.parent))
        base = [sys.executable, '-B', str(ROOT / 'install.py'), '--targets', 'codex', '--session-hooks']
        preview = subprocess.run([*base, 'install', '--dry-run'], env=env, capture_output=True, text=True)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertNotIn('DO_NOT_PRINT_THIS', preview.stdout + preview.stderr)
        self.assertFalse((config.parent / '.wonsky-state').exists())
        installed = subprocess.run([*base, 'install'], env=env, capture_output=True, text=True)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertFalse((config.parent / 'skills').exists())
        status = subprocess.run([*base, 'status'], env=env, capture_output=True, text=True)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn('host execution is not verified', status.stdout)
        removed = subprocess.run([*base, 'remove'], env=env, capture_output=True, text=True)
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertEqual(json.loads(config.read_text())['personal'], 'DO_NOT_PRINT_THIS')

    @unittest.skipIf(os.name == 'nt', 'POSIX command execution; Windows schemas are checked separately')
    def test_generated_host_commands_run_actual_helper(self):
        repo = self.root / 'test repository'
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        for host in ('claude', 'codex', 'cursor', 'antigravity'):
            plan = plan_hook(self.target(host), ROOT, Path(sys.executable), 'Linux', 'install')
            if host == 'antigravity':
                handler = plan.entry['SessionStart'][0]
                payload = {'conversationId': 'smoke-test', 'workspacePaths': [str(repo)]}
            else:
                handler = plan.entry if host == 'cursor' else plan.entry['hooks'][0]
                payload = {'session_id': 'smoke-test', 'cwd': str(repo), 'workspace_roots': [str(repo)]}
            command = [handler['command'], *handler['args']] if 'args' in handler else ['/bin/sh', '-c', handler['command']]
            result = subprocess.run(command, input=json.dumps(payload), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--host ' + host, result.stdout)
            self.assertIsInstance(json.loads(result.stdout), dict)
        self.assertFalse((repo / '.agent-ledger').exists(), 'lazy hooks must not create empty ledgers')


if __name__ == '__main__':
    unittest.main()
