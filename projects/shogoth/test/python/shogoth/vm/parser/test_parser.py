#!/usr/bin/env python3

from shogoth.parser import parse

import pytest


@pytest.mark.parametrize('example', [
    "true",
    "false",
    "nil",
    "foo",
    '"this is a trivial string"',
    r'/this is a trivial pattern/',
    "[]",
    "[[]]",
    "[[[]]]",
    "()",
    "(())",
    "((()))",
    "{}",

    # Decimals
    "10",
    "01", # odd but legal

    # Octal
    "0o7",

    # Binary
    "0b1",

    # Hex
    "0x1",
    "0xF",
    "0xa",

    # FIXME: Floats (ugh)
])
def test_parses(example):
    assert parse(example)
