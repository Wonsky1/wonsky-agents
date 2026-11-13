"""Guarded hook file reads, atomic replacement and local recovery backups."""

import json
import os
from pathlib import Path
import tempfile
from typing import Optional
import uuid

from scripts.managed_files import symlink_in_chain
from scripts.models.hook_plan import HookPlan


def read_bytes(path: Path) -> Optional[bytes]:
    if symlink_in_chain(path) is not None:
        raise ValueError('Refusing symlinked hook configuration: {}'.format(path))
    if path.exists() and not path.is_file():
        raise ValueError('Hook configuration is not a regular file: {}'.format(path))
    return path.read_bytes() if path.exists() else None


def read_object(data: Optional[bytes], path: Path) -> dict:
    if data is None:
        return {}
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: {}'.format(key))
            result[key] = value
        return result
    try:
        result = json.loads(data.decode('utf-8-sig'), object_pairs_hook=unique)
        if not isinstance(result, dict):
            raise ValueError('Expected an object')
        return result
    except (ValueError, UnicodeError) as error:
        raise ValueError('Invalid JSON at {}; preserved: {}'.format(path, error)) from error


def encode(document: dict) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def replace_file(path: Path, data: Optional[bytes]) -> None:
    read_bytes(path)
    if data is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix='.wonsky-hook-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def apply_hook_plan(plan: HookPlan) -> None:
    if plan.status in ('absent', 'unsupported', 'configured', 'conflict'):
        if plan.status == 'conflict':
            raise ValueError(plan.message)
        return
    if read_bytes(plan.config) != plan.before or read_bytes(plan.state) != plan.state_before:
        raise ValueError('Hook configuration changed after preview; review again: {}'.format(plan.config))
    if plan.after == plan.before and plan.state_after == plan.state_before:
        return
    if plan.before is not None and plan.after != plan.before:
        backup = plan.state.parent / 'hook-backups' / uuid.uuid4().hex / plan.config.name
        replace_file(backup, plan.before)
    # Recheck after backup, before replacing settings.
    if read_bytes(plan.config) != plan.before or read_bytes(plan.state) != plan.state_before:
        raise ValueError('Hook configuration changed during backup; review again')
    replace_file(plan.config, plan.after)
    try:
        replace_file(plan.state, plan.state_after)
    except (OSError, ValueError):
        # Avoid overwriting a concurrent edit while recovering our failed write.
        if read_bytes(plan.config) == plan.after:
            replace_file(plan.config, plan.before)
        raise
