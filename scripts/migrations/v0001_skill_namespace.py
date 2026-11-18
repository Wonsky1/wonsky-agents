"""Plan migration 0001 from legacy runtime slugs to wa-prefixed folders."""

from pathlib import Path
from typing import Optional

from scripts.filesystem.managed import digest, file_bytes, read_state, regular_files, snapshot, symlink_in_chain
from scripts.migrations.models.plan import MigrationPlan
from scripts.skills.distribution import distribution_issue
from scripts.skills.names import runtime_skill_name

NAMESPACE_MIGRATION_ID = '0001-wa-skill-namespace'


def namespace_plans(skills: list, targets: list, baseline: Optional[Path] = None) -> list:
    result = []
    for target in targets:
        for skill in skills:
            old = target.path / skill.name
            new = target.path / runtime_skill_name(skill.name)
            if old == new or not (old.exists() or old.is_symlink()):
                continue
            if distribution_issue(skill.name, target.key):
                continue
            state = target.path / '.wonsky-state' / (skill.name + '.json')
            new_state = state.with_name(new.name + '.json')
            journal = state.parent / 'migrations' / NAMESPACE_MIGRATION_ID / (skill.name + '.json')
            blocked = any(symlink_in_chain(path) is not None for path in (old, new, state, new_state, journal))
            if blocked or not old.is_dir():
                raise ValueError('Unsafe legacy migration path; preserved: {}'.format(old))
            before = file_bytes(state)
            owned = read_state(state)
            manifest = old / 'SKILL.md'
            trusted = bool(owned.get('SKILL.md'))
            matches = (symlink_in_chain(manifest) is None and manifest.is_file()
                       and owned.get('SKILL.md') == digest(manifest))
            previous = baseline / 'skills' / skill.name if baseline else None
            if not trusted and previous and previous.is_dir():
                original = regular_files(previous)
                matches = bool(original.get('SKILL.md')) and all(
                    (old / name).is_file() and symlink_in_chain(old / name) is None and
                    digest(old / name) == digest(path) for name, path in original.items())
                trusted = matches
            status, reason = 'ready', 'Move the verified legacy skill and its ownership record.'
            if not trusted:
                status, reason = 'unowned', 'Unverified legacy folder retained; install the prefixed skill alongside it.'
            elif not matches:
                status, reason = 'blocked', 'Owned SKILL.md was edited or deleted; review it before migrating.'
            elif new.exists() or new.is_symlink() or new_state.exists():
                status, reason = 'blocked', 'Both legacy and prefixed locations/state exist; review them before migrating.'
            result.append(MigrationPlan(NAMESPACE_MIGRATION_ID, old, new, state, new_state, journal,
                                        status, reason, snapshot(old), before, file_bytes(journal)))
    return result
