"""
Lilith's reader takes parsed blocks and applies languages, building a module structure.
"""

import logging
import typing as t
from warnings import warn

from lilith.parser import Block, parse_buffer, Symbol


log = logging.getLogger(__name__)


class Import(t.NamedTuple):
    src: Symbol
    names: t.Dict[Symbol, Symbol]
    wild: bool = False


class Def(object):
    UNSET = object()

    def __init__(self, block, value=UNSET):
        self._block = block
        self._value = value

    def __eq__(self, other):
        return self.block == other.block

    def __repr__(self):
        return f"Def(block={self._block!r}, set={self._value is not self.UNSET})"

    @property
    def block(self):
        return self._block

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class Module(t.NamedTuple):
    name: Symbol
    imports: t.List[Import]
    defs: t.Dict[str, Def]


def read_buffer(buffer: str, name: str = "&buff") -> Module:
    """Read a module out of a string [or file]"""

    m = Module(Symbol(name), [], {})
    for block in parse_buffer(buffer, name):
        if block.app.target == Symbol("def"):
            if len(block.args.positionals) == 2:
                def_name, expr = block.args.positionals
                m.defs[def_name] = Def(Block(expr, block.body_lines))
            else:
                raise SyntaxError("!def[<name>, <expr>; <kwargs>] <body>")

            if block.args.kwargs:
                warn("!def[<kwargs>] are ignored")

        elif block.app.target == Symbol("import"):
            # FIXME (arrdem 2021-08-21):
            #   This doesn't simplify imports as it goes.
            #   Multiple imports from the same source will wind up with multiple importlist entries.
            iname = block.args.positionals[0]
            wild = block.args.kwargs.get(Symbol("wild"), False)
            rename = block.args.kwargs.get(Symbol("as"), {})
            imports = (
                block.args.positionals[1] if len(block.args.positionals) == 2 else []
            )
            m.imports.append(
                Import(iname, {rename.get(i, i): i for i in imports}, wild)
            )

        else:
            raise SyntaxError(f"Unsupported block !{block.tag}[..]")

    return m


def read_file(path: str):
    """Read a module out of a file."""

    with open(path) as fp:
        return read_buffer(fp.read(), path)
