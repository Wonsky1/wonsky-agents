"""Exercise the packaged installer/updater against temporary installations only."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts.managed_files import snapshot
from scripts.update_cli import main
from scripts.update_review import default_choice


ROOT = Path(__file__).resolve().parents[1]


class UpdateCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.package = self.root / 'package'
        self.package.mkdir()
        shutil.copytree(ROOT / 'scripts', self.package / 'scripts',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ('install.py', 'update.py'):
            shutil.copy2(ROOT / name, self.package / name)
        self.put(self.package, 'skills/sample/SKILL.md', 'old skill\n')
        self.put(self.package, 'README.md', 'package documentation\n')
        self.canonical = self.root / 'home/.wonsky-agents'
        self.runtime_root = self.root / 'home/.codex/skills'
        self.runtime = self.runtime_root / 'sample'
        self.environment = dict(os.environ, HOME=str(self.root / 'home'),
                                USERPROFILE=str(self.root / 'home'),
                                CODEX_HOME=str(self.root / 'home/.codex'),
                                WONSKY_AGENTS_HOME=str(self.canonical),
                                PYTHONPATH='', PYTHONDONTWRITEBYTECODE='1', PATH='')
        result = self.run_program('install.py', '--targets', 'codex')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.offer = self.root / 'offered-collection'
        shutil.copytree(self.package, self.offer)
        self.put(self.offer, 'skills/sample/SKILL.md', 'new skill\n')

    def put(self, root, name, contents):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding='utf-8')
        return path

    def run_program(self, program, *arguments, environment=None):
        return subprocess.run([sys.executable, '-B', str(self.package / program), *map(str, arguments)],
                              cwd=self.root, env=environment or self.environment,
                              text=True, capture_output=True, timeout=30)

    def update(self, *arguments, environment=None):
        return self.run_program('update.py', '--from', self.offer, '--targets', 'codex',
                                *arguments, environment=environment)

    def installed(self):
        return snapshot(self.canonical), snapshot(self.runtime_root)

    def preview(self):
        report = self.root / 'review.json'
        result = self.update('--dry-run', '--report', report)
        self.assertIn(result.returncode, (0, 2), result.stdout + result.stderr)
        return report, json.loads(report.read_text(encoding='utf-8'))

    def test_fresh_install_includes_updater_and_original_content_snapshots(self):
        self.assertTrue((self.canonical / 'update.py').is_file())
        state = json.loads((self.canonical / '.wonsky-state/collection.json').read_text())
        self.assertEqual(state['version'], 2)
        self.assertIn('skills/sample/SKILL.md', state['files'])
        self.assertTrue((self.canonical / '.wonsky-state/objects' /
                         state['files']['skills/sample/SKILL.md']).is_file())

    def test_preview_covers_canonical_and_runtime_without_installed_writes(self):
        before = self.installed()
        report, data = self.preview()
        self.assertEqual(self.installed(), before)
        self.assertEqual(len(data['plans']), 3)
        destinations = {Path(plan['id']) for plan in data['plans']}
        self.assertIn(self.canonical / 'skills/sample', destinations)
        self.assertIn(self.runtime, destinations)
        self.assertTrue(report.is_file())

    def test_yes_updates_unchanged_units_and_keeps_runtime_manual_edits(self):
        self.put(self.runtime, 'SKILL.md', 'my runtime edit\n')
        result = self.update('--yes')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual((self.canonical / 'skills/sample/SKILL.md').read_text(), 'new skill\n')
        self.assertEqual((self.runtime / 'SKILL.md').read_text(), 'my runtime edit\n')
        self.assertIn('kept', result.stdout)

    def test_exact_reviewed_replace_updates_runtime_and_backs_up_manual_edit(self):
        self.put(self.runtime, 'SKILL.md', 'my runtime edit\n')
        report, data = self.preview()
        data['choices'][str(self.runtime)]['choice'] = 'replace'
        report.write_text(json.dumps(data), encoding='utf-8')
        result = self.update('--decisions', report, '--yes')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.runtime / 'SKILL.md').read_text(), 'new skill\n')
        backups = list((self.canonical / '.wonsky-backups').glob('*/files/SKILL.md'))
        self.assertTrue(any(path.read_text() == 'my runtime edit\n' for path in backups))

    def test_stale_source_invalidates_saved_review_without_installed_writes(self):
        report, data = self.preview()
        before = self.installed()
        self.put(self.offer, 'skills/sample/SKILL.md', 'changed after review\n')
        result = self.update('--decisions', report, '--yes')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('changed since review', result.stderr)
        self.assertEqual(self.installed(), before)

    def test_incomplete_decisions_are_rejected_without_installed_writes(self):
        report, data = self.preview()
        del data['choices'][str(self.runtime)]
        report.write_text(json.dumps(data), encoding='utf-8')
        before = self.installed()
        result = self.update('--decisions', report, '--yes')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.installed(), before)

    def test_cancelling_final_confirmation_leaves_installation_unchanged(self):
        before = self.installed()
        with mock.patch.dict(os.environ, self.environment, clear=True), redirect_stdout(io.StringIO()):
            with mock.patch('scripts.update_cli.choose', side_effect=lambda plans, terminal: {
                    plan.id: default_choice(plan) for plan in plans}):
                with mock.patch('scripts.update_cli.confirm', return_value=False):
                    result = main(['--from', str(self.offer), '--targets', 'codex', '--terminal'])
        self.assertEqual(result, 0)
        self.assertEqual(self.installed(), before)

    def test_report_cannot_overwrite_unrelated_user_skill(self):
        user_skill = self.put(self.runtime_root, 'foreign/SKILL.md', 'my unrelated skill\n')
        before = self.installed()
        result = self.update('--dry-run', '--report', user_skill)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.installed(), before)
        self.assertEqual(user_skill.read_text(), 'my unrelated skill\n')

    def test_report_cannot_overwrite_global_agents_instructions(self):
        instructions = self.put(self.root, 'home/.codex/AGENTS.md', 'my global instructions\n')
        result = self.update('--dry-run', '--report', instructions)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(instructions.read_text(), 'my global instructions\n')

    def test_report_cannot_overwrite_an_existing_unrelated_user_file(self):
        user_file = self.put(self.root, 'my-notes.json', 'my personal data\n')
        result = self.update('--dry-run', '--report', user_file)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(user_file.read_text(), 'my personal data\n')

    def test_report_cannot_modify_the_offered_collection(self):
        incoming = self.offer / 'README.md'
        before = snapshot(self.offer)
        result = self.update('--dry-run', '--report', incoming)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(snapshot(self.offer), before)

    def test_a_report_generated_by_the_updater_can_be_refreshed(self):
        report, original = self.preview()
        result = self.update('--dry-run', '--report', report)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        current = json.loads(report.read_text())
        self.assertEqual(current['choices'], original['choices'])

    def test_local_secret_paths_are_reported_without_secret_contents(self):
        secret = 'SYNTHETIC_LOCAL_SECRET_123'
        self.put(self.runtime, '.env', 'TOKEN=' + secret + '\n')
        report = self.root / 'secret-review.json'
        before = self.installed()
        result = self.update('--dry-run', '--report', report)
        self.assertIn(result.returncode, (0, 2), result.stdout + result.stderr)
        self.assertNotIn(secret, result.stdout + result.stderr + report.read_text())
        self.assertIn('.env', report.read_text())
        self.assertEqual(self.installed(), before)

    def test_canonical_and_runtime_overlap_is_rejected_before_any_write(self):
        environment = dict(self.environment, CODEX_HOME=str(self.canonical))
        before = self.installed()
        result = self.update('--yes', environment=environment)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.installed(), before)

    def test_aliased_runtime_destinations_are_rejected_before_any_write(self):
        alias = self.root / 'home/.agents'
        environment = dict(self.environment, CODEX_HOME=str(alias))
        before = self.installed(), snapshot(alias)
        result = self.update('--targets', 'codex,agents', '--yes', environment=environment)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual((self.installed(), snapshot(alias)), before)

    def test_runtime_inside_offered_source_is_rejected_without_source_or_installed_writes(self):
        environment = dict(self.environment, CODEX_HOME=str(self.offer / 'runtime'))
        before = self.installed(), snapshot(self.offer)
        result = self.update('--yes', environment=environment)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual((self.installed(), snapshot(self.offer)), before)

    def test_installer_hashes_but_does_not_snapshot_private_configuration_bytes(self):
        secret = 'SYNTHETIC_PRIVATE_PROFILE_123'
        self.put(self.canonical, 'skills/github-pr-review/SKILL.md', 'review skill\n')
        self.put(self.canonical, 'skills/github-pr-review/reviewer-preferences.md', secret)
        self.put(self.canonical, 'skills/sample/.env', secret)
        result = self.run_program('install.py', '--sync-only', '--targets', 'codex')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        state_root = self.runtime_root / '.wonsky-state'
        state = json.loads((state_root / 'github-pr-review.json').read_text())
        self.assertIn('reviewer-preferences.md', state['files'])
        for path in state_root.rglob('*'):
            if path.is_file():
                self.assertNotIn(secret.encode(), path.read_bytes())

    def test_update_preserves_previously_managed_private_files_absent_from_new_source(self):
        names = ('skills/sample/.env', 'skills/sample/reviewer-preferences.md')
        for name in names:
            self.put(self.package, name, 'my retained private configuration\n')
        installation = self.run_program('install.py', '--update', '--targets', 'codex')
        self.assertEqual(installation.returncode, 0, installation.stdout + installation.stderr)
        result = self.update('--yes')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in names:
            with self.subTest(name=name):
                canonical_file = self.canonical / name
                runtime_file = self.runtime / Path(name).name
                self.assertTrue(canonical_file.is_file(), 'Private canonical file was removed: ' + name)
                self.assertTrue(runtime_file.is_file(), 'Private runtime file was removed: ' + name)
                self.assertEqual(canonical_file.read_text(), 'my retained private configuration\n')
                self.assertEqual(runtime_file.read_text(), 'my retained private configuration\n')


if __name__ == '__main__':
    unittest.main()
