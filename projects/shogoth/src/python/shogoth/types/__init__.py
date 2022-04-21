"""The public interface for shogoth's baked-in types."""

from .keyword import Keyword
from .symbol import Symbol

from abc import ABC
from typing import NamedTuple, List, Mapping, Any

from uuid import UUID, uuid4


class TypeVariable(NamedTuple):
    name: str
    id: UUID = uuid4()


class ArrayExpr(NamedTuple):
    child: Any


class SumExpr(NamedTuple):
    children: List[Any]


class ProductExpr(NamedTuple):
    children: Mapping[str, Any]


####################################################################################################
####################################################################################################
####################################################################################################

class Function(NamedTuple):
    """The type of a function; a subset of its signature."""


class FunctionRef(NamedTuple):
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
