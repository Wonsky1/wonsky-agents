#!/usr/bin/env python3
"""Run explicitly selected tests one at a time to locate a new file or directory.

Usage: python3 find_polluter.py .git 'src/**/*.test.ts' -- npm test -- '{test}'
Exit 0: every selected test succeeded without creating the path; 1: pollution
appeared; 2: discovery, precondition or runner failed (the result is incomplete).
The helper never deletes pollution or invokes a shell.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pollution", type=Path, help="Path that must be absent before running")
    parser.add_argument("test_pattern", help="Glob relative to the working directory")
    parser.add_argument("runner", nargs=argparse.REMAINDER,
                        help="After --, runner arguments including one literal {test}")
    args = parser.parse_args(argv)
    runner = args.runner
    if runner and runner[0] == "--":
        runner = runner[1:]
    if runner.count("{test}") != 1:
        parser.error("provide an explicit runner with one {test}, e.g. -- npm test -- '{test}'")
    pattern = Path(args.test_pattern)
    if pattern.is_absolute() or ".." in pattern.parts:
        parser.error("test_pattern must stay inside the working directory")
    if os.path.lexists(args.pollution):
        print(f"incomplete: pollution already exists: {args.pollution}; nothing was run", file=sys.stderr)
        return 2
    root = Path.cwd().resolve()
    try:
        tests = sorted(path for path in root.glob(args.test_pattern) if path.is_file())
        for path in tests:
            path.resolve().relative_to(root)
    except (OSError, ValueError, NotImplementedError) as error:
        print(f"incomplete: cannot discover tests: {error}", file=sys.stderr)
        return 2
    if not tests:
        print(f"incomplete: no test files matched {args.test_pattern!r}; nothing was run", file=sys.stderr)
        return 2
    print(f"Selected {len(tests)} test files", flush=True)
    for index, path in enumerate(tests, 1):
        relative = str(path.relative_to(root))
        if os.path.lexists(args.pollution):
            print("incomplete: pollution appeared between test runs; attribution is unknown", file=sys.stderr)
            return 2
        print(f"[{index}/{len(tests)}] {relative}", flush=True)
        command = [relative if arg == "{test}" else arg for arg in runner]
        try:
            completed = subprocess.run(command, check=False)
        except OSError as error:
            print(f"incomplete: could not start runner: {error}", file=sys.stderr)
            return 2
        if os.path.lexists(args.pollution):
            print(f"Pollution appeared while running {relative}: {args.pollution}", flush=True)
            if completed.returncode:
                print(f"Runner also failed with exit {completed.returncode}; inspect its output.", file=sys.stderr)
            return 1
        if completed.returncode:
            print(f"incomplete: runner failed for {relative} with exit {completed.returncode}; no clean claim", file=sys.stderr)
            return 2
    print(f"No pollution observed in {len(tests)} successful test-file runs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
