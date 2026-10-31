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
        self.home = Path(self.temp.name).resolve()

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
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source/example'
        self.source.mkdir(parents=True)
        (self.source / 'SKILL.md').write_text('example', encoding='utf-8')
        (self.source / 'references').mkdir()
        (self.source / 'references/a.md').write_text('reference', encoding='utf-8')
        self.dest = self.root / 'target/example'

    def test_same_name_foreign_skill_is_unchanged_and_reported(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'SKILL.md').write_text('user skill', encoding='utf-8')
        (self.dest / 'extra.txt').write_text('keep', encoding='utf-8')
        result = sync_skill(self.source, self.dest)
        self.assertEqual(result.status, 'conflict')
        self.assertIn('SKILL.md', result.conflicts)
        self.assertEqual((self.dest / 'SKILL.md').read_text(), 'user skill')
        self.assertFalse((self.dest / 'references').exists())
        self.assertFalse((self.dest.parent / '.wonsky-state').exists())

    def test_new_skill_added_alongside_unrelated_skill(self):
        unrelated = self.dest.parent / 'unrelated/SKILL.md'
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text('keep', encoding='utf-8')
        self.assertEqual(sync_skill(self.source, self.dest).status, 'added')
        self.assertEqual((self.dest / 'references/a.md').read_text(), 'reference')
        self.assertEqual(unrelated.read_text(), 'keep')

    def test_unchanged_managed_files_update_and_extras_survive(self):
        sync_skill(self.source, self.dest)
        (self.dest / 'personal.txt').write_text('mine', encoding='utf-8')
        (self.source / 'SKILL.md').write_text('updated', encoding='utf-8')
        self.assertEqual(sync_skill(self.source, self.dest).status, 'updated')
        self.assertEqual((self.dest / 'SKILL.md').read_text(), 'updated')
        self.assertEqual((self.dest / 'personal.txt').read_text(), 'mine')

    def test_locally_modified_managed_file_blocks_whole_skill(self):
        sync_skill(self.source, self.dest)
        (self.dest / 'SKILL.md').write_text('my changes', encoding='utf-8')
        (self.source / 'SKILL.md').write_text('upstream change', encoding='utf-8')
        (self.source / 'new.py').write_text('# new', encoding='utf-8')
        self.assertEqual(sync_skill(self.source, self.dest).status, 'conflict')
        self.assertEqual((self.dest / 'SKILL.md').read_text(), 'my changes')
        self.assertFalse((self.dest / 'new.py').exists())

    def test_deleted_managed_file_is_not_silently_restored(self):
        sync_skill(self.source, self.dest)
        (self.dest / 'SKILL.md').unlink()
        self.assertEqual(sync_skill(self.source, self.dest).status, 'conflict')
        self.assertFalse((self.dest / 'SKILL.md').exists())

    def test_obsolete_files_are_retained(self):
        sync_skill(self.source, self.dest)
        (self.source / 'references/a.md').unlink()
        sync_skill(self.source, self.dest)
        self.assertEqual((self.dest / 'references/a.md').read_text(), 'reference')

    def test_byte_identical_legacy_copy_is_adopted(self):
        import shutil
        shutil.copytree(self.source, self.dest)
        (self.dest / 'user.txt').write_text('keep', encoding='utf-8')
        self.assertEqual(sync_skill(self.source, self.dest).status, 'unchanged')
        (self.source / 'SKILL.md').write_text('updated', encoding='utf-8')
        self.assertEqual(sync_skill(self.source, self.dest).status, 'updated')
        self.assertEqual((self.dest / 'user.txt').read_text(), 'keep')

    def test_explicit_baseline_can_recognize_old_copy_without_overriding_edits(self):
        import shutil
        baseline = self.root / 'baseline'
        shutil.copytree(self.source, baseline)
        shutil.copytree(self.source, self.dest)
        (self.source / 'SKILL.md').write_text('new version', encoding='utf-8')
        self.assertEqual(sync_skill(self.source, self.dest, baseline=baseline).status, 'updated')
        (self.dest / 'SKILL.md').write_text('local edits', encoding='utf-8')
        self.assertEqual(sync_skill(self.source, self.dest, baseline=baseline).status, 'conflict')
        self.assertEqual((self.dest / 'SKILL.md').read_text(), 'local edits')

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
        sync_skill(self.source, self.dest)
        profile = self.dest / 'reviewer-preferences.md'
        profile.write_text('private history', encoding='utf-8')
        sync_skill(self.source, self.dest)
        self.assertEqual(profile.read_text(), 'private history')

    def test_private_profile_edits_conflict_when_source_also_contains_profile(self):
        (self.source / 'reviewer-preferences.md').write_text('original', encoding='utf-8')
        sync_skill(self.source, self.dest)
        (self.dest / 'reviewer-preferences.md').write_text('private edit', encoding='utf-8')
        (self.source / 'reviewer-preferences.md').write_text('canonical edit', encoding='utf-8')
        self.assertEqual(sync_skill(self.source, self.dest).status, 'conflict')
        self.assertEqual((self.dest / 'reviewer-preferences.md').read_text(), 'private edit')

    def test_existing_agents_is_never_overwritten_even_when_managed(self):
        (self.source / 'AGENTS.md').write_text('original instructions', encoding='utf-8')
        sync_skill(self.source, self.dest)
        (self.source / 'AGENTS.md').write_text('new instructions', encoding='utf-8')
        result = sync_skill(self.source, self.dest)
        self.assertIn('AGENTS.md', result.preserved)
        self.assertEqual((self.dest / 'AGENTS.md').read_text(), 'original instructions')

    @unittest.skipIf(os.name == 'nt', 'Creating symlinks may require Windows privileges')
    def test_destination_symlink_is_preserved_without_writing_target(self):
        other = self.root / 'other'
        other.mkdir()
        (other / 'keep').write_text('private', encoding='utf-8')
        self.dest.parent.mkdir()
        self.dest.symlink_to(other, target_is_directory=True)
        self.assertEqual(sync_skill(self.source, self.dest).status, 'conflict')
        self.assertTrue(self.dest.is_symlink())
        self.assertFalse((other / 'SKILL.md').exists())

    @unittest.skipIf(os.name == 'nt', 'Creating symlinks may require Windows privileges')
    def test_nested_destination_symlink_is_not_followed(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'SKILL.md').write_text('example', encoding='utf-8')
        other = self.root / 'other'
        other.mkdir()
        (self.dest / 'references').symlink_to(other, target_is_directory=True)
        self.assertEqual(sync_skill(self.source, self.dest).status, 'conflict')
        self.assertEqual(list(other.iterdir()), [])

    @unittest.skipIf(os.name == 'nt', 'Creating symlinks may require Windows privileges')
    def test_destination_ancestor_symlink_is_preserved_without_external_writes(self):
        outside = self.root / 'external'
        outside.mkdir()
        self.dest.parent.symlink_to(outside, target_is_directory=True)
        result = sync_skill(self.source, self.dest)
        self.assertEqual(result.status, 'conflict')
        self.assertEqual(list(outside.iterdir()), [])
        self.assertTrue(self.dest.parent.is_symlink())

    def test_source_scan_error_is_not_a_successful_incomplete_copy(self):
        import scripts.managed_files as managed
        walk = managed.os.walk

        def fail_walk(root, **kwargs):
            kwargs['onerror'](PermissionError('source references unreadable'))
            return iter(())

        with mock.patch.object(managed.os, 'walk', fail_walk):
            with self.assertRaises(PermissionError):
                sync_skill(self.source, self.dest)
        self.assertFalse(self.dest.parent.exists())

    def test_destination_scan_error_preserves_existing_copy(self):
        import scripts.managed_files as managed
        sync_skill(self.source, self.dest)
        (self.source / 'SKILL.md').write_text('updated', encoding='utf-8')
        walk = managed.os.walk

        def fail_destination(root, **kwargs):
            if Path(root) == self.dest:
                kwargs['onerror'](PermissionError('destination unreadable'))
                return iter(())
            return walk(root, **kwargs)

        with mock.patch.object(managed.os, 'walk', fail_destination):
            with self.assertRaises(PermissionError):
                sync_skill(self.source, self.dest)
        self.assertEqual((self.dest / 'SKILL.md').read_text(), 'example')

    def test_failed_source_validation_leaves_destination_untouched(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'keep').touch()
        (self.source / 'SKILL.md').unlink()
        with self.assertRaises(ValueError):
            sync_skill(self.source, self.dest)
        self.assertTrue((self.dest / 'keep').exists())

    def test_copy_failure_retains_previous_skill(self):
        sync_skill(self.source, self.dest)
        (self.source / 'SKILL.md').write_text('next', encoding='utf-8')
        with mock.patch('scripts.managed_files.shutil.copytree', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                sync_skill(self.source, self.dest)
        self.assertEqual((self.dest / 'SKILL.md').read_text(), 'example')
        self.assertEqual(list(self.dest.parent.glob('.wonsky-sync-*')), [])

    def test_replacement_failure_restores_previous_skill(self):
        sync_skill(self.source, self.dest)
        (self.source / 'SKILL.md').write_text('next', encoding='utf-8')
        replace = Path.replace

        def fail_install(path, target):
            if path.name == 'new':
                raise OSError('destination busy')
            return replace(path, target)

        with mock.patch.object(Path, 'replace', fail_install):
            with self.assertRaises(OSError):
                sync_skill(self.source, self.dest)
        self.assertEqual((self.dest / 'SKILL.md').read_text(), 'example')
        self.assertEqual(list(self.dest.parent.glob('.wonsky-sync-*')), [])

    def test_failed_restore_keeps_backup(self):
        sync_skill(self.source, self.dest)
        (self.source / 'SKILL.md').write_text('next', encoding='utf-8')
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
        backups = list(self.dest.parent.glob('.wonsky-sync-*/previous/SKILL.md'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'example')

    def test_dry_run_does_not_create_files_or_state(self):
        self.assertEqual(sync_skill(self.source, self.dest, dry_run=True).status, 'added')
        self.assertFalse(self.dest.parent.exists())

    def test_corrupt_state_is_not_treated_as_ownership(self):
        sync_skill(self.source, self.dest)
        state = self.dest.parent / '.wonsky-state/example.json'
        state.write_text('{"version": 1, "files": {"../escape": "bad"}}', encoding='utf-8')
        with self.assertRaises(ValueError):
            sync_skill(self.source, self.dest)
        self.assertEqual((self.dest / 'SKILL.md').read_text(), 'example')

    def collection(self):
        collection = self.root / 'collection'
        (collection / 'skills/example').mkdir(parents=True)
        (collection / 'skills/example/SKILL.md').write_text('new', encoding='utf-8')
        (collection / 'install.py').write_text('# installer', encoding='utf-8')
        (collection / 'AGENTS.md').write_text('collection instructions', encoding='utf-8')
        return collection

    def test_collection_install_is_gitless_and_preserves_existing_agents_and_profile(self):
        collection = self.collection()
        (collection / '.git').mkdir()
        (collection / '.env').write_text('secret', encoding='utf-8')
        canonical = self.root / 'canonical'
        profile = canonical / 'skills/github-pr-review/reviewer-preferences.md'
        profile.parent.mkdir(parents=True)
        profile.write_text('private', encoding='utf-8')
        (canonical / 'AGENTS.md').write_text('user instructions', encoding='utf-8')
        result = install_collection(collection, canonical, update=True)
        self.assertEqual(result.status, 'updated')
        self.assertEqual((canonical / 'skills/example/SKILL.md').read_text(), 'new')
        self.assertEqual((canonical / 'AGENTS.md').read_text(), 'user instructions')
        self.assertEqual(profile.read_text(), 'private')
        self.assertFalse((canonical / '.git').exists())
        self.assertFalse((canonical / '.env').exists())

    def test_collection_managed_update_preserves_instructions_and_local_changes_block(self):
        collection = self.collection()
        canonical = self.root / 'canonical'
        install_collection(collection, canonical)
        (collection / 'install.py').write_text('# next installer', encoding='utf-8')
        (collection / 'AGENTS.md').write_text('new guidance', encoding='utf-8')
        self.assertEqual(install_collection(collection, canonical, update=True).status, 'updated')
        self.assertEqual((canonical / 'AGENTS.md').read_text(), 'collection instructions')
        (canonical / 'skills/example/SKILL.md').write_text('my edit', encoding='utf-8')
        (collection / 'install.py').write_text('# third', encoding='utf-8')
        self.assertEqual(install_collection(collection, canonical, update=True).status, 'conflict')
        self.assertEqual((canonical / 'install.py').read_text(), '# next installer')

    def test_existing_install_requires_explicit_update(self):
        self.dest.mkdir(parents=True)
        (self.dest / 'keep').touch()
        with self.assertRaises(ValueError):
            install_collection(self.source.parent, self.dest, update=False)
        self.assertTrue((self.dest / 'keep').exists())


class PickerTests(unittest.TestCase):
    def test_missing_gui_falls_back_to_checkbox_terminal_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            targets = detect_targets(Path(tmp).resolve(), 'Linux', {}, lambda name: None)
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
            home = Path(tmp).resolve()
            env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
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
            home = Path(tmp).resolve()
            canonical = home / '.wonsky-agents'
            env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PATH='',
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

    def test_conflict_exit_and_dry_run_preserve_global_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            skill = home / '.codex/skills/macos-design-guidelines'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text('my same-name skill', encoding='utf-8')
            global_agents = home / '.codex/AGENTS.md'
            global_agents.write_text('my global instructions', encoding='utf-8')
            env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                       WONSKY_AGENTS_HOME=str(ROOT), CODEX_HOME=str(home / '.codex'))
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'install.py'),
                                     '--sync-only', '--dry-run', '--targets', 'codex'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('conflicts 1', result.stdout)
            self.assertFalse((home / '.codex/skills/.wonsky-state').exists())
            self.assertEqual((skill / 'SKILL.md').read_text(), 'my same-name skill')
            self.assertEqual(global_agents.read_text(), 'my global instructions')

    def test_zip_update_preview_includes_retained_canonical_extras(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            package = home / 'download'
            package.mkdir()
            shutil.copy2(ROOT / 'install.py', package / 'install.py')
            shutil.copytree(ROOT / 'scripts', package / 'scripts',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            source = package / 'skills/example'
            canonical = home / '.wonsky-agents'
            for directory in (source, canonical / 'skills/example', home / '.codex/skills/example'):
                directory.mkdir(parents=True)
                (directory / 'SKILL.md').write_text('same', encoding='utf-8')
            (canonical / 'skills/example/private.txt').write_text('canonical extra', encoding='utf-8')
            local = home / '.codex/skills/example/private.txt'
            local.write_text('runtime personal', encoding='utf-8')
            env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                       WONSKY_AGENTS_HOME=str(canonical), CODEX_HOME=str(home / '.codex'))
            for extra in (['--dry-run'], []):
                result = subprocess.run([sys.executable, '-B', str(package / 'install.py'),
                                         '--update', '--targets', 'codex', *extra],
                                        env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn('conflicts 1', result.stdout)
                self.assertEqual(local.read_text(), 'runtime personal')
                if extra:
                    self.assertFalse((canonical / '.wonsky-state').exists())
                    self.assertFalse((home / '.codex/skills/.wonsky-state').exists())

    def test_zip_preview_accepts_assets_only_canonical_folder(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            package = home / 'download'
            package.mkdir()
            shutil.copy2(ROOT / 'install.py', package / 'install.py')
            shutil.copytree(ROOT / 'scripts', package / 'scripts',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            source = package / 'skills/example'
            source.mkdir(parents=True)
            (source / 'SKILL.md').write_text('incoming skill', encoding='utf-8')
            canonical = home / '.wonsky-agents'
            retained = canonical / 'skills/example'
            retained.mkdir(parents=True)
            (retained / 'private.txt').write_text('keep', encoding='utf-8')
            env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                       WONSKY_AGENTS_HOME=str(canonical), CODEX_HOME=str(home / '.codex'))
            for extra in (['--dry-run'], []):
                result = subprocess.run([sys.executable, '-B', str(package / 'install.py'),
                                         '--update', '--targets', 'codex', *extra],
                                        env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('added 1', result.stdout)
                if extra:
                    self.assertFalse((home / '.codex').exists())
            self.assertEqual((home / '.codex/skills/example/private.txt').read_text(), 'keep')

    def test_invalid_target_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                       WONSKY_AGENTS_HOME=str(home / '.wonsky-agents'))
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'install.py'),
                                     '--targets', 'unknown'],
                                    env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(home.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
