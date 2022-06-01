#!/usr/bin/env python3

import pytest
from shoggoth.vm import *


@pytest.fixture
def vm():
    return Interpreter(BOOTSTRAP)
