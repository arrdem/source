#!/usr/bin/env python3

"""The implementation of Shogoth's lexical analyzer."""

from abc import ABC
from dataclasses import dataclass
import typing as t

from shoggoth.types import (
    Keyword,
    List,
    Symbol,
    Vec,
)


@dataclass
class Namespace:
    name: Symbol
    mappings: t.Mapping[Symbol, t.Any]

    def resolve(self, name: Symbol) -> t.Optional[Symbol]:
        if name in self.mappings:
            return name.qualify(self.name.name)

    def __contains__(self, item):
        return item.namespace == self.name and item.unqualified() in self.mappings

    def __getitem__(self, key: Symbol):
        return self.mappings[key.unqualified()]

    def get(self, key: Symbol, default=None):
        if key in self:
            return self[key]
        else:
            return default


class Expr(ABC):
    pass


@dataclass
class ConstExpr(Expr):
    val: t.Any


@dataclass
class ListExpr(Expr):
    children: t.List[t.Any]


@dataclass
class MapExpr(Expr):
    kvs: t.List[t.Tuple[t.Any, t.Any]]


@dataclass
class InvokeExpr(Expr):
    target: Expr
    args: t.List[Expr]
    # FIXME: kwargs/star-args?


@dataclass
class IfExpr(Expr):
    """(if* test then else)"""
    test: Expr
    pos_branch: Expr
    neg_branch: Expr


@dataclass
class LetExpr(Expr):
    """(let* [name binding name2 binding2] body)"""
    bindings: t.List[t.Tuple[Symbol, Expr]]
    body: Expr


@dataclass
class FnExpr(Expr):
    """(fn* args body)"""
    args: t.List[Symbol]
    body: Expr


BOOTSTRAP = "lang.shoggoth.v0.bootstrap"
SPECIALS = Namespace(Symbol(BOOTSTRAP), {
    Symbol("if*"): None,
    Symbol("let*"): None,
    Symbol("fn*"): None,
})


GLOBALS = Namespace(Symbol("lang.shoggoth.v0.core"), {
})


# FIXME: This is really expand... isn't it.
class Analyzer:
    def __init__(self, specials, globals):
        self._specials = specials
        self._globals = globals

    def resolve(self, module, name: Symbol):
        return module.resolve(name) or self._globals.resolve(name) or self._specials.resolve(name)

    def analyze(self, module: Namespace, expr: t.Any):

        def _analyze(e):
            return self.analyze(module, e)

        if isinstance(expr, (int, float, str, Keyword)):
            return ConstExpr(expr)

        if isinstance(expr, Vec):
            return ListExpr([self.analyze(module, e) for e in expr])

        if isinstance(expr, List) and len(expr) > 1 and isinstance(expr[0], Symbol):
            if (target := self.resolve(module, expr[0])):
                match target:
                    case Symbol("if*", BOOTSTRAP):
                        assert len(expr) == 4
                        return IfExpr(_analyze(expr[1]), _analyze(expr[2]), _analyze(expr[3]))

                    case Symbol("let*", BOOTSTRAP):
                        assert len(expr) == 3
                        return LetExpr([(name, _analyze(e)) for name, e in expr[1]], _analyze(expr[2]))

                    case Symbol("fn*", BOOTSTRAP):
                        assert len(expr) == 3
                        return FnExpr(expr[1], _analyze(expr[2]))

                    # FIXME: Macros go here? Or is macroexpansion separate?

                    case _:
                        return InvokeExpr(_analyze(target), [_analyze(e) for e in expr[1:]])


        raise ValueError(f"Unable to analyze {expr!r} ({type(expr)})")
