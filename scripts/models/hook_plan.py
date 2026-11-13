"""A previewable hook configuration edit and its concurrency guards."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class HookPlan:
    target: str
    config: Path
    state: Path
    status: str
    message: str
    entry: dict
    before: Optional[bytes] = None
    after: Optional[bytes] = None
    state_before: Optional[bytes] = None
    state_after: Optional[bytes] = None
