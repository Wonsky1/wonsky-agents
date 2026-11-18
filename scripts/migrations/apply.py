"""Back up and apply individual migrations, with guarded rollback and journals."""

import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

from scripts.filesystem.managed import snapshot, symlink_in_chain
from scripts.filesystem.managed import file_bytes
from scripts.migrations.models.plan import MigrationPlan


def validate_migration(plan: MigrationPlan) -> None:
    if plan.status != 'ready':
        raise ValueError('Migration is not ready: {}'.format(plan.reason))
    for path in (plan.source, plan.destination, plan.state_source, plan.state_destination, plan.journal):
        if symlink_in_chain(path) is not None:
            raise ValueError('Migration path became a symlink; review again: {}'.format(path))
    if (snapshot(plan.source) != plan.files or file_bytes(plan.state_source) != plan.state_before or
            file_bytes(plan.journal) != plan.journal_before or plan.destination.exists() or
            plan.state_destination.exists()):
        raise ValueError('Migration files changed after preview; review again: {}'.format(plan.source))


def _write_journal(path: Path, data: dict) -> None:
    file_bytes(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.migration-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def apply_migration(plan: MigrationPlan) -> Path:
    validate_migration(plan)
    backup = plan.state_source.parent / 'migration-backups' / plan.migration_id / uuid.uuid4().hex
    if symlink_in_chain(backup) is not None:
        raise ValueError('Symlinked migration backup; preserved: {}'.format(backup))
    shutil.copytree(plan.source, backup / 'files', symlinks=True)
    if snapshot(backup / 'files') != plan.files:
        raise OSError('Migration backup differs from preview; source preserved: {}'.format(backup))
    if plan.state_before is not None:
        (backup / 'installation-state.json').write_bytes(plan.state_before)
    record = {'version': 1, 'migration_id': plan.migration_id, 'status': 'complete',
              'source': str(plan.source), 'destination': str(plan.destination), 'backup': str(backup)}
    (backup / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    validate_migration(plan)
    moved_skill = moved_state = False
    try:
        plan.source.rename(plan.destination)
        moved_skill = True
        if plan.state_before is not None:
            plan.state_source.rename(plan.state_destination)
            moved_state = True
        _write_journal(plan.journal, record)
    except (OSError, ValueError) as error:
        try:
            if moved_state:
                plan.state_destination.rename(plan.state_source)
            if moved_skill:
                plan.destination.rename(plan.source)
        except OSError as rollback_error:
            raise OSError('Migration rollback failed; backup at {}: {}'.format(backup, rollback_error)) from error
        raise OSError('Migration failed; original restored. Backup at {}: {}'.format(backup, error)) from error
    return backup
