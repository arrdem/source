"""
Tests covering the YAML linter.
"""

import pytest
from yamlschema import lint_buffer


@pytest.mark.parametrize(
    "schema, obj",
    [
        ({"type": "number"}, "---\n1.0"),
        ({"type": "integer"}, "---\n3"),
        ({"type": "string"}, "---\nfoo bar baz"),
        ({"type": "string", "maxLength": 15}, "---\nfoo bar baz"),
        ({"type": "string", "minLength": 10}, "---\nfoo bar baz"),
        ({"type": "string", "pattern": "^foo.*"}, "---\nfoo bar baz"),
        ({"type": "object", "additionalProperties": True}, "---\nfoo: bar\nbaz: qux"),
        (
            {"type": "object", "properties": {"foo": {"type": "string"}}},
            "---\nfoo: bar\nbaz: qux",
        ),
        (
            {
                "type": "object",
                "properties": {"foo": {"type": "string"}},
                "additionalProperties": False,
            },
            "---\nfoo: bar",
        ),
        ({"type": "object", "properties": {"foo": {"type": "object"}}}, "---\nfoo: {}"),
        (
            {
                "type": "object",
                "properties": {"foo": {"type": "array", "items": {"type": "object"}}},
            },
            "---\nfoo: [{}, {}, {foo: bar}]",
        ),
    ],
)
def test_lint_document_ok(schema, obj):
    assert not list(lint_buffer(schema, obj))


@pytest.mark.parametrize(
    "msg, schema, obj",
    [
        # Numerics
        ("Floats are not ints", {"type": "integer"}, "---\n1.0"),
        ("Ints are not floats", {"type": "number"}, "---\n1"),
        # Numerics - range limits. Integer edition
        (
            "1 is the limit of the range",
            {"type": "integer", "exclusiveMaximum": 1},
            "---\n1",
        ),
        (
            "1 is the limit of the range",
            {"type": "integer", "exclusiveMinimum": 1},
            "---\n1",
        ),
        ("1 is out of the range", {"type": "integer", "minimum": 2}, "---\n1"),
        ("1 is out of the range", {"type": "integer", "maximum": 0}, "---\n1"),
        ("1 is out of the range", {"type": "integer", "exclusiveMinimum": 1}, "---\n1"),
        # Numerics - range limits. Number/Float edition
        (
            "1 is the limit of the range",
            {"type": "number", "exclusiveMaximum": 1},
            "---\n1.0",
        ),
        (
            "1 is the limit of the range",
            {"type": "number", "exclusiveMinimum": 1},
            "---\n1.0",
        ),
        ("1 is out of the range", {"type": "number", "minimum": 2}, "---\n1.0"),
        ("1 is out of the range", {"type": "number", "maximum": 0}, "---\n1.0"),
        (
            "1 is out of the range",
            {"type": "number", "exclusiveMinimum": 1},
            "---\n1.0",
        ),
        # String shit
        ("String too short", {"type": "string", "minLength": 1}, "---\n''"),
        ("String too long", {"type": "string", "maxLength": 1}, "---\nfoo"),
        (
            "String does not match pattern",
            {"type": "string", "pattern": "bar"},
            "---\nfoo",
        ),
        (
            "String does not fully match pattern",
            {"type": "string", "pattern": "foo"},
            "---\nfooooooooo",
        ),
    ],
)
def test_lint_document_fails(msg, schema, obj):
    assert list(lint_buffer(schema, obj)), msg


@pytest.mark.parametrize(
    "msg, schema, obj",
    [
        (
            "Basic usage of $ref",
            {
                "$ref": "#/definitions/Foo",
                "definitions": {
                    "Foo": {"type": "string"},
                },
            },
            "---\nfoo",
        ),
        (
            "Use of nested references",
            {
                "$ref": "#/definitions/Foos",
                "definitions": {
                    "Foos": {"type": "array", "items": {"$ref": "#/definitions/Foo"}},
                    "Foo": {"type": "string"},
                },
            },
            "---\n- foo\n- bar\n- baz",
        ),
    ],
)
def test_ref_references(msg, schema, obj):
    assert not list(lint_buffer(schema, obj)), msg
