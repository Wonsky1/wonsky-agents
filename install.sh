#!/bin/sh
# Optional macOS/Linux launcher. install.py is also usable directly.
set -eu
root=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
      exec "$candidate" "$root/install.py" "$@"
    fi
  fi
done
echo "Python 3.9+ is required. Install Python from https://www.python.org/downloads/ and run this launcher again. No pip packages, Git or rsync are needed." >&2
exit 1
