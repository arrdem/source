#!/usr/bin/env python3

import pytest
from ichor import *


@pytest.fixture
def vm():
    return Interpreter(BOOTSTRAP)
