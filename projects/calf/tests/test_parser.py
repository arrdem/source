"""
Tests of calf.parser
"""

import calf.parser as cp
from conftest import parametrize

import pytest


@parametrize("text", [
    '"',
    '"foo bar',
    '"""foo bar',
    '"""foo bar"',
])
def test_bad_strings_raise(text):
    """Tests asserting we won't let obviously bad strings fly."""
    # FIXME (arrdem 2021-03-13):
    #   Can we provide this behavior in the lexer rather than in the parser?
    with pytest.raises(ValueError):
        next(cp.parse_buffer(text))


@parametrize("text", [
    "[1.0",
    "(1.0",
    "{1.0",
])
def test_unterminated_raises(text):
    """Tests asserting that we don't let unterminated collections parse."""
    with pytest.raises(cp.CalfMissingCloseParseError):
        next(cp.parse_buffer(text))


@parametrize("text", [
    "[{]",
    "[(]",
    "({)",
    "([)",
    "{(}",
    "{[}",
])
def test_unbalanced_raises(text):
    """Tests asserting that we don't let missmatched collections parse."""
    with pytest.raises(cp.CalfUnexpectedCloseParseError):
        next(cp.parse_buffer(text))


@parametrize("buff, value", [
    ('"foo"', "foo"),
    ('"foo\tbar"', "foo\tbar"),
    ('"foo\n\rbar"', "foo\n\rbar"),
    ('"foo\\"bar\\""', "foo\"bar\""),
    ('"""foo"""', 'foo'),
    ('"""foo"bar"baz"""', 'foo"bar"baz'),
])
def test_strings_round_trip(buff, value):
    assert next(cp.parse_buffer(buff)) == value

@parametrize('text, element_types', [
    # Integers
    ("(1)", ["INTEGER"]),
    ("( 1 )", ["INTEGER"]),
    ("(,1,)", ["INTEGER"]),
    ("(1\n)", ["INTEGER"]),
    ("(\n1\n)", ["INTEGER"]),
    ("(1, 2, 3, 4)", ["INTEGER", "INTEGER", "INTEGER", "INTEGER"]),

    # Floats
    ("(1.0)", ["FLOAT"]),
    ("(1.0e0)", ["FLOAT"]),
    ("(1e0)", ["FLOAT"]),
    ("(1e0)", ["FLOAT"]),

    # Symbols
    ("(foo)", ["SYMBOL"]),
    ("(+)", ["SYMBOL"]),
    ("(-)", ["SYMBOL"]),
    ("(*)", ["SYMBOL"]),
    ("(foo-bar)", ["SYMBOL"]),
    ("(+foo-bar+)", ["SYMBOL"]),
    ("(+foo-bar+)", ["SYMBOL"]),
    ("( foo bar )", ["SYMBOL", "SYMBOL"]),

    # Keywords
    ("(:foo)", ["KEYWORD"]),
    ("( :foo )", ["KEYWORD"]),
    ("(\n:foo\n)", ["KEYWORD"]),
    ("(,:foo,)", ["KEYWORD"]),
    ("(:foo :bar)", ["KEYWORD", "KEYWORD"]),
    ("(:foo :bar 1)", ["KEYWORD", "KEYWORD", "INTEGER"]),

    # Strings
    ('("foo", "bar", "baz")', ["STRING", "STRING", "STRING"]),

    # Lists
    ('([] [] ())', ["SQLIST", "SQLIST", "LIST"]),
])
def test_parse_list(text, element_types):
    """Test we can parse various lists of contents."""
    l_t = next(cp.parse_buffer(text, discard_whitespace=True))
    assert l_t.type == "LIST"
    assert [t.type for t in l_t] == element_types


@parametrize('text, element_types', [
    # Integers
    ("[1]", ["INTEGER"]),
    ("[ 1 ]", ["INTEGER"]),
    ("[,1,]", ["INTEGER"]),
    ("[1\n]", ["INTEGER"]),
    ("[\n1\n]", ["INTEGER"]),
    ("[1, 2, 3, 4]", ["INTEGER", "INTEGER", "INTEGER", "INTEGER"]),

    # Floats
    ("[1.0]", ["FLOAT"]),
    ("[1.0e0]", ["FLOAT"]),
    ("[1e0]", ["FLOAT"]),
    ("[1e0]", ["FLOAT"]),

    # Symbols
    ("[foo]", ["SYMBOL"]),
    ("[+]", ["SYMBOL"]),
    ("[-]", ["SYMBOL"]),
    ("[*]", ["SYMBOL"]),
    ("[foo-bar]", ["SYMBOL"]),
    ("[+foo-bar+]", ["SYMBOL"]),
    ("[+foo-bar+]", ["SYMBOL"]),
    ("[ foo bar ]", ["SYMBOL", "SYMBOL"]),

    # Keywords
    ("[:foo]", ["KEYWORD"]),
    ("[ :foo ]", ["KEYWORD"]),
    ("[\n:foo\n]", ["KEYWORD"]),
    ("[,:foo,]", ["KEYWORD"]),
    ("[:foo :bar]", ["KEYWORD", "KEYWORD"]),
    ("[:foo :bar 1]", ["KEYWORD", "KEYWORD", "INTEGER"]),

    # Strings
    ('["foo", "bar", "baz"]', ["STRING", "STRING", "STRING"]),

    # Lists
    ('[[] [] ()]', ["SQLIST", "SQLIST", "LIST"]),
])
def test_parse_sqlist(text, element_types):
    """Test we can parse various 'square' lists of contents."""
    l_t = next(cp.parse_buffer(text, discard_whitespace=True))
    assert l_t.type == "SQLIST"
    assert [t.type for t in l_t] == element_types


@parametrize('text, element_pairs', [
    ("{}",
     []),

    ("{:foo 1}",
     [["KEYWORD", "INTEGER"]]),

    ("{:foo 1, :bar 2}",
     [["KEYWORD", "INTEGER"],
      ["KEYWORD", "INTEGER"]]),

    ("{foo 1, bar 2}",
     [["SYMBOL", "INTEGER"],
      ["SYMBOL", "INTEGER"]]),

    ("{foo 1, bar -2}",
     [["SYMBOL", "INTEGER"],
      ["SYMBOL", "INTEGER"]]),

    ("{foo 1, bar -2e0}",
     [["SYMBOL", "INTEGER"],
      ["SYMBOL", "FLOAT"]]),

    ("{foo ()}",
     [["SYMBOL", "LIST"]]),

    ("{foo []}",
     [["SYMBOL", "SQLIST"]]),

    ("{foo {}}",
     [["SYMBOL", "DICT"]]),

    ('{"foo" {}}',
     [["STRING", "DICT"]])
])
def test_parse_dict(text, element_pairs):
    """Test we can parse various mappings."""
    d_t = next(cp.parse_buffer(text, discard_whitespace=True))
    assert d_t.type == "DICT"
    assert [[t.type for t in pair] for pair in d_t.value] == element_pairs


@parametrize("text", [
    "{1}",
    "{1, 2, 3}",
    "{:foo}",
    "{:foo :bar :baz}"
])
def test_parse_bad_dict(text):
    """Assert that dicts with missmatched pairs don't parse."""
    with pytest.raises(Exception):
        next(cp.parse_buffer(text))


@parametrize("text", [
    "()",
    "(1 1.1 1e2 -2 foo :foo foo/bar :foo/bar [{},])",
    "{:foo bar, :baz [:qux]}",
    "'foo",
    "'[foo bar :baz 'qux, {}]",
    "#foo []",
    "^{} bar",
])
def test_examples(text):
    """Shotgun examples showing we can parse some stuff."""

    assert list(cp.parse_buffer(text))
