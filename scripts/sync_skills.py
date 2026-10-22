"""Cross-platform install/sync entry point; no third-party Python packages."""

import argparse
import os
from pathlib import Path
import platform
import sys
from typing import List, Optional

from scripts.agent_targets import detect_targets, select_keys
from scripts.skill_files import check_overlap, install_collection, sync_skill, validate_skill
from scripts.target_picker import pick_targets


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Install and sync Wonsky Agents using Python 3.9+ standard library only.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--all', action='store_true', help='sync every detected agent')
    mode.add_argument('--targets', help='comma-separated targets: cursor,claude,codex,antigravity,agents; detection not required')
    parser.add_argument('--dry-run', action='store_true', help='preview without creating, replacing or deleting files')
    parser.add_argument('--list', action='store_true', help='list detected and available targets without writing files')
    parser.add_argument('--terminal', action='store_true', help='use terminal selection instead of optional graphical checkboxes')
    parser.add_argument('--sync-only', action='store_true', help='sync the existing canonical collection without installing it')
    parser.add_argument('--update', action='store_true', help='replace collection files in an existing canonical installation from this download')
    args = parser.parse_args(argv)
    try:
        system = platform.system()
        if system not in ('Darwin', 'Linux', 'Windows'):
            raise ValueError('Supported operating systems: macOS, Linux and Windows (detected {}).'.format(system))
        home = Path.home()
        package = Path(__file__).resolve().parents[1]
        canonical = Path(os.environ.get('WONSKY_AGENTS_HOME') or home / '.wonsky-agents').expanduser().resolve()
        source = canonical if args.sync_only else package
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
        # Validate the whole plan before any destination is modified.
        for skill in skills:
            validate_skill(skill)
        for target in selected:
            check_overlap(skills_root, target.path)
            for skill in skills:
                check_overlap(skill, target.path / skill.name)
        if not args.sync_only:
            same = check_overlap(package, canonical)
            if not same and canonical.exists() and any(canonical.iterdir()) and not args.update:
                raise ValueError('Canonical directory already exists: {}. Run its installer or pass --update.'.format(canonical))
            if not same:
                print('{} collection: {} -> {}'.format('Would install' if args.dry_run else 'Installing', package, canonical))
                if not args.dry_run:
                    install_collection(package, canonical, update=args.update)
                    skills_root = canonical / 'skills'
                    skills = [skills_root / skill.name for skill in skills]
        for target in selected:
            print('{} {} skills -> {} ({})'.format('Would sync' if args.dry_run else 'Syncing', len(skills), target.path, target.label))
            if not args.dry_run:
                for skill in skills:
                    preserve = ('reviewer-preferences.md',) if skill.name == 'github-pr-review' else ()
                    sync_skill(skill, target.path / skill.name, preserve=preserve)
        print('{}: {} skills x {} destinations.{}'.format('Dry run complete' if args.dry_run else 'Synced',
              len(skills), len(selected), ' No files changed.' if args.dry_run else ''))
        return 0
    except (ValueError, OSError, EOFError) as error:
        print('error: {}'.format(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nCancelled.', file=sys.stderr)
        return 130
