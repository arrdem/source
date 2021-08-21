"""

"""

from lilith.interpreter import Bindings, Runtime, eval
from lilith.reader import Module
from lilith.parser import Args, Apply, Symbol

import pytest


@pytest.mark.parametrize(
    "expr, expected",
    [
        (1, 1),
        ([1, 2], [1, 2]),
        ({"foo": "bar"}, {"foo": "bar"}),
    ],
)
def test_eval(expr, expected):
    assert (
        eval(
            Runtime("test", dict()),
            Module("__repl__", dict()),
            Bindings("__root__", None),
            expr,
        )
        == expected
    )


def test_hello_world(capsys):
    assert (
        eval(
            Runtime("test", {}),
            Module("__repl__", {Symbol("print"): print}),
            Bindings("__root__", None),
            Apply(Symbol("print"), Args(["hello, world"], {})),
        )
        is None
    )
    captured = capsys.readouterr()
    assert captured.out == "hello, world\n"
