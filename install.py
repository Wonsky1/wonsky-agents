#!/usr/bin/env python3
"""Run with Python; Git, Bash, rsync and pip packages are not required."""

import sys

if sys.version_info < (3, 9):
    sys.exit('Wonsky Agents requires Python 3.9 or newer. No pip packages are needed.')

sys.dont_write_bytecode = True

from scripts.sync_skills import main

if __name__ == '__main__':
    sys.exit(main())
