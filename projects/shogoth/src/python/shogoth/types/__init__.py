"""The public interface for shogoth's baked-in types."""


import typing as t
from uuid import UUID, uuid4


class TypeVariable(t.NamedTuple):
    name: str
    id: UUID = uuid4()


class ArrayExpr(t.NamedTuple):
    child: t.Any


class SumExpr(t.NamedTuple):
    children: t.List[t.Any]


class ProductExpr(t.NamedTuple):
    children: t.Mapping[str, t.Any]


####################################################################################################
####################################################################################################
####################################################################################################

class Function(t.NamedTuple):
    """The type of a function; a subset of its signature."""


class FunctionRef(t.NamedTuple):
    raw: str
    type_params: list
    name: str
    args: list
    ret: list

    @staticmethod
    def parse_list(l):
        return [e for e in l.split(",") if e]

    @classmethod
    def parse(cls, raw: str):
        vars, name, args, ret = raw.split(";")
        return cls(
            raw,
            cls.parse_list(vars),
            name,
            cls.parse_list(args),
            cls.parse_list(ret)
        )


class Closure(t.NamedTuple):
    target: t.Union["Closure", FunctionRef]
    args: t.List[t.Any]


# FIXME (arrdem 2022-05-30):
#   Find a better name for this
class Vec(list):
    pass


class List(list):
    pass
