#!/usr/bin/env python3

"""The public interface for shoggoth's baked-in types."""


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
