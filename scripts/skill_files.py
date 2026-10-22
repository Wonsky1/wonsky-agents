"""Copy complete skills using only Python, staging replacements before writes."""

from pathlib import Path
import shutil
import tempfile
from typing import Sequence


IGNORED = shutil.ignore_patterns('.DS_Store', '__pycache__', '*.pyc', '*.pyo',
                                 '.pytest_cache', '.ruff_cache', '.mypy_cache')


def validate_skill(source: Path) -> None:
    if not source.is_dir() or not (source / 'SKILL.md').is_file():
        raise ValueError('Not a skill directory: {}'.format(source))
    if source.is_symlink() or any(p.is_symlink() for p in source.rglob('*')):
        raise ValueError('Canonical skills must contain regular files/directories, not symlinks: {}'.format(source))


def check_overlap(source: Path, destination: Path) -> bool:
    """Return True for identical paths; reject nested trees before writing."""
    src, dst = source.resolve(), destination.resolve()
    if src == dst:
        return True
    if src in dst.parents or dst in src.parents:
        raise ValueError('Source and destination overlap: {} and {}'.format(source, destination))
    return False


def sync_skill(source: Path, destination: Path, preserve: Sequence[str] = ()) -> None:
    validate_skill(source)
    if check_overlap(source, destination) and not destination.is_symlink():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.wonsky-sync-', dir=destination.parent))
    staged, previous = staging / 'new', staging / 'previous'
    installed = False
    try:
        shutil.copytree(source, staged, ignore=IGNORED)
        for name in preserve:
            old = destination / name
            if old.is_file() and not old.is_symlink() and not (staged / name).exists():
                shutil.copy2(old, staged / name)
        if destination.exists() or destination.is_symlink():
            destination.replace(previous)
        try:
            staged.replace(destination)
            installed = True
        except OSError:
            if previous.exists() or previous.is_symlink():
                previous.replace(destination)
            raise
    finally:
        # Retain the backup if restoring it failed; never erase the only old copy.
        if (previous.exists() or previous.is_symlink()) and not installed:
            raise OSError('Replacement failed; original skill retained at {}'.format(previous))
        shutil.rmtree(staging)


def install_collection(source: Path, canonical: Path, update: bool = False) -> None:
    if check_overlap(source, canonical):
        return
    if canonical.exists() and any(canonical.iterdir()) and not update:
        raise ValueError('Canonical directory already exists: {}. Use its installer, or --update to replace collection files.'.format(canonical))
    skills = sorted(p for p in (source / 'skills').iterdir() if (p / 'SKILL.md').is_file())
    if not skills:
        raise ValueError('No skills found in {}'.format(source / 'skills'))
    for skill in skills:
        validate_skill(skill)
    canonical.mkdir(parents=True, exist_ok=True)
    for name in ('README.md', 'CHANGELOG.md', '.gitignore', 'install.py', 'install.sh', 'install.ps1',
                 'scripts', 'docs', 'tests', '.github'):
        item = source / name
        if item.is_dir():
            shutil.copytree(item, canonical / name, dirs_exist_ok=True, ignore=IGNORED)
        elif item.is_file():
            shutil.copy2(item, canonical / name)
    for skill in skills:
        preserve = ('reviewer-preferences.md',) if skill.name == 'github-pr-review' else ()
        sync_skill(skill, canonical / 'skills' / skill.name, preserve=preserve)
