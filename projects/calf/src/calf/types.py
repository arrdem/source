"""Core types for Calf.

I don't love baking these in, but there's one place to start and there'll be a
considerable amount of bootstrappy nonsense to get through. So just start with
good ol' fashioned types and type aliases.
"""

from typing import *

import pyrsistent as p


class Symbol(NamedTuple):
    name: str
    namespace: Optional[str]

    @classmethod
    def of(cls, name: str, namespace: str = None):
        return cls(name, namespace)


class Keyword(NamedTuple):
    name: str
    namespace: Optional[str]

    @classmethod
    def of(cls, name: str, namespace: str = None):
        return cls(name, namespace)


# FIXME (arrdem 2021-03-20):
#
#   Don't just go out to Pyrsistent for the datatypes. Do something somewhat
#   smarter, especially given the games Pyrsistent is playing around loading
#   ctype implementations for performance. God only knows about correctness tho.

Map = p.PMap
Map.of = staticmethod(p.pmap)

Vector = p.PVector
Vector.of = staticmethod(p.pvector)

Set = p.PSet
Set.of = staticmethod(p.pset)
