#!/usr/bin/env python3

from ichor.state import FUNC, VAR

import pytest


@pytest.mark.parametrize('sig', [
    ";not;bool;bool",
    ";and;bool,bool;bool",
    ";or;bool,bool,bool;bool",
])
def test_func_parses(sig):
    assert FUNC.parse(sig)


@pytest.mark.parametrize('sig', [
    ";bool;true(),false()",
    "A,B;pair;pair(a:A,b:B)",
    "A,B,C;tripple;tripple(a:A,b:B,c:C)",
    "A,B,C,D;quad;quad(a:A,b:B,c:C,d:D)",
    "A,B,C,D,E;quint;quint(a:A,b:B,c:C,d:D,e:E)",
])
def test_var_parses(sig):
    assert VAR.parse(sig)
