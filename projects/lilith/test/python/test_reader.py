"""Tests covering the reader."""

from lilith.parser import Apply, Args, Block
from lilith.reader import Module, read_buffer

import pytest


@pytest.mark.parametrize('example, expected', [
    ("""!def[main, lang[lil]]\nprint["hello, world"]\n""",
     Module("&buff", {"main": Block(Apply('lang', Args(["lil"], {})), ["print[\"hello, world\"]"])}))
])
def test_read(example, expected):
    got = read_buffer(example)
    print(got)
    assert got == expected
