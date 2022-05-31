#!/usr/bin/env python3

import pytest
from shogoth.vm import *


@pytest.fixture
def vm():
    return Interpreter(BOOTSTRAP)
