#!/usr/bin/env python3

from .fixtures import *  # noqa

from ichor import isa, TRUE, FALSE, NOT1
import pytest


@pytest.mark.parametrize("stack,ret", [
    [[TRUE], [FALSE]],
    [[FALSE], [TRUE]],
])
def test_not(vm, stack, ret):
    assert vm.run([
        isa.IDENTIFIERC(NOT1),
        isa.FUNREF(),
        isa.CALLF(1),
        isa.RETURN(1)
    ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False], [False]],
#     [[True, False], [True]],
#     [[False, True], [True]],
#     [[True, True], [True]],
# ])
# def test_or(vm, stack, ret):
#     assert vm.run([
#         isa.IDENTIFIERC(OR2),
#         isa.FUNREF(),
#         isa.CALLF(2),
#         isa.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False], [False]],
#     [[True, False], [False]],
#     [[False, True], [False]],
#     [[True, True], [True]],
# ])
# def test_and(vm, stack, ret):
#     assert vm.run([
#         isa.IDENTIFIERC(AND2),
#         isa.FUNREF(),
#         isa.CALLF(2),
#         isa.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False], [False]],
#     [[True, False], [True]],
#     [[False, True], [True]],
#     [[True, True], [False]],
# ])
# def test_xor2(vm, stack, ret):
#     assert vm.run([
#         isa.IDENTIFIERC(XOR2),
#         isa.FUNREF(),
#         isa.CALLF(2),
#         isa.RETURN(1)
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
#         isa.IDENTIFIERC(XOR3),
#         isa.FUNREF(),
#         isa.CALLF(3),
#         isa.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[], [FunctionRef.parse(NOT1)]]
# ])
# def test_funref(vm, stack, ret):
#     assert vm.run([
#         isa.IDENTIFIERC(NOT1),
#         isa.FUNREF(),
#         isa.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False], [True]]
# ])
# def test_callf(vm, stack, ret):
#     assert vm.run([
#         isa.IDENTIFIERC(NOT1),
#         isa.FUNREF(),
#         isa.CALLF(1),
#         isa.RETURN(1)
#     ], stack = stack) == ret


# @pytest.mark.parametrize("stack,ret", [
#     [[False, False], [False]],
#     [[True, False], [True]],
#     [[False, True], [True]],
#     [[True, True], [False]],
# ])
# def test_callc(vm, stack, ret):
#     assert vm.run([
#         isa.IDENTIFIERC(XOR2),
#         isa.FUNREF(),
#         isa.CLOSUREF(1),
#         isa.CALLC(1),
#         isa.RETURN(1),
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
#         isa.IDENTIFIERC(XOR3),
#         isa.FUNREF(),
#         isa.CLOSUREF(1),
#         isa.CLOSUREC(1),
#         isa.CALLC(1),
#         isa.RETURN(1),
#     ], stack = stack) == ret
