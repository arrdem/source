"""A shim for executing pytest."""

import sys

import pytest


if __name__ == "__main__":
    cmdline = ["--ignore=external"] + sys.argv[1:]
    print(cmdline, file=sys.stderr)
    sys.exit(pytest.main(cmdline))
