import argparse
from pathlib import Path

from favorites.store import load, save


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("command", choices=["add", "list"])
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()
    items = load(args.store)
    if args.command == "add":
        if not args.value:
            parser.error("add requires a nonempty ID")
        if args.value not in items:
            items.append(args.value)
        save(args.store, items)
    else:
        print("\n".join(items))
