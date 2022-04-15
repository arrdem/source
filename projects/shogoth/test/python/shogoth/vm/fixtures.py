#!/usr/bin/env python3

import pytest
from shogoth.vm import *

import pytest

@pytest.fixture
def vm():
    return Interpreter(BOOTSTRAP)
