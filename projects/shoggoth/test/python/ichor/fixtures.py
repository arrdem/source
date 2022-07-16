#!/usr/bin/env python3

from ichor import BOOTSTRAP, Interpreter
import pytest


@pytest.fixture
def vm():
    return Interpreter(BOOTSTRAP)
