"""Apply reviewed file updates with permanent backups and rollback on failure."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import Optional
import uuid

from scripts.managed_files import blocked_path, symlink_in_chain, write_state
from scripts.models.sync_result import SyncResult
from scripts.models.update import ApplyResult, UpdatePlan
from scripts.update_plan import validate_plan


def _backup(plan: UpdatePlan, choice: str, backup_root: Path) -> Path:
    if symlink_in_chain(backup_root) is not None:
        raise ValueError('Refusing symlinked backup directory: {}'.format(backup_root))
    root = backup_root.absolute()
    if plan.scope is None and (root == plan.destination or plan.destination in root.parents):
        raise ValueError('Backups must be outside the reviewed skill directory')
    root.mkdir(parents=True, exist_ok=True)
    backup = root / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex)
    backup.mkdir()
    for name, value in sorted(plan.local_fingerprint.items()):
        source, target = plan.destination / name, backup / 'files' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if value[0] == 'dir':
            target.mkdir(exist_ok=True)
        elif value[0] == 'link':
            target.symlink_to(value[1], target_is_directory=source.is_dir())
        else:
            if symlink_in_chain(source) is not None:
                raise ValueError('Destination changed during backup: {}'.format(source))
            shutil.copy2(source, target)
    if plan.state_fingerprint is not None:
        (backup / 'installation-state.json').write_bytes(plan.state_fingerprint)
    (backup / 'manifest.json').write_text(json.dumps({
        'version': 1, 'label': plan.label, 'destination': str(plan.destination),
        'state_path': str(plan.state_path), 'choice': choice,
        'files': plan.local_fingerprint, 'new_hashes': dict(plan.new_hashes),
    }, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return backup


def _write_atomic(path: Path, value: bytes, mode: Optional[int] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.wonsky-write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(value)
        if mode is not None:
            os.chmod(temporary, mode)
        Path(temporary).replace(path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def _record_originals(plan: UpdatePlan) -> None:
    recorded = {}
    originals = {}
    for name, fingerprint in plan.new_hashes.items():
        if PurePosixPath(name).name.casefold() == 'agents.md' and name in plan.preserved:
            # Retain original ownership, never claim user bytes are vendor originals.
            if name in plan.previous_hashes:
                recorded[name] = plan.previous_hashes[name]
            continue
        recorded[name] = fingerprint
        originals[name] = plan.contents[name]
    write_state(plan.state_path, recorded, originals=originals)


def apply_plan(plan: UpdatePlan, choice: str, backup_root: Path) -> ApplyResult:
    """Keep a unit, safely update it, or explicitly replace reviewed vendor files.

    Extra local files and existing AGENTS.md always survive. Removed upstream
    files are deleted only when they belonged to the recorded original unit.
    """
    if choice not in ('keep', 'update', 'replace'):
        raise ValueError('Unknown update choice: {}'.format(choice))
    if choice == 'keep':
        return ApplyResult(SyncResult('kept', preserved=plan.preserved))
    validate_plan(plan)
    if plan.blocked:
        raise ValueError('Blocked paths cannot be replaced: {}'.format(', '.join(plan.blocked)))
    if choice == 'update' and plan.conflicts:
        raise ValueError('Local edits require Keep or explicit Replace: {}'.format(', '.join(plan.conflicts)))
    if not plan.replacement_changes:
        # Byte-identical adoption only changes installer bookkeeping, not user files.
        _record_originals(plan)
        return ApplyResult(SyncResult('unchanged', preserved=plan.preserved))
    backup = _backup(plan, choice, backup_root)
    validate_plan(plan)
    changes = [change.path for change in plan.replacement_changes]
    completed = []
    created_directories = set()
    old_state = plan.state_fingerprint
    try:
        for name in changes:
            target = plan.destination / name
            if symlink_in_chain(plan.destination) is not None or blocked_path(plan.destination, name):
                raise ValueError('Destination path changed or became unsafe: {}'.format(name))
            completed.append(name)
            if name in plan.contents:
                for parent in target.parents:
                    if parent == plan.destination.parent:
                        break
                    if not parent.exists():
                        created_directories.add(parent)
                _write_atomic(target, plan.contents[name], plan.files[name].stat().st_mode)
            elif name in plan.previous_hashes and target.exists():
                target.unlink()
        _record_originals(plan)
    except (OSError, ValueError) as error:
        failures = []
        for name in reversed(completed):
            target, original = plan.destination / name, backup / 'files' / name
            try:
                if symlink_in_chain(plan.destination) is not None or blocked_path(plan.destination, name):
                    raise ValueError('Unsafe rollback path: {}'.format(target))
                if original.is_file():
                    _write_atomic(target, original.read_bytes(), original.stat().st_mode)
                elif target.exists():
                    target.unlink()
            except (OSError, ValueError) as rollback_error:
                failures.append(str(rollback_error))
        for directory in sorted(created_directories, key=lambda path: len(path.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        try:
            if old_state is None:
                if plan.state_path.exists():
                    plan.state_path.unlink()
            else:
                _write_atomic(plan.state_path, old_state)
        except (OSError, ValueError) as rollback_error:
            failures.append(str(rollback_error))
        detail = ' Rollback errors: {}.'.format('; '.join(failures)) if failures else ' Original files restored.'
        raise OSError('Update failed. Backup retained at {}.{} {}'.format(backup, detail, error)) from error
    status = ('updated' if plan.local_fingerprint else 'added') if changes else 'unchanged'
    return ApplyResult(SyncResult(status, preserved=plan.preserved), backup)
