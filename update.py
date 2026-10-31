#!/usr/bin/env python3
"""Review and update Wonsky Agents with Python's standard library."""

import sys

if sys.version_info < (3, 9):
    sys.exit('Wonsky Agents requires Python 3.9 or newer. No pip packages are needed.')

sys.dont_write_bytecode = True

from scripts.update_cli import main

if __name__ == '__main__':
    sys.exit(main())
