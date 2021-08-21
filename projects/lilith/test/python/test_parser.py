"""tests covering the Lilith parser."""

from lilith.parser import block_grammar, Block

import pytest

@pytest.mark.parametrize('example, result', [
    ('!def[syntax]',
     Block('def', ['syntax'], None, [])),
    ('!frag[lang: md]',
     Block('frag', None, {'lang': 'md'}, [])),
    ('!frag[foo, lang: md]',
     Block('frag', ['foo'], {'lang': 'md'}, [])),
])
def test_parse_header(example, result):
    assert block_grammar.parse(example) == result


(
    """!def[designdoc]
!frag[lang: md]
# Designdoc

A design document""",
     None
)
