"""Manual-only skills never reach runtimes that cannot enforce invocation policy."""

from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

from scripts.models.target import Target
from scripts.update_apply import apply_plan
from scripts.update_collection import canonical_plans, runtime_plans
from scripts.update_review import default_choice


class ManualSkillDistributionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        skill = self.source / 'skills/remote-server'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('---\nname: remote-server\ndescription: Manual SSH\n---\nRemote\n')
        self.canonical = self.root / 'canonical'
        self.plans = canonical_plans(self.source, self.canonical)
        self.choices = {plan.id: default_choice(plan) for plan in self.plans}

    def target(self, key):
        return Target(key, key, self.root / key / 'skills', True)

    def test_unsupported_runtime_preview_skips_skill_without_creating_files(self):
        for key in ('antigravity', 'agents'):
            with self.subTest(key=key), redirect_stdout(io.StringIO()) as output:
                target = self.target(key)
                plans = runtime_plans(self.plans, self.choices, [target])
                self.assertEqual(plans, [])
                self.assertFalse(target.path.exists())
                self.assertIn('manual-only', output.getvalue())
                self.assertIn(str(self.canonical / 'skills/remote-server/SKILL.md'), output.getvalue())

    def test_supported_runtimes_receive_skill(self):
        for key in ('codex', 'claude', 'cursor'):
            with self.subTest(key=key):
                target = self.target(key)
                plans = runtime_plans(self.plans, self.choices, [target])
                self.assertEqual(len(plans), 1)
                self.assertEqual(plans[0].destination, target.path / 'remote-server')
                self.assertFalse(plans[0].blocked)

    def test_existing_unsupported_copy_is_blocked_and_preserved_even_when_canonical_kept(self):
        for key in ('antigravity', 'agents'):
            for choice in ('keep', 'update'):
                with self.subTest(key=key, choice=choice):
                    target = self.target(key)
                    destination = target.path / 'remote-server'
                    destination.mkdir(parents=True, exist_ok=True)
                    manifest = destination / 'SKILL.md'
                    manifest.write_text('personal previous skill\n')
                    choices = dict(self.choices, **{self.plans[1].id: choice})
                    plans = runtime_plans(self.plans, choices, [target])
                    self.assertEqual(len(plans), 1)
                    self.assertTrue(plans[0].blocked)
                    self.assertIn('remove', plans[0].blocked[0])
                    self.assertEqual(default_choice(plans[0]), 'keep')
                    apply_plan(plans[0], 'keep', self.root / 'backups')
                    self.assertEqual(manifest.read_text(), 'personal previous skill\n')
                    self.assertFalse((target.path / '.wonsky-state').exists())

    def test_existing_unsupported_symlink_is_rejected_without_following_or_removing_it(self):
        target = self.target('agents')
        target.path.mkdir(parents=True)
        outside = self.root / 'outside'
        outside.mkdir()
        sentinel = outside / 'SKILL.md'
        sentinel.write_text('unrelated file\n')
        destination = target.path / 'remote-server'
        try:
            destination.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('symlink creation not available')
        with self.assertRaisesRegex(ValueError, 'manual-only'):
            runtime_plans(self.plans, self.choices, [target])
        self.assertTrue(destination.is_symlink())
        self.assertEqual(sentinel.read_text(), 'unrelated file\n')

    def test_installer_sync_applies_same_manual_only_boundary(self):
        repo = Path(__file__).resolve().parents[1]
        env = dict(os.environ, HOME=str(self.root), USERPROFILE=str(self.root),
                   WONSKY_AGENTS_HOME=str(self.source), CODEX_HOME=str(self.root / '.codex'))
        result = subprocess.run([sys.executable, '-B', str(repo / 'install.py'), '--sync-only',
                                 '--targets', 'codex,agents,antigravity'], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / '.codex/skills/remote-server/SKILL.md').is_file())
        self.assertFalse((self.root / '.agents/skills/remote-server').exists())
        self.assertFalse((self.root / '.gemini/config/skills/remote-server').exists())
        self.assertIn('manual-only', result.stdout)


if __name__ == '__main__':
    unittest.main()
