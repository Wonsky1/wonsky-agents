"""An incoming collection staged for a read-only update preview."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UpdateSource:
    root: Path
    revision: str
    provenance: str
