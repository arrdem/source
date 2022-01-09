"""The shogoth reader."""


from typing import Any
from shogoth.parser import parse

from lark import Tree, Token
from lark import Lark, Transformer, v_args

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
        return ["read-eval", ["symbol", x]]

    def keyword(self, x):
        return ["read-eval", ["keyword", x]]

    def _read(self, tree: Tree) -> Any:
        match tree:
          case Tree(Token('RULE', 'expr'), children):
            return self._read(children[0])

          case Tree(Token('RULE', 'plist'), children):
            return [self._read(c) for c in children]

          case Tree(Token('RULE', 'blist'), children):
            return [self._read(c) for c in children]

          case Tree(Token('RULE', 'mapping'), children):
            return dict(self._read(c) for c in children)

          case Tree(Token('RULE', 'kv'), [k, v]):
            return (self._read(k), self._read(v))

          case Tree(Token('RULE', 'atom'), [a]):
            return self._read(a)

          case Token('INT', x):
            return int(x)

          case Token('FLOAT', x):
            return float(x)

          case Token('KEYWORD', x):
            return self.keyword(x)

          case Token('SYMBOL', x):
            return self.symbol(x)

          case _:
            return tree

    def read(self, buffer):
        return self._read(self._parse(buffer))
