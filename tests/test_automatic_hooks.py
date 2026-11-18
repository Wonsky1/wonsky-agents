"""Default recovery setup uses temporary homes and real installer entry points."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AutomaticHookTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.package = self.root / 'package'
        shutil.copytree(ROOT / 'scripts', self.package / 'scripts',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copytree(ROOT / 'skills/session-ledger', self.package / 'skills/session-ledger')
        shutil.copy2(ROOT / 'install.py', self.package / 'install.py')
        self.home = self.root / 'home'
        self.canonical = self.home / '.wonsky-agents'
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                        CODEX_HOME=str(self.home / '.codex'), COPILOT_HOME=str(self.home / '.copilot'),
                        WONSKY_AGENTS_HOME=str(self.canonical))

    def install(self, *args):
        return subprocess.run([sys.executable, '-B', str(self.package / 'install.py'),
                               '--targets', 'claude,codex,cursor,antigravity,agents,copilot', *args],
                              env=self.env, capture_output=True, text=True, timeout=30)

    def configs(self):
        return [self.home / name for name in ('.claude/settings.json', '.codex/hooks.json',
                                              '.cursor/hooks.json', '.gemini/config/hooks.json',
                                              '.copilot/hooks/wonsky-session-ledger.json')]

    def test_install_previews_then_configures_all_supported_hosts_idempotently(self):
        preview = self.install('--dry-run')
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn('Recovery hook', preview.stdout)
        self.assertFalse(self.home.exists())
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        before = {p: p.read_bytes() for p in self.configs()}
        self.assertFalse((self.home / '.agents/hooks.json').exists())
        if os.name != 'nt':
            for data in before.values():
                self.assertIn(str(self.canonical), data.decode())
        repeat = self.install('--sync-only')
        self.assertEqual(repeat.returncode, 0, repeat.stdout + repeat.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in self.configs()})

    def test_opt_out_copies_skills_without_configuring_hooks(self):
        result = self.install('--no-session-hooks')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.canonical / 'skills/session-ledger/scripts/ledger.py').is_file())
        self.assertFalse(any(p.exists() for p in self.configs()))

    def test_invalid_settings_are_preserved_and_prevent_partial_install(self):
        config = self.configs()[0]
        config.parent.mkdir(parents=True)
        config.write_text('{invalid', encoding='utf-8')
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(config.read_text(), '{invalid')
        self.assertFalse(self.canonical.exists())


if __name__ == '__main__':
    unittest.main()
