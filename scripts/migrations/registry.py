"""Ordered migration registration and lookup of planned runtime moves."""

from pathlib import Path
from typing import Optional

from scripts.migrations.models.plan import MigrationPlan
from scripts.migrations.v0001_skill_namespace import namespace_plans

# IDs in concrete migrations are permanent; append future planners in order.
MIGRATIONS = (namespace_plans,)


def plan_migrations(skills: list, targets: list, baseline: Optional[Path] = None) -> list:
    return [plan for planner in MIGRATIONS for plan in planner(skills, targets, baseline)]


def ready_migration(plans: list, destination: Path) -> Optional[MigrationPlan]:
    return next((plan for plan in plans if plan.destination == destination and plan.status == 'ready'), None)
