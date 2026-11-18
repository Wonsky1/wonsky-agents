"""Coordinate automatic recovery setup with installer and updater reviews."""

import hashlib
import json
from pathlib import Path
import sys

from scripts.hooks.files import apply_hook_plan, read_bytes
from scripts.hooks.setup import plan_hook


def plan_recovery(targets: list, canonical: Path, helper: Path, system: str) -> list:
    if helper is None or not helper.is_file():
        return []
    return [plan_hook(target, canonical, Path(sys.executable), system, 'install', helper)
            for target in targets]


def show_recovery(plans: list) -> None:
    for plan in plans:
        print('{} recovery: {} -> {}. {}'.format(plan.target, plan.status, plan.config, plan.message))
        if plan.status not in ('unsupported', 'conflict'):
            print('  Recovery hook: ' + json.dumps(plan.entry, ensure_ascii=False))


def recovery_review(plans: list) -> list:
    """Expose only our entries; bind approval to hashes of private settings."""
    result = []
    for plan in plans:
        fingerprint = [hashlib.sha256(data).hexdigest() if data is not None else None
                       for data in (plan.before, plan.state_before)]
        data = {'target': plan.target, 'config': str(plan.config), 'status': plan.status,
                'entry': plan.entry, 'fingerprint': fingerprint}
        token = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        result.append({'target': plan.target, 'config': str(plan.config),
                       'status': plan.status, 'entry': plan.entry, 'token': token})
    return result


def validate_recovery(plans: list) -> None:
    for plan in plans:
        if plan.status == 'conflict':
            raise ValueError('{}: {} Use --no-session-hooks to update skills only.'.format(plan.target, plan.message))
        if plan.status == 'unsupported':
            continue
        if read_bytes(plan.config) != plan.before or read_bytes(plan.state) != plan.state_before:
            raise ValueError('Hook configuration changed after preview; review again: {}'.format(plan.config))


def apply_recovery(plans: list, canonical: Path) -> None:
    validate_recovery(plans)
    if any(plan.status != 'unsupported' for plan in plans):
        if not (canonical / 'skills/session-ledger/scripts/ledger.py').is_file():
            raise ValueError('Recovery helper was not installed; hook settings preserved.')
    for plan in plans:
        apply_hook_plan(plan)
