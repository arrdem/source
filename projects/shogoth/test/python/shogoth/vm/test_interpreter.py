"""
Tests coverign the VM interpreter
"""

from shogoth.vm import *

vm = Interpreter(BOOTSTRAP)


def test_true():
    assert vm.run([Opcode.TRUE(), Opcode.RETURN(1)]) == [True]


def test_false():
    assert vm.run([Opcode.FALSE(), Opcode.RETURN(1)]) == [False]


def test_return():
    assert vm.run([Opcode.FALSE(), Opcode.RETURN(0)]) == []
    assert vm.run([Opcode.TRUE(), Opcode.FALSE(), Opcode.RETURN(1)]) == [False]
    assert vm.run([Opcode.TRUE(), Opcode.FALSE(), Opcode.RETURN(2)]) == [False, True]


def test_dup():
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


def test_rot():
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


def test_drop():
    assert vm.run([
        Opcode.TRUE(),
        Opcode.FALSE(),
        Opcode.DROP(1),
        Opcode.RETURN(1)
    ]) == [True]


def test_not():
    assert vm.run([
        Opcode.TRUE(),
        Opcode.CALL(NOT),
        Opcode.RETURN(1)
    ]) == [False]

    assert vm.run([
        Opcode.FALSE(),
        Opcode.CALL(NOT),
        Opcode.RETURN(1)
    ]) == [True]


def test_or():
    assert vm.run([
        Opcode.FALSE(),
        Opcode.FALSE(),
        Opcode.CALL(OR),
        Opcode.RETURN(1)
    ]) == [False]

    assert vm.run([
        Opcode.TRUE(),
        Opcode.FALSE(),
        Opcode.CALL(OR),
        Opcode.RETURN(1)
    ]) == [True]

    assert vm.run([
        Opcode.FALSE(),
        Opcode.TRUE(),
        Opcode.CALL(OR),
        Opcode.RETURN(1)
    ]) == [True]

    assert vm.run([
        Opcode.TRUE(),
        Opcode.TRUE(),
        Opcode.CALL(OR),
        Opcode.RETURN(1)
    ]) == [True]


def test_and():
    assert vm.run([
        Opcode.FALSE(),
        Opcode.FALSE(),
        Opcode.CALL(AND),
        Opcode.RETURN(1)
    ]) == [False]

    assert vm.run([
        Opcode.TRUE(),
        Opcode.FALSE(),
        Opcode.CALL(AND),
        Opcode.RETURN(1)
    ]) == [False]

    assert vm.run([
        Opcode.FALSE(),
        Opcode.TRUE(),
        Opcode.CALL(AND),
        Opcode.RETURN(1)
    ]) == [False]

    assert vm.run([
        Opcode.TRUE(),
        Opcode.TRUE(),
        Opcode.CALL(AND),
        Opcode.RETURN(1)
    ]) == [True]


def test_xor():
    assert vm.run([
        Opcode.FALSE(),
        Opcode.FALSE(),
        Opcode.CALL(XOR),
        Opcode.RETURN(1)
    ]) == [False]

    assert vm.run([
        Opcode.TRUE(),
        Opcode.FALSE(),
        Opcode.CALL(XOR),
        Opcode.RETURN(1)
    ]) == [True]

    assert vm.run([
        Opcode.FALSE(),
        Opcode.TRUE(),
        Opcode.CALL(XOR),
        Opcode.RETURN(1)
    ]) == [True]

    assert vm.run([
        Opcode.TRUE(),
        Opcode.TRUE(),
        Opcode.CALL(XOR),
        Opcode.RETURN(1)
    ]) == [False]
