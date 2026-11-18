"""Native hook input/output adapters; payload metadata never becomes shell code."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Dict, Optional

from session_ledger.git import resolve_root
from session_ledger.identity import binding
from session_ledger.models.ledger import LedgerError, Root
from session_ledger.storage import find_ledger, new_ledger

HOOK_HOSTS = ('claude', 'codex', 'cursor', 'antigravity', 'copilot')


def workspace_root(host: str, payload: dict) -> Optional[Root]:
    if host in ('claude', 'codex', 'copilot'):
        cwd = payload.get('cwd')
        if not isinstance(cwd, str) or not cwd:
            return None
        root = resolve_root(cwd)
        return root if root.is_git else None
    key = 'workspace_roots' if host == 'cursor' else 'workspacePaths'
    workspaces = payload.get(key)
    if not isinstance(workspaces, list) or not workspaces:
        return None
    if not all(isinstance(path, str) and path for path in workspaces):
        raise LedgerError('invalid workspace paths in hook input')
    roots = {resolve_root(path) for path in workspaces}
    if len(roots) == 1:
        root = next(iter(roots))
        return root if root.is_git else None
    cwd = payload.get('cwd')
    if isinstance(cwd, str) and cwd:
        current = resolve_root(cwd)
        if current.is_git and current in roots:
            return current
    raise LedgerError('multiple workspaces; no unambiguous cwd, ledger hook skipped')


def command(*args: str) -> str:
    script = str(Path(__file__).resolve().parents[1] / 'ledger.py')
    parts = [sys.executable, script, *args]
    return subprocess.list2cmdline(parts) if os.name == 'nt' else shlex.join(parts)


def hook_output(host: str, payload: dict, create: bool = False) -> Optional[Dict[str, object]]:
    field = 'conversationId' if host == 'antigravity' else 'session_id'
    session = payload.get(field)
    if host == 'copilot':
        if ('sessionId' in payload and 'session_id' in payload
                and payload['sessionId'] != payload['session_id']):
            raise LedgerError('conflicting Copilot session IDs; ledger hook skipped')
        session = payload.get('sessionId', session)
    if session is None:
        return None
    identity = binding(host, session)
    root = workspace_root(host, payload)
    if root is None:
        return None
    source = payload.get('source', 'startup')
    if not isinstance(source, str):
        raise LedgerError('invalid hook source')
    ledger = find_ledger(root, identity)
    if ledger is None and create and source in ('startup', 'clear'):
        ledger = new_ledger(root, 'session', identity)
    identity_args = ['--host', identity.host, '--session', identity.session]
    repo_args = ['--repo', str(root.path)]
    if ledger:
        message = ('Session ledger: ' + str(ledger.path) + ' | id: ' + ledger.identifier
                   + '. Lookup: ' + command('path', *identity_args, *repo_args))
    elif source in ('resume', 'compact'):
        message = ('No ledger bound to this session. Bind a known ledger path with: '
                   + command('bind', '<ledger-path>', *identity_args))
    else:
        message = ('No ledger bound to this session. Create one with: '
                   + command('new', '--slug', '<task>', *identity_args, *repo_args))
    if host in ('claude', 'codex'):
        return {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': message}}
    if host == 'cursor':
        return {'additional_context': message}
    if host == 'copilot':
        return {'additionalContext': message}
    return {'injectSteps': [{'systemMessage': {'systemMessage': message}}]}


def run_hook(host: str, create: bool) -> int:
    try:
        raw = sys.stdin.buffer.read(1048577)
        if not raw.strip():
            return 0
        if len(raw) > 1048576:
            raise LedgerError('hook input exceeds 1 MiB')
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return 0
        output = hook_output(host, payload, create)
        if output:
            print(json.dumps(output))
    except (LedgerError, OSError, ValueError, UnicodeError) as error:
        print('session-ledger hook: ' + str(error), file=sys.stderr)
    return 0
