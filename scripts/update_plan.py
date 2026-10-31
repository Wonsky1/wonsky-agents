"""Build three-way, read-only update previews without running installed code."""

import difflib
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
from typing import Mapping, Optional

from scripts import managed_files
from scripts.managed_files import blocked_path, read_state, safe_key, snapshot, symlink_in_chain
from scripts.models.update import FileChange, UpdatePlan


def content_hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def private_path(name: str) -> bool:
    parts = tuple(part.casefold() for part in PurePosixPath(name).parts)
    return (parts[-1] == 'reviewer-preferences.md' or
            any(part.startswith('.env') and part != '.env.example' for part in parts))


def scoped_snapshot(destination: Path, scope: Optional[tuple]) -> dict:
    if scope is None:
        return snapshot(destination)
    found = {}
    for name in scope:
        path = destination / name
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink():
            found[name] = ('link', os.readlink(path))
        elif path.is_dir():
            found[name] = ('dir',)
            found.update({name + '/' + key: value for key, value in snapshot(path).items()})
        elif path.is_file():
            found[name] = ('file', managed_files.digest(path), path.stat().st_mode)
        else:
            raise ValueError('Unsupported destination entry: {}'.format(path))
    return found


def state_bytes(path: Path) -> Optional[bytes]:
    if symlink_in_chain(path) is not None:
        raise ValueError('Refusing symlinked installation state: {}'.format(path))
    return path.read_bytes() if path.exists() else None


def _describe(before: Optional[bytes], after: Optional[bytes], before_hash: Optional[str],
              after_hash: Optional[str], name: str, comparison: str) -> str:
    if before is None and before_hash is not None:
        return 'Original bytes unavailable (SHA-256 {}). See local-to-new comparison.\n'.format(before_hash)
    old, new = before or b'', after or b''
    try:
        if b'\0' in old or b'\0' in new:
            raise UnicodeError()
        old_text, new_text = old.decode('utf-8'), new.decode('utf-8')
    except UnicodeError:
        return 'Binary file: {} bytes ({}) -> {} bytes ({})\n'.format(
            len(old) if before is not None else 0, before_hash or 'absent',
            len(new) if after is not None else 0, after_hash or 'absent')
    lines = difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                                 fromfile='{}/before/{}'.format(comparison, name),
                                 tofile='{}/after/{}'.format(comparison, name))
    return ''.join(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n'
                   for line in lines)


def _change(name: str, before: Optional[bytes], after: Optional[bytes], comparison: str,
            known: bool, before_hash: Optional[str] = None, kind: Optional[str] = None) -> FileChange:
    old_hash = before_hash if before_hash is not None else (content_hash(before) if before is not None else None)
    new_hash = content_hash(after) if after is not None else None
    actual_kind = kind or ('added' if old_hash is None else 'deleted' if new_hash is None else 'modified')
    return FileChange(name, actual_kind, comparison, old_hash, new_hash,
                      len(before) if before is not None else None,
                      len(after) if after is not None else None,
                      _describe(before, after, old_hash, new_hash, name, comparison), known)


def _originals(state_path: Path, previous: dict, baseline: Optional[Mapping[str, Path]]) -> dict:
    originals = {}
    for name, fingerprint in previous.items():
        if private_path(name):
            continue
        value = managed_files.read_original(state_path, fingerprint)
        if value is None and baseline and name in baseline:
            path = baseline[name]
            if symlink_in_chain(path) is not None or not path.is_file():
                raise ValueError('Baseline must contain regular files: {}'.format(path))
            candidate = path.read_bytes()
            if content_hash(candidate) == fingerprint:
                value = candidate
        if value is not None:
            if content_hash(value) != fingerprint:
                raise ValueError('Corrupt original installation content for {}'.format(name))
            originals[name] = value
    return originals


def build_plan(files: Mapping[str, Path], destination: Path, state_path: Path,
               baseline: Optional[Mapping[str, Path]] = None, label: str = '',
               known_hashes: Optional[Mapping[str, str]] = None) -> UpdatePlan:
    """Compare original/local/new files; absent originals are explicitly unknown.

    A skill is a whole review unit. Collection support files use only their top
    level owners, excluding unrelated skills, Git metadata and installation state.
    """
    destination, state_path = destination.absolute(), state_path.absolute()
    if any(not safe_key(name) for name in files):
        raise ValueError('Unsafe source-relative path')
    # Private configuration/preferences are never distributed or recorded as originals.
    source = {name: path for name, path in files.items() if not private_path(name)}
    if baseline and any(not safe_key(name) for name in baseline):
        raise ValueError('Unsafe baseline-relative path')
    for path in source.values():
        if symlink_in_chain(path) is not None or not path.is_file():
            raise ValueError('Source must contain regular files: {}'.format(path))
        if destination == path.resolve() or destination in path.resolve().parents:
            raise ValueError('Update source overlaps destination: {}'.format(path))
    link = symlink_in_chain(destination) or symlink_in_chain(state_path)
    if link is not None:
        raise ValueError('Refusing symlinked update path: {}'.format(link))
    if destination.exists() and not destination.is_dir():
        raise ValueError('Destination is not a directory: {}'.format(destination))
    if known_hashes is not None and any(
            not isinstance(name, str) or not safe_key(name) or
            not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{64}', value) is None
            for name, value in known_hashes.items()):
        raise ValueError('Invalid previous installation hashes')
    owned = read_state(state_path)
    previous = dict(known_hashes or {}, **owned)
    if baseline:
        for name, path in baseline.items():
            if private_path(name):
                continue
            if symlink_in_chain(path) is not None or not path.is_file():
                raise ValueError('Baseline must contain regular files: {}'.format(path))
            previous.setdefault(name, content_hash(path.read_bytes()))
    originals = _originals(state_path, previous, baseline)
    contents = {name: path.read_bytes() for name, path in source.items()}
    incoming = {name: content_hash(value) for name, value in contents.items()}
    skill = 'SKILL.md' in source or (destination / 'SKILL.md').is_file()
    scope = None if skill else tuple(sorted({PurePosixPath(name).parts[0] for name in set(source) | set(previous)}))
    before = scoped_snapshot(destination, scope)
    existing = {name: (destination / name).read_bytes() for name, item in before.items()
                if item[0] == 'file' and not private_path(name)}
    local, upstream, replacement, conflicts, blocked, preserved = [], [], [], [], [], []
    known = state_path.exists() or baseline is not None or known_hashes is not None
    names = sorted(set(previous) | set(source) | set(existing))
    for name in names:
        if private_path(name):
            if name in before:
                preserved.append(name)
            continue
        old_hash, new_hash = previous.get(name), incoming.get(name)
        actual = existing.get(name)
        if name in before and before[name][0] == 'link':
            actual = ('Symlink -> ' + before[name][1] + '\n').encode('utf-8')
        actual_hash = content_hash(actual) if actual is not None else None
        target = destination / name
        retained_instruction = PurePosixPath(name).name.casefold() == 'agents.md' and (
            name in before or target.exists() or target.is_symlink())
        if retained_instruction:
            preserved.append(name)
        if name in source or name in previous:
            if blocked_path(destination, name) and not retained_instruction:
                blocked.append(name)
                conflicts.append(name)
        if name in previous and actual_hash != old_hash:
            local.append(_change(name, originals.get(name), actual, 'base-to-local', name in originals, old_hash))
            if not retained_instruction:
                conflicts.append(name)
        elif name not in previous and actual is not None:
            if name not in source:
                local.append(_change(name, None, actual, 'base-to-local' if known else 'original-unknown',
                                     known, kind='added' if known else 'untracked'))
                preserved.append(name)
            elif known:
                local.append(_change(name, None, actual, 'base-to-local', True, kind='added'))
                if actual_hash != new_hash and not retained_instruction:
                    conflicts.append(name)
            elif actual_hash != new_hash:
                local.append(_change(name, actual, contents.get(name), 'local-to-new', False, kind='untracked'))
                if not retained_instruction:
                    conflicts.append(name)
        if old_hash != new_hash:
            upstream.append(_change(name, originals.get(name), contents.get(name), 'base-to-new',
                                    name in originals if old_hash is not None else known, old_hash))
        if (name in source or name in previous) and actual_hash != new_hash and not retained_instruction:
            replacement.append(_change(name, actual, contents.get(name), 'local-to-new', True))
    for name, item in sorted(before.items()):
        if private_path(name):
            preserved.append(name)
            continue
        if item[0] == 'link' and name not in previous and name not in source:
            local.append(_change(name, None, ('Symlink -> ' + item[1] + '\n').encode('utf-8'),
                                 'base-to-local' if known else 'original-unknown', known,
                                 kind='added' if known else 'untracked'))
            preserved.append(name)
    changed = bool(replacement)
    status = 'conflict' if conflicts else ('updated' if destination.exists() else 'added') if changed else 'unchanged'
    return UpdatePlan(str(destination), label or str(destination), destination, state_path, source, contents,
                      incoming, previous, tuple(local), tuple(upstream), tuple(replacement), status,
                      tuple(sorted(set(conflicts))), tuple(sorted(set(blocked))), tuple(sorted(set(preserved))),
                      not known, before, state_bytes(state_path), scope)


def validate_plan(plan: UpdatePlan) -> None:
    """Approval is valid only for the exact source, local files and state reviewed."""
    if symlink_in_chain(plan.destination) is not None or symlink_in_chain(plan.state_path) is not None:
        raise ValueError('Update path became a symlink; build a new preview')
    if state_bytes(plan.state_path) != plan.state_fingerprint:
        raise ValueError('Installation state changed after preview; build a new preview')
    if scoped_snapshot(plan.destination, plan.scope) != plan.local_fingerprint:
        raise ValueError('Local files changed after preview; build a new preview')
    for name, path in plan.files.items():
        if symlink_in_chain(path) is not None or not path.is_file() or content_hash(path.read_bytes()) != plan.new_hashes[name]:
            raise ValueError('Update source changed after preview: {}'.format(name))


def effective_files(plan: UpdatePlan, choice: str) -> dict:
    """Return the virtual reviewed unit for planning dependent runtime copies."""
    if choice not in ('keep', 'update', 'replace'):
        raise ValueError('Unknown update choice: {}'.format(choice))
    validate_plan(plan)
    current = {name: plan.destination / name for name, item in plan.local_fingerprint.items()
               if item[0] == 'file'}
    if choice == 'keep':
        return current
    if plan.blocked or (choice == 'update' and plan.conflicts):
        raise ValueError('Cannot derive updated files for an unresolved or blocked unit')
    for name in plan.previous_hashes:
        if name not in plan.files and name not in plan.preserved:
            current.pop(name, None)
    current.update({name: path for name, path in plan.files.items() if name not in plan.preserved})
    return current
