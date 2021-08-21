"""
Variously poor parsing for Lilith.
"""

import typing as t
import re

import lark

class Block(t.NamedTuple):
    tag: str
    args: list
    kwargs: list
    body_lines: list

    @property
    def body(self):
        return "\n".join(self.body_lines)


class TreeToTuples(lark.Transformer):
    def kwargs(self, args):
        d = {}
        key, val = args[0:2]
        if len(args) == 3:
            d.update(args[2])
        d[key.value] = val.value
        return d

    def args(self, args):
        _args = [args[0].value]
        if len(args) == 2:
            _args = _args + args[1]
        return _args

    def header(self, parse_args):
        print("Header", parse_args)
        tag = None
        args = None
        kwargs = None
        body = []

        iargs = iter(parse_args[1])
        tag = parse_args[0]
        v = next(iargs, None)
        if isinstance(v, list):
            args = v
            v = next(iargs, None)
        if isinstance(v, dict):
            kwargs = v

        return Block(tag, args, kwargs, body)


block_grammar = lark.Lark("""
%import common.WORD
%import common.WS
%ignore WS
?start: header

args: WORD ("," args)?
kwargs: WORD ":" WORD ("," kwargs)?
arguments: args "," kwargs | args | kwargs
header: "!" WORD "[" arguments? "]"
""",
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
