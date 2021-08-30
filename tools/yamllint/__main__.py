#!/usr/bin/python

# WARNING: Yamllint is GPL3'd code.

"""A shim for executing yamllint."""

import re
import sys

from yamllint.cli import run


if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw?|\.exe)?$", "", sys.argv[0])
    sys.exit(run())
