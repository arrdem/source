#!/usr/bin/env python3

from .fixtures import *  # noqa

from ichor import *
from ichor.isa import Opcode
import pytest


@pytest.mark.parametrize("stack,ret", [
    [[True], [False]],
    [[True], [False]],
])
def test_not(vm, stack, ret):
    assert vm.run([Opcode.CALLS(NOT1), Opcode.RETURN(1)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[False, False], [False]],
    [[True, False], [True]],
    [[False, True], [True]],
    [[True, True], [True]],
])
def test_or(vm, stack, ret):
    assert vm.run([Opcode.CALLS(OR2), Opcode.RETURN(1)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[False, False], [False]],
    [[True, False], [False]],
    [[False, True], [False]],
    [[True, True], [True]],
])
def test_and(vm, stack, ret):
    assert vm.run([Opcode.CALLS(AND2), Opcode.RETURN(1)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[False, False], [False]],
    [[True, False], [True]],
    [[False, True], [True]],
    [[True, True], [False]],
])
def test_xor2(vm, stack, ret):
    assert vm.run([Opcode.CALLS(XOR2), Opcode.RETURN(1)], stack = stack) == ret

@pytest.mark.parametrize("stack,ret", [
    [[False, False, False], [False]],
    [[True,  False, False], [True]],
    [[False, True,  False], [True]],
    [[True,  True,  False], [True]],
    [[True,  True,  True],  [False]],
    [[False, True,  True],  [True]],
    [[False, False, True],  [True]],
])
def test_xor3(vm, stack, ret):
    assert vm.run([Opcode.CALLS(XOR3), Opcode.RETURN(1)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[], [FunctionRef.parse(NOT1)]]
])
def test_funref(vm, stack, ret):
    assert vm.run([Opcode.FUNREF(NOT1), Opcode.RETURN(1)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[], [True]]
])
def test_callf(vm, stack, ret):
    assert vm.run([Opcode.FALSE(), Opcode.FUNREF(NOT1), Opcode.CALLF(1), Opcode.RETURN(1)], stack = stack) == ret
