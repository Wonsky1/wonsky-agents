#!/bin/sh
# Compatibility launcher. The Python helper also runs directly on Windows.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for interpreter in python3 python; do
  if command -v "$interpreter" >/dev/null 2>&1 &&
     "$interpreter" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
    exec "$interpreter" "$script_dir/find_polluter.py" "$@"
  fi
done
echo "Python 3.9 or later is required. Run find_polluter.py with that interpreter." >&2
exit 2
