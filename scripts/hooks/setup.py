"""Plan optional session recovery integrations without replacing user settings."""

from pathlib import Path

from scripts.hooks.definitions import hook_entries, hook_entry, replace_entries
from scripts.hooks.files import encode, read_bytes, read_object
from scripts.hooks.models.plan import HookPlan
from scripts.installation.models.target import Target


def hook_config_path(target: Target) -> Path:
    """Locate the host hook document, including Copilot's dedicated CLI file."""
    if target.key == 'copilot':
        return target.path.parent / 'hooks/wonsky-session-ledger.json'
    return target.path.parent / ('settings.json' if target.key == 'claude' else 'hooks.json')


def plan_hook(target: Target, canonical: Path, python: Path, system: str,
              action: str, helper_source: Path = None) -> HookPlan:
    if action not in ('install', 'remove', 'status'):
        raise ValueError('Unknown hook action: {}'.format(action))
    config = hook_config_path(target)
    state = target.path.parent / '.wonsky-state/session-ledger-hook.json'
    if target.key == 'agents':
        return HookPlan(target.key, config, state, 'unsupported',
                        'Shared skills directory has no hook runtime; configure the consuming host.', {})
    desired = hook_entry(target.key, canonical, python, system)
    before, state_before = read_bytes(config), read_bytes(state)
    document, record = read_object(before, config), read_object(state_before, state)
    if record and (record.get('version') != 1 or record.get('host') != target.key
                   or not isinstance(record.get('entry'), dict)):
        raise ValueError('Invalid hook ownership record; preserved: {}'.format(state))
    entries = hook_entries(document, target.key)
    owned = record.get('entry')
    match = [i for i, entry in enumerate(entries) if entry == (owned or desired)]
    suspicious = any('session-ledger' in str(entry) for entry in entries)
    conflict = ((owned is not None and len(match) != 1)
                or len(match) > 1 or (owned is None and not match and suspicious)
                or (target.key == 'antigravity' and entries and not match))
    if conflict:
        return HookPlan(target.key, config, state, 'conflict',
                        'Existing ledger hook was edited, removed or duplicated; preserve and review it.',
                        desired, before, before, state_before, state_before)
    if action == 'status':
        status = 'configured' if match else 'absent'
        message = ('Configuration found; host execution is not verified.' if match else 'No session recovery hook configured.')
        if match and target.key == 'codex':
            message += ' Codex requires review/trust of this exact hook in /hooks.'
        return HookPlan(target.key, config, state, status, message, desired)
    if action == 'remove':
        if not owned:
            return HookPlan(target.key, config, state, 'absent',
                            'No owned hook to remove; unowned entries are preserved.', desired)
        del entries[match[0]]
        replace_entries(document, target.key, entries)
        return HookPlan(target.key, config, state, 'remove', 'Remove only the unchanged owned hook.',
                        desired, before, encode(document), state_before, None)
    helper = helper_source or canonical / 'skills/session-ledger/scripts/ledger.py'
    if not helper.is_file():
        raise ValueError('Session ledger helper is missing: {}'.format(helper))
    if not python.is_file():
        raise ValueError('Python interpreter is missing: {}'.format(python))
    if match:
        entries[match[0]] = desired
    else:
        entries.append(desired)
    replace_entries(document, target.key, entries)
    after = before if match and (owned or desired) == desired else encode(document)
    state_after = encode({'version': 1, 'host': target.key, 'entry': desired})
    status = 'unchanged' if after == before and state_after == state_before else ('update' if match else 'add')
    message = 'Merge one recovery hook; preserve other settings and hooks.'
    if target.key == 'codex':
        message += ' Review/trust it in Codex /hooks before it can run.'
    return HookPlan(target.key, config, state, status, message, desired,
                    before, after, state_before, state_after)
