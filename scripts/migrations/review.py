"""Render migration previews and fingerprint the exact reviewed evidence."""

import hashlib
import json


def migration_review(plans: list) -> list:
    result = []
    for plan in plans:
        fingerprint = {'files': plan.files, 'state': hashlib.sha256(plan.state_before).hexdigest()
                       if plan.state_before is not None else None,
                       'journal': hashlib.sha256(plan.journal_before).hexdigest()
                       if plan.journal_before is not None else None}
        data = {'id': plan.migration_id, 'from': str(plan.source), 'to': str(plan.destination),
                'status': plan.status, 'reason': plan.reason, 'fingerprint': fingerprint}
        token = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        result.append({key: value for key, value in dict(data, token=token).items() if key != 'fingerprint'})
    return result


def show_migrations(plans: list) -> None:
    for plan in plans:
        print('Migration {}: {} -> {} [{}]. {}'.format(
            plan.migration_id, plan.source, plan.destination, plan.status, plan.reason))
