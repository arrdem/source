#!/usr/bin/env python3

"""Tests covering the Ichor ISA and state model."""

from ichor.impl import Stackframe
from ichor.state import *

import pytest


@pytest.fixture
def frame():
    return Stackframe(None, 0)


def test_stackframe_lifo(frame):
    frame.push(0)
    frame.push(1)
    frame.push(2)
    assert frame.pop() == 2
    assert frame.pop() == 1
    assert frame.pop() == 0


def test_stackframe_dup(frame):
    frame.push(0)
    frame.push(1)
    frame.push(2)
    frame.push(3)
    frame.push(4)

    frame.dup(1)
    assert len(frame) == 6
    assert frame.pop() == 4
    assert frame.pop() == 4

    frame.dup(2)
    assert frame.pop() == 3
    assert frame.pop() == 2
    assert frame.pop() == 3
    assert frame.pop() == 2


def test_stackframe_drop(frame):
    frame.push(0)
    frame.push(1)
    frame.push(2)
    frame.push(3)
    frame.push(4)

    assert len(frame) == 5

    frame.drop(2)
    assert len(frame) == 3
    assert frame.pop() == 2


def test_stackframe_slot(frame):
    frame.push(0)
    frame.push(1)
    frame.push(2)
    frame.push(3)
    frame.push(4)

    frame.slot(0)
    assert frame.pop() == 0

    frame.slot(1)
    assert frame.pop() == 1

    frame.slot(2)
    assert frame.pop() == 2
