# YAML Schema

A library that implements some amount of jsonschema validation against YAML document ASTs.

Unlike other JSON-schema validation tools which give document path relative errors, this approach allows for line & file errors more appropriate to user-facing tools.
yamlschema [(PyPi)](https://pypi.org/project/yamlschema/) [(Github)](https://github.com/Brightmd/yamlschema) [(source)](https://github.com/Brightmd/yamlschema/blob/master/yamlschema/lib.py) just loads the YAML document fully and punts directly to jsonschema; making it difficult-to-impossible to map errors back to source locations.

## API Overview

### `yamlschema.LintRecord(level, node, schema, message)`

LintRecords are what linting produces.
Each LintRecord contains the YAML AST node which failed validation, the schema it failed to validate against, and some metadata.

`level` is a `LintLevel` which attempts to explain what "kind" of error this piece of lint represents.
For instance `LintLevel.MISSING` encodes missing `properties`.
`LintLevel.MISSMATCH` encodes type mismatches.
`LintLevel.UNEXPECTED` encodes unexpected/disallowed keys and other errors.

### `yamlschema.YamlLinter(schema)`

The linter itself is implemented as a class with a variety of instance methods; allowing the linter to be hacked by users much in the same way that JSON encodiers and decoders can be hacked.

The linter "interface" consists of `__init__(schema: dict)`; being a loaded JSON schema as a dict tree and `lint_document(schema, node) -> Iterable[LintRecord]` which initiates the recursive linting.

The reference implementation of the linter recursively calls `lint_document` on every sub-structure in the document.

### `yamlschema.lint_file(schema, path, cls=YamlLinter)`

As conveniences, yamlschema gives you a couple entrypoints that handle constructing the linter class, using `yaml.compose()` to get an AST and starting linting for you.
`lint_file` and `lint_buffer` respectively allow the user to either bring a file path or a string of YAML.

## Example

``` python-console
>>> from yamlschema import lint_buffer
>>> list(lint_buffer({"type": "integer"}, "---\n1.0"))
[
  LintRecord(
    level=<LintLevel.MISSMATCH: 2>,
    node=ScalarNode(tag='tag:yaml.org,2002:float', value='1.0'),
    schema={'type': 'integer'},
    message="Expected an integer, got a 'tag:yaml.org,2002:float'"
  )
]
```
