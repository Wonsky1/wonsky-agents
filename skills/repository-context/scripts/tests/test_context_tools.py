"""Behavior checks use temporary repositories and never mutate user projects."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HELPER = Path(__file__).resolve().parents[1] / 'context_tools.py'
spec = importlib.util.spec_from_file_location('context_tools', HELPER)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ContextToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'repo'
        self.root.mkdir()

    def write(self, relative, contents='instructions'):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding='utf-8')
        return path

    def git_init(self, path=None):
        subprocess.run(['git', 'init', '-q', str(path or self.root)], check=True)

    def test_git_discovery_includes_every_ancestor_without_reading(self):
        self.git_init()
        for name in ('AGENTS.md', 'src/AGENTS.md', 'src/billing/AGENTS.md',
                     'src/CLAUDE.md', 'src/billing/AGENTS.override.md'):
            self.write(name)
        scope = self.write('src/billing/handler.py', 'pass')
        self.write('src/other/AGENTS.md')
        self.write('docs/agent-context/index.md')
        with mock.patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
            data = helper.discover(scope)
        self.assertEqual(data['repository_root'], str(self.root))
        self.assertEqual(data['scope_path'], str(scope))
        self.assertEqual(data['scope_kind'], 'file')
        self.assertFalse(data['contents_read'])
        candidates = data['instruction_candidates']
        self.assertEqual([Path(c['path']).relative_to(self.root).as_posix() for c in candidates],
                         ['AGENTS.md', 'src/AGENTS.md', 'src/CLAUDE.md',
                          'src/billing/AGENTS.md', 'src/billing/AGENTS.override.md'])
        self.assertEqual(candidates[2]['kind'], 'host_specific_candidate')
        self.assertEqual(data['context_index']['status'], 'discovered')

    def test_nongit_root_is_explicit_and_missing_scope_is_error(self):
        scope = self.write('component/code.py')
        with self.assertRaisesRegex(ValueError, 'No Git repository'):
            helper.discover(scope)
        data = helper.discover(scope.parent, self.root)
        self.assertEqual(data['scope_kind'], 'directory')
        self.assertEqual(data['context_index']['status'], 'missing')
        with self.assertRaises(FileNotFoundError):
            helper.discover(self.root / 'planned.py', self.root)

    def test_global_instructions_are_explicit_and_may_be_outside(self):
        outside = self.base / 'AGENTS.md'
        outside.write_text('global', encoding='utf-8')
        data = helper.discover(self.root, self.root, [outside])
        self.assertEqual(data['instruction_candidates'], [])
        self.assertEqual(data['global_instruction_candidates'][0]['status'], 'discovered')

    def test_symlink_instruction_escape_is_reported_not_read(self):
        outside = self.base / 'private.md'
        outside.write_text('private', encoding='utf-8')
        (self.root / 'AGENTS.md').symlink_to(outside)
        with mock.patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
            data = helper.discover(self.root, self.root)
        self.assertEqual(data['instruction_candidates'][0]['status'], 'outside_repository')

    def test_symlink_scope_cannot_switch_repository(self):
        self.git_init()
        outside = self.base / 'other_repo'
        outside.mkdir()
        self.git_init(outside)
        (outside / 'child').mkdir()
        link = self.root / 'link'
        link.symlink_to(outside, target_is_directory=True)
        for root in (None, self.root):
            with self.subTest(root=root), self.assertRaisesRegex(ValueError, 'escapes'):
                helper.discover(link / 'child', root)

    def test_internal_symlink_scope_uses_resolved_ancestor_chain(self):
        self.write('actual/AGENTS.md')
        link = self.root / 'alias'
        link.symlink_to(self.root / 'actual', target_is_directory=True)
        data = helper.discover(link, self.root)
        self.assertEqual(data['scope_path'], str(self.root / 'actual'))
        self.assertEqual(len(data['instruction_candidates']), 1)

    def test_links_check_relative_targets_references_spaces_and_cycles(self):
        self.write('docs/other.md', '[back](index.md)\n[not traversed](missing.md)')
        self.write('docs/file with spaces.md')
        self.write('docs/a(b).md')
        source = self.write('docs/index.md', '''[other](other.md#section)
[space](<file with spaces.md> "title")
[percent](file%20with%20spaces.md)
[paren](a(b).md)
[ref][label]
[label][]
[label]
[label]: other.md "title"
''')
        data = helper.check_links(source, self.root)
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['links']), 7)

    def test_links_report_missing_and_escapes_including_symlinks(self):
        outside = self.base / 'secret'
        outside.write_text('secret', encoding='utf-8')
        (self.root / 'escaped').symlink_to(outside)
        source = self.write('index.md', '[missing](absent.md)\n[outside](../secret)\n[link](escaped)')
        data = helper.check_links(source, self.root)
        self.assertFalse(data['ok'])
        self.assertEqual([link['status'] for link in data['links']],
                         ['missing', 'outside_repository', 'outside_repository'])
        self.assertEqual([link['line'] for link in data['links']], [1, 2, 3])

    def test_checker_refuses_outside_markdown_source_before_read(self):
        outside = self.base / 'outside.md'
        outside.write_text('private', encoding='utf-8')
        link = self.root / 'index.md'
        link.symlink_to(outside)
        with mock.patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
            with self.assertRaisesRegex(ValueError, 'inside the repository'):
                helper.check_links(link, self.root)

    def test_links_ignore_code_comments_remote_urls_and_anchors(self):
        source = self.write('index.md', '''```md
[example](missing-code.md)
```
~~~
[example](missing-tilde.md)
~~~
    [example](indented.md)
`[example](inline.md)`
``[example](inline-two.md)``
<!-- [comment](missing-comment.md) -->
[web](https://example.com/a)
[mail](mailto:a@example.com)
[protocol-relative](//example.com/a)
[anchor](#section)
''')
        data = helper.check_links(source, self.root)
        self.assertTrue(data['ok'])
        self.assertEqual(data['links'], [])
        self.assertEqual(data['ignored_external_or_anchor_links'], 4)

    def test_undefined_reference_is_reported(self):
        source = self.write('index.md', '[named][missing]\n[ordinary bracket prose]')
        data = helper.check_links(source, self.root)
        self.assertFalse(data['ok'])
        self.assertEqual(data['links'], [{'line': 1, 'reference': 'missing', 'status': 'undefined_reference'}])

    def test_fingerprint_changes_with_contents_and_does_not_claim_agent_read(self):
        source = self.write('rule.md', 'first')
        first = helper.fingerprint([source])
        self.assertEqual(first['files'][0]['sha256'], hashlib.sha256(b'first').hexdigest())
        source.write_text('second', encoding='utf-8')
        second = helper.fingerprint([source])
        self.assertNotEqual(first['files'][0]['sha256'], second['files'][0]['sha256'])
        self.assertIn('not that an agent has read', first['notice'])
        self.assertEqual(second['files'][0]['size_bytes'], 6)

    def test_all_helpers_leave_repository_content_unchanged(self):
        self.git_init()
        self.write('AGENTS.md')
        source = self.write('docs/agent-context/index.md', '[rules](../../AGENTS.md)')

        def snapshot():
            return {str(path.relative_to(self.root)): path.read_bytes()
                    for path in self.root.rglob('*') if path.is_file()}

        before = snapshot()
        helper.discover(source)
        helper.check_links(source, self.root)
        helper.fingerprint([source])
        self.assertEqual(snapshot(), before)

    def test_cli_exit_codes_and_json_error(self):
        source = self.write('index.md', '[missing](absent.md)')
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = helper.main(['check-links', str(source), '--repo-root', str(self.root)])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(stdout.getvalue())['ok'])
        with contextlib.redirect_stderr(stderr):
            code = helper.main(['discover', str(self.root / 'missing'), '--repo-root', str(self.root)])
        self.assertEqual(code, 2)
        self.assertIn('error', json.loads(stderr.getvalue()))


if __name__ == '__main__':
    unittest.main()
