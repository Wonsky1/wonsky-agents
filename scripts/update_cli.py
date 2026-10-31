"""Review canonical and runtime updates before touching installed files."""

import argparse
import json
import os
from pathlib import Path
import platform
import sys
from typing import Optional

from scripts.agent_targets import detect_targets, select_keys
from scripts.managed_files import symlink_in_chain
from scripts.skill_files import check_overlap
from scripts.target_picker import pick_targets
from scripts.update_apply import apply_plan
from scripts.update_collection import canonical_plans, runtime_plans
from scripts.update_plan import validate_plan
from scripts.update_review import (choose, confirm, default_choice, describe, load_decisions,
                                   report_data, reviewed_choices)
from scripts.update_source import open_update_source


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
    targets.add_argument('--targets', help='comma-separated cursor,claude,codex,antigravity,agents')
    targets.add_argument('--all', action='store_true', help='select all detected destinations')
    parser.add_argument('--terminal', action='store_true', help='use terminal review instead of optional Tk windows')
    parser.add_argument('--dry-run', action='store_true', help='preview; never change installed files or ownership state')
    parser.add_argument('--report', type=Path, help='save complete review evidence and choices as local JSON outside the installation')
    parser.add_argument('--decisions', type=Path, help='use choices/tokens from an inspected report; stale or incomplete approvals are rejected')
    parser.add_argument('--yes', action='store_true', help='apply safe updates or exact reviewed decisions without a final prompt; never blindly replace local edits')
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
            runtime_units = runtime_plans(canonical_units, canonical_choices, selected, baseline)
            runtime_choices = _choices(runtime_units, args, saved)
            plans = canonical_units + runtime_units
            choices = dict(canonical_choices, **runtime_choices)
            if saved is not None and not args.dry_run and set(saved) != {plan.id for plan in plans}:
                raise ValueError('Reviewed choices do not cover this exact resulting plan; regenerate the preview.')
            for plan in plans:
                if plan.status != 'unchanged' or plan.local_changes:
                    print(describe(plan))
                print('{}: {}'.format(plan.label, choices[plan.id]))
            data = report_data(plans, choices, source.revision)
            if args.report:
                _write_report(args.report, data, plans, [canonical, source.root, *(target.path for target in available)])
            kept = sum(choice == 'keep' for choice in choices.values())
            changed = sum(bool(plan.replacement_changes) and choices[plan.id] != 'keep' for plan in plans)
            print('Plan: {} units change content; {} units kept.'.format(changed, kept))
            if args.dry_run:
                print('Preview only. No installed files or ownership state changed. Unresolved local edits default to Keep.')
                return 2 if kept else 0
            if not args.yes and not confirm(args.terminal):
                print('Cancelled. Installed files and state unchanged.')
                return 0
            # Validate every approval before starting the first unit, then recheck per apply.
            for plan in plans:
                validate_plan(plan)
            counts = {}
            backups = canonical / '.wonsky-backups'
            for plan in plans:
                result = apply_plan(plan, choices[plan.id], backups)
                counts[result.result.status] = counts.get(result.result.status, 0) + 1
                if result.backup:
                    print('Backup retained: {}'.format(result.backup))
            print('Finished: {}'.format(', '.join('{} {}'.format(number, status) for status, number in sorted(counts.items()))))
            print('Existing AGENTS.md and personal extra files were preserved. No Git commit, reset or push was performed.')
            return 2 if kept else 0
    except (OSError, ValueError, EOFError) as error:
        print('error: {}'.format(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nCancelled.', file=sys.stderr)
        return 130
