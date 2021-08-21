"""
Pytest fixtures.
"""

from lilith.parser import Block, parser_with_transformer, GRAMMAR

import pytest


@pytest.fixture
def args_grammar():
    return parser_with_transformer(GRAMMAR, "args")


@pytest.fixture
def kwargs_grammar():
    return parser_with_transformer(GRAMMAR, "kwargs")


@pytest.fixture
def arguments_grammar():
    return parser_with_transformer(GRAMMAR, "arguments")

@pytest.fixture
def header_grammar():
    return parser_with_transformer(GRAMMAR, "header")