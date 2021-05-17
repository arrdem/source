"""A shim for executing pytest."""

import os
import sys

import pytest

if __name__ == "__main__":
    cmdline = ["--ignore=external"] + sys.argv[1:]
    sys.exit(pytest.main(cmdline))
