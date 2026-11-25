import json
from pathlib import Path


def load(path: Path) -> list[str]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save(path: Path, items: list[str]) -> None:
    path.write_text(json.dumps(items) + "\n")
