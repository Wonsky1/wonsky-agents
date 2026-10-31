"""Update only unchanged, previously recorded files; preserve user-owned content."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from typing import Dict, Mapping, Optional

from scripts.models.sync_result import SyncResult


STATE_VERSION = 2
IGNORED = shutil.ignore_patterns('.DS_Store', '__pycache__', '*.pyc', '*.pyo',
                                 '.pytest_cache', '.ruff_cache', '.mypy_cache')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_error(error: OSError) -> None:
    raise error


def symlink_in_chain(path: Path) -> Optional[Path]:
    for candidate in (path.absolute(), *path.absolute().parents):
        if candidate.is_symlink():
            return candidate
    return None


def regular_files(root: Path) -> Dict[str, Path]:
    """Inventory source files without following links or copying runtime caches."""
    found = {}
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        parent_path = Path(parent)
        ignored = IGNORED(str(parent_path), dirs + files)
        for name in dirs + files:
            if (parent_path / name).is_symlink():
                raise ValueError('Source contains a symlink: {}'.format(parent_path / name))
        dirs[:] = sorted(name for name in dirs if name not in ignored)
        for name in sorted(files):
            if name not in ignored:
                path = parent_path / name
                if not path.is_file():
                    raise ValueError('Source is not a regular file: {}'.format(path))
                found[path.relative_to(root).as_posix()] = path
    return found


def safe_key(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and all(
        part not in ('', '.', '..') and ':' not in part and '\\' not in part
        for part in value.split('/'))


def read_state(path: Path) -> Dict[str, str]:
    if symlink_in_chain(path) is not None:
        raise ValueError('Refusing symlinked installation state: {}'.format(path))
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        files = data['files']
        if data['version'] not in (1, STATE_VERSION) or not isinstance(files, dict):
            raise ValueError()
        if any(not isinstance(key, str) or not safe_key(key) or
               not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value)
               for key, value in files.items()):
            raise ValueError()
        return files
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError('Invalid installation state; no files changed: {}'.format(path)) from error


def read_original(state_path: Path, sha: str) -> Optional[bytes]:
    """Return verified original bytes, never guessed contents or symlink targets."""
    if not re.fullmatch(r'[0-9a-f]{64}', sha):
        return None
    path = state_path.parent / 'objects' / sha
    if symlink_in_chain(path) is not None:
        raise ValueError('Refusing symlinked original snapshot: {}'.format(path))
    if not path.is_file():
        return None
    data = path.read_bytes()
    return data if hashlib.sha256(data).hexdigest() == sha else None


def write_state(path: Path, files: Mapping[str, str],
                originals: Optional[Mapping[str, bytes]] = None) -> None:
    if symlink_in_chain(path) is not None:
        raise ValueError('Refusing symlinked installation state: {}'.format(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    for name, data in (originals or {}).items():
        if Path(name).name.casefold() == 'reviewer-preferences.md' or any(
                part.casefold().startswith('.env') and part.casefold() != '.env.example' for part in Path(name).parts):
            # Track fingerprints if requested, but do not cache private source text.
            continue
        sha = hashlib.sha256(data).hexdigest()
        if not safe_key(name) or files.get(name) != sha:
            raise ValueError('Original snapshot does not match manifest: {}'.format(name))
        target = path.parent / 'objects' / sha
        if symlink_in_chain(target) is not None:
            raise ValueError('Refusing symlinked original snapshot: {}'.format(target))
        target.parent.mkdir(mode=0o700, exist_ok=True)
        if target.is_file() and target.read_bytes() == data:
            continue
        original_fd, original_tmp = tempfile.mkstemp(prefix='.original-', dir=target.parent)
        try:
            with os.fdopen(original_fd, 'wb') as stream:
                stream.write(data)
            Path(original_tmp).replace(target)
        finally:
            Path(original_tmp).unlink(missing_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.state-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump({'version': STATE_VERSION, 'files': dict(sorted(files.items()))}, stream, indent=2)
            stream.write('\n')
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def blocked_path(destination: Path, name: str) -> bool:
    current = destination
    if current.is_symlink():
        return True
    for part in PurePosixPath(name).parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return True
    path = destination / name
    return path.is_symlink() or (path.exists() and not path.is_file())


def snapshot(root: Path) -> dict:
    """Detect edits made while staging, including destination-only files and links."""
    if not root.exists():
        return {}
    found = {}
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        for name in dirs + files:
            path = Path(parent) / name
            key = path.relative_to(root).as_posix()
            if path.is_symlink():
                found[key] = ('link', os.readlink(path))
            elif path.is_file():
                found[key] = ('file', digest(path), path.stat().st_mode)
            elif path.is_dir():
                found[key] = ('dir',)
            else:
                raise ValueError('Unsupported destination entry: {}'.format(path))
    return found


def sync_files(files: Mapping[str, Path], destination: Path, state_path: Path,
               baseline: Optional[Mapping[str, Path]] = None, dry_run: bool = False) -> SyncResult:
    """Stage a complete unit; any ordinary file conflict leaves that unit untouched.

    An explicit baseline may recognize a legacy copy only when its bytes match.
    Existing AGENTS.md files are always retained, even when previously managed.
    No user-owned file is deleted. Obsolete managed files are retained too.
    """
    link = symlink_in_chain(destination) or symlink_in_chain(state_path)
    if link is not None:
        return SyncResult('conflict', (str(link),))
    if destination.exists() and not destination.is_dir():
        return SyncResult('conflict', (str(destination),))
    if any(not safe_key(name) for name in files):
        raise ValueError('Unsafe source-relative path')
    owned = read_state(state_path)
    previous = dict(owned)
    if baseline is not None:
        for name, path in baseline.items():
            if name not in previous:
                previous[name] = digest(path)
    conflicts, preserved, changed = [], [], []
    incoming = {}
    for name, source in files.items():
        target = destination / name
        if PurePosixPath(name).name == 'AGENTS.md' and (target.exists() or target.is_symlink() or blocked_path(destination, name)):
            preserved.append(name)
            continue
        if blocked_path(destination, name):
            conflicts.append(name)
            continue
        wanted = digest(source)
        incoming[name] = wanted
        if target.is_file():
            actual = digest(target)
            if actual == wanted:
                continue
            if previous.get(name) != actual:
                conflicts.append(name)
                continue
        elif name in previous:
            # Deleting a managed file is a local edit too; do not silently restore it.
            conflicts.append(name)
            continue
        changed.append(name)
    if conflicts:
        return SyncResult('conflict', tuple(sorted(conflicts)), tuple(sorted(preserved)))
    existed = destination.exists()
    status = ('updated' if existed else 'added') if changed else 'unchanged'
    result = SyncResult(status, preserved=tuple(sorted(preserved)))
    if dry_run:
        return result
    if not changed:
        # Adopt byte-identical legacy copies without rewriting their contents.
        write_state(state_path, dict(owned, **incoming),
                    originals={name: files[name].read_bytes() for name in incoming})
        return result
    before = snapshot(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.wonsky-sync-', dir=destination.parent))
    staged, backup = staging / 'new', staging / 'previous'
    installed = False
    try:
        if existed:
            shutil.copytree(destination, staged, symlinks=True)
        else:
            staged.mkdir()
        for name in changed:
            target = staged / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(files[name], target)
            if digest(target) != incoming[name]:
                raise OSError('Source changed while staging; retry: {}'.format(files[name]))
        if snapshot(destination) != before:
            raise OSError('Destination changed while staging; retry: {}'.format(destination))
        if existed:
            destination.replace(backup)
        try:
            staged.replace(destination)
            installed = True
        except OSError:
            if backup.exists():
                backup.replace(destination)
            raise
        write_state(state_path, dict(owned, **incoming),
                    originals={name: files[name].read_bytes() for name in incoming})
    finally:
        if backup.exists() and not installed:
            raise OSError('Replacement failed; original retained at {}'.format(backup))
        shutil.rmtree(staging)
    return result
