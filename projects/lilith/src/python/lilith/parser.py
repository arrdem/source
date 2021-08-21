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


class Block(t.NamedTuple):
    tag: str
    args: Args
    body_lines: list

    @property
    def body(self):
        return "\n".join(self.body_lines)


class TreeToTuples(lark.Transformer):
    def atom(self, args):
        return args[0]

    def expr(self, args):
        return args[0]

    def args(self, args):
        _args = [args[0].value]
        if len(args) == 2:
            _args = _args + args[1]
        return _args

    def kwargs(self, args):
        d = {}
        key, val = args[0:2]
        if len(args) == 3:
            d.update(args[2])
        d[key.value] = val.value
        return d

    def _args_kwargs(self, args):
        return lark.Tree('args', (args[0], args[1]))

    def _args(self, args):
        return lark.Tree('args', (args[0], {}))

    def _kwargs(self, args):
        return lark.Tree('args', ([], args[0]))

    def arguments(self, args):
        return args

    def header(self, args):
        print("Header", args)
        tag = args[0]
        arguments = args[1] if len(args) > 1 else ([], {})
        body = []

        return Block(tag, Args(*arguments), body)


def parser_with_transformer(grammar, start="header"):
    return lark.Lark(grammar,
                     start=start,
                     parser='lalr',
                     transformer=TreeToTuples())


def shotgun_parse(buff: str) -> t.List[object]:
    def _parse():
        block = None
        for line in buff.splitlines():
            if line.startswith("!"):
                if block:
                    yield block
                block = [line]
            else:
                block.append(line)
        if block:
            yield block

    return list(_parse())
