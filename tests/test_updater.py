"""Updater previews and writes use synthetic files in temporary homes only."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.managed_files import regular_files, snapshot, write_state
from scripts.update_apply import apply_plan
from scripts.update_plan import build_plan, effective_files, validate_plan


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / 'new'
        self.local = self.root / 'installed' / 'sample'
        self.state = self.root / 'installed' / '.wonsky-state' / 'sample.json'
        self.backups = self.root / 'backups'
        self.source.mkdir()
        self.local.mkdir(parents=True)

    def put(self, root, name, value):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value if isinstance(value, bytes) else value.encode())
        return target

    def original(self, files):
        contents = {name: value if isinstance(value, bytes) else value.encode() for name, value in files.items()}
        for name, value in contents.items():
            self.put(self.local, name, value)
        write_state(self.state, {name: hashlib.sha256(value).hexdigest() for name, value in contents.items()},
                    originals=contents)

    def plan(self):
        return build_plan(regular_files(self.source), self.local, self.state, label='Sample')

    def test_known_original_lists_modified_added_deleted_and_separate_upstream_diff(self):
        self.original({'SKILL.md': 'original\n', 'gone.txt': 'old\n'})
        self.put(self.local, 'SKILL.md', 'user edit\n')
        (self.local / 'gone.txt').unlink()
        self.put(self.local, 'notes.txt', 'personal\n')
        self.put(self.source, 'SKILL.md', 'new release\n')
        self.put(self.source, 'gone.txt', 'old\n')
        plan = self.plan()
        self.assertEqual({change.path: change.kind for change in plan.local_changes},
                         {'SKILL.md': 'modified', 'gone.txt': 'deleted', 'notes.txt': 'added'})
        self.assertIn('-original', plan.local_changes[0].diff)
        self.assertIn('+user edit', plan.local_changes[0].diff)
        self.assertIn('+new release', plan.upstream_changes[0].diff)
        self.assertEqual(plan.status, 'conflict')

    def test_unknown_original_never_claims_exact_manual_changes(self):
        self.put(self.local, 'SKILL.md', 'local version\n')
        self.put(self.source, 'SKILL.md', 'incoming version\n')
        plan = self.plan()
        self.assertTrue(plan.unknown_original)
        self.assertEqual(plan.local_changes[0].kind, 'untracked')
        self.assertFalse(plan.local_changes[0].baseline_known)
        self.assertEqual(plan.local_changes[0].comparison, 'local-to-new')
        self.assertIn('-local version', plan.local_changes[0].diff)

    def test_hash_only_original_reports_missing_bytes_but_proves_managed_edit(self):
        value = b'original\n'
        self.state.parent.mkdir(parents=True)
        self.state.write_text(json.dumps({'version': 1, 'files': {'SKILL.md': hashlib.sha256(value).hexdigest()}}))
        self.put(self.local, 'SKILL.md', 'local edit\n')
        self.put(self.source, 'SKILL.md', 'incoming\n')
        plan = self.plan()
        self.assertFalse(plan.local_changes[0].baseline_known)
        self.assertIn('Original bytes unavailable', plan.local_changes[0].diff)
        self.assertIn('-local edit', plan.replacement_changes[0].diff)

    def test_trusted_legacy_baseline_recovers_full_original_diff(self):
        baseline = self.root / 'baseline'
        baseline.mkdir()
        self.put(baseline, 'SKILL.md', 'original\n')
        self.put(self.local, 'SKILL.md', 'local\n')
        self.put(self.source, 'SKILL.md', 'incoming\n')
        plan = build_plan(regular_files(self.source), self.local, self.state, regular_files(baseline))
        self.assertFalse(plan.unknown_original)
        self.assertIn('-original', plan.local_changes[0].diff)

    def test_partial_recovered_baseline_retains_hashes_for_edited_uncached_files(self):
        baseline = self.root / 'recovered'
        baseline.mkdir()
        self.put(baseline, 'asset.txt', 'unchanged original\n')
        self.put(self.local, 'asset.txt', 'unchanged original\n')
        self.put(self.local, 'SKILL.md', 'manual edit\n')
        self.put(self.source, 'asset.txt', 'unchanged original\n')
        self.put(self.source, 'SKILL.md', 'new release\n')
        original = {'SKILL.md': hashlib.sha256(b'old original\n').hexdigest(),
                    'asset.txt': hashlib.sha256(b'unchanged original\n').hexdigest()}
        plan = build_plan(regular_files(self.source), self.local, self.state,
                          baseline=regular_files(baseline), known_hashes=original)
        change = next(change for change in plan.local_changes if change.path == 'SKILL.md')
        self.assertEqual(change.kind, 'modified')
        self.assertFalse(change.baseline_known)
        self.assertEqual(change.before_hash, original['SKILL.md'])
        self.assertIn('Original bytes unavailable', change.diff)
        self.assertIn('-manual edit', next(change for change in plan.replacement_changes
                                           if change.path == 'SKILL.md').diff)

    def test_current_unit_state_takes_precedence_over_legacy_hashes(self):
        self.original({'SKILL.md': 'recorded current\n'})
        self.put(self.source, 'SKILL.md', 'new\n')
        plan = build_plan(regular_files(self.source), self.local, self.state,
                          known_hashes={'SKILL.md': hashlib.sha256(b'older legacy\n').hexdigest()})
        self.assertEqual(plan.local_changes, ())
        self.assertEqual(plan.previous_hashes['SKILL.md'], hashlib.sha256(b'recorded current\n').hexdigest())

    def test_keep_leaves_entire_skill_and_state_unchanged(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.local, 'SKILL.md', 'local\n')
        self.put(self.source, 'SKILL.md', 'new\n')
        self.put(self.source, 'extra.txt', 'new file\n')
        before, state = snapshot(self.local), self.state.read_bytes()
        result = apply_plan(self.plan(), 'keep', self.backups)
        self.assertEqual(result.result.status, 'kept')
        self.assertEqual(snapshot(self.local), before)
        self.assertEqual(self.state.read_bytes(), state)
        self.assertFalse(self.backups.exists())

    def test_update_rejects_local_edit_without_writing(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.local, 'SKILL.md', 'local\n')
        self.put(self.source, 'SKILL.md', 'new\n')
        with self.assertRaisesRegex(ValueError, 'explicit Replace'):
            apply_plan(self.plan(), 'update', self.backups)
        self.assertEqual((self.local / 'SKILL.md').read_text(), 'local\n')
        self.assertFalse(self.backups.exists())

    def test_explicit_replace_backs_up_changes_and_preserves_user_extras_and_agents(self):
        self.original({'SKILL.md': 'old\n', 'AGENTS.md': 'old instructions\n', 'obsolete.txt': 'old asset\n'})
        self.put(self.local, 'SKILL.md', 'my edits\n')
        self.put(self.local, 'AGENTS.md', 'my instructions\n')
        self.put(self.local, 'extra/personal.txt', 'my notes\n')
        self.put(self.source, 'SKILL.md', 'new\n')
        self.put(self.source, 'AGENTS.md', 'new instructions\n')
        result = apply_plan(self.plan(), 'replace', self.backups)
        self.assertEqual((self.local / 'SKILL.md').read_text(), 'new\n')
        self.assertEqual((self.local / 'AGENTS.md').read_text(), 'my instructions\n')
        self.assertEqual((self.local / 'extra/personal.txt').read_text(), 'my notes\n')
        self.assertFalse((self.local / 'obsolete.txt').exists())
        self.assertEqual((result.backup / 'files/SKILL.md').read_text(), 'my edits\n')
        self.assertEqual((result.backup / 'files/extra/personal.txt').read_text(), 'my notes\n')
        self.assertTrue((result.backup / 'manifest.json').is_file())

    def test_unchanged_managed_files_update_and_originals_advance(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.source, 'SKILL.md', 'new\n')
        result = apply_plan(self.plan(), 'update', self.backups)
        self.assertEqual(result.result.status, 'updated')
        self.put(self.local, 'SKILL.md', 'new local edit\n')
        next_plan = self.plan()
        self.assertIn('-new\n', next_plan.local_changes[0].diff)

    def test_user_deleted_file_requires_choice_and_replace_restores_it(self):
        self.original({'SKILL.md': 'old\n', 'asset.txt': 'asset\n'})
        (self.local / 'asset.txt').unlink()
        self.put(self.source, 'SKILL.md', 'old\n')
        self.put(self.source, 'asset.txt', 'asset\n')
        plan = self.plan()
        self.assertIn('asset.txt', plan.conflicts)
        apply_plan(plan, 'replace', self.backups)
        self.assertEqual((self.local / 'asset.txt').read_text(), 'asset\n')

    def test_user_added_file_colliding_with_new_vendor_file_requires_choice(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.local, 'added.txt', 'my file\n')
        self.put(self.source, 'SKILL.md', 'new\n')
        self.put(self.source, 'added.txt', 'vendor file\n')
        plan = self.plan()
        self.assertIn('added.txt', plan.conflicts)
        self.assertEqual(next(change for change in plan.local_changes if change.path == 'added.txt').kind, 'added')

    def test_binary_comparison_includes_sizes_and_hashes(self):
        self.original({'SKILL.md': 'skill\n', 'asset.bin': b'\x00old'})
        self.put(self.local, 'asset.bin', b'\x00mine')
        self.put(self.source, 'SKILL.md', 'skill\n')
        self.put(self.source, 'asset.bin', b'\x00new')
        change = self.plan().local_changes[0]
        self.assertIn('4 bytes', change.diff)
        self.assertIn('5 bytes', change.diff)
        self.assertIn(hashlib.sha256(b'\x00mine').hexdigest(), change.diff)

    def test_diff_is_not_truncated(self):
        self.original({'SKILL.md': ''.join('old {}\n'.format(index) for index in range(4000))})
        self.put(self.local, 'SKILL.md', ''.join('local {}\n'.format(index) for index in range(4000)))
        self.put(self.source, 'SKILL.md', 'new\n')
        self.assertIn('+local 3999', self.plan().local_changes[0].diff)

    def test_crlf_and_missing_final_newline_are_explicit_in_diff(self):
        self.original({'SKILL.md': b'old\r\nlast'})
        self.put(self.local, 'SKILL.md', b'local\r\nchanged')
        self.put(self.source, 'SKILL.md', b'new\r\nlast')
        diff = self.plan().local_changes[0].diff
        self.assertIn('-old\r\n', diff)
        self.assertIn('+local\r\n', diff)
        self.assertIn('\\ No newline at end of file', diff)
        self.assertIn('base-to-local/before/SKILL.md', diff)

    def test_unchanged_unit_adopts_originals_without_copying_user_files_or_backup(self):
        self.put(self.local, 'SKILL.md', 'same\n')
        self.put(self.source, 'SKILL.md', 'same\n')
        before = snapshot(self.local)
        result = apply_plan(self.plan(), 'update', self.backups)
        self.assertIsNone(result.backup)
        self.assertFalse(self.backups.exists())
        self.assertTrue(self.state.is_file())
        self.assertEqual(snapshot(self.local), before)

    def test_agents_symlink_is_retained_without_following_or_blocking_update(self):
        external = self.put(self.root, 'my-agent-instructions.txt', 'private instructions\n')
        self.put(self.local, 'SKILL.md', 'old\n')
        self.put(self.source, 'SKILL.md', 'old\n')
        self.put(self.source, 'AGENTS.md', 'vendor instructions\n')
        try:
            (self.local / 'AGENTS.md').symlink_to(external)
        except OSError:
            self.skipTest('Symlinks unavailable')
        plan = self.plan()
        self.assertEqual(plan.blocked, ())
        self.assertIn('AGENTS.md', plan.preserved)
        self.assertIn('Symlink ->', next(change for change in plan.local_changes if change.path == 'AGENTS.md').diff)
        apply_plan(plan, 'replace', self.backups)
        self.assertTrue((self.local / 'AGENTS.md').is_symlink())
        self.assertEqual(external.read_text(), 'private instructions\n')

    def test_previously_managed_private_files_are_not_removed_or_exposed(self):
        private = {'.env': 'LOCAL_SECRET_ONLY\n', 'nested/.ENV.production': 'LOCAL_ENV_ONLY\n',
                   'Reviewer-Preferences.MD': 'LOCAL_PROFILE_ONLY\n'}
        self.original(dict(private, **{'SKILL.md': 'old\n'}))
        self.put(self.source, 'SKILL.md', 'new\n')
        plan = self.plan()
        for name in private:
            self.assertIn(name, plan.preserved)
            self.assertNotIn(name, {change.path for change in plan.replacement_changes})
            self.assertNotIn(name, {change.path for change in plan.local_changes})
            self.assertNotIn(name, {change.path for change in plan.upstream_changes})
        apply_plan(plan, 'update', self.backups)
        for name, value in private.items():
            self.assertEqual((self.local / name).read_text(), value)

    def test_deleted_previously_managed_private_file_is_not_restored(self):
        self.original({'SKILL.md': 'old\n', '.env': 'old private\n'})
        (self.local / '.env').unlink()
        self.put(self.source, 'SKILL.md', 'new\n')
        self.put(self.source, '.env', 'incoming private\n')
        plan = self.plan()
        self.assertNotIn('.env', plan.contents)
        self.assertNotIn('.env', plan.conflicts)
        apply_plan(plan, 'replace', self.backups)
        self.assertFalse((self.local / '.env').exists())

    def test_private_incoming_files_never_overwrite_or_create_cached_originals(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.local, '.ENV', 'my private\n')
        self.put(self.source, 'SKILL.md', 'new\n')
        secret = b'incoming private bytes\n'
        for name in ('.ENV', 'reviewer-preferences.md', 'deep/.env.secret/value.txt'):
            self.put(self.source, name, secret)
        plan = self.plan()
        self.assertEqual(set(plan.contents), {'SKILL.md'})
        effective = effective_files(plan, 'update')
        self.assertEqual(effective['.ENV'], self.local / '.ENV')
        self.assertNotIn('reviewer-preferences.md', effective)
        apply_plan(plan, 'update', self.backups)
        self.assertEqual((self.local / '.ENV').read_text(), 'my private\n')
        self.assertFalse((self.local / 'reviewer-preferences.md').exists())
        self.assertFalse((self.state.parent / 'objects' / hashlib.sha256(secret).hexdigest()).exists())

    def test_env_example_remains_an_ordinary_distributed_file(self):
        self.original({'SKILL.md': 'old\n', '.env.example': 'OLD=\n'})
        self.put(self.source, 'SKILL.md', 'new\n')
        self.put(self.source, '.env.example', 'NEW=\n')
        plan = self.plan()
        self.assertIn('.env.example', plan.contents)
        apply_plan(plan, 'update', self.backups)
        self.assertEqual((self.local / '.env.example').read_text(), 'NEW=\n')

    def test_instruction_name_case_variants_are_preserved_portably(self):
        self.original({'SKILL.md': 'old\n', 'agents.md': 'my instructions\n'})
        self.put(self.source, 'SKILL.md', 'new\n')
        self.put(self.source, 'agents.md', 'vendor instructions\n')
        plan = self.plan()
        self.assertIn('agents.md', plan.preserved)
        apply_plan(plan, 'replace', self.backups)
        self.assertEqual((self.local / 'agents.md').read_text(), 'my instructions\n')

    def test_source_drift_invalidates_preview(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.source, 'SKILL.md', 'new\n')
        plan = self.plan()
        self.put(self.source, 'SKILL.md', 'changed after review\n')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            apply_plan(plan, 'update', self.backups)

    def test_local_extra_drift_invalidates_whole_skill_preview(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.source, 'SKILL.md', 'new\n')
        plan = self.plan()
        self.put(self.local, 'personal.txt', 'created after review\n')
        with self.assertRaisesRegex(ValueError, 'Local files changed'):
            apply_plan(plan, 'update', self.backups)

    def test_state_drift_invalidates_preview(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.source, 'SKILL.md', 'new\n')
        plan = self.plan()
        self.state.write_text(self.state.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'state changed'):
            apply_plan(plan, 'update', self.backups)

    def test_failure_restores_original_files_and_retains_backup(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.source, 'SKILL.md', 'new\n')
        plan, old_state = self.plan(), self.state.read_bytes()
        with mock.patch('scripts.update_apply.write_state', side_effect=OSError('simulated state failure')):
            with self.assertRaisesRegex(OSError, 'Backup retained'):
                apply_plan(plan, 'update', self.backups)
        self.assertEqual((self.local / 'SKILL.md').read_text(), 'old\n')
        self.assertEqual(self.state.read_bytes(), old_state)
        self.assertEqual(len(list(self.backups.iterdir())), 1)

    def test_source_symlink_is_rejected(self):
        external = self.put(self.root, 'external.txt', 'private\n')
        try:
            (self.source / 'SKILL.md').symlink_to(external)
        except OSError:
            self.skipTest('Symlinks unavailable')
        with self.assertRaisesRegex(ValueError, 'regular files'):
            build_plan({'SKILL.md': self.source / 'SKILL.md'}, self.local, self.state)

    def test_destination_symlink_cannot_be_replaced(self):
        self.put(self.source, 'SKILL.md', 'new\n')
        external = self.put(self.root, 'external.txt', 'private\n')
        try:
            (self.local / 'SKILL.md').symlink_to(external)
        except OSError:
            self.skipTest('Symlinks unavailable')
        plan = self.plan()
        self.assertEqual(plan.blocked, ('SKILL.md',))
        with self.assertRaisesRegex(ValueError, 'Blocked paths'):
            apply_plan(plan, 'replace', self.backups)
        self.assertEqual(external.read_text(), 'private\n')

    def test_unsafe_source_names_are_rejected(self):
        source = self.put(self.source, 'SKILL.md', 'new\n')
        for name in ('../escape', '/absolute', 'a\\b', 'C:/escape'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Unsafe'):
                build_plan({name: source}, self.local, self.state)

    def test_collection_support_scope_excludes_skills_and_git(self):
        self.put(self.source, 'README.md', 'readme\n')
        self.put(self.local, 'skills/other/SKILL.md', 'private\n')
        self.put(self.local, '.git/config', 'private git\n')
        plan = self.plan()
        self.put(self.local, 'skills/other/SKILL.md', 'other update\n')
        validate_plan(plan)
        result = apply_plan(plan, 'update', self.backups)
        self.assertFalse((result.backup / 'files/.git/config').exists())
        self.assertEqual((self.local / 'skills/other/SKILL.md').read_text(), 'other update\n')

    def test_effective_files_preserves_local_extras_and_instructions_for_runtime_plan(self):
        self.original({'SKILL.md': 'old\n', 'obsolete.txt': 'remove\n', 'AGENTS.md': 'mine\n'})
        self.put(self.local, 'personal.txt', 'keep\n')
        self.put(self.source, 'SKILL.md', 'new\n')
        self.put(self.source, 'AGENTS.md', 'vendor\n')
        plan = self.plan()
        updated = effective_files(plan, 'update')
        self.assertEqual(updated['SKILL.md'], self.source / 'SKILL.md')
        self.assertEqual(updated['AGENTS.md'], self.local / 'AGENTS.md')
        self.assertEqual(updated['personal.txt'], self.local / 'personal.txt')
        self.assertNotIn('obsolete.txt', updated)
        self.assertIn('obsolete.txt', effective_files(plan, 'keep'))

    def test_fresh_install_creates_files_state_originals_and_backup_manifest(self):
        self.local.rmdir()
        self.put(self.source, 'SKILL.md', 'new\n')
        result = apply_plan(self.plan(), 'update', self.backups)
        self.assertEqual(result.result.status, 'added')
        self.assertTrue(self.state.is_file())
        self.assertTrue((result.backup / 'manifest.json').is_file())
        self.assertEqual((self.local / 'SKILL.md').read_text(), 'new\n')

    def test_existing_unmanaged_agents_is_preserved_on_clean_update(self):
        self.put(self.local, 'AGENTS.md', 'mine\n')
        self.put(self.source, 'SKILL.md', 'new\n')
        self.put(self.source, 'AGENTS.md', 'vendor\n')
        plan = self.plan()
        self.assertNotIn('AGENTS.md', plan.conflicts)
        apply_plan(plan, 'update', self.backups)
        self.assertEqual((self.local / 'AGENTS.md').read_text(), 'mine\n')

    def test_rollback_removes_newly_created_empty_directories(self):
        self.original({'SKILL.md': 'old\n'})
        self.put(self.source, 'SKILL.md', 'new\n')
        self.put(self.source, 'new/nested/asset.txt', 'new\n')
        before = snapshot(self.local)
        with mock.patch('scripts.update_apply.write_state', side_effect=OSError('state failure')):
            with self.assertRaises(OSError):
                apply_plan(self.plan(), 'update', self.backups)
        self.assertEqual(snapshot(self.local), before)

    def test_source_overlap_is_rejected(self):
        source = self.put(self.local, 'SKILL.md', 'local\n')
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            build_plan({'SKILL.md': source}, self.local, self.state)


if __name__ == '__main__':
    unittest.main()
