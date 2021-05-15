"""
"""

from conftest import parametrize

from calf.reader import read_buffer


@parametrize(
    "text",
    [
        "()",
        "[]",
        "[[[[[[[[[]]]]]]]]]",
        "{1 {2 {}}}",
        '"foo"',
        "foo",
        "'foo",
        "^foo bar",
        "^:foo bar",
        "{\"foo\" '([:bar ^:foo 'baz 3.14159e0])}",
        "[:foo bar 'baz lo/l, 1, 1.2. 1e-5 -1e2]",
    ],
)
def test_read(text):
    assert list(read_buffer(text))
