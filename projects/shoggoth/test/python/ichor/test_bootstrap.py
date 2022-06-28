#!/usr/bin/env python3

from .fixtures import *  # noqa

from ichor import *
import pytest


@pytest.mark.parametrize("stack,ret", [
    [[TRUE], [FALSE]],
    [[FALSE], [TRUE]],
])
def test_not(vm, stack, ret):
    assert vm.run([
        Opcode.IDENTIFIERC(NOT1),
        Opcode.FUNREF(),
        Opcode.CALLF(1),
        Opcode.RETURN(1)
    ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False], [False]],
#     [[True, False], [True]],
#     [[False, True], [True]],
#     [[True, True], [True]],
# ])
# def test_or(vm, stack, ret):
#     assert vm.run([
#         Opcode.IDENTIFIERC(OR2),
#         Opcode.FUNREF(),
#         Opcode.CALLF(2),
#         Opcode.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False], [False]],
#     [[True, False], [False]],
#     [[False, True], [False]],
#     [[True, True], [True]],
# ])
# def test_and(vm, stack, ret):
#     assert vm.run([
#         Opcode.IDENTIFIERC(AND2),
#         Opcode.FUNREF(),
#         Opcode.CALLF(2),
#         Opcode.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False], [False]],
#     [[True, False], [True]],
#     [[False, True], [True]],
#     [[True, True], [False]],
# ])
# def test_xor2(vm, stack, ret):
#     assert vm.run([
#         Opcode.IDENTIFIERC(XOR2),
#         Opcode.FUNREF(),
#         Opcode.CALLF(2),
#         Opcode.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False, False], [False]],
#     [[True,  False, False], [True]],
#     [[False, True,  False], [True]],
#     [[True,  True,  False], [True]],
#     [[True,  True,  True],  [False]],
#     [[False, True,  True],  [True]],
#     [[False, False, True],  [True]],
# ])
# def test_xor3(vm, stack, ret):
#     assert vm.run([
#         Opcode.IDENTIFIERC(XOR3),
#         Opcode.FUNREF(),
#         Opcode.CALLF(3),
#         Opcode.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[], [FunctionRef.parse(NOT1)]]
# ])
# def test_funref(vm, stack, ret):
#     assert vm.run([
#         Opcode.IDENTIFIERC(NOT1),
#         Opcode.FUNREF(),
#         Opcode.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False], [True]]
# ])
# def test_callf(vm, stack, ret):
#     assert vm.run([
#         Opcode.IDENTIFIERC(NOT1),
#         Opcode.FUNREF(),
#         Opcode.CALLF(1),
#         Opcode.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False], [False]],
#     [[True, False], [True]],
#     [[False, True], [True]],
#     [[True, True], [False]],
# ])
# def test_callc(vm, stack, ret):
#     assert vm.run([
#         Opcode.IDENTIFIERC(XOR2),
#         Opcode.FUNREF(),
#         Opcode.CLOSUREF(1),
#         Opcode.CALLC(1),
#         Opcode.RETURN(1),
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False, False], [False]],
#     [[True,  False, False], [True]],
#     [[False, True,  False], [True]],
#     [[True,  True,  False], [True]],
#     [[True,  True,  True],  [False]],
#     [[False, True,  True],  [True]],
#     [[False, False, True],  [True]],
# ])
# def test_closurec(vm, stack, ret):
#     assert vm.run([
#         Opcode.IDENTIFIERC(XOR3),
#         Opcode.FUNREF(),
#         Opcode.CLOSUREF(1),
#         Opcode.CLOSUREC(1),
#         Opcode.CALLC(1),
#         Opcode.RETURN(1),
#     ], stack = stack) == ret
