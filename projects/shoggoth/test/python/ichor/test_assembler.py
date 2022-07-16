#!/usr/bin/env python3

from ichor import FuncBuilder, isa

import pytest

@pytest.fixture
def builder() -> FuncBuilder:
    return FuncBuilder()


def test_forwards_label(builder: FuncBuilder):
    l = builder.make_label()
    builder.write(isa.GOTO(l))
    builder.write(isa.DROP(0)) # no-op
    builder.write(l)
    builder.write(isa.DROP(0)) # no-op
    instrs = builder.build()
    assert instrs == [
        isa.GOTO(2),
        isa.DROP(0),
        isa.DROP(0),
    ]


def test_backwards_label(builder: FuncBuilder):
    l = builder.make_label()
    builder.write(l)
    builder.write(isa.DROP(0)) # no-op
    builder.write(isa.GOTO(l))
    instrs = builder.build()
    assert instrs == [
        isa.DROP(0),
        isa.GOTO(0),
    ]


def test_self_label(builder: FuncBuilder):
    l = builder.make_label()
    builder.write(isa.DROP(0)) # no-op
    builder.write(l)
    builder.write(isa.GOTO(l))
    instrs = builder.build()
    assert instrs == [
        isa.DROP(0),
        isa.GOTO(1),
    ]
