"""One guarded, reviewable filesystem migration for a runtime skill."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class MigrationPlan:
    migration_id: str
    source: Path
    destination: Path
    state_source: Path
    state_destination: Path
    journal: Path
    status: str
    reason: str
    files: Dict[str, tuple]
    state_before: Optional[bytes]
    journal_before: Optional[bytes]
