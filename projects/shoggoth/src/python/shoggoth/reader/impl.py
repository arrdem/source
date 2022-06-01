#!/usr/bin/env python3

"""The shoggoth reader."""

import sys


assert sys.version_info > (3, 10, 0), "`match` support is required"

import re
from typing import Any

from lark import Token, Tree
from shoggoth.parser import parse
from shoggoth.types import (
    Keyword,
    List,
    Symbol,
    Vec,
)


# Monkeypatching for py3.10 matching
Tree.__match_args__ = ("data", "children")
Token.__match_args__ = ("type", "value")


class Reader(object):
    """An extension of parsing that produces meaningful trees. Can be extended with userland hooks."""

    def __init__(self):
        pass

    def _parse(self, buffer):
        return parse(buffer)

    def symbol(self, x):
        return Symbol(x)

    def keyword(self, x):
        return Keyword(x)

    def pattern(self, x):
        return re.compile(x[1:-1].replace("\\/", "/"))

    def _read(self, tree: Tree) -> Any:
        match tree:
          case Tree(Token("RULE", "expr"), children):
            return self._read(children[0])

          case Tree(Token("RULE", "plist"), children):
            return List([self._read(c) for c in children])

          case Tree(Token("RULE", "blist"), children):
            return Vec([self._read(c) for c in children])

          case Tree(Token("RULE", "mapping"), children):
            return dict(self._read(c) for c in children)

          case Tree(Token("RULE", "kv"), [k, v]):
            return (self._read(k), self._read(v))

          case Tree(Token("RULE", "atom"), [a]):
            return self._read(a)

          case Tree(Token("RULE", "num"), [a]):
            return self._read(a)

          case Token("INT", x):
            return int(x)

          case Token("FLOAT", x):
            return float(x)

          case Token("KEYWORD", x):
            return self.keyword(x)

          case Token("PATTERN", x):
            return self.pattern(x)

          case Token("TRUE", _):
            return True

          case Token("FALSE", _):
            return False

          case Token("NIL", _):
            return None

          # Symbol is very much the catch-all of the grammar
          case Token("SYMBOL", x):
            return self.symbol(x)

          case _:
            return tree

    def read(self, buffer):
        return self._read(self._parse(buffer))
