"""An agent installation destination and its detection status."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Target:
    key: str
    label: str
    path: Path
    detected: bool
