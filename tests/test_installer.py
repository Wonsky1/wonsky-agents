"""Installer checks use temporary homes; never touch installed agent skills."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts.agent_targets import detect_targets, select_keys
from scripts.skill_files import install_collection, sync_skill
from scripts.target_picker import pick_targets


ROOT = Path(__file__).resolve().parents[1]


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def targets(self, system, env=None, commands=()):
        return detect_targets(self.home, system, env or {}, lambda name: name if name in commands else None)

    def test_config_directories_work_on_all_platforms(self):
        for name in ('.cursor', '.claude', '.codex', '.gemini/config', '.agents'):
            (self.home / name).mkdir(parents=True)
        for system in ('Darwin', 'Linux', 'Windows'):
            with self.subTest(system=system):
                targets = self.targets(system)
                self.assertEqual(len(targets), 5)
                self.assertTrue(all(t.detected for t in targets))
                self.assertEqual(targets[3].path, self.home / '.gemini/config/skills')

    def test_clean_home_keeps_explicit_targets_available(self):
        targets = self.targets('Linux')
        self.assertFalse(any(t.detected for t in targets))
        self.assertEqual(select_keys(targets, 'codex,antigravity,codex', False), ['codex', 'antigravity'])
        self.assertEqual(select_keys(targets, None, True), [])

    def test_unknown_target_is_rejected(self):
        with self.assertRaises(ValueError):
            select_keys(self.targets('Linux'), 'codez', False)

    def test_command_detection(self):
        targets = self.targets('Linux', commands=('claude', 'agy'))
        self.assertEqual([t.key for t in targets if t.detected], ['claude', 'antigravity'])

    def test_windows_per_user_app_detection(self):
        local = self.home / 'AppData/Local'
        exe = local / 'Programs/cursor/Cursor.exe'
        exe.parent.mkdir(parents=True)
        exe.touch()
        targets = self.targets('Windows', {'LOCALAPPDATA': str(local)})
        self.assertTrue(targets[0].detected)

    def test_linux_desktop_file_detection(self):
        desktop = self.home / '.local/share/applications/cursor.desktop'
        desktop.parent.mkdir(parents=True)
        desktop.touch()
        self.assertTrue(self.targets('Linux')[0].detected)

    def test_macos_user_app_detection(self):
        (self.home / 'Applications/Cursor.app').mkdir(parents=True)
        self.assertTrue(self.targets('Darwin')[0].detected)

    def test_custom_codex_home_is_respected(self):
        custom = self.home / 'custom codex'
        custom.mkdir()
        targets = self.targets('Linux', {'CODEX_HOME': str(custom)})
        codex = next(t for t in targets if t.key == 'codex')
        self.assertTrue(codex.detected)
        self.assertEqual(codex.path, custom / 'skills')


class CopyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source/example'
        self.source.mkdir(parents=True)
        (self.source / 'SKILL.md').write_text('example', encoding='utf-8')
        (self.source / 'references').mkdir()
        (self.source / 'references/a.md').write_text('reference', encoding='utf-8')
        self.dest = self.root / 'target/example'

    def test_copy_replaces_matching_skill_and_preserves_unrelated_skill(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'obsolete.md').touch()
        unrelated = self.dest.parent / 'unrelated/SKILL.md'
        unrelated.parent.mkdir()
        unrelated.write_text('keep', encoding='utf-8')
        sync_skill(self.source, self.dest)
        self.assertEqual((self.dest / 'references/a.md').read_text(), 'reference')
        self.assertFalse((self.dest / 'obsolete.md').exists())
        self.assertEqual(unrelated.read_text(), 'keep')

    def test_cache_files_are_not_copied(self):
        (self.source / '__pycache__').mkdir()
        (self.source / '__pycache__/a.pyc').touch()
        (self.source / '.DS_Store').touch()
        sync_skill(self.source, self.dest)
        self.assertFalse((self.dest / '__pycache__').exists())
        self.assertFalse((self.dest / '.DS_Store').exists())

    def test_same_source_and_destination_is_safe(self):
        sync_skill(self.source, self.source)
        self.assertEqual((self.source / 'SKILL.md').read_text(), 'example')

    def test_overlapping_destination_is_rejected(self):
        with self.assertRaises(ValueError):
            sync_skill(self.source, self.source / 'nested')
        self.assertFalse((self.source / 'nested').exists())

    def test_private_profile_is_retained_when_absent_from_source(self):
        self.dest.mkdir(parents=True)
        profile = self.dest / 'reviewer-preferences.md'
        profile.write_text('private history', encoding='utf-8')
        sync_skill(self.source, self.dest, preserve=('reviewer-preferences.md',))
        self.assertEqual(profile.read_text(), 'private history')

    @unittest.skipIf(os.name == 'nt', 'Creating symlinks may require Windows privileges')
    def test_destination_symlink_is_replaced_without_writing_its_target(self):
        other = self.root / 'other'
        other.mkdir()
        (other / 'keep').write_text('private', encoding='utf-8')
        self.dest.parent.mkdir()
        self.dest.symlink_to(other, target_is_directory=True)
        sync_skill(self.source, self.dest)
        self.assertFalse(self.dest.is_symlink())
        self.assertTrue((other / 'keep').exists())
        self.assertFalse((other / 'SKILL.md').exists())

    @unittest.skipIf(os.name == 'nt', 'Creating symlinks may require Windows privileges')
    def test_symlink_to_canonical_skill_becomes_an_independent_copy(self):
        self.dest.parent.mkdir()
        self.dest.symlink_to(self.source, target_is_directory=True)
        sync_skill(self.source, self.dest)
        self.assertFalse(self.dest.is_symlink())
        (self.dest / 'SKILL.md').write_text('destination edit', encoding='utf-8')
        self.assertEqual((self.source / 'SKILL.md').read_text(), 'example')

    def test_failed_source_validation_leaves_destination_untouched(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'keep').touch()
        (self.source / 'SKILL.md').unlink()
        with self.assertRaises(ValueError):
            sync_skill(self.source, self.dest)
        self.assertTrue((self.dest / 'keep').exists())

    def test_copy_failure_retains_previous_skill(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'keep').write_text('old skill', encoding='utf-8')
        with mock.patch('scripts.skill_files.shutil.copytree', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                sync_skill(self.source, self.dest)
        self.assertEqual((self.dest / 'keep').read_text(), 'old skill')
        self.assertEqual(list(self.dest.parent.glob('.wonsky-sync-*')), [])

    def test_replacement_failure_restores_previous_skill(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'keep').write_text('old skill', encoding='utf-8')
        replace = Path.replace

        def fail_install(path, target):
            if path.name == 'new':
                raise OSError('destination busy')
            return replace(path, target)

        with mock.patch.object(Path, 'replace', fail_install):
            with self.assertRaises(OSError):
                sync_skill(self.source, self.dest)
        self.assertEqual((self.dest / 'keep').read_text(), 'old skill')
        self.assertEqual(list(self.dest.parent.glob('.wonsky-sync-*')), [])

    def test_failed_restore_keeps_backup_even_if_another_writer_created_destination(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'keep').write_text('old skill', encoding='utf-8')
        replace = Path.replace

        def fail_install_and_restore(path, target):
            if path.name == 'new':
                self.dest.mkdir()
                raise OSError('destination busy')
            if path.name == 'previous':
                raise OSError('restore failed')
            return replace(path, target)

        with mock.patch.object(Path, 'replace', fail_install_and_restore):
            with self.assertRaises(OSError):
                sync_skill(self.source, self.dest)
        backups = list(self.dest.parent.glob('.wonsky-sync-*/previous/keep'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'old skill')

    def test_collection_install_is_gitless_and_keeps_existing_private_profile(self):
        collection = self.root / 'collection'
        (collection / 'skills/example').mkdir(parents=True)
        (collection / 'skills/example/SKILL.md').write_text('new', encoding='utf-8')
        (collection / 'install.py').write_text('# installer', encoding='utf-8')
        (collection / '.git').mkdir()
        (collection / '.env').write_text('secret', encoding='utf-8')
        canonical = self.root / 'canonical'
        profile = canonical / 'skills/github-pr-review/reviewer-preferences.md'
        profile.parent.mkdir(parents=True)
        profile.write_text('private', encoding='utf-8')
        install_collection(collection, canonical, update=True)
        self.assertEqual((canonical / 'skills/example/SKILL.md').read_text(), 'new')
        self.assertEqual(profile.read_text(), 'private')
        self.assertFalse((canonical / '.git').exists())
        self.assertFalse((canonical / '.env').exists())

    def test_existing_install_requires_explicit_update(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'keep').touch()
        with self.assertRaises(ValueError):
            install_collection(self.source.parent, self.dest, update=False)
        self.assertTrue((self.dest / 'keep').exists())


class PickerTests(unittest.TestCase):
    def test_missing_gui_falls_back_to_checkbox_terminal_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            targets = detect_targets(Path(tmp), 'Linux', {}, lambda name: None)
            with mock.patch('scripts.target_picker.gui_picker', return_value=None), \
                    mock.patch('sys.stdin.isatty', return_value=True), \
                    mock.patch('builtins.input', side_effect=['3 4', '']), \
                    mock.patch('builtins.print'):
                self.assertEqual(pick_targets(targets), ['codex', 'antigravity'])

    def test_cancel_is_distinct_from_gui_unavailable(self):
        with mock.patch('scripts.target_picker.gui_picker', return_value=[]), \
                mock.patch('sys.stdin.isatty', return_value=True), \
                mock.patch('builtins.input', side_effect=AssertionError('must not prompt again')):
            self.assertEqual(pick_targets([]), [])

    def test_unattended_runs_require_explicit_selection(self):
        with mock.patch('sys.stdin.isatty', return_value=False):
            with self.assertRaisesRegex(ValueError, '--targets'):
                pick_targets([])


class CommandTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'install.py'), *args],
                              capture_output=True, text=True)

    def test_help_explains_dependency(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Python', result.stdout)

    def test_dry_run_in_temporary_home_makes_no_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            env = dict(os.environ, HOME=tmp, USERPROFILE=tmp,
                       WONSKY_AGENTS_HOME=str(home / '.wonsky-agents'),
                       CODEX_HOME=str(home / '.codex'))
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'install.py'),
                                     '--dry-run', '--targets', 'codex'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('codex', result.stdout.lower())
            self.assertEqual(list(home.iterdir()), [])

    def test_install_then_sync_from_fresh_home_without_git_or_rsync(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            canonical = home / '.wonsky-agents'
            env = dict(os.environ, HOME=tmp, USERPROFILE=tmp, PATH='',
                       WONSKY_AGENTS_HOME=str(canonical), CODEX_HOME=str(home / '.codex'))
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'install.py'),
                                     '--targets', 'codex'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((canonical / 'install.sh').is_file())
            self.assertTrue((canonical / 'install.ps1').is_file())
            self.assertFalse((canonical / '.git').exists())
            self.assertFalse((canonical / 'skills/repository-context/scripts/__pycache__').exists())
            installed = home / '.codex/skills/macos-design-guidelines/SKILL.md'
            self.assertEqual(installed.read_bytes(), (ROOT / 'skills/macos-design-guidelines/SKILL.md').read_bytes())
            result = subprocess.run([sys.executable, '-B', str(canonical / 'install.py'),
                                     '--sync-only', '--targets', 'codex'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_target_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            env = dict(os.environ, HOME=tmp, USERPROFILE=tmp,
                       WONSKY_AGENTS_HOME=str(home / '.wonsky-agents'))
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'install.py'),
                                     '--targets', 'unknown'],
                                    env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(home.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
