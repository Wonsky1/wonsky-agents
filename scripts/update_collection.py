"""Construct canonical and runtime review units without changing installed files."""

from pathlib import Path
from typing import Mapping, Optional

from scripts.managed_files import digest, read_original, read_state, regular_files, symlink_in_chain
from scripts.models.update import UpdatePlan
from scripts.skill_files import check_overlap, collection_files, validate_skill
from scripts.update_plan import build_plan, effective_files


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
                  baseline: Optional[Path] = None) -> list:
    result = []
    for plan in plans[1:]:
        name = plan.destination.name
        choice = choices[plan.id]
        # Keeping a canonical skill means the offered update is skipped for that skill.
        if choice == 'keep':
            continue
        source = public_files(effective_files(plan, choice))
        for target in targets:
            previous = baseline / 'skills' / name if baseline else None
            prior = public_files(regular_files(previous)) if previous and previous.is_dir() else None
            result.append(build_plan(source, target.path / name,
                                     target.path / '.wonsky-state' / (name + '.json'), baseline=prior,
                                     label=target.label + ' / ' + name))
    return result
