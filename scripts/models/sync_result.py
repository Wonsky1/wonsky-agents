"""Installation outcomes shared by file operations and the command interface."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SyncResult:
    status: str
    conflicts: Tuple[str, ...] = ()
    preserved: Tuple[str, ...] = ()
