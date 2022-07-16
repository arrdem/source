"""
Tests coverign the VM interpreter
"""

from .fixtures import *  # noqa

from ichor import (
    FALSE,
    InterpreterError,
    isa,
    TRUE,
)
import pytest


def test_return(vm):
    assert vm.run([isa.RETURN(0)], stack=[TRUE, FALSE]) == []
    assert vm.run([isa.RETURN(1)], stack=[TRUE, FALSE]) == [TRUE]
    assert vm.run([isa.RETURN(2)], stack=[TRUE, FALSE]) == [TRUE, FALSE]


def test_dup(vm):
    assert vm.run([isa.DUP(1), isa.RETURN(3)], stack=[FALSE, TRUE]) == [FALSE, TRUE, TRUE]
    assert vm.run([isa.DUP(2), isa.RETURN(4)], stack=[FALSE, TRUE]) == [FALSE, TRUE, FALSE, TRUE]


def test_rot(vm):
    assert vm.run([
        isa.ROT(2),
        isa.RETURN(2)
    ], stack=[FALSE, TRUE]) == [TRUE, FALSE]

    assert vm.run([
        isa.ROT(2),
        isa.RETURN(5)
    ], stack=[TRUE, TRUE, TRUE, FALSE, TRUE]) == [TRUE, TRUE, TRUE, TRUE, FALSE]

    assert vm.run([
        isa.ROT(3),
        isa.RETURN(3)
    ], stack=[FALSE, TRUE, FALSE]) == [FALSE, FALSE, TRUE]


def test_drop(vm):
    assert vm.run([
        isa.DROP(1),
        isa.RETURN(1)
    ], stack=[TRUE, FALSE]) == [TRUE]


def test_dup_too_many(vm):
    with pytest.raises(InterpreterError):
        vm.run([isa.DUP(1)])

    with pytest.raises(InterpreterError):
        vm.run([isa.DUP(2)], stack=[FALSE])


def test_rot_too_many(vm):
    with pytest.raises(InterpreterError):
        vm.run([isa.ROT(1)])

    with pytest.raises(InterpreterError):
        vm.run([isa.ROT(2)], stack=[FALSE])


def test_drop_too_many(vm):
    with pytest.raises(InterpreterError):
        vm.run([isa.DROP(1)])

    with pytest.raises(InterpreterError):
        vm.run([isa.DROP(2)], stack=[FALSE])
