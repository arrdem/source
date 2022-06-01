"""A quick and dirty parser for Shogoth."""

from typing import Any

from lark import Lark


PARSER = Lark(r'''
start: expr
expr: plist | blist | mapping | quote | atom

plist: "(" expr* ")" // paren list
blist: "[" expr* "]"  // brackets list
mapping: "{" kv* "}"
kv: expr expr
quote: "'" expr

atom: keyword | pattern | num | string | true | false | nil | symbol
num: hex | octal | bin | int | float

keyword: ":" SYMBOL
symbol: SYMBOL
SYMBOL: /[^(){}#'"\s]+/

// FIXME: These two don't deal with escapes correctly at all

string: STRING
STRING: /".*?"/

pattern: PATTERN
PATTERN: /\/.*?\//

true: /true/
false: /false/
nil: /nil/

// NOTE: order-prescidence matters here, 0x, 0b, 0o etc. require lookahead

int: INT
INT: /[+-]?[0-9]+/

hex: HEX
HEX: /0x[0-9a-fA-F_]+/

octal: OCTAL
OCTAL: /0o[0-7_]+/

bin: BIN
BIN: /0b[01_]+/

float: FLOAT

COMMENT: /;.*?\n/

%import common.FLOAT  // float
%ignore " "           // Disregard spaces in text
%ignore ","           // Treat commas as whitespace
%ignore COMMENT       // Disregard comments
''', start=["expr"])


def parse(input: str) -> Any:
    '''Parse a string using the shoggoth (lisp) gramar, returning an unmodified tree.'''

    return PARSER.parse(input)
