"""
Tests covering the YAML linter.
"""

from yamlschema import lint_buffer

import pytest


@pytest.mark.parametrize('schema, obj', [
    ({"type": "number"}, "---\n1.0"),
    ({"type": "integer"}, "---\n3"),
    ({"type": "string"}, "---\nfoo bar baz"),
    ({"type": "string", "maxLength": 15}, "---\nfoo bar baz"),
    ({"type": "string", "minLength": 10}, "---\nfoo bar baz"),
    ({"type": "string", "pattern": "^foo.*"}, "---\nfoo bar baz"),
])
def test_lint_document_ok(schema, obj):
    assert not list(lint_buffer(schema, obj))
