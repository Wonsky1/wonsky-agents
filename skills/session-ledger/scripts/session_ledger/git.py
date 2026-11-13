"""Git root discovery and verified ignore checks."""
import os
from pathlib import Path
import subprocess
from typing import List, Optional

from session_ledger.models.ledger import LedgerError, Root


def run_git(root: Path, args: List[str]) -> subprocess.CompletedProcess:
    # A hook may inherit another Git process's repository/index overrides.
    # Always discover and inspect the repository containing the requested path.
    environment = dict(os.environ)
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE',
                'GIT_PREFIX'):
        environment.pop(key, None)
    environment['LC_ALL'] = 'C'
    try:
        return subprocess.run(['git', *args], cwd=str(root), capture_output=True,
                              text=True, env=environment, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LedgerError('cannot verify Git repository: ' + str(error)) from error


def resolve_root(repo: Optional[str] = None) -> Root:
    start = Path(repo).expanduser() if repo is not None else Path.cwd()
    if not start.is_dir():
        raise LedgerError('repository directory does not exist: ' + str(start))
    start = start.resolve()
    marker = any((path / '.git').exists() or (path / '.git').is_symlink()
                 for path in (start, *start.parents))
    try:
        result = run_git(start, ['rev-parse', '--show-toplevel'])
    except LedgerError:
        if repo is not None and not marker:
            return Root(start, False)
        raise
    if result.returncode == 0 and result.stdout.strip():
        return Root(Path(result.stdout.strip()).resolve(), True)
    if marker or 'not a git repository' not in result.stderr.lower():
        raise LedgerError('cannot resolve Git repository: ' + result.stderr.strip())
    if repo is None:
        raise LedgerError('not inside a Git repository; pass --repo PATH')
    return Root(start, False)


def verify_ignored(root: Root, path: Path) -> None:
    if not root.is_git:
        return
    relative = path.relative_to(root.path).as_posix()
    result = run_git(root.path, ['check-ignore', '-q', '--', relative])
    if result.returncode == 1:
        raise LedgerError(relative + ' is NOT ignored by Git (or is tracked); preserve and review existing ignore rules')
    if result.returncode != 0:
        raise LedgerError('Git ignore verification failed: ' + result.stderr.strip())
