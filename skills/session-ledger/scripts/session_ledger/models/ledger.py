"""Validated identity and stored ledger records."""
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


class LedgerError(Exception):
    """An actionable error reported without a traceback."""


@dataclass(frozen=True)
class Binding:
    host: str
    session: str

    @property
    def key(self) -> str:
        return self.host + ':' + self.session


@dataclass(frozen=True)
class Root:
    path: Path
    is_git: bool


@dataclass(frozen=True)
class Ledger:
    path: Path
    identifier: str
    bindings: Tuple[Binding, ...]
    created: str
