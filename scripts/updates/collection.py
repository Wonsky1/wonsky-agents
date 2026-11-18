"""Construct canonical and runtime review units without changing installed files."""

from dataclasses import replace
from pathlib import Path
from typing import Mapping, Optional

from scripts.filesystem.managed import digest, read_original, read_state, regular_files, symlink_in_chain
from scripts.updates.models.plan import UpdatePlan
from scripts.migrations.registry import ready_migration
from scripts.skills.files import check_overlap, collection_files, validate_skill
from scripts.skills.distribution import distribution_issue, distribution_names
from scripts.skills.names import runtime_skill_name
from scripts.updates.plan import build_plan, effective_files


def public_files(files: Mapping[str, Path]) -> dict:
    return {name: path for name, path in files.items()
            if Path(name).name.casefold() != 'reviewer-preferences.md' and
            not any((part.casefold().startswith('.env') and part.casefold() != '.env.example') or
                    part.startswith(('.wonsky-state', '.wonsky-backups', '.wonsky-sync-')) for part in Path(name).parts)}


def _baseline(canonical: Path, prefix: str, explicit: Optional[Path]) -> tuple:
    if explicit is not None:
        folder = explicit / prefix if prefix else explicit
        if folder.is_dir():
            return (public_files(regular_files(folder)) if prefix else {
                name: path for name, path in public_files(collection_files(folder)).items()
                if not name.startswith('skills/')}), {}
    state = canonical / '.wonsky-state' / 'collection.json'
    hashes = read_state(state)
    found, known = {}, {}
    for name, sha in hashes.items():
        if prefix:
            if not name.startswith(prefix + '/'):
                continue
            relative = name[len(prefix) + 1:]
        else:
            if name.startswith('skills/'):
                continue
            relative = name
        known[relative] = sha
        if not public_files({relative: canonical / name}):
            continue
        value = read_original(state, sha)
        if value is not None:
            found[relative] = state.parent / 'objects' / sha
        else:
            installed = canonical / name
            if symlink_in_chain(installed) is None and installed.is_file() and digest(installed) == sha:
                found[relative] = installed
    return found or None, known


def canonical_plans(source: Path, canonical: Path, baseline: Optional[Path] = None) -> list:
    if check_overlap(source, canonical):
        raise ValueError('The new collection must be staged outside the canonical installation; use a download or --from another folder.')
    files = public_files(collection_files(source))
    support = {name: path for name, path in files.items() if not name.startswith('skills/')}
    recovered, known = _baseline(canonical, '', baseline)
    plans = [build_plan(support, canonical, canonical / '.wonsky-state' / 'support.json',
                        baseline=recovered, known_hashes=known or None, label='Canonical installer and documentation')]
    skills = sorted(path for path in (source / 'skills').iterdir()
                    if not path.name.startswith('.') and (path / 'SKILL.md').is_file())
    for skill in skills:
        validate_skill(skill)
        prefix = 'skills/' + skill.name
        recovered, known = _baseline(canonical, prefix, baseline)
        plans.append(build_plan(public_files(regular_files(skill)), canonical / prefix,
                                canonical / '.wonsky-state' / 'canonical-skills' / (skill.name + '.json'),
                                baseline=recovered, known_hashes=known or None, label='Canonical / ' + skill.name))
    return plans


def runtime_plans(plans: list, choices: Mapping[str, str], targets: list,
                  baseline: Optional[Path] = None, migrations: Optional[list] = None) -> list:
    result = []
    for plan in plans[1:]:
        name = plan.destination.name
        installed_name = runtime_skill_name(name)
        choice = choices[plan.id]
        source = None
        for target in targets:
            destination = target.path / installed_name
            exists = destination.exists() or destination.is_symlink()
            issue = distribution_issue(name, target.key, exists)
            if issue:
                for restricted_name in distribution_names(name, target.key):
                    restricted = target.path / restricted_name
                    exists = restricted.exists() or restricted.is_symlink()
                    message = '{}. Attach {} explicitly to use it.'.format(
                        distribution_issue(name, target.key, exists), plan.destination / 'SKILL.md')
                    if exists:
                        if symlink_in_chain(restricted) is not None or not restricted.is_dir():
                            raise ValueError('{}: {}'.format(restricted, message))
                        blocked = build_plan({}, restricted, target.path / '.wonsky-state' / (restricted_name + '.json'),
                                             label=target.label + ' / ' + restricted_name)
                        result.append(replace(blocked, status='blocked', blocked=(message,),
                                              upstream_changes=(), replacement_changes=()))
                    else:
                        print('{} / {}: {}'.format(target.label, restricted_name, message))
                continue
            # Keeping a canonical skill skips its offered runtime update, but an
            # existing unsupported manual-only copy must still be reported above.
            if choice == 'keep':
                continue
            if source is None:
                source = public_files(effective_files(plan, choice))
            previous = baseline / 'skills' / name if baseline else None
            prior = public_files(regular_files(previous)) if previous and previous.is_dir() else None
            migration = ready_migration(migrations or [], destination)
            local = migration.source if migration else destination
            state = migration.state_source if migration else target.path / '.wonsky-state' / (installed_name + '.json')
            runtime = build_plan(source, local, state, baseline=prior, label=target.label + ' / ' + installed_name)
            result.append(replace(runtime, id=str(destination), destination=destination,
                                  state_path=target.path / '.wonsky-state' / (installed_name + '.json')))
    return result
