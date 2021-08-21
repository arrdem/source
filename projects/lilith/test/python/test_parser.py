"""tests covering the Lilith parser."""

from lilith.parser import Args, Block, parser_with_transformer, GRAMMAR

import pytest


@pytest.mark.parametrize('example, result', [
    ("1", ["1"]),
    ("1, 2", ["1", "2"]),
    ("1, 2, 3", ["1", "2", "3"]),
])
def test_parse_args(args_grammar, example, result):
    assert args_grammar.parse(example) == result


@pytest.mark.parametrize('example, result', [
    ("foo: bar", {"foo": "bar"}),
    ("foo: bar, baz: qux", {"foo": "bar", "baz": "qux"}),
])
def test_parse_kwargs(kwargs_grammar, example, result):
    assert kwargs_grammar.parse(example) == result


@pytest.mark.parametrize('example, result', [
    ("1", (["1"], {})),
    ("1, 2", (["1", "2"], {})),
    ("1, 2, 3", (["1", "2", "3"], {})),
    ("foo: bar", ([], {"foo": "bar"})),
    ("foo: bar, baz: qux", ([], {"foo": "bar", "baz": "qux"})),
    ("1; foo: bar, baz: qux", (["1"], {"foo": "bar", "baz": "qux"})),
])
def test_parse_arguments(arguments_grammar, example, result):
    assert arguments_grammar.parse(example) == result

@pytest.mark.parametrize('example, result', [
    ('!def[syntax]',
     Block('def', Args(['syntax'], {}), [])),
    ('!frag[lang: md]',
     Block('frag', Args([], {'lang': 'md'}), [])),
    ('!frag[foo; lang: md]',
     Block('frag', Args(['foo'], {'lang': 'md'}), [])),
])
def test_parse_header(header_grammar, example, result):
    assert header_grammar.parse(example) == result
