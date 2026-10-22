#!/bin/sh
# Compatibility entry point; copying is performed by Python, not rsync.
set -eu
script_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
exec "$script_dir/../install.sh" --sync-only "$@"
