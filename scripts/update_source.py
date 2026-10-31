"""Load a local collection or stage a pinned GitHub download without executing it."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from typing import Iterator, Optional
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import zipfile
import zlib

from scripts.managed_files import regular_files, symlink_in_chain
from scripts.models.update_source import UpdateSource


REPOSITORY = 'Wonsky1/wonsky-agents'
API_URL = 'https://api.github.com/repos/{}/commits/main'.format(REPOSITORY)
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_EXPANDED_BYTES = 128 * 1024 * 1024
MAX_MEMBERS = 20000
MAX_API_BYTES = 1024 * 1024
REQUEST_TIMEOUT = 30
RESERVED_NAMES = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} | {
    '{}{}'.format(prefix, number) for prefix in ('COM', 'LPT')
    for number in tuple(range(1, 10)) + ('\u00b9', '\u00b2', '\u00b3')
}


def _request(url: str, *, api: bool = False) -> Request:
    request = Request(url, headers={
        'User-Agent': 'wonsky-agents-updater',
        'Accept': 'application/vnd.github+json' if api else 'application/zip',
    })
    token = (os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN') or '').strip()
    if token:
        if any(ord(char) < 32 or ord(char) > 126 for char in token):
            raise ValueError('GitHub authentication token contains an invalid control character.')
        # Unredirected headers are deliberately not forwarded to a different URL.
        request.add_unredirected_header('Authorization', 'Bearer ' + token)
    return request


def _fetch(url: str, target: Path, limit: int, *, api: bool = False) -> None:
    """Keep errors actionable without echoing headers, token values or response bodies."""
    try:
        request = _request(url, api=api)
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response, target.open('xb') as stream:
            downloaded = 0
            while True:
                chunk = response.read(min(65536, limit + 1 - downloaded))
                if not chunk:
                    break
                downloaded += len(chunk)
                if downloaded > limit:
                    raise ValueError('GitHub update response exceeds the permitted download size.')
                stream.write(chunk)
    except HTTPError as error:
        # HTTPError also owns a response stream; closing avoids resource-warning
        # diagnostics that could otherwise include an untrusted server reason.
        error.close()
        if error.code in (401, 403, 404):
            message = ('GitHub could not provide the update (HTTP {}). Check repository access, '
                       'the API rate limit, or GH_TOKEN/GITHUB_TOKEN permissions.').format(error.code)
        else:
            message = 'GitHub could not provide the update (HTTP {}). Try again later.'.format(error.code)
        raise ValueError(message) from None
    except (URLError, OSError, TimeoutError):
        raise ValueError('Could not download the GitHub update. Check network access and retry.') from None


def _latest_revision(work: Path) -> str:
    metadata = work / 'revision.json'
    _fetch(API_URL, metadata, MAX_API_BYTES, api=True)
    try:
        payload = json.loads(metadata.read_text(encoding='utf-8'))
        revision = payload['sha']
        if not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}', revision):
            raise ValueError()
    except (UnicodeError, ValueError, KeyError, TypeError):
        raise ValueError('GitHub returned invalid revision metadata; no collection was installed.') from None
    return revision


def _safe_parts(member: zipfile.ZipInfo) -> tuple:
    value = member.filename
    if member.orig_filename != value or not value or value.startswith('/') or '\\' in value:
        raise ValueError('Update ZIP contains an unsafe path.')
    value = value[:-1] if member.is_dir() else value
    parts = tuple(value.split('/'))
    if not parts or any(
            part in ('', '.', '..') or part.endswith(('.', ' ')) or
            any(ord(char) < 32 or ord(char) == 127 or char in '<>:"|?*' for char in part) or
            part.split('.')[0].rstrip(' ').upper() in RESERVED_NAMES
            for part in parts):
        raise ValueError('Update ZIP contains a path incompatible with safe cross-platform installation.')
    mode = member.external_attr >> 16
    kind = stat.S_IFMT(mode)
    if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise ValueError('Update ZIP contains a symlink or special file.')
    if ((kind == stat.S_IFDIR and not member.is_dir()) or
            (kind == stat.S_IFREG and member.is_dir()) or member.flag_bits & 1):
        raise ValueError('Update ZIP contains an invalid or encrypted entry.')
    if member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise ValueError('Update ZIP uses an unsupported compression method.')
    return parts


def _archive_members(archive: zipfile.ZipFile) -> list:
    """Validate the entire directory before creating any extracted file."""
    members = archive.infolist()
    if not members or len(members) > MAX_MEMBERS:
        raise ValueError('Update ZIP is empty or contains too many entries.')
    total = 0
    seen, portable, files, parents, roots, result = set(), {}, set(), set(), set(), []
    for member in members:
        parts = _safe_parts(member)
        roots.add(parts[0])
        total += member.file_size
        if member.file_size < 0 or total > MAX_EXPANDED_BYTES:
            raise ValueError('Update ZIP exceeds the permitted extracted size.')
        if parts in seen:
            raise ValueError('Update ZIP contains duplicate entries.')
        seen.add(parts)
        for count in range(1, len(parts) + 1):
            prefix = parts[:count]
            key = tuple(unicodedata.normalize('NFC', part).casefold() for part in prefix)
            if key in portable and portable[key] != prefix:
                raise ValueError('Update ZIP contains paths that collide on Windows or macOS.')
            portable[key] = prefix
            if prefix in files and count < len(parts):
                raise ValueError('Update ZIP uses a file as a parent directory.')
        if not member.is_dir():
            if parts in parents:
                raise ValueError('Update ZIP uses a file as a parent directory.')
            files.add(parts)
        parents.update(parts[:count] for count in range(1, len(parts)))
        result.append((member, parts))
    if len(roots) != 1 or not any(len(parts) > 1 for _, parts in result):
        raise ValueError('Update ZIP must contain one collection directory.')
    return result


def _private_or_generated(parts: tuple) -> bool:
    if any(part in ('.git', '.wonsky-state', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache')
           for part in parts):
        return True
    name = parts[-1]
    return (name == 'reviewer-preferences.md' or
            any(part.startswith('.env') and part != '.env.example' for part in parts) or
            name.endswith(('.pyc', '.pyo')) or name == '.DS_Store')


def _extract(archive_path: Path, destination: Path) -> Path:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = _archive_members(archive)
            for member, parts in members:
                if _private_or_generated(parts):
                    continue
                target = destination.joinpath(*parts)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as incoming, target.open('xb') as output:
                    shutil.copyfileobj(incoming, output, length=65536)
                target.chmod(0o755 if (member.external_attr >> 16) & 0o111 else 0o644)
            return destination / members[0][1][0]
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError, zlib.error):
        raise ValueError('GitHub returned an invalid or unsupported update ZIP.') from None


def _validate_collection(root: Path) -> None:
    if symlink_in_chain(root) is not None or not root.is_dir():
        raise ValueError('Update source must be an existing regular collection directory.')
    for name in ('install.py', 'scripts', 'skills'):
        path = root / name
        if path.is_symlink() or (not path.is_file() if name == 'install.py' else not path.is_dir()):
            raise ValueError('Update source is missing a regular {} entry.'.format(name))
    regular_files(root / 'scripts')
    regular_files(root / 'skills')
    skills = [path for path in (root / 'skills').iterdir() if path.is_dir()]
    if not skills or any(not (path / 'SKILL.md').is_file() for path in skills):
        raise ValueError('Update source must contain skill directories with SKILL.md files.')


@contextmanager
def open_update_source(path: Optional[Path] = None) -> Iterator[UpdateSource]:
    """Yield a validated collection; only downloaded staging is removed on exit.

    A local folder is reported as revision ``unknown``: it is the proposed new
    content, never evidence of what was originally installed. No source code
    from either source is imported or executed.
    """
    if path is not None:
        supplied = Path(path).expanduser().absolute()
        if supplied.is_symlink():
            raise ValueError('Update source must be an existing regular collection directory.')
        root = supplied.resolve()
        _validate_collection(root)
        yield UpdateSource(root, 'unknown', 'local folder: {}'.format(root))
        return
    with tempfile.TemporaryDirectory(prefix='wonsky-update-') as temporary:
        # macOS's default temporary directory may be reached through /var.
        work = Path(temporary).resolve()
        revision = _latest_revision(work)
        archive_path = work / 'collection.zip'
        url = 'https://api.github.com/repos/{}/zipball/{}'.format(REPOSITORY, revision)
        _fetch(url, archive_path, MAX_ARCHIVE_BYTES)
        root = _extract(archive_path, work / 'extracted')
        _validate_collection(root)
        yield UpdateSource(root, revision, 'GitHub {} at {}'.format(REPOSITORY, revision))
