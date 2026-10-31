"""Reviewable installation plans and file comparisons."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple

from scripts.models.sync_result import SyncResult


@dataclass(frozen=True)
class FileChange:
    path: str
    kind: str
    comparison: str
    before_hash: Optional[str]
    after_hash: Optional[str]
    before_size: Optional[int]
    after_size: Optional[int]
    diff: str
    baseline_known: bool


@dataclass(frozen=True)
class UpdatePlan:
    id: str
    label: str
    destination: Path
    state_path: Path
    files: Mapping[str, Path]
    contents: Mapping[str, bytes]
    new_hashes: Mapping[str, str]
    previous_hashes: Mapping[str, str]
    local_changes: Tuple[FileChange, ...]
    upstream_changes: Tuple[FileChange, ...]
    replacement_changes: Tuple[FileChange, ...]
    status: str
    conflicts: Tuple[str, ...]
    blocked: Tuple[str, ...]
    preserved: Tuple[str, ...]
    unknown_original: bool
    local_fingerprint: Dict[str, tuple]
    state_fingerprint: Optional[bytes]
    scope: Optional[Tuple[str, ...]]


@dataclass(frozen=True)
class ApplyResult:
    result: SyncResult
    backup: Optional[Path] = None
