"""Preserve user skills and instructions while installing managed collection files."""

from pathlib import Path
from typing import Optional

from scripts.managed_files import regular_files, sync_files, symlink_in_chain
from scripts.models.sync_result import SyncResult


def validate_skill(source: Path) -> None:
    if not source.is_dir() or not (source / 'SKILL.md').is_file():
        raise ValueError('Not a skill directory: {}'.format(source))
    if source.is_symlink():
        raise ValueError('Canonical skills must not be symlinks: {}'.format(source))
    regular_files(source)


def check_overlap(source: Path, destination: Path) -> bool:
    """Return True for identical paths; reject nested trees before writing."""
    src, dst = source.resolve(), destination.resolve()
    if src == dst:
        return True
    if src in dst.parents or dst in src.parents:
        raise ValueError('Source and destination overlap: {} and {}'.format(source, destination))
    return False


def sync_skill(source: Path, destination: Path,
               baseline: Optional[Path] = None, dry_run: bool = False,
               retained_source: Optional[Path] = None) -> SyncResult:
    validate_skill(source)
    link = symlink_in_chain(destination)
    if link is not None:
        return SyncResult('conflict', (str(link),))
    same = check_overlap(source, destination)
    if same and not destination.is_symlink():
        return SyncResult('unchanged')
    files = regular_files(source)
    if retained_source is not None and retained_source.exists():
        if not dry_run:
            raise ValueError('retained_source is only valid for a read-only preview')
        if retained_source.is_symlink() or not retained_source.is_dir():
            raise ValueError('Retained source must be a regular directory: {}'.format(retained_source))
        check_overlap(retained_source, destination)
        retained = regular_files(retained_source)
        # Preview the canonical tree after a preserving ZIP update, not just
        # the incoming download. Existing instruction bytes remain canonical.
        files = dict(retained, **{name: path for name, path in files.items()
                                 if Path(name).name != 'AGENTS.md' or name not in retained})
    # A private profile absent from the source is naturally preserved, like any extra file.
    baseline_files = regular_files(baseline) if baseline and baseline.is_dir() else None
    state = destination.parent / '.wonsky-state' / (destination.name + '.json')
    return sync_files(files, destination, state, baseline=baseline_files, dry_run=dry_run)


def collection_files(source: Path) -> dict:
    """Only ship the documented collection; never copy Git or private environment files."""
    files = {}
    for name in ('AGENTS.md', 'README.md', 'CHANGELOG.md', '.gitignore', 'install.py', 'install.sh', 'install.ps1', 'update.py',
                 'scripts', 'docs', 'tests', '.github', 'skills'):
        path = source / name
        if path.is_symlink():
            raise ValueError('Collection source contains a symlink: {}'.format(path))
        if path.is_dir():
            files.update({name + '/' + key: value for key, value in regular_files(path).items()})
        elif path.is_file():
            files[name] = path
    return files


def install_collection(source: Path, canonical: Path, update: bool = False,
                       baseline: Optional[Path] = None, dry_run: bool = False) -> SyncResult:
    link = symlink_in_chain(canonical)
    if link is not None:
        return SyncResult('conflict', (str(link),))
    if check_overlap(source, canonical):
        return SyncResult('unchanged')
    if canonical.exists() and not canonical.is_dir():
        return SyncResult('conflict', (str(canonical),))
    if canonical.exists() and any(canonical.iterdir()) and not update:
        raise ValueError('Canonical directory already exists: {}. Use its installer, or --update for a preserving update.'.format(canonical))
    skills = sorted(p for p in (source / 'skills').iterdir() if (p / 'SKILL.md').is_file())
    if not skills:
        raise ValueError('No skills found in {}'.format(source / 'skills'))
    for skill in skills:
        validate_skill(skill)
    return sync_files(collection_files(source), canonical, canonical / '.wonsky-state' / 'collection.json',
                      baseline=collection_files(baseline) if baseline else None, dry_run=dry_run)
