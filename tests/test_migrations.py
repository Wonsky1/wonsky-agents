"""Real install/update entry points upgrade legacy runtime layouts safely."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts.filesystem.managed import snapshot
from scripts.installation.targets import detect_targets
from scripts.migrations.apply import apply_migration
from scripts.migrations.registry import plan_migrations
from scripts.skills.files import install_collection, sync_skill


ROOT = Path(__file__).resolve().parents[1]


class NamespaceMigrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.package = self.root / 'offered'
        shutil.copytree(ROOT / 'scripts', self.package / 'scripts',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ('install.py', 'update.py'):
            shutil.copy2(ROOT / name, self.package / name)
        self.source = self.package / 'skills/sample'
        self.source.mkdir(parents=True)
        self.original = '---\nname: sample\ndescription: Original workflow.\n---\nOriginal\n'
        (self.source / 'SKILL.md').write_text(self.original, encoding='utf-8')
        self.home = self.root / 'home'
        self.canonical = self.home / '.wonsky-agents'
        shutil.copytree(self.package, self.canonical)
        self.runtime = self.home / '.codex/skills'
        self.legacy = self.runtime / 'sample'
        self.destination = self.runtime / 'wa-sample'
        sync_skill(self.source, self.legacy)
        (self.legacy / 'personal.txt').write_text('local extra', encoding='utf-8')
        (self.source / 'SKILL.md').write_text(self.original.replace('name: sample', 'name: wa-sample'), encoding='utf-8')
        shutil.copy2(self.source / 'SKILL.md', self.canonical / 'skills/sample/SKILL.md')
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                        CODEX_HOME=str(self.home / '.codex'), WONSKY_AGENTS_HOME=str(self.canonical))

    def run_program(self, name='install.py', *args):
        command = [sys.executable, '-B', str(self.package / name), '--targets', 'codex', '--no-session-hooks']
        command += ['--from', str(self.package)] if name == 'update.py' else ['--sync-only']
        return subprocess.run([*command, *args], env=self.env, capture_output=True, text=True, timeout=30)

    def test_installer_previews_then_migrates_with_backup_and_journal(self):
        before = snapshot(self.home)
        preview = self.run_program('install.py', '--dry-run')
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertIn('0001-wa-skill-namespace', preview.stdout)
        self.assertEqual(snapshot(self.home), before)
        result = self.run_program()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.legacy.exists())
        self.assertEqual((self.destination / 'personal.txt').read_text(), 'local extra')
        self.assertIn('name: wa-sample', (self.destination / 'SKILL.md').read_text())
        self.assertFalse((self.runtime / '.wonsky-state/sample.json').exists())
        self.assertTrue((self.runtime / '.wonsky-state/wa-sample.json').is_file())
        journals = list((self.runtime / '.wonsky-state/migrations').rglob('sample.json'))
        self.assertEqual(len(journals), 1)
        journal = json.loads(journals[0].read_text())
        self.assertEqual(journal['status'], 'complete')
        backup = Path(journal['backup'])
        self.assertEqual((backup / 'files/SKILL.md').read_text(), self.original)
        self.assertEqual((backup / 'files/personal.txt').read_text(), 'local extra')
        before = snapshot(self.home)
        repeated = self.run_program()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(snapshot(self.home), before)

    def test_both_owned_names_block_migration_before_writing(self):
        sync_skill(self.source, self.destination)
        before = snapshot(self.home)
        result = self.run_program()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(snapshot(self.home), before)

    def test_unknown_personal_legacy_folder_is_preserved(self):
        (self.runtime / '.wonsky-state/sample.json').unlink()
        (self.legacy / 'SKILL.md').write_text('unrelated personal skill', encoding='utf-8')
        result = self.run_program()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.legacy / 'SKILL.md').read_text(), 'unrelated personal skill')
        self.assertTrue((self.destination / 'SKILL.md').is_file())

    def test_edited_owned_instructions_are_reported_without_writes(self):
        (self.legacy / 'SKILL.md').write_text('locally edited instructions', encoding='utf-8')
        before = snapshot(self.home)
        result = self.run_program()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(snapshot(self.home), before)

    def test_updater_reviews_migration_and_preserves_local_extras(self):
        report = self.root / 'review.json'
        before = snapshot(self.home)
        preview = self.run_program('update.py', '--dry-run', '--report', str(report))
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertEqual(snapshot(self.home), before)
        reviewed = json.loads(report.read_text())
        self.assertEqual(len(reviewed['migrations']), 1)
        self.assertEqual(reviewed['migrations'][0]['status'], 'ready')
        result = self.run_program('update.py', '--decisions', str(report), '--yes')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.legacy.exists())
        self.assertEqual((self.destination / 'personal.txt').read_text(), 'local extra')
        self.assertIn('name: wa-sample', (self.destination / 'SKILL.md').read_text())

    def test_trusted_new_updater_upgrades_an_owned_old_canonical_install(self):
        offered = (self.source / 'SKILL.md').read_bytes()
        shutil.rmtree(self.canonical)
        (self.source / 'SKILL.md').write_text(self.original, encoding='utf-8')
        install_collection(self.package, self.canonical)
        (self.source / 'SKILL.md').write_bytes(offered)
        result = self.run_program('update.py', '--yes')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.legacy.exists())
        self.assertEqual((self.destination / 'SKILL.md').read_bytes(), offered)
        self.assertEqual((self.canonical / 'skills/sample/SKILL.md').read_bytes(), offered)
        self.assertEqual((self.destination / 'personal.txt').read_text(), 'local extra')

    def test_updater_rejects_changed_migration_before_any_write(self):
        report = self.root / 'review.json'
        preview = self.run_program('update.py', '--dry-run', '--report', str(report))
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        (self.legacy / 'personal.txt').write_text('changed after review', encoding='utf-8')
        before = snapshot(self.home)
        result = self.run_program('update.py', '--decisions', str(report), '--yes')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(snapshot(self.home), before)

    def migration(self):
        target = next(target for target in detect_targets(self.home, 'Linux', self.env, lambda name: None)
                      if target.key == 'codex')
        return plan_migrations([self.source], [target])[0]

    def test_journal_failure_rolls_back_folder_and_ownership(self):
        plan = self.migration()
        files, state = snapshot(self.legacy), plan.state_source.read_bytes()
        with mock.patch('scripts.migrations.apply._write_journal', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'original restored'):
                apply_migration(plan)
        self.assertEqual(snapshot(self.legacy), files)
        self.assertEqual(plan.state_source.read_bytes(), state)
        self.assertFalse(self.destination.exists())
        self.assertFalse(plan.state_destination.exists())
        self.assertFalse(plan.journal.exists())
        self.assertTrue(list((self.runtime / '.wonsky-state/migration-backups').rglob('manifest.json')))

    def test_destination_appearing_after_preview_is_preserved(self):
        plan = self.migration()
        self.destination.mkdir()
        (self.destination / 'personal').write_text('another writer', encoding='utf-8')
        before = snapshot(self.home)
        with self.assertRaisesRegex(ValueError, 'changed after preview'):
            apply_migration(plan)
        self.assertEqual(snapshot(self.home), before)

    def test_explicit_baseline_migrates_an_untracked_byte_identical_old_copy(self):
        baseline = self.root / 'trusted previous collection/skills/sample'
        baseline.mkdir(parents=True)
        (baseline / 'SKILL.md').write_text(self.original, encoding='utf-8')
        (self.runtime / '.wonsky-state/sample.json').unlink()
        result = self.run_program('install.py', '--baseline', str(baseline.parents[1]))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.legacy.exists())
        self.assertEqual((self.destination / 'personal.txt').read_text(), 'local extra')

    def test_runtime_keep_also_keeps_its_migration(self):
        report = self.root / 'review.json'
        preview = self.run_program('update.py', '--dry-run', '--report', str(report))
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        reviewed = json.loads(report.read_text())
        reviewed['choices'][str(self.destination)]['choice'] = 'keep'
        report.write_text(json.dumps(reviewed), encoding='utf-8')
        result = self.run_program('update.py', '--decisions', str(report), '--yes')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertTrue(self.legacy.exists())
        self.assertFalse(self.destination.exists())
        self.assertFalse((self.runtime / '.wonsky-state/migrations').exists())


if __name__ == '__main__':
    unittest.main()
