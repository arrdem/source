"""
Tests coverign the VM interpreter
"""

import pytest
from shogoth.vm import *

from .fixtures import * # noqa


def test_true(vm):
    assert vm.run([Opcode.TRUE(), Opcode.RETURN(1)]) == [True]


def test_false(vm):
    assert vm.run([Opcode.FALSE(), Opcode.RETURN(1)]) == [False]


def test_return(vm):
    assert vm.run([Opcode.FALSE(), Opcode.RETURN(0)]) == []
    assert vm.run([Opcode.TRUE(), Opcode.FALSE(), Opcode.RETURN(1)]) == [False]
    assert vm.run([Opcode.TRUE(), Opcode.FALSE(), Opcode.RETURN(2)]) == [False, True]


def test_dup(vm):
    assert vm.run([
        Opcode.TRUE(),
        Opcode.FALSE(),
        Opcode.DUP(1),
        Opcode.RETURN(3)
    ]) == [False, False, True]

    assert vm.run([
        Opcode.TRUE(),
        Opcode.FALSE(),
        Opcode.DUP(2),
        Opcode.RETURN(4)
    ]) == [False, True, False, True]


def test_rot(vm):
    assert vm.run([
        Opcode.TRUE(),
        Opcode.FALSE(),
        Opcode.ROT(2),
        Opcode.RETURN(2)
    ]) == [True, False]

    assert vm.run([
        Opcode.FALSE(),
        Opcode.TRUE(),
        Opcode.FALSE(),
        Opcode.ROT(3),
        Opcode.RETURN(3)
    ]) == [False, False, True]


def test_drop(vm):
    assert vm.run([
        Opcode.TRUE(),
        Opcode.FALSE(),
        Opcode.DROP(1),
        Opcode.RETURN(1)
    ]) == [True]


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
