"""tests covering the Lilith parser."""

from lilith.parser import Apply, Args, Block, GRAMMAR, parse_buffer, parser_with_transformer
import pytest


@pytest.mark.parametrize('example, expected', [
    ("1", [1]),
    ("1, 2", [1, 2]),
    ("1, 2, 3", [1, 2, 3]),
])
def test_parse_args(args_grammar, example, expected):
    assert args_grammar.parse(example) == expected


@pytest.mark.parametrize('example, expected', [
    ("foo: bar", {"foo": "bar"}),
    ("foo: bar, baz: qux", {"foo": "bar", "baz": "qux"}),
])
def test_parse_kwargs(kwargs_grammar, example, expected):
    assert kwargs_grammar.parse(example) == expected


@pytest.mark.parametrize('example, expected', [
    ("1", ([1], {})),
    ("1, 2", ([1, 2], {})),
    ("1, 2, 3", ([1, 2, 3], {})),
    ("foo: bar", ([], {"foo": "bar"})),
    ("foo: bar, baz: qux", ([], {"foo": "bar", "baz": "qux"})),
    ("1; foo: bar, baz: qux", ([1], {"foo": "bar", "baz": "qux"})),
])
def test_parse_arguments(arguments_grammar, example, expected):
    assert arguments_grammar.parse(example) == expected


@pytest.mark.parametrize('example, expected', [
    ('!def[syntax]',
     Block(Apply('def', Args(['syntax'], {})), [])),
    ('!frag[lang: md]',
     Block(Apply('frag', Args([], {'lang': 'md'})), [])),
    ('!frag[foo; lang: md]',
     Block(Apply('frag', Args(['foo'], {'lang': 'md'})), [])),
    ("!int.add[1, 2]",
     Block(Apply('int.add', Args([1, 2], {})), [])),
])
def test_parse_header(header_grammar, example, expected):
    assert header_grammar.parse(example) == expected


@pytest.mark.parametrize('example, expected', [
    ("!frag[lang: md]",
     [Block(Apply('frag', Args([], {"lang": "md"})), [])]),
    ("""!frag[lang: md]\nHello, world!\n\n""",
     [Block(Apply('frag', Args([], {"lang": "md"})), ["Hello, world!", ""])]),
    ("""!frag[lang: md]\nHello, world!\n\n!def[bar]""",
     [Block(Apply('frag', Args([], {"lang": "md"})), ["Hello, world!", ""]),
      Block(Apply('def', Args(["bar"], {})), [])]),
])
def test_block_parser(example, expected):
    assert parse_buffer(example) == expected
