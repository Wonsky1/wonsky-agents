"""Translate a single ledger command into documented host hook schemas."""

import base64
from pathlib import Path
import shlex


def shell_command(arguments: list, system: str) -> str:
    if system != 'Windows':
        return shlex.join(arguments)
    # An explicit native PowerShell invocation works independently of the
    # host's outer Windows shell. Paths are literal strings, never expansions.
    script = '& ' + ' '.join("'" + value.replace("'", "''") + "'" for value in arguments)
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    return 'powershell.exe -NoLogo -NoProfile -NonInteractive -EncodedCommand ' + encoded


def hook_entry(host: str, canonical: Path, python: Path, system: str) -> dict:
    args = ['-B', str(canonical / 'skills/session-ledger/scripts/ledger.py'), 'hook', '--host', host]
    if host == 'copilot':
        return {'type': 'command', 'exec': str(python), 'args': args, 'timeoutSec': 10}
    if host == 'claude':
        # Exec form avoids shell interpretation on every platform.
        handler = {'type': 'command', 'command': str(python), 'args': args, 'timeout': 10}
        return {'hooks': [handler]}
    handler = {'type': 'command', 'command': shell_command([str(python), *args], system), 'timeout': 10}
    if host == 'codex':
        return {'hooks': [handler]}
    if host == 'cursor':
        return handler
    if host == 'antigravity':
        return {'SessionStart': [handler]}
    raise ValueError('No hook adapter for {}'.format(host))


def hook_entries(document: dict, host: str) -> list:
    """Return an owned working list without silently replacing malformed data."""
    if host == 'antigravity':
        key = 'wonsky-session-ledger'
        return [document[key]] if key in document else []
    if host in ('cursor', 'copilot'):
        if document.get('version', 1) != 1:
            raise ValueError('Unsupported {} hooks version; configuration preserved'.format(host.title()))
        document.setdefault('version', 1)
    hooks = document.setdefault('hooks', {})
    if not isinstance(hooks, dict):
        raise ValueError('Expected a hooks object; configuration preserved')
    event = 'sessionStart' if host in ('cursor', 'copilot') else 'SessionStart'
    entries = hooks.setdefault(event, [])
    if not isinstance(entries, list):
        raise ValueError('Expected a {} array; configuration preserved'.format(event))
    return entries


def replace_entries(document: dict, host: str, entries: list) -> None:
    if host == 'antigravity':
        if entries:
            document['wonsky-session-ledger'] = entries[0]
        else:
            document.pop('wonsky-session-ledger', None)
    else:
        event = 'sessionStart' if host in ('cursor', 'copilot') else 'SessionStart'
        if entries:
            document['hooks'][event] = entries
        else:
            document['hooks'].pop(event, None)
