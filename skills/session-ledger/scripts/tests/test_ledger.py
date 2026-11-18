"""CLI regression tests; all repository and hook writes use temporary directories."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(os.environ.get('LEDGER_TEST_SCRIPT', Path(__file__).resolve().parents[1] / 'ledger.py'))


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'repo'
        self.root.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.env = {key: value for key, value in os.environ.items()
                    if key not in ('AGENT_SESSION_ID', 'AGENT_HOST', 'CLAUDE_CODE_SESSION_ID',
                                   'CODEX_THREAD_ID', 'CLAUDE_ENV_FILE')}

    def run_cli(self, *args, stdin=None, env=None, root=None):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), *map(str, args)],
                              cwd=root or self.root, env={**self.env, **(env or {})},
                              input=stdin, capture_output=True, text=True)

    def new(self, session='session-123', slug='task', host=None, **kwargs):
        args = ['new', '--slug', slug]
        if session is not None:
            args.extend(['--session', session])
        if host:
            args.extend(['--host', host])
        result = self.run_cli(*args, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(result.stdout.strip())

    def ledger_id(self, path):
        return re.search(r'\| id: (\S+) \|', path.read_text()).group(1)

    def symlink(self, link, target, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except OSError:
            self.skipTest('symlink creation unavailable without platform privileges')

    def test_new_is_idempotent_and_ignored(self):
        first = self.new()
        self.assertEqual(first, self.new(slug='changed'))
        status = subprocess.run(['git', 'status', '--porcelain'], cwd=self.root,
                                capture_output=True, text=True, check=True)
        self.assertEqual(status.stdout, '')

    def test_shared_session_prefix_does_not_collide(self):
        first = self.new('abcdefgh-111')
        second = self.new('abcdefgh-222')
        self.assertNotEqual(self.ledger_id(first), self.ledger_id(second))
        for path in (first, second):
            found = self.run_cli('path', '--id', self.ledger_id(path))
            self.assertEqual(Path(found.stdout.strip()), path)

    def test_host_namespaces_keep_sessions_separate(self):
        claude = self.new(host='claude')
        codex = self.new(host='codex')
        self.assertNotEqual(claude, codex)
        self.assertEqual(Path(self.run_cli('path', '--host', 'claude', '--session', 'session-123').stdout.strip()), claude)

    def test_binding_already_owned_session_is_rejected(self):
        first = self.new('first-123')
        second = self.new('second-123')
        original = second.read_bytes()
        result = self.run_cli('bind', second, '--session', 'first-123')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(second.read_bytes(), original)
        self.assertEqual(Path(self.run_cli('path', '--session', 'first-123').stdout.strip()), first)

    def test_resume_bind_and_duplicate_bind(self):
        path = self.new()
        self.assertEqual(self.run_cli('bind', path, '--session', 'resumed-123').returncode, 0)
        again = self.run_cli('bind', path, '--session', 'resumed-123')
        self.assertIn('already bound', again.stdout)
        self.assertEqual(Path(self.run_cli('path', '--session', 'resumed-123').stdout.strip()), path)

    def test_existing_ambiguous_identity_is_rejected(self):
        first = self.new('first-123')
        second = self.new('other-123')
        second.write_text(second.read_text().replace('other-123', 'first-123'))
        result = self.run_cli('path', '--session', 'first-123')
        self.assertEqual(result.returncode, 2)
        self.assertIn('ambiguous', result.stderr.lower())

    def test_without_session_recovers_using_printed_id(self):
        result = self.run_cli('new', '--slug', 'unknown-session')
        self.assertEqual(result.returncode, 0, result.stderr)
        path = Path(result.stdout.strip())
        identifier = self.ledger_id(path)
        self.assertIn('--id ' + identifier, result.stderr)
        self.assertEqual(Path(self.run_cli('find', '--id', identifier).stdout.strip()), path)
        missing = self.run_cli('path')
        self.assertEqual(missing.returncode, 2)
        self.assertIn('--id', missing.stderr)

    def test_session_and_id_cannot_silently_disagree(self):
        first = self.new('first-123')
        second = self.new('second-123')
        result = self.run_cli('path', '--session', 'first-123', '--id', self.ledger_id(second))
        self.assertEqual(result.returncode, 2)

    def test_unknown_session_is_not_found(self):
        self.assertEqual(self.run_cli('path', '--session', 'missing-123').returncode, 1)

    def test_symlinked_folder_rejected_before_external_write(self):
        external = self.base / 'external'; external.mkdir()
        self.symlink(self.root / '.agent-ledger', external, directory=True)
        result = self.run_cli('new', '--slug', 'task', '--session', 'session-123')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(external.iterdir()), [])

    def test_symlinked_ignore_rejected_before_external_write(self):
        folder = self.root / '.agent-ledger'; folder.mkdir()
        external = self.base / 'important'; external.write_text('preserve me\n')
        self.symlink(folder / '.gitignore', external)
        result = self.run_cli('new', '--slug', 'task', '--session', 'session-123')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(external.read_text(), 'preserve me\n')
        self.assertEqual(list(folder.glob('*.md')), [])

    def test_custom_ignore_is_preserved(self):
        folder = self.root / '.agent-ledger'; folder.mkdir()
        ignore = folder / '.gitignore'; ignore.write_text('# custom\n*.tmp\n')
        result = self.run_cli('new', '--slug', 'task', '--session', 'session-123')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(ignore.read_text(), '# custom\n*.tmp\n')
        self.assertEqual(list(folder.glob('*.md')), [])

    def test_negated_ignore_rejected_before_ledger_write(self):
        folder = self.root / '.agent-ledger'; folder.mkdir()
        (folder / '.gitignore').write_text('*\n!*.md\n')
        result = self.run_cli('new', '--slug', 'task', '--session', 'session-123')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(folder.glob('*.md')), [])

    def test_existing_tracked_ledger_is_not_returned_or_modified(self):
        path = self.new()
        subprocess.run(['git', 'add', '-f', str(path)], cwd=self.root, check=True)
        original = path.read_bytes()
        for args in [('new', '--slug', 'task', '--session', 'session-123'),
                     ('bind', path, '--session', 'resumed-123')]:
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(path.read_bytes(), original)

    def test_binding_symlinked_ledger_does_not_modify_target(self):
        path = self.new()
        external = self.base / 'external.md'; external.write_bytes(path.read_bytes())
        path.unlink(); self.symlink(path, external)
        original = external.read_bytes()
        self.assertEqual(self.run_cli('bind', path, '--session', 'resumed-123').returncode, 2)
        self.assertEqual(external.read_bytes(), original)

    def test_missing_git_fails_closed_in_repository(self):
        result = self.run_cli('new', '--slug', 'task', '--session', 'session-123', env={'PATH': ''})
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / '.agent-ledger').exists())

    def test_git_errors_fail_closed(self):
        (self.root / '.git' / 'config').write_text('not a git config\n')
        result = self.run_cli('new', '--slug', 'task', '--session', 'session-123')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / '.agent-ledger').exists())

    def test_inherited_git_directory_cannot_redirect_explicit_repository(self):
        other = self.base / 'other'
        subprocess.run(['git', 'init', '-q', str(other)], check=True)
        result = self.run_cli('new', '--slug', 'scoped', '--repo', self.root,
                              env={'GIT_DIR': str(other / '.git'), 'GIT_WORK_TREE': str(other)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).parent, self.root / '.agent-ledger')
        self.assertFalse((other / '.agent-ledger').exists())

    def test_explicit_plain_directory_is_supported_without_false_guarantee(self):
        plain = self.base / 'plain'; plain.mkdir()
        result = self.run_cli('new', '--slug', 'task', '--repo', plain, root=plain)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('not a Git repository', result.stderr)
        self.assertTrue(Path(result.stdout.strip()).exists())

    def test_ledger_header_survives_braces_in_slug(self):
        path = self.new(slug='{created} task')
        self.assertIn('## D.', path.read_text())
        self.assertNotIn('{id}', path.read_text())

    def test_pending_durable_proposals(self):
        path = self.new()
        text = path.read_text().replace('## D. Decisions', '## D. Decisions\n- use UTC [durable]\n- use ruff [durable: proposed]\n- done [durable: approved]')
        path.write_text(text)
        self.assertIn('2 pending', self.run_cli('proposals', path).stdout)

    def test_invalid_environment_is_rejected(self):
        result = self.run_cli('new', '--slug', 'task', env={'AGENT_SESSION_ID': 'bad; echo injected'})
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / '.agent-ledger').exists())

    def test_hook_host_shapes_and_explicit_identity(self):
        payloads = {
            'claude': {'session_id': 'hook-123', 'cwd': str(self.root), 'source': 'startup'},
            'codex': {'session_id': 'hook-123', 'cwd': str(self.root), 'source': 'startup'},
            'cursor': {'session_id': 'hook-123', 'workspace_roots': [str(self.root)]},
            'antigravity': {'conversationId': 'hook-123', 'workspacePaths': [str(self.root)]},
        }
        for host, payload in payloads.items():
            with self.subTest(host=host):
                result = self.run_cli('hook', '--host', host, stdin=json.dumps(payload))
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                context = (output['hookSpecificOutput']['additionalContext'] if host in ('claude', 'codex')
                           else output['additional_context'] if host == 'cursor'
                           else output['injectSteps'][0]['systemMessage']['systemMessage'])
                self.assertIn('--session hook-123', context)
                self.assertIn('--host ' + host, context)
        self.assertFalse((self.root / '.agent-ledger').exists())

    def test_hook_invalid_input_is_nonblocking_and_does_not_write_env(self):
        env_file = self.base / 'env.sh'
        for payload in ['bad json', '[]', '{"cwd":"\\u0000"}', json.dumps({'cwd': str(self.root), 'session_id': ['wrong']})]:
            result = self.run_cli('hook', '--host', 'claude', stdin=payload,
                                  env={'CLAUDE_ENV_FILE': str(env_file), 'AGENT_SESSION_ID': 'bad; echo injected'})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '')
        self.assertFalse(env_file.exists())
        self.assertFalse((self.root / '.agent-ledger').exists())

    def test_copilot_identity_aliases_and_existing_ledger(self):
        path = self.new(session='copilot-123', host='copilot')
        payloads = [{'sessionId': 'copilot-123'}, {'session_id': 'copilot-123'},
                    {'sessionId': 'copilot-123', 'session_id': 'copilot-123'}]
        for identity in payloads:
            with self.subTest(identity=identity):
                result = self.run_cli('hook', '--host', 'copilot',
                                      stdin=json.dumps(dict(identity, cwd=str(self.root))))
                self.assertEqual(result.returncode, 0, result.stderr)
                context = json.loads(result.stdout)['additionalContext']
                self.assertIn(str(path), context)
                self.assertIn('--host copilot', context)

    def test_copilot_conflicting_or_unsafe_identity_skips_without_writes(self):
        payloads = [{'sessionId': 'first-123', 'session_id': 'other-123'},
                    {'sessionId': 'bad; echo injected'}, {'session_id': ['wrong']},
                    {'sessionId': '', 'session_id': 'valid-123'},
                    {'sessionId': None, 'session_id': 'valid-123'}]
        for identity in payloads:
            with self.subTest(identity=identity):
                result = self.run_cli('hook', '--host', 'copilot', '--create',
                                      stdin=json.dumps(dict(identity, cwd=str(self.root))))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, '')
        self.assertFalse((self.root / '.agent-ledger').exists())

    def test_hook_does_not_guess_between_workspaces(self):
        other = self.base / 'other'; other.mkdir()
        subprocess.run(['git', 'init', '-q', str(other)], check=True)
        result = self.run_cli('hook', '--host', 'cursor', '--create', stdin=json.dumps({
            'session_id': 'hook-123', 'workspace_roots': [str(self.root), str(other)]}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertFalse((self.root / '.agent-ledger').exists())
        self.assertFalse((other / '.agent-ledger').exists())

    def test_hook_create_then_resume_uses_same_ledger(self):
        payload = {'session_id': 'hook-123', 'cwd': str(self.root), 'source': 'startup'}
        start = self.run_cli('hook', '--host', 'codex', '--create', stdin=json.dumps(payload))
        self.assertEqual(start.returncode, 0, start.stderr)
        paths = list((self.root / '.agent-ledger').glob('*.md'))
        self.assertEqual(len(paths), 1)
        payload['source'] = 'resume'
        resumed = self.run_cli('hook', '--host', 'codex', stdin=json.dumps(payload))
        self.assertIn(str(paths[0]), json.loads(resumed.stdout)['hookSpecificOutput']['additionalContext'])

    def test_overlapping_create_does_not_duplicate_session(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.run_cli('new', '--slug', 'same', '--session', 'same-123'), range(2)))
        self.assertTrue(any(result.returncode == 0 for result in results))
        self.assertTrue(all(result.returncode in (0, 2) for result in results))
        retried = self.new('same-123')
        self.assertEqual(list((self.root / '.agent-ledger').glob('*.md')), [retried])

    def test_existing_mutation_lock_is_preserved(self):
        path = self.new()
        lock = path.parent / '.lock'
        lock.write_text('other operation\n')
        result = self.run_cli('new', '--slug', 'task', '--session', 'new-123')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(lock.read_text(), 'other operation\n')
        self.assertEqual(list(path.parent.glob('*.md')), [path])

    def test_missing_bind_file_has_no_traceback(self):
        result = self.run_cli('bind', self.root / '.agent-ledger' / 'missing.md', '--session', 'session-123')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
