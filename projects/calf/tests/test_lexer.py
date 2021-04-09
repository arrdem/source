"""
Tests of calf.lexer

Tests both basic functionality, some examples and makes sure that arbitrary token sequences round
trip through the lexer.
"""

import calf.lexer as cl
from conftest import parametrize

import pytest


def lex_single_token(buffer):
    """Lexes a single token from the buffer."""

    return next(iter(cl.lex_buffer(buffer)))


@parametrize(
    "text,token_type",
    [
        ("(", "PAREN_LEFT",),
        (")", "PAREN_RIGHT",),
        ("[", "BRACKET_LEFT",),
        ("]", "BRACKET_RIGHT",),
        ("{", "BRACE_LEFT",),
        ("}", "BRACE_RIGHT",),
        ("^", "META",),
        ("#", "MACRO_DISPATCH",),
        ("'", "SINGLE_QUOTE"),
        ("foo", "SYMBOL",),
        ("foo/bar", "SYMBOL"),
        (":foo", "KEYWORD",),
        (":foo/bar", "KEYWORD",),
        (" ,,\t ,, \t", "WHITESPACE",),
        ("\n\r", "WHITESPACE"),
        ("\n", "WHITESPACE"),
        ("  ,    ", "WHITESPACE",),
        ("; this is a sample comment\n", "COMMENT"),
        ('"foo"', "STRING"),
        ('"foo bar baz"', "STRING"),
    ],
)
def test_lex_examples(text, token_type):
    t = lex_single_token(text)
    assert t.value == text
    assert t.type == token_type


@parametrize(
    "text,token_types",
    [
        ("foo^bar", ["SYMBOL", "META", "SYMBOL"]),
        ("foo bar", ["SYMBOL", "WHITESPACE", "SYMBOL"]),
        ("foo-bar", ["SYMBOL"]),
        ("foo\nbar", ["SYMBOL", "WHITESPACE", "SYMBOL"]),
        (
            "{[^#()]}",
            [
                "BRACE_LEFT",
                "BRACKET_LEFT",
                "META",
                "MACRO_DISPATCH",
                "PAREN_LEFT",
                "PAREN_RIGHT",
                "BRACKET_RIGHT",
                "BRACE_RIGHT",
            ],
        ),
        ("+", ["SYMBOL"]),
        ("-", ["SYMBOL"]),
        ("1", ["INTEGER"]),
        ("-1", ["INTEGER"]),
        ("-1.0", ["FLOAT"]),
        ("-1e3", ["FLOAT"]),
        ("+1.3e", ["FLOAT"]),
        ("f", ["SYMBOL"]),
        ("f1", ["SYMBOL"]),
        ("f1g2", ["SYMBOL"]),
        ("foo13-bar", ["SYMBOL"]),
        ("foo+13-12bar", ["SYMBOL"]),
        ("+-+-+-+-+", ["SYMBOL"]),
    ],
)
def test_lex_compound_examples(text, token_types):
    t = cl.lex_buffer(text)
    result_types = [token.type for token in t]
    assert result_types == token_types
