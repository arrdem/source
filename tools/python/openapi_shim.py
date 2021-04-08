#!/usr/bin/env python3

"""Shim for executing the openapi spec validator."""

import re
import sys

from openapi_spec_validator.__main__ import main

if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())
