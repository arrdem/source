"""
JSONSchema linting for YAML documents.
"""

import logging
import typing as t

from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode


log = logging.getLogger(__name__)


def lint_mapping(schema, node: Node) -> t.List[str]:
  lint: t.List[str] = []
  if schema["type"] != "object" or not isinstance(node, MappingNode):
    raise TypeError(
        f"Expected {schema['type']}, got {node.id} {str(node.start_mark).lstrip()}"
    )

  additional_allowed: bool = schema.get("additionalProperties", False) != False
  additional_type: t.Union[dict, bool] = (
    schema.get("additionalProperties") if additional_allowed
    else {}
  )
  properties: dict = schema.get("properties", {})
  required: t.List[str] = schema.get("required", [])

  for k in required:
    if k not in [_k.value for _k, _v in node.value]:
      raise TypeError(
          f"Required key {k!r} absent from mapping {str(node.start_mark).lstrip()}"
      )

  for k, v in node.value:
    if k.value in properties:
      lint.extend(lint_document(properties.get(k.value), v))

    elif additional_allowed:
      # 'true' is a way to encode the any type.
      if additional_type == True:
        pass
      else:
        lint.extend(lint_document(additional_type, v))
    else:
      lint.append(
          f"Key {k.value!r} is not allowed by schema {str(node.start_mark).lstrip()}"
      )

  return lint


def lint_sequence(schema, node: Node) -> t.List[str]:
  """"FIXME.

  There aren't sequences we need to lint in the current schema design, punting.

  """

  if schema["type"] != "array" or not isinstance(node, SequenceNode):
    raise TypeError(
      f"Expected {schema['type']}, got {node.id} {str(node.start_mark).lstrip()}"
    )

  lint = []
  subschema = schema.get("items")
  if subschema:
    for item in node.value:
      lint.extend(lint_document(subschema, item))
  return lint


def lint_scalar(schema, node: Node) -> t.List[str]:
  """FIXME.

  The only terminal we care about linting in the current schema is {"type": "string"}.

  """
  if schema["type"] not in ["string", "number"] or not isinstance(node, ScalarNode):
    raise TypeError(
      f"Expected {schema['type']}, got {node.id} {str(node.start_mark).lstrip()}"
    )

  lint = []
  if schema["type"] == "string":
    if not isinstance(node.value, str):
      lint.append(f"Expected string, got {node.id} {str(node.start_mark).lstrip()}")
  else:
    log.info(f"Ignoring unlintable scalar, schema {schema!r} {str(node.start_mark).lstrip()}")

  return lint


def lint_document(schema, node):
  """Lint a document.

  Given a Node within a document (or the root of a document!), return a
  (possibly empty!) list of lint or raise in case of fatal errors.

  """

  if schema == True or schema == {}:
    return []
  elif isinstance(node, MappingNode):
    return lint_mapping(schema, node)
  elif isinstance(node, SequenceNode):
    return lint_sequence(schema, node)
  elif isinstance(node, ScalarNode):
    return lint_scalar(schema, node)
  else:
    return []
