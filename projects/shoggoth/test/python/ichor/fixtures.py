#!/usr/bin/env python3

from ichor import Interpreter, BOOTSTRAP
import pytest


@pytest.fixture
def vm():
    return Interpreter(BOOTSTRAP)
