#!/usr/bin/env python3

from .fixtures import *  # noqa

import pytest
from shogoth.vm import *


@pytest.mark.parametrize("stack,ret", [
    [[True], [False]],
    [[True], [False]],
])
def test_not(vm, stack, ret):
    assert vm.run([Opcode.CALLS(NOT)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[False, False], [False]],
    [[True, False], [True]],
    [[False, True], [True]],
    [[True, True], [True]],
])
def test_or(vm, stack, ret):
    assert vm.run([Opcode.CALLS(OR)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[False, False], [False]],
    [[True, False], [False]],
    [[False, True], [False]],
    [[True, True], [True]],
])
def test_and(vm, stack, ret):
    assert vm.run([Opcode.CALLS(AND)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[False, False], [False]],
    [[True, False], [True]],
    [[False, True], [True]],
    [[True, True], [False]],
])
def test_xor(vm, stack, ret):
    assert vm.run([Opcode.CALLS(XOR)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[], [FunctionRef.parse(NOT)]]
])
def test_funref(vm, stack, ret):
    assert vm.run([Opcode.FUNREF(NOT), Opcode.RETURN(1)], stack = stack) == ret


@pytest.mark.parametrize("stack,ret", [
    [[], [True]]
])
def test_callf(vm, stack, ret):
    assert vm.run([Opcode.FALSE(), Opcode.FUNREF(NOT), Opcode.CALLF(1)], stack = stack) == ret
