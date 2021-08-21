"""
Variously poor parsing for Lilith.
"""

import typing as t
import re
from importlib.resources import read_text

import lark

GRAMMAR = read_text('lilith', 'grammar.lark')


# !foo[bar]
# !def[name]
# !frag[lang: yaml]
# !end
# all this following tex
class Args(t.NamedTuple):
    positionals: object = []
    kwargs: object = {}


class Apply(t.NamedTuple):
    name: str
    args: Args


class Block(t.NamedTuple):
    app: Apply
    body_lines: list

    @property
    def tag(self):
        return self.app.tag

    @property
    def args(self):
        return self.app.args

    @property
    def body(self):
        return "\n".join(self.body_lines)


class TreeToTuples(lark.Transformer):
    def string(self, args):
        # FIXME (arrdem 2021-08-21):
        #   Gonna have to do escape sequences here
        return args[0].value

    def int(self, args):
        return int(args[0])

    def float(self, args):
        return float(args[0])

    def number(self, args):
        return args[0]

    def word(self, args):
        """args: ['a'] ['a' ['b', 'c', 'd']]"""
        return ".".join(a.value for a in args)

    def atom(self, args):
        return args[0]

    def expr(self, args):
        return args[0]

    def application(self, args):
        tag = args[0]
        args = args[1] if len(args) > 1 else Args()
        return Apply(tag, args)

    def args(self, args):
        _args = [args[0]]
        if len(args) == 2:
            _args = _args + args[1]
        return _args

    def kwargs(self, args):
        d = {}
        key, val = args[0:2]
        if len(args) == 3:
            d.update(args[2])
        d[key] = val
        return d

    def a_args_kwargs(self, args):
        return Args(args[0], args[1])

    def a_args(self, args):
        return Args(args[0], {})

    def a_kwargs(self, args):
        return Args([], args[0])

    def arguments(self, args):
        return args[0]

    def header(self, args):
        return Block(args[0], [])


def parser_with_transformer(grammar, start="header"):
    return lark.Lark(grammar,
                     start=start,
                     parser='lalr',
                     transformer=TreeToTuples())



def parse_expr(buff: str):
    return parser_with_transformer(GRAMMAR, "expr").parse(buff)


def parse_buffer(buff: str, name: str = "&buff") -> t.List[object]:
    header_parser = parser_with_transformer(GRAMMAR, "header")

    def _parse():
        block = None
        for line in buff.splitlines():
            if line.startswith("!"):
                if block:
                    yield block
                block = header_parser.parse(line)
            elif block:
                block.body_lines.append(line)
            else:
                raise SyntaxError("Buffers must start with a ![] block")
        if block:
            yield block

    return list(_parse())
