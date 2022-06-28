"""
Tests coverign the VM interpreter
"""

from .fixtures import *  # noqa

from ichor import *
import pytest


def test_return(vm):
    assert vm.run([Opcode.RETURN(0)], stack=[TRUE, FALSE]) == []
    assert vm.run([Opcode.RETURN(1)], stack=[TRUE, FALSE]) == [TRUE]
    assert vm.run([Opcode.RETURN(2)], stack=[TRUE, FALSE]) == [TRUE, FALSE]


def test_dup(vm):
    assert vm.run([Opcode.DUP(1), Opcode.RETURN(3)], stack=[FALSE, TRUE]) == [FALSE, TRUE, TRUE]
    assert vm.run([Opcode.DUP(2), Opcode.RETURN(4)], stack=[FALSE, TRUE]) == [FALSE, TRUE, FALSE, TRUE]


def test_rot(vm):
    assert vm.run([
        Opcode.ROT(2),
        Opcode.RETURN(2)
    ], stack=[FALSE, TRUE]) == [TRUE, FALSE]

    assert vm.run([
        Opcode.ROT(3),
        Opcode.RETURN(3)
    ], stack=[FALSE, TRUE, FALSE]) == [FALSE, FALSE, TRUE]


def test_drop(vm):
    assert vm.run([
        Opcode.DROP(1),
        Opcode.RETURN(1)
    ], stack=[TRUE, FALSE]) == [TRUE]


def test_dup_too_many(vm):
    with pytest.raises(InterpreterError):
        vm.run([Opcode.DUP(1)])

    with pytest.raises(InterpreterError):
        vm.run([Opcode.FALSE(), Opcode.DUP(2)])


def test_rot_too_many(vm):
    with pytest.raises(InterpreterError):
        vm.run([Opcode.ROT(1)])

    with pytest.raises(InterpreterError):
        vm.run([Opcode.TRUE(), Opcode.ROT(2)])


def test_drop_too_many(vm):
    with pytest.raises(InterpreterError):
        vm.run([Opcode.DROP(1)])

    with pytest.raises(InterpreterError):
        vm.run([Opcode.TRUE(), Opcode.DROP(2)])
