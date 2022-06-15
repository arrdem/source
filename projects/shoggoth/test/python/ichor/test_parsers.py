#!/usr/bin/env python3

from ichor.state import FUNC, VAR

import pytest


@pytest.mark.parametrize('sig,parse', [
    (";not;bool;bool", ((), "not", ("bool",), ("bool",))),
    (";and;bool,bool;bool", ((), "and", ("bool", "bool"), ("bool",))),
    (";or;bool,bool,bool;bool", ((), "or", ("bool", "bool", "bool"), ("bool",))),
])
def test_func_parses(sig, parse):
    assert FUNC.parse(sig) == parse


@pytest.mark.parametrize('sig,parse', [
    (";bool;true(),false()", ((), "bool", (("true", ()), ("false", ())))),
    ("A,B;pair;pair(a:A,b:B)", (("A", "B"), "pair", (("pair", (("a", "A"), ("b", "B"))),))),
])
def test_var_parses(sig, parse):
    assert VAR.parse(sig) == parse
