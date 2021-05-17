"""
JSONSchema linting for YAML documents.
"""

import logging
import typing as t
from enum import Enum
from io import StringIO
import re

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode


log = logging.getLogger(__name__)


class LintLevel(Enum):
    """Lint outcome levels."""

    MISSING = 1
    MISSMATCH = 2
    UNEXPECTED = 3


class LintRecord(t.NamedTuple):
    """A linting record."""

    level: LintLevel
    node: Node
    schema: object
    message: str

    @property
    def start_mark(self):
        return self.node.start_mark


class YamlLinter(object):
    """YAML linting against JSON schemas."""

    def __init__(self, schema):
        self._schema = schema

    def dereference(self, schema):
        """Dereference a {"$ref": ""} form."""

        if schema in [True, False]:
            return schema

        elif ref := schema.get("$ref"):
            document_url, path = ref.split("#")
            # FIXME (arrdem 2021-05-17):
            #   Build support for loading and caching schemas from elsewhere.
            assert not document_url
            assert path.startswith("/")
            path = path[1:].split("/")
            schema = self._schema
            for e in path:
                if not e:
                    raise ValueError(f"Unable to dereference {ref}; contains empty segment!")
                if not (schema := schema.get(e)):
                    raise ValueError(f"Unable to dereference {ref}; references missing sub-document!")

        return schema

    def lint_mapping(self, schema, node: Node) -> t.Iterable[LintRecord]:
        """FIXME."""

        if schema["type"] != "object" or not isinstance(node, MappingNode):
            yield LintRecord(
                LintLevel.MISSMATCH,
                node,
                schema,
                f"Expected {schema['type']}, got {node.id} {str(node.start_mark).lstrip()}",
            )

        additional_type: t.Union[dict, bool] = schema.get("additionalProperties", True)
        properties: dict = schema.get("properties", {})
        required: t.Iterable[LintRecord] = schema.get("required", [])

        for k in required:
            if k not in [_k.value for _k, _v in node.value]:
                yield LintRecord(
                    LintLevel.MISSING,
                    node,
                    schema,
                    f"Required key {k!r} absent from mapping {str(node.start_mark).lstrip()}",
                )

        for k, v in node.value:
            if k.value in properties:
                yield from self.lint_document(v, properties.get(k.value))

            elif additional_type:
                yield from self.lint_document(v, additional_type)

            else:
                yield LintRecord(
                    LintLevel.UNEXPECTED,
                    node,
                    schema,
                    f"Key {k.value!r} is not allowed by schema {str(node.start_mark).lstrip()}",
                )

    def lint_sequence(self, schema, node: Node) -> t.Iterable[LintRecord]:
        """FIXME.

        There aren't sequences we need to lint in the current schema design, punting.

        """

        if schema["type"] != "array" or not isinstance(node, SequenceNode):
            yield LintRecord(
                LintLevel.MISSMATCH,
                node,
                schema,
                f"Expected {schema['type']}, got {node.id} {str(node.start_mark).lstrip()}",
            )

        subschema = schema.get("items")
        if subschema:
            for item in node.value:
                yield from self.lint_document(item, subschema)

    def lint_scalar(self, schema, node: Node) -> t.Iterable[LintRecord]:
        """FIXME.

        The only terminal we care about linting in the current schema is {"type": "string"}.

        """

        if schema["type"] == "string":
            yield from self.lint_string(schema, node)
        elif schema["type"] == "integer":
            yield from self.lint_integer(schema, node)
        elif schema["type"] == "number":
            yield from self.lint_number(schema, node)
        else:
            raise NotImplementedError(f"Scalar type {schema['type']} is not supported")

    def lint_string(self, schema, node: Node) -> t.Iterable[LintRecord]:
        """FIXME."""

        if node.tag != "tag:yaml.org,2002:str":
            yield LintRecord(
                LintLevel.MISSMATCH, node, schema, f"Expected a string, got a {node}"
            )

        if maxl := schema.get("maxLength"):
            if len(node.value) > maxl:
                yield LintRecord(
                    LintLevel.MISSMATCH, node, schema, f"Expected a shorter string"
                )

        if minl := schema.get("minLength"):
            if len(node.value) < minl:
                yield LintRecord(
                    LintLevel.MISSMATCH, node, schema, f"Expected a longer string"
                )

        if pat := schema.get("pattern"):
            if not re.fullmatch(pat, node.value):
                yield LintRecord(
                    LintLevel.MISSMATCH,
                    node,
                    schema,
                    f"Expected a string matching the pattern",
                )

    def lint_integer(self, schema, node: Node) -> t.Iterable[LintRecord]:
        if node.tag == "tag:yaml.org,2002:int":
            value = int(node.value)
            yield from self._lint_num_range(schema, node, value)

        else:
            yield LintRecord(
                LintLevel.MISSMATCH, node, schema, f"Expected an integer, got a {node.tag}"
            )

    def lint_number(self, schema, node: Node) -> t.Iterable[LintRecord]:
        if node.tag == "tag:yaml.org,2002:float":
            value = float(node.value)
            yield from self._lint_num_range(schema, node, value)

        else:
            yield LintRecord(
                LintLevel.MISSMATCH, node, schema, f"Expected an integer, got a {node.tag}"
            )

    def _lint_num_range(self, schema, node: Node, value) -> t.Iterable[LintRecord]:
        """"FIXME."""

        if (base := schema.get("multipleOf")) is not None:
            if value % base != 0:
                yield LintRecord(
                    LintLevel.MISSMATCH,
                    node,
                    schema,
                    f"Expected a multiple of {base}, got {value}",
                )

        if (max := schema.get("exclusiveMaximum")) is not None:
            if value >= max:
                yield LintRecord(
                    LintLevel.MISSMATCH,
                    node,
                    schema,
                    f"Expected a value less than {max}, got {value}",
                )

        if (max := schema.get("maximum")) is not None:
            if value > max:
                yield LintRecord(
                    LintLevel.MISSMATCH,
                    node,
                    schema,
                    f"Expected a value less than or equal to {max}, got {value}",
                )

        if (min := schema.get("exclusiveMinimum")) is not None:
            if value <= min:
                yield LintRecord(
                    LintLevel.MISSMATCH,
                    node,
                    schema,
                    f"Expected a value greater than {min}, got {value}",
                )

        if (min := schema.get("minimum")) is not None:
            if value < min:
                yield LintRecord(
                    LintLevel.MISSMATCH,
                    node,
                    schema,
                    f"Expected a value greater than or equal to {min}, got {value}",
                )

    def lint_document(self, node, schema=None) -> t.Iterable[LintRecord]:
        """Lint a document.

        Given a Node within a document (or the root of a document!), return a
        (possibly empty!) list of lint or raise in case of fatal errors.

        """

        schema = schema or self._schema  # Fixing up the schema source
        schema = self.dereference(schema)  # And dereference it if needed

        # Special schemas
        # These are schemas that accept everything.
        if schema == True or schema == {}:
            yield from []

        # This is the schema that rejects everything.
        elif schema == False:
            yield LintRecord(
                LintLevel.UNEXPECTED, node, schema, "Received an unexpected value"
            )

        # Walking the PyYAML node hierarchy
        elif isinstance(node, MappingNode):
            yield from self.lint_mapping(schema, node)

        elif isinstance(node, SequenceNode):
            yield from self.lint_sequence(schema, node)

        elif isinstance(node, ScalarNode):
            yield from self.lint_scalar(schema, node)

        else:
            raise RuntimeError(f"Unsupported PyYAML node {type(node)}")


def lint_node(schema, node, cls=YamlLinter) -> t.Iterable[LintRecord]:
    """Lint a composed PyYAML AST node using a schema and linter."""

    linter = cls(schema)
    yield from linter.lint_document(node)


def lint_buffer(schema, buff: str, cls=YamlLinter) -> t.Iterable[LintRecord]:
    """Lint a buffer (string)."""

    with StringIO(buff) as f:
        node = yaml.compose(f)
    yield from lint_node(schema, node, cls=cls)


def lint_file(schema, path, cls=YamlLinter) -> t.Iterable[LintRecord]:
    """Lint a file."""

    with open(path) as f:
        node = yaml.compose(f)
    yield from lint_node(schema, node, cls=cls)
