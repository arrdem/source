"""
Tests covering the Flowmetal parser.
"""

from math import nan

import flowmetal.parser as p

import pytest


def test_parse_list():
    """Trivial parsing a list."""
    assert isinstance(p.parses("()"), p.ListToken)
    assert p.parses("()").paren == p.ListType.ROUND


@pytest.mark.parametrize('txt, val', [
    ('1', 1),
    ('2', 2),
    ('103', 103),
    ('504', 504),
    # Sign prefixes
    ('-1', -1),
    ('+1', +1),
    # Underscores as whitespace
    ('1_000_000', 1e6),
    ('+1_000', 1000),
    ('-1_000', -1000),
    # Variable base
    ('2r1', 1),
    ('2r10', 2),
    ('2r100', 4),
    ('2r101', 5),
    ('+2r10', 2),
    ('-2r10', -2),
    # Octal
    ('00', 0),
    ('01', 1),
    ('010', 8),
    ('+010', 8),
    ('-010', -8),
    # Hex
    ('0x0', 0),
    ('0xF', 15),
    ('0x10', 16),
    ('+0x10', 16),
    ('-0x10', -16),
])
def test_parse_num(txt, val):
    """Some trivial cases of parsing numbers."""
    assert isinstance(p.parses(txt), p.IntegerToken)
    assert p.parses(txt).data == val


@pytest.mark.parametrize('frac', [
    '1/2', '1/4', '1/512',
])
def test_parse_ratio(frac):
    """Test covering the ratio notation."""
    assert isinstance(p.parses(frac), p.FractionToken)
    assert p.parses(frac).data == p.Fraction(frac)



@pytest.mark.parametrize('sym,', [
    'a',
    'b',
    '*earmuff-style*',
    '+kebab-style+',
    'JAVA_CONSTANT_STYLE',
])
def test_parse_sym(sym):
    """Some trivial cases of parsing symbols."""
    assert isinstance(p.parses(sym), p.SymbolToken)
    assert p.parses(sym).data == sym


@pytest.mark.parametrize('txt, tokenization', [
    ('(1 2 3)',
     [(p.IntegerToken, '1'),
      (p.WhitespaceToken, ' '),
      (p.IntegerToken, '2'),
      (p.WhitespaceToken, ' '),
      (p.IntegerToken, '3')]),
    ('(a 1 b 2)',
     [(p.SymbolToken, 'a'),
      (p.WhitespaceToken, ' '),
      (p.IntegerToken, '1'),
      (p.WhitespaceToken, ' '),
      (p.SymbolToken, 'b'),
      (p.WhitespaceToken, ' '),
      (p.IntegerToken, '2')])
])
def test_list_contents(txt, tokenization):
    """Parse examples of list contents."""
    assert isinstance(p.parses(txt), p.ListToken)

    lelems = p.parses(txt).data
    for (type, text), token in zip(tokenization, lelems):
        assert isinstance(token, type)
        assert token.raw == text


@pytest.mark.parametrize('txt, value', [
    ('1.0', 1.0),
    ('-1.0', -1.0),
    ('1.01', 1.01),
    ('1e0', 1e0),
    ('1e3', 1e3),
    ('1e-3', 1e-3),
    ('1.01e3', 1.01e3),
    ('1_000e0', 1e3),
])
def test_float_values(txt, value):
    """Some examples of floats."""
    assert isinstance(p.parses(txt), p.FloatToken)
    assert p.parses(txt).data == value


@pytest.mark.parametrize('txt, tokenization', [
    ('+1', p.IntegerToken),
    ('+1+', p.SymbolToken),
    ('+1e', p.SymbolToken),
    ('+1e3', p.FloatToken),
    ('+1.0', p.FloatToken),
    ('+1.0e3', p.FloatToken),
    ('a.b', p.SymbolToken),
    ('1.b', p.SymbolToken),
])
def test_ambiguous_floats(txt, tokenization):
    """Parse examples of 'difficult' floats and symbols."""
    assert isinstance(p.parses(txt), tokenization), "Token type didn't match!"
    assert p.parses(txt).raw == txt, "Parse wasn't total!"


@pytest.mark.parametrize('txt,', [
    r'""',
    r'"foo"',
    r'"foo bar baz qux"',
    r'"foo\nbar\tbaz\lqux"',
    r'''"foo
    bar
    baz
    qux"''',
    r'"\000 \x00"',
    r'"\"\""',
])
def test_string(txt):
    """Some examples of strings, and of escape sequences."""
    assert isinstance(p.parses(txt), p.StringToken)


@pytest.mark.parametrize('txt,', [
    ':foo',
    ':foo/bar',
    ':foo.bar/baz?',
])
def test_keyword(txt):
    """Some examples of keywords."""
    assert isinstance(p.parses(txt), p.KeywordToken)
