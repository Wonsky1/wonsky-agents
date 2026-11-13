"""Cross-platform install/sync entry point; no third-party Python packages."""

import argparse
import json
import os
from pathlib import Path
import platform
import sys
from typing import List, Optional

from scripts.agent_targets import detect_targets, select_keys
from scripts.hook_files import apply_hook_plan
from scripts.session_hooks import plan_hook
from scripts.recovery_setup import apply_recovery, plan_recovery, show_recovery, validate_recovery
from scripts.skill_distribution import distribution_issue
from scripts.skill_files import check_overlap, install_collection, sync_skill, validate_skill
from scripts.target_picker import pick_targets


def report_result(label, result):
    print('  {}: {}'.format(label, result.status))
    for name in result.conflicts:
        print('    conflict (kept): {}'.format(name))
    for name in result.preserved:
        print('    existing instructions preserved: {}'.format(name))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Install and sync Wonsky Agents using Python 3.9+ standard library only.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--all', action='store_true', help='sync every detected agent')
    mode.add_argument('--targets', help='comma-separated targets: cursor,claude,codex,antigravity,agents; detection not required')
    parser.add_argument('--dry-run', action='store_true', help='preview without creating, replacing or deleting files')
    parser.add_argument('--list', action='store_true', help='list detected and available targets without writing files')
    parser.add_argument('--terminal', action='store_true', help='use terminal selection instead of optional graphical checkboxes')
    parser.add_argument('--sync-only', action='store_true', help='sync the existing canonical collection without installing it')
    parser.add_argument('--update', action='store_true', help='update an existing canonical installation while preserving local edits')
    parser.add_argument('--baseline', type=Path, help='previous trusted collection folder; recognize legacy copies only when file bytes match')
    hooks = parser.add_mutually_exclusive_group()
    hooks.add_argument('--session-hooks', choices=('install', 'remove', 'status'),
                       help='manage only recovery hooks for selected hosts')
    hooks.add_argument('--no-session-hooks', action='store_true', help='skip automatic recovery hook setup')
    args = parser.parse_args(argv)
    try:
        system = platform.system()
        if system not in ('Darwin', 'Linux', 'Windows'):
            raise ValueError('Supported operating systems: macOS, Linux and Windows (detected {}).'.format(system))
        home = Path.home()
        package = Path(__file__).resolve().parents[1]
        canonical = Path(os.environ.get('WONSKY_AGENTS_HOME') or home / '.wonsky-agents').expanduser().absolute()
        source = canonical if args.sync_only else package
        baseline = args.baseline.expanduser().resolve() if args.baseline else None
        if baseline is not None and not (baseline / 'skills').is_dir():
            raise ValueError('--baseline must contain the previous collection skills/ folder')
        skills_root = source / 'skills'
        if not skills_root.is_dir():
            raise ValueError('Canonical skills directory not found: {}'.format(skills_root))
        skills = sorted(p for p in skills_root.iterdir() if (p / 'SKILL.md').is_file() and not p.name.startswith('.'))
        if not skills:
            raise ValueError('No SKILL.md directories found in {}'.format(skills_root))
        print('System: {} | Python: {} | Canonical: {}'.format(system, platform.python_version(), canonical))
        targets = detect_targets(home, system, os.environ)
        for target in targets:
            print('  {}: {} -> {}'.format(target.key, 'detected' if target.detected else 'not detected', target.path))
        if args.list or (args.dry_run and not args.targets and not args.all):
            print('Explicit --targets can also prepare skills for agents that are not detected.')
            return 0
        keys = select_keys(targets, args.targets, args.all)
        if args.targets is None and not args.all:
            keys = pick_targets(targets, args.terminal)
        if not keys:
            print('No targets selected. On a clean machine, use --targets codex (or another target).')
            return 0
        selected = [target for target in targets if target.key in keys]
        if args.session_hooks:
            # This mode is independent of skill copying, including removal after
            # a user has removed or edited a runtime skill.
            plans = [plan_hook(target, canonical, Path(sys.executable), system, args.session_hooks)
                     for target in selected]
            for plan in plans:
                print('{}: {} -> {}. {}'.format(plan.target, plan.status, plan.config, plan.message))
                if args.session_hooks == 'install' and plan.status not in ('unsupported', 'conflict'):
                    print('  Recovery hook: ' + json.dumps(plan.entry, ensure_ascii=False))
            if any(plan.status == 'conflict' for plan in plans):
                print('Hook configuration preserved. Resolve reported ownership conflicts before retrying.')
                return 2
            if not args.dry_run and args.session_hooks != 'status':
                for plan in plans:
                    apply_hook_plan(plan)
            return 0
        # Validate the whole plan before any destination is modified.
        for skill in skills:
            validate_skill(skill)
        for target in selected:
            check_overlap(skills_root, target.path)
            for skill in skills:
                check_overlap(skill, target.path / skill.name)
        recovery = [] if args.no_session_hooks else plan_recovery(
            selected, canonical, source / 'skills/session-ledger/scripts/ledger.py', system)
        show_recovery(recovery)
        validate_recovery(recovery)
        preview_canonical = None
        if not args.sync_only:
            same = check_overlap(package, canonical)
            if not same:
                print('{} collection: {} -> {}'.format('Previewing' if args.dry_run else 'Installing', package, canonical))
                result = install_collection(package, canonical, update=args.update,
                                            baseline=baseline, dry_run=args.dry_run)
                report_result('collection', result)
                if result.status == 'conflict':
                    print('Collection unchanged. Resolve the reported files before updating or syncing this download.')
                    return 2
                if args.dry_run:
                    preview_canonical = canonical
                else:
                    skills_root = canonical / 'skills'
                    skills = [skills_root / skill.name for skill in skills]
        counts = {'added': 0, 'updated': 0, 'unchanged': 0, 'conflict': 0}
        for target in selected:
            print('{} {} skills -> {} ({})'.format('Previewing' if args.dry_run else 'Syncing', len(skills), target.path, target.label))
            for skill in skills:
                destination = target.path / skill.name
                exists = destination.exists() or destination.is_symlink()
                issue = distribution_issue(skill.name, target.key, exists)
                if issue:
                    print('  {}: {}. Attach {} explicitly to use it.'.format(
                        destination, issue, skills_root / skill.name / 'SKILL.md'))
                    if exists:
                        counts['conflict'] += 1
                    continue
                previous = baseline / 'skills' / skill.name if baseline else None
                result = sync_skill(skill, target.path / skill.name, baseline=previous, dry_run=args.dry_run,
                                    retained_source=preview_canonical / 'skills' / skill.name if preview_canonical else None)
                counts[result.status] += 1
                if result.status == 'conflict' or result.preserved:
                    report_result(str(target.path / skill.name), result)
        print('{}: added {}, updated {}, unchanged {}, conflicts {}.{}'.format(
              'Preview' if args.dry_run else 'Finished', counts['added'], counts['updated'],
              counts['unchanged'], counts['conflict'], ' No files changed.' if args.dry_run else ''))
        if counts['conflict']:
            print('Conflicting skill folders were left untouched. No user files were overwritten or deleted.')
            return 2
        if not args.dry_run:
            apply_recovery(recovery, canonical)
        return 0
    except (ValueError, OSError, EOFError) as error:
        print('error: {}'.format(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nCancelled.', file=sys.stderr)
        return 130
