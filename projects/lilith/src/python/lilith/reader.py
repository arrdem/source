"""
Lilith's reader takes parsed blocks and applies languages, building a module structure.
"""

import logging
import typing as t
from .parser import Block, Args, parse_buffer
from warnings import warn

log = logging.getLogger(__name__)

class Module(t.NamedTuple):
    name: str
    defs: t.Dict[str, Block]


def read_buffer(buffer: str, name: str = "&buff") -> Module:
    """Read a module out of a string [or file]"""

    m = Module(name, {})
    for block in parse_buffer(buffer, name):
        if block.app.name == "def":
            if len(block.args.positionals) == 2:
                def_name, expr = block.args.positionals
                m.defs[def_name] = Block(expr, block.body_lines)
            else:
                raise SyntaxError("!def[<name>, <expr>; <kwargs>] <body>")

            if block.args.kwargs:
                warn("!def[<kwargs>] are ignored")

        else:
            raise SyntaxError(f"Unsupported block !{block.tag}[..]")

    return m


def read_file(path: str):
    """Read a module out of a file."""

    with open(path) as fp:
        return read_buffer(fp.read(), path)
