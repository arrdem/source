#!/usr/bin/env python3

from ichor import FuncBuilder, Opcode

import pytest

@pytest.fixture
def builder() -> FuncBuilder:
    return FuncBuilder()


def test_forwards_label(builder: FuncBuilder):
    l = builder.make_label()
    builder.write(Opcode.GOTO(l))
    builder.write(Opcode.DROP(0)) # no-op
    builder.set_label(l)
    builder.write(Opcode.DROP(0)) # no-op
    instrs = builder.build()
    assert instrs == [
        Opcode.GOTO(2),
        Opcode.DROP(0),
        Opcode.DROP(0),
    ]


def test_backwards_label(builder: FuncBuilder):
    l = builder.make_label()
    builder.set_label(l)
    builder.write(Opcode.DROP(0)) # no-op
    builder.write(Opcode.GOTO(l))
    instrs = builder.build()
    assert instrs == [
        Opcode.DROP(0),
        Opcode.GOTO(0),
    ]


def test_self_label(builder: FuncBuilder):
    l = builder.make_label()
    builder.write(Opcode.DROP(0)) # no-op
    builder.set_label(l)
    builder.write(Opcode.GOTO(l))
    instrs = builder.build()
    assert instrs == [
        Opcode.DROP(0),
        Opcode.GOTO(1),
    ]
