#!/usr/bin/env python3

"""The core VM/interpreter model."""


import typing as t

from ichor.isa import Opcode
from lark import Lark, Transformer, v_args, Token


class Identifier(t.NamedTuple):
    name: str


GRAMMAR = r"""
fun: constraints ";" name ";" arguments ";" ret

arguments: (type ","?)*
ret: (type ","?)*
constraints: (constraint ","?)*
constraint: type

var: constraints ";" name ";" arms
arms: (arm ","?)+
arm: name "(" bindings ")"

bindings: (binding ","?)*
binding: name ":" type

type: NAME
name: NAME
NAME: /[^;,:⊢()<>\[\]{}|]+/
"""

class FuncT(Transformer):
    @v_args(inline=True)
    def fun(self, constraints, name, arguments, ret):
        return (constraints, name, arguments, ret)

    def constraints(self, args):
        return (*args,)

    def arguments(self, args):
        return tuple(args)

    def ret(self, args):
        return tuple(args)

    @v_args(inline=True)
    def NAME(self, name: Token):
        return name.value

    @v_args(inline=True)
    def name(self, name):
        return name

    @v_args(inline=True)
    def type(self, name):
        return name


FUNC = Lark(GRAMMAR, start="fun", parser='lalr', transformer=FuncT())


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


class Function(t.NamedTuple):
    name: str
    arguments: t.List[str]
    returns: t.List[str]
    instructions: t.List[Opcode]
    typevars: t.List[t.Any] = []
    typeconstraints: t.List[t.Any] = []
    metadata: dict = {}

    @classmethod
    def build(cls, name: str, instructions: t.List[Opcode]):
        pass


class VarT(FuncT):
    @v_args(inline=True)
    def var(self, constraints, name, arms):
        return (constraints, name, arms)

    @v_args(inline=True)
    def constraint(self, name):
        return name

    def arms(self, arms):
        return tuple(arms)

    def binding(self, binding):
        return tuple(binding)

    def bindings(self, bindings):
        return tuple(bindings)

    @v_args(inline=True)
    def arm(self, name, bindings):
        return (name, bindings)



VAR = Lark(GRAMMAR, start="var", parser='lalr', transformer=VarT())

class Type(t.NamedTuple):
    name: str
    constructors: t.List[t.Tuple[str, t.List[str]]]
    typevars: t.List[t.Any] = []
    typeconstraints: t.List[t.Any] = []
    metadata: dict = {}


class Closure(t.NamedTuple):
    # Note that a closure over a closure is equivalent to a single closure which extends the captured stack fragment, so
    # there's no need for a union here as we can simply convert nested closures.
    funref: FunctionRef
    frag: t.List[t.Any]


class Struct(t.NamedTuple):
    name: str
    type_params: list
    children: t.Mapping[str, t.Any]


class Module(t.NamedTuple):
    codepage: list = []
    functions: dict = {}
    types: dict = {}
    constants: dict = {}

    def copy(self) -> "Module":
        return Module(
            self.codepage.copy(),
            self.functions.copy(),
            self.types.copy(),
            self.constants.copy(),
        )

    @staticmethod
    def translate(start: int, end: int, i: Opcode):
        # FIXME: Consolidate bounds checks somehow
        match i:
            case Opcode.IF(t):
                d = t + start
                assert start <= d < end
                return Opcode.IF(d)

            case Opcode.GOTO(t):
                d = t + start
                assert start <= d < end
                return Opcode.GOTO(d)

            case _:
                return i

    def define_function(self, name, opcodes):
        """Enter a function into module.

        Side-effects the codepage and name table.

        """

        try:
            sig = FunctionRef.parse(name)
            assert sig.name
        except:
            raise ValueError("Illegal name provided")

        start = len(self.codepage)
        self.functions[name] = start
        for op in opcodes:
            self.codepage.append(self.translate(start, start + len(opcodes), op))
        return name

    def define_type(self, name, signature):
        self.types[name] = signature
        return name

    def __str__(self):
        b = []
        marks = {v: k for k, v in self.functions.items()}
        for i, o in zip(range(1<<64), self.codepage):
            if(i in marks):
                b.append(f"{marks[i]}:")
                b.append(f"{i: >10}: {o}")
        return "\n".join(b)
