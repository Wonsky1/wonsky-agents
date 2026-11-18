"""Copilot detection and CLI integration use temporary homes and repositories."""

import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys
import tempfile
import unittest

from scripts.installation.targets import detect_targets
from scripts.hooks.definitions import hook_entry
from scripts.hooks.files import apply_hook_plan
from scripts.installation.models.target import Target
from scripts.hooks.setup import plan_hook
from scripts.skills.distribution import distribution_issue


ROOT = Path(__file__).resolve().parents[1]


class CopilotTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def detected(self, environment=None, commands=()):
        return detect_targets(self.root, 'Linux', environment or {},
                              lambda name: name if name in commands else None)

    def copilot(self, **kwargs):
        return next(target for target in self.detected(**kwargs) if target.key == 'copilot')

    def target(self):
        return Target('copilot', 'GitHub Copilot', self.root / '.copilot/skills', True)

    def plan(self, action='install', system='Linux'):
        return plan_hook(self.target(), ROOT, Path(sys.executable), system, action)

    def test_target_appended_preserves_indices_and_personal_path(self):
        targets = self.detected()
        self.assertEqual([target.key for target in targets],
                         ['cursor', 'claude', 'codex', 'antigravity', 'agents', 'copilot'])
        self.assertEqual(targets[-1].path, self.root / '.copilot/skills')
        self.assertFalse(targets[-1].detected)

    def test_config_cli_and_override_detection(self):
        self.assertTrue(self.copilot(commands=('copilot',)).detected)
        (self.root / '.copilot').mkdir()
        self.assertTrue(self.copilot().detected)
        custom = self.root / 'custom copilot'
        custom.mkdir()
        target = self.copilot(environment={'COPILOT_HOME': str(custom)})
        self.assertTrue(target.detected)
        self.assertEqual(target.path, custom / 'skills')

    def test_vscode_alone_does_not_detect_copilot(self):
        (self.root / '.vscode').mkdir()
        (self.root / '.config/Code').mkdir(parents=True)
        self.assertFalse(self.copilot(commands=('code',)).detected)

    def test_installed_copilot_extensions_detected(self):
        for editor in ('.vscode', '.vscode-insiders'):
            for extension in ('github.copilot-1.400.0', 'github.copilot-chat-0.35.0'):
                with self.subTest(editor=editor, extension=extension):
                    path = self.root / editor / 'extensions' / extension
                    path.mkdir(parents=True)
                    self.assertTrue(self.copilot().detected)
                    path.rmdir()

    def test_remote_server_supported(self):
        self.assertIsNone(distribution_issue('remote-server', 'copilot'))

    def test_direct_command_schema_on_every_platform(self):
        for system in ('Linux', 'Darwin', 'Windows'):
            with self.subTest(system=system):
                plan = self.plan(system=system)
                self.assertEqual(plan.config, self.root / '.copilot/hooks/wonsky-session-ledger.json')
                self.assertEqual(plan.state, self.root / '.copilot/.wonsky-state/session-ledger-hook.json')
                self.assertEqual(plan.entry, {
                    'type': 'command', 'exec': str(Path(sys.executable)),
                    'args': ['-B', str(ROOT / 'skills/session-ledger/scripts/ledger.py'),
                             'hook', '--host', 'copilot'], 'timeoutSec': 10})
                self.assertEqual(json.loads(plan.after), {'version': 1, 'hooks': {'sessionStart': [plan.entry]}})

    def test_merge_idempotency_remove_preserve_settings_and_other_hook_files(self):
        config = self.root / '.copilot/hooks/wonsky-session-ledger.json'
        config.parent.mkdir(parents=True)
        personal = config.with_name('personal.json')
        personal.write_text('{"personal":true}', encoding='utf-8')
        settings = config.parent.parent / 'config.json'
        settings.write_text('{"private":"preserved"}', encoding='utf-8')
        config.write_text(json.dumps({'version': 1, 'hooks': {'sessionStart': [
            {'type': 'command', 'exec': 'personal-command'}]}, 'personal': True}), encoding='utf-8')
        apply_hook_plan(self.plan())
        installed = config.read_bytes()
        self.assertEqual(self.plan().status, 'unchanged')
        apply_hook_plan(self.plan())
        self.assertEqual(config.read_bytes(), installed)
        apply_hook_plan(self.plan('remove'))
        result = json.loads(config.read_text())
        self.assertEqual(result['hooks']['sessionStart'], [{'type': 'command', 'exec': 'personal-command'}])
        self.assertTrue(result['personal'])
        self.assertEqual(personal.read_text(), '{"personal":true}')
        self.assertEqual(settings.read_text(), '{"private":"preserved"}')
        self.assertEqual(self.plan('status').status, 'absent')

    def test_windows_paths_remain_literal_argument_values(self):
        canonical = PureWindowsPath(r"C:\Users\O'Brien & Co\collection")
        python = PureWindowsPath(r'C:\Program Files\Python\python.exe')
        entry = hook_entry('copilot', canonical, python, 'Windows')
        self.assertEqual(entry['exec'], str(python))
        self.assertEqual(entry['args'][1], str(canonical / 'skills/session-ledger/scripts/ledger.py'))
        self.assertEqual(entry['args'][-2:], ['--host', 'copilot'])
        self.assertNotIn('command', entry)

    def test_unsupported_hook_version_preserved(self):
        config = self.root / '.copilot/hooks/wonsky-session-ledger.json'
        config.parent.mkdir(parents=True)
        config.write_text('{"version":2,"hooks":{}}')
        with self.assertRaisesRegex(ValueError, 'version'):
            self.plan()
        self.assertEqual(config.read_text(), '{"version":2,"hooks":{}}')

    def test_generated_command_runs_helper_lazily(self):
        repo = self.root / 'repository with spaces'
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        entry = self.plan().entry
        result = subprocess.run([entry['exec'], *entry['args']],
                                input=json.dumps({'sessionId': 'copilot-123', 'cwd': str(repo)}),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--host copilot', json.loads(result.stdout)['additionalContext'])
        self.assertIn('--session copilot-123', result.stdout)
        self.assertFalse((repo / '.agent-ledger').exists())


if __name__ == '__main__':
    unittest.main()
