"""Review canonical and runtime updates before touching installed files."""

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import platform
import sys
from typing import Optional

from scripts.installation.targets import detect_targets, select_keys
from scripts.filesystem.managed import symlink_in_chain
from scripts.migrations.apply import apply_migration, validate_migration
from scripts.migrations.review import migration_review
from scripts.migrations.registry import plan_migrations, ready_migration
from scripts.migrations.review import show_migrations
from scripts.hooks.setup import hook_config_path
from scripts.skills.files import check_overlap
from scripts.hooks.recovery import apply_recovery, plan_recovery, recovery_review, show_recovery, validate_recovery
from scripts.installation.picker import pick_targets
from scripts.updates.apply import apply_plan
from scripts.updates.collection import canonical_plans, runtime_plans
from scripts.skills.names import runtime_skill_name
from scripts.updates.plan import effective_files, validate_plan
from scripts.updates.review import (choose, confirm, default_choice, describe, load_decisions,
                                   report_data, reviewed_choices)
from scripts.updates.source import open_update_source


def _choices(plans: list, args, saved: Optional[dict]) -> dict:
    if saved is not None:
        return reviewed_choices(plans, saved, require_all=not args.dry_run)
    if args.dry_run or args.yes:
        return {plan.id: default_choice(plan) for plan in plans}
    review = [plan for plan in plans if plan.status != 'unchanged' or plan.local_changes]
    result = {plan.id: default_choice(plan) for plan in plans}
    if review:
        result.update(choose(review, args.terminal))
    return result


def _write_report(path: Path, data: dict, plans: list, protected: list) -> None:
    target = path.expanduser().absolute()
    # A report path must not become an accidental overwrite of unrelated skills,
    # instructions, source files or user data, even outside the selected units.
    if symlink_in_chain(target) is not None:
        raise ValueError('Report paths must not contain symlinks.')
    if target.name.casefold() in ('agents.md', 'claude.md', '.cursorrules'):
        raise ValueError('A report cannot be saved as an instruction file.')
    for folder in [*protected, *(plan.destination for plan in plans)]:
        dest, resolved = folder.resolve(), target.resolve()
        if resolved == dest or dest in resolved.parents:
            raise ValueError('Save the review report outside collection/source/agent skill directories.')
    if target.exists():
        try:
            previous = json.loads(target.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError, OSError) as error:
            raise ValueError('Refusing to overwrite an existing non-report file: {}'.format(target)) from error
        if not isinstance(previous, dict) or previous.get('kind') != 'wonsky-agents-update-review':
            raise ValueError('Refusing to overwrite an existing non-report file: {}'.format(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Full local review report: {}'.format(target))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Review and update Wonsky Agents with Python 3.9+ only.')
    parser.add_argument('--from', dest='source', type=Path, help='read a separate extracted collection instead of downloading GitHub main')
    parser.add_argument('--baseline', type=Path, help='trusted previous collection for older installations without original snapshots')
    targets = parser.add_mutually_exclusive_group()
    targets.add_argument('--targets', help='comma-separated cursor,claude,codex,antigravity,agents,copilot')
    targets.add_argument('--all', action='store_true', help='select all detected destinations')
    parser.add_argument('--terminal', action='store_true', help='use terminal review instead of optional Tk windows')
    parser.add_argument('--dry-run', action='store_true', help='preview; never change installed files or ownership state')
    parser.add_argument('--report', type=Path, help='save complete review evidence and choices as local JSON outside the installation')
    parser.add_argument('--decisions', type=Path, help='use choices/tokens from an inspected report; stale or incomplete approvals are rejected')
    parser.add_argument('--yes', action='store_true', help='apply safe updates or exact reviewed decisions without a final prompt; never blindly replace local edits')
    parser.add_argument('--no-session-hooks', action='store_true', help='skip automatic recovery hook setup')
    args = parser.parse_args(argv)
    try:
        system = platform.system()
        if system not in ('Darwin', 'Linux', 'Windows'):
            raise ValueError('Supported operating systems: macOS, Linux and Windows.')
        home = Path.home()
        canonical = Path(os.environ.get('WONSKY_AGENTS_HOME') or home / '.wonsky-agents').expanduser().absolute()
        baseline = args.baseline.expanduser().resolve() if args.baseline else None
        if baseline and not (baseline / 'skills').is_dir():
            raise ValueError('--baseline needs a trusted collection containing skills/.')
        available = detect_targets(home, system, os.environ)
        keys = select_keys(available, args.targets, args.all)
        if args.targets is None and not args.all:
            keys = pick_targets(available, args.terminal)
        if not keys:
            print('No destinations selected. Nothing changed.')
            return 0
        selected = [target for target in available if target.key in keys]
        print('System: {} | Python: {} | Canonical: {}'.format(system, platform.python_version(), canonical))
        with open_update_source(args.source) as source:
            print('Offered version: {} ({})'.format(source.revision, source.provenance))
            seen = set()
            for target in selected:
                resolved = target.path.resolve()
                if resolved in seen:
                    raise ValueError('Selected runtime destinations overlap; choose one target for each skills directory.')
                seen.add(resolved)
                for protected in (canonical, source.root):
                    if check_overlap(protected, target.path):
                        raise ValueError('Runtime destinations must not overlap the canonical collection or update source.')
            for index, target in enumerate(selected):
                for other in selected[index + 1:]:
                    check_overlap(target.path, other.path)
            saved = load_decisions(args.decisions, source.revision) if args.decisions else None
            canonical_units = canonical_plans(source.root, canonical, baseline)
            canonical_choices = _choices(canonical_units, args, saved)
            migration_skills = [plan.destination for plan in canonical_units[1:]
                                if canonical_choices[plan.id] != 'keep']
            migrations = plan_migrations(migration_skills, selected, baseline)
            show_migrations(migrations)
            if any(plan.status == 'blocked' for plan in migrations):
                print('Migration conflicts preserved. Review the reported folders before retrying.')
                return 2
            runtime_units = runtime_plans(canonical_units, canonical_choices, selected, baseline, migrations)
            runtime_choices = _choices(runtime_units, args, saved)
            plans = canonical_units + runtime_units
            choices = dict(canonical_choices, **runtime_choices)
            if saved is not None and not args.dry_run and set(saved) != {plan.id for plan in plans}:
                raise ValueError('Reviewed choices do not cover this exact resulting plan; regenerate the preview.')
            for plan in plans:
                if plan.status != 'unchanged' or plan.local_changes:
                    print(describe(plan))
                print('{}: {}'.format(plan.label, choices[plan.id]))
            recovery = []
            for plan in canonical_units[1:]:
                if plan.destination.name == 'session-ledger' and canonical_choices[plan.id] != 'keep' and not args.no_session_hooks:
                    helper = effective_files(plan, canonical_choices[plan.id]).get('scripts/ledger.py')
                    eligible = [target for target in selected if choices.get(str(target.path / runtime_skill_name('session-ledger'))) != 'keep']
                    recovery = plan_recovery(eligible, canonical, helper, system)
            show_recovery(recovery)
            data = report_data(plans, choices, source.revision)
            data['migrations'] = migration_review(migrations)
            data['recovery_hooks'] = recovery_review(recovery)
            if args.decisions and not args.dry_run:
                review = json.loads(args.decisions.read_text(encoding='utf-8'))
                if review.get('migrations', []) != data['migrations']:
                    raise ValueError('Migrations changed or were not reviewed; regenerate the preview.')
                reviewed = review.get('recovery_hooks', [])
                if reviewed != data['recovery_hooks']:
                    raise ValueError('Recovery hooks changed or were not reviewed; regenerate the preview.')
            if args.report:
                hook_paths = [path for target in available for path in (
                    hook_config_path(target),
                    target.path.parent / '.wonsky-state')]
                _write_report(args.report, data, plans,
                              [canonical, source.root, *(target.path for target in available), *hook_paths])
            kept = sum(choice == 'keep' for choice in choices.values())
            changed = sum(bool(plan.replacement_changes) and choices[plan.id] != 'keep' for plan in plans)
            print('Plan: {} units change content; {} units kept.'.format(changed, kept))
            if args.dry_run:
                print('Preview only. No installed files or ownership state changed. Unresolved local edits default to Keep.')
                return 2 if kept else 0
            if not args.yes and not confirm(args.terminal):
                print('Cancelled. Installed files and state unchanged.')
                return 0
            validate_recovery(recovery)
            for migration in migrations:
                if migration.status == 'ready':
                    validate_migration(migration)
            # Validate every approval before starting the first unit, then recheck per apply.
            for plan in plans:
                migration = ready_migration(migrations, plan.destination)
                local = replace(plan, destination=migration.source, state_path=migration.state_source) if migration else plan
                validate_plan(local)
            counts = {}
            backups = canonical / '.wonsky-backups'
            for plan in plans:
                migration = ready_migration(migrations, plan.destination)
                if migration and choices[plan.id] != 'keep':
                    print('Migration backup retained: {}'.format(apply_migration(migration)))
                result = apply_plan(plan, choices[plan.id], backups)
                counts[result.result.status] = counts.get(result.result.status, 0) + 1
                if result.backup:
                    print('Backup retained: {}'.format(result.backup))
            apply_recovery(recovery, canonical)
            print('Finished: {}'.format(', '.join('{} {}'.format(number, status) for status, number in sorted(counts.items()))))
            print('Existing AGENTS.md and personal extra files were preserved. No Git commit, reset or push was performed.')
            if recovery:
                print('Recovery hook setup completed for supported selected hosts. Codex still requires host hook trust.')
            return 2 if kept else 0
    except (OSError, ValueError, EOFError) as error:
        print('error: {}'.format(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nCancelled.', file=sys.stderr)
        return 130
