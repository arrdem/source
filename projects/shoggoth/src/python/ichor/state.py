#!/usr/bin/env python3

"""The core VM/interpreter model."""

import typing as t

from ichor.isa import Opcode

from pyrsistent import pdeque, PDeque
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
NAME: /[^;,:⊢(){}|]+/
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
    name: str

    @classmethod
    def parse(cls, raw: str):
        return cls(raw)


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
        constraints, name, args, rets = FUNC.parse(name)
        # FIXME: Constraints probably needs some massaging
        # FIXME: Need to get typevars from somewhere
        # They both probably live in the same list
        return cls(name, args, rets, instructions, typeconstraints=constraints)

    @property
    def signature(self):
        # FIXME: This should be more meaningful - likely including a type and code fingerprint
        return f"{self.name};{len(self.arguments)};{len(self.returns)}"


class TypeT(FuncT):
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



TYPE = Lark(GRAMMAR, start="var", parser='lalr', transformer=TypeT())


class TypeRef(t.NamedTuple):
    name: str


class VariantRef(t.NamedTuple):
    type: TypeRef
    arm: str


class Type(t.NamedTuple):
    name: str
    constructors: t.Dict[str, t.List[str]]
    typevars: t.List[t.Any] = []
    typeconstraints: t.List[t.Any] = []
    metadata: dict = {}

    @classmethod
    def build(cls, name: str):
        constraints, name, arms = TYPE.parse(name)
        # FIXME: Constraints probably needs some massaging
        # FIXME: Need to get typevars from somewhere
        # They both probably live in the same list
        return cls(name, dict(arms), typeconstraints=constraints)

    @property
    def signature(self):
        return self.name


class Variant(t.NamedTuple):
    type: str
    variant: str
    fields: t.Tuple


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
    functions: t.Dict[str, Function] = {}
    labels: t.Dict[str, int] = {}
    codepage: list = []
    types: t.Dict[str, Type] = {}
    constants: dict = {}

    def copy(self) -> "Module":
        return Module(
            self.functions.copy(),
            self.labels.copy(),
            self.codepage.copy(),
            self.types.copy(),
            self.constants.copy(),
        )

    @staticmethod
    def translate(start: int, end: int, i: Opcode):
        # FIXME: Consolidate bounds checks somehow
        match i:
            case Opcode.VTEST(t):
                d = t + start
                assert start <= d < end
                return Opcode.VTEST(d)

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
        func = Function.build(name, opcodes)
        self.functions[func.signature] = func
        self.labels[func.signature] = start = len(self.codepage)
        for op in opcodes:
            self.codepage.append(self.translate(start, start + len(opcodes), op))
        return func.signature

    def define_type(self, name):
        type = Type.build(name)
        self.types[type.signature] = type
        return type.signature

    def __str__(self):
        b = []
        b.append("types:")
        for sig, type in self.types.items():
            b.append(f"  {sig!r}:")
            b.append(f"    name: {type.name}")
            b.append(f"    typeconstraints: {type.typeconstraints}")
            b.append(f"    arms:")
            for arm in type.constructors:
                b.append(f"    - {arm}")

        b.append("functions:")
        for sig, fun in self.functions.items():
            b.append(f"  {sig!r}:")
            b.append(f"    name: {fun.name}")
            b.append(f"    typeconstraints: {fun.typeconstraints}")
            b.append(f"    arguments: {fun.arguments}")
            b.append(f"    returns: {fun.returns}")
            b.append(f"    ip: {self.labels[fun.signature]}")

        b.append("codepage:")
        marks = {v: k for k, v in self.labels.items()}
        for i, o in zip(range(1<<64), self.codepage):
            if(i in marks):
                b.append(f"  {marks[i]!r}:")
            b.append(f"  {i: >10}: {o}")
        return "\n".join(b)


def rotate(l):
    return [l[-1]] + l[:-1]


class Stackframe(object):
    def __init__(self,
                 fun: Function,
                 ip: int,
                 stack: t.Optional[t.List[t.Any]] = None,
                 parent: t.Optional["Stackframe"] = None):
        self._fun = fun
        self._ip = ip
        self._stack: t.List = stack or []
        self._parent = parent

    def push(self, obj):
        self._stack.append(obj)

    def pop(self):
        return self._stack.pop()

    def dup(self, nargs):
        self._stack.extend(self._stack[-nargs:])

    def drop(self, nargs):
        self._stack = self._stack[:-nargs]

    def rot(self, nargs):
        self._stack[nargs:].extend(rotate(self._stack[:nargs]))

    def slot(self, n):
        self.push(self._stack[n])

    def call(self, fun: Function, ip) -> "Stackframe":
        assert isinstance(fun, Function)
        assert isinstance(ip, int)
        self._ip += 1
        nargs = len(fun.arguments)
        args, self._stack = self._stack[:nargs], self._stack[nargs:]
        return Stackframe(
            fun,
            ip,
            stack=args,
            parent=self,
        )

    def ret(self, nargs) -> "Stackframe":
        assert nargs >= 0
        assert isinstance(self._parent, Stackframe)
        self._parent._stack.extend(self._stack[:nargs])
        return self._parent

    def goto(self, target: int):
        self._ip = target

    @property
    def depth(self):
        if self._parent == None:
            return 0
        else:
            return self._parent.depth + 1

    def __getitem__(self, key):
        return self._stack.__getitem__(key)

    def __len__(self):
        return len(self._stack)

    def __iter__(self):
        return iter(self._stack)
