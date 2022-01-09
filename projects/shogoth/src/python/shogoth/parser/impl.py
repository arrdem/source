"""A quick and dirty parser for Shogoth."""

from typing import Any

from lark import Lark


PARSER = Lark('''\
start: expr
expr: plist | blist | mapping | quote | atom

plist: "(" expr* ")" // paren list
blist: "[" expr* "]"  // brackets list
mapping: "{" kv* "}"
kv: expr expr
quote: "'" expr

atom: KEYWORD | PATTERN | INT | FLOAT | STRING | TRUE | FALSE | NIL | SYMBOL
KEYWORD: ":" SYMBOL
SYMBOL: /[^(){}#'"\s]+/

// FIXME: These two don't deal with escapes correctly at all
STRING: /".*?"/
PATTERN: /\/.*?\//

TRUE: /true/
FALSE: /false/
NIL: /nil/
INT: /[+-]?[0-9]+/

%import common.FLOAT  // float
%ignore " "           // Disregard spaces in text
%ignore ","           // Treat commas as whitespace
%ignore /;.*/         // Disregard comments
''', start=["expr"])


def parse(input: str) -> Any:
    '''Parse a string using the shogoth (lisp) gramar, returning an unmodified tree.'''

    return PARSER.parse(input)
