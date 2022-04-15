#!/usr/bin/env python3

import pytest
from shogoth.vm import *

from .fixtures import * # noqa


@pytest.mark.parametrize('stack,ret', [
    [[True], [False]],
    [[True], [False]],
])
def test_not(vm, stack, ret):
    assert vm.run([Opcode.CALL(NOT)], stack = stack) == ret


@pytest.mark.parametrize('stack,ret', [
    [[False, False], [False]],
    [[True, False], [True]],
    [[False, True], [True]],
    [[True, True], [True]],
])
def test_or(vm, stack, ret):
    assert vm.run([Opcode.CALL(OR)], stack = stack) == ret


@pytest.mark.parametrize('stack,ret', [
    [[False, False], [False]],
    [[True, False], [False]],
    [[False, True], [False]],
    [[True, True], [True]],
])
def test_and(vm, stack, ret):
    assert vm.run([Opcode.CALL(AND)], stack = stack) == ret


@pytest.mark.parametrize('stack,ret', [
    [[False, False], [False]],
    [[True, False], [True]],
    [[False, True], [True]],
    [[True, True], [False]],
])
def test_xor(vm, stack, ret):
    assert vm.run([Opcode.CALL(XOR)], stack = stack) == ret
