"""A shim for executing pytest."""

import os
import sys

import pytest

if __name__ == "__main__":
    print(sys.version_info, file=sys.stderr)
    print(sys.argv, file=sys.stderr)

    cmdline = ["--ignore=external"] + sys.argv[1:]
    print(cmdline, file=sys.stderr)

    for e in sys.path:
        print(f" - {os.path.realpath(e)}", file=sys.stderr)

    sys.exit(pytest.main(cmdline))
