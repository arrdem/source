#!/usr/bin/env python3

"""The core VM/interpreter model."""


import typing as t

from ichor.isa import Opcode


class Identifier(t.NamedTuple):
    name: str


class FunctionSignature(t.NamedTuple):
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
