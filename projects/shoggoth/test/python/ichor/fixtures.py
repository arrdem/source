#!/usr/bin/env python3

from ichor import *
import pytest


@pytest.fixture
def vm():
    return Interpreter(BOOTSTRAP)
