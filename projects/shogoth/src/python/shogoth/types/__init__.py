"""The public interface for shogoth's baked-in types."""

from .keyword import Keyword
from .symbol import Symbol

from abc import ABC
from typing import NamedTuple, List, Mapping

from uuid import UUID, uuid4


class TypeExpr(ABC):
    """A type expression"""

    bindings: []


class TypeVariable(TypeExpr):
    name: str
    id: UUID = uuid4()


class PrimitiveExpr(object):
    class Nat(TypeExpr): pass
    class N8(Nat): pass
    class N16(Nat): pass
    class N32(Nat): pass
    class N64(Nat): pass
    class N128(Nat): pass
    class N256(Nat): pass
    class N512(Nat): pass

    class Unsigned(TypeExpr): pass
    class U8(Unsigned): pass
    class U16(Unsigned): pass
    class U32(Unsigned): pass
    class U64(Unsigned): pass
    class U128(Unsigned): pass
    class U256(Unsigned): pass
    class U512(): pass

    class Integer(TypeExpr): pass
    class I8(Integer): pass
    class I16(Integer): pass
    class I32(Integer): pass
    class I64(Integer): pass
    class I128(Integer): pass
    class I256(Integer): pass
    class I512(Integer): pass

    class Floating(TypeExpr): pass
    class F8(Floating): pass
    class F16(Floating): pass
    class F32(Floating): pass
    class F64(Floating): pass
    class F128(Floating): pass
    class F256(Floating): pass
    class F512(Floating): pass



class ArrayExpr(TypeExpr):
    child: TypeExpr


class SumExpr(TypeExpr):
    children: List[TypeExpr]


class ProductExpr(TypeExpr):
    children: Mapping[str, TypeExpr]


####################################################################################################
####################################################################################################
####################################################################################################

class Function(NamedTuple):
    """The type of a function; a subset of its signature."""


class FunctionSignature(NamedTuple):
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
