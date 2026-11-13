"""Guarded repository-local persistence and exclusive mutation ownership."""
from contextlib import contextmanager
import datetime as dt
import os
from pathlib import Path
import stat
import tempfile
from typing import Iterator, List, Optional
import uuid

from session_ledger.git import resolve_root, verify_ignored
from session_ledger.markdown import add_binding, parse_header, render, slugify
from session_ledger.models.ledger import Binding, Ledger, LedgerError, Root

FOLDER = '.agent-ledger'
IGNORE_TEXT = '# Session ledger local files\n*\n'
TEMPLATE = Path(__file__).resolve().parents[2] / 'templates' / 'ledger.md'


def checked_file(path: Path, missing_ok: bool = False) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        if missing_ok:
            return
        raise LedgerError('file does not exist: ' + str(path))
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise LedgerError('expected a regular, unlinked file (no symlinks): ' + str(path))


def checked_folder(root: Root, create: bool = False) -> Path:
    folder = root.path / FOLDER
    if folder.is_symlink():
        raise LedgerError('symlinked ledger directory is not supported: ' + str(folder))
    if create:
        folder.mkdir(mode=0o700, exist_ok=True)
    if folder.exists() and not folder.is_dir():
        raise LedgerError('ledger storage is not a directory: ' + str(folder))
    if folder.resolve() != root.path / FOLDER:
        raise LedgerError('ledger directory escapes repository')
    return folder


def read_text(path: Path) -> str:
    checked_file(path)
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(str(path), flags), encoding='utf-8') as handle:
        return handle.read()


def write_new(path: Path, text: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(str(path), flags, 0o600), 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text)


def prepare_storage(root: Root) -> Path:
    folder = checked_folder(root, create=True)
    ignore = folder / '.gitignore'
    checked_file(ignore, missing_ok=True)
    if not ignore.exists():
        write_new(ignore, IGNORE_TEXT)
    verify_ignored(root, ignore)
    return folder


@contextmanager
def mutation(root: Root) -> Iterator[Path]:
    folder = prepare_storage(root)
    lock = folder / '.lock'
    checked_file(lock, missing_ok=True)
    verify_ignored(root, lock)
    try:
        write_new(lock, str(os.getpid()) + '\n')
    except FileExistsError as error:
        raise LedgerError('ledger is busy; retry after the other operation finishes (stale lock: ' + str(lock) + ')') from error
    try:
        yield folder
    finally:
        lock.unlink()


def read_ledgers(root: Root) -> List[Ledger]:
    folder = checked_folder(root)
    if not folder.exists():
        return []
    checked_file(folder / '.gitignore', missing_ok=True)
    ledgers = []
    for path in sorted(folder.glob('*.md')):
        checked_file(path)
        verify_ignored(root, path)
        ledgers.append(parse_header(path, read_text(path)))
    return ledgers


def find_ledger(root: Root, identity: Optional[Binding] = None,
                identifier: Optional[str] = None) -> Optional[Ledger]:
    matches = [item for item in read_ledgers(root)
               if (identity is not None and identity in item.bindings)
               or (identifier is not None and identifier == item.identifier)]
    if len(matches) > 1:
        raise LedgerError('ambiguous ledger identity; inspect the files explicitly')
    return matches[0] if matches else None


def new_ledger(root: Root, slug: str, identity: Optional[Binding]) -> Ledger:
    with mutation(root) as folder:
        existing = find_ledger(root, identity) if identity else None
        if existing:
            return existing
        today = dt.date.today()
        identifier = uuid.uuid4().hex
        while find_ledger(root, identifier=identifier):
            identifier = uuid.uuid4().hex
        path = folder / (today.strftime('%Y%m%d') + '-' + identifier + '-' + slugify(slug) + '.md')
        checked_file(path, missing_ok=True)
        verify_ignored(root, path)
        text = render(TEMPLATE.read_text(encoding='utf-8'), slug, path.relative_to(root.path).as_posix(),
                      identifier, identity, today)
        write_new(path, text)
        return parse_header(path, text)


def root_for_ledger(raw: str) -> Root:
    path = Path(os.path.abspath(os.path.expanduser(raw)))
    if path.parent.name != FOLDER or path.suffix != '.md':
        raise LedgerError('ledger must be a Markdown file directly inside ' + FOLDER)
    root = resolve_root(str(path.parent.parent))
    folder = checked_folder(root)
    if path.parent != folder:
        raise LedgerError('ledger does not belong to this repository root')
    checked_file(path)
    verify_ignored(root, path)
    return root


def load_ledger(raw: str) -> Ledger:
    root = root_for_ledger(raw)
    path = root.path / FOLDER / Path(raw).name
    return parse_header(path, read_text(path))


def bind_session(raw: str, identity: Binding) -> bool:
    root = root_for_ledger(raw)
    path = root.path / FOLDER / Path(raw).name
    with mutation(root) as folder:
        owner = find_ledger(root, identity)
        if owner:
            if owner.path != path:
                raise LedgerError('session already belongs to ' + str(owner.path))
            return False
        current = read_text(path)
        parse_header(path, current)
        updated = add_binding(current, identity)
        # Replace atomically, preserving the previous complete ledger on write failure.
        descriptor, name = tempfile.mkstemp(prefix='.write-', dir=str(folder))
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as handle:
                handle.write(updated)
            checked_file(path)
            verify_ignored(root, path)
            os.replace(str(temporary), str(path))
        finally:
            if temporary.exists():
                temporary.unlink()
    return True
