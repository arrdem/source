#!/usr/bin/env python3.10

"""The Shogoth VM implementation.

The whole point of shogoth is that program executions are checkpointable and restartable. This requires that rather than
using a traditional recursive interpreter which is difficult to snapshot, interpretation in shogoth occur within a
context (a virtual machine) which DOES have an easily introspected and serialized representation.

## The Shogoth VM Architecture


- NOT    [bool] -> [bool]
- IF     [then: addr, else: addr, cond: bool] -> []
- CALL   [procedure, n, ...] -> [...]
- RETURN [n, ...]

"""

from random import Random
from typing import NamedTuple

class Module(NamedTuple):
    opcodes: list = []
    functions: dict = {}
    types: dict = {}
    constants: dict = {}

    rand: Random = Random()

    def copy(self):
        return Module(
            self.opcodes.copy(),
            self.functions.copy(),
            self.types.copy(),
            self.constants.copy(),
        )

    @staticmethod
    def translate(offset: int, i: "Opcode"):
        match i:
            case Opcode.IF(t):
                return Opcode.IF(t + offset)
            case Opcode.GOTO(t, anywhere=False):
                return Opcode.GOTO(t + offset)
            case _:
                return i

    def define_function(self, name, opcodes):
        start = len(self.opcodes)
        self.functions[name] = start
        for op in opcodes:
            self.opcodes.append(self.translate(start, op))
        return name


class Opcode:
    class TRUE(NamedTuple):
        """() -> (bool)
        Push the constant TRUE onto the stack.
        """

    class FALSE(NamedTuple):
        """() -> (bool)
        Push the constant FALSE onto the stack.
        """

    class IF(NamedTuple):
        """(bool) -> ()
        Branch to another point if the top item of the stack is TRUE.
        Otherwise fall through.
        """

        target: int

    # not, and, or, xor etc. can all be functions given if.

    class DUP(NamedTuple):
        """(A, B, ...) -> (A, B, ...)
        Duplicate the top N items of the stack.
        """

        nargs: int = 1

    class ROT(NamedTuple):
        """(A, B, ... Z) -> (Z, A, B, ...)
        Rotate the top N elements of the stack.
        """

        nargs: int = 2

    class DROP(NamedTuple):
        """(*) -> ()
        Drop the top N items of the stack.
        """

        nargs: int = 1

    class CALL(NamedTuple):
        """(*) -> ()
        Branch to `target` pushing the current point onto the call stack.
        The callee will see a stack containg only the provided `nargs`.
        A subsequent RETURN will return execution to the next point.
        """

        funref: str

    class RETURN(NamedTuple):
        """(*) -> ()
        Return to the source of the last `CALL`.
        The returnee will see the top `nargs` values of the present stack appended to theirs.
        All other values on the stack will be discarded.
        If the call stack is empty, `RETURN` will exit the interpreter.
        """

        nargs: int

    class GOTO(NamedTuple):
        """() -> ()
        Branch to another point within the same bytecode segment.
        """

        target: int
        anywhere: bool = False

    class STRUCT(NamedTuple):
        """(*) -> (T)
        Consume the top N items of the stack, producing a struct.
        """

        nargs: int
        structref: str

    class FIELD(NamedTuple):
        """(A) -> (B)
        Consume the struct reference at the top of the stack, producing the value of the referenced field.
        """

        fieldref: str


def rotate(l):
    return [l[-1]] + l[:-1]


class FunctionSignature(NamedTuple):
    type_params: list
    name: str
    args: list
    sig: list

    @staticmethod
    def parse_list(l):
        return [e for e in l.split(",") if e]

    @classmethod
    def parse(cls, name: str):
        vars, name, args, sig = name.split(";")
        return cls(
            cls.parse_list(vars),
            name,
            cls.parse_list(args),
            cls.parse_list(sig)
        )


class Stackframe(object):
    def __init__(self, stack=None, name=None, ip=None, parent=None):
        self.stack = stack or []
        self.name = name or ";unknown;;"
        self.ip = ip or 0
        self.parent = parent

    def push(self, obj):
        self.stack.insert(0, obj)

    def pop(self):
        return self.stack.pop(0)

    def call(self, signature, ip):
        nargs = len(signature.args)
        args, self.stack = self.stack[:nargs], self.stack[nargs:]
        return Stackframe(
                stack=args,
                name=signature.name,
                ip=ip,
                parent=self
            )

    def ret(self, nargs):
        self.parent.stack = self.stack[:nargs] + self.parent.stack
        return self.parent

    def dup(self, nargs):
        self.stack = self.stack[:nargs] + self.stack

    def drop(self, nargs):
        self.stack = self.stack[nargs:]

    def rot(self, nargs):
        self.stack = rotate(self.stack[:nargs]) + self.stack[nargs:]


class Interpreter(object):
    def __init__(self, bootstrap_module):
        self.bootstrap = bootstrap_module

    def run(self, opcodes):
        """Directly interpret some opcodes in the configured environment."""

        stack = Stackframe()
        mod = self.bootstrap.copy()
        mod.define_function(";<entry>;;", opcodes)
        stack.ip = mod.functions[";<entry>;;"]

        while True:
            op = mod.opcodes[stack.ip]
            print(stack.ip, op, stack.stack)
            match op:
                case Opcode.TRUE():
                    stack.push(True)

                case Opcode.FALSE():
                    stack.push(False)

                case Opcode.IF(target):
                    if not stack.pop():
                        stack.ip = target
                        continue

                case Opcode.DUP(n):
                    stack.dup(n)

                case Opcode.ROT(n):
                    stack.rot(n)

                case Opcode.DROP(n):
                    stack.drop(n)

                case Opcode.CALL(dest):
                    sig = FunctionSignature.parse(dest)
                    ip = mod.functions[dest]
                    stack = stack.call(sig, ip)
                    continue

                case Opcode.RETURN(n):
                    if stack.parent:
                        stack = stack.ret(n)
                    else:
                        return stack.stack[:n]

                case Opcode.GOTO(n, _):
                    stack.ip = n
                    continue

                case _:
                    raise Exception(f"Unhandled interpreter state {op}")

            stack.ip += 1


BOOTSTRAP = Module()

NOT = ";/lang/shogoth/v0/bootstrap/not;bool;bool"
BOOTSTRAP.define_function(
    NOT,
    [
        Opcode.IF(target=3),
        Opcode.FALSE(),
        Opcode.RETURN(1),
        Opcode.TRUE(),
        Opcode.RETURN(1),
    ],
)

OR = ";/lang/shogoth/v0/bootstrap/or;bool,bool;bool"
BOOTSTRAP.define_function(
    OR,
    [
        Opcode.IF(target=3),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        Opcode.IF(target=6),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        Opcode.FALSE(),
        Opcode.RETURN(1)
    ],
)

AND = ";/lang/shogoth/v0/bootstrap/and;bool,bool;bool"
BOOTSTRAP.define_function(
    AND,
    [
        Opcode.IF(target=3),
        Opcode.IF(target=3),
        Opcode.GOTO(target=5),
        Opcode.FALSE(),
        Opcode.RETURN(1),
        Opcode.TRUE(),
        Opcode.RETURN(1),
    ],
)

XOR = ";/lang/shogoth/v0/bootstrap/xor;bool,bool;bool"
BOOTSTRAP.define_function(
    XOR,
    [
        Opcode.DUP(nargs=2),
        # !A && B
        Opcode.CALL(";/lang/shogoth/v0/bootstrap/not;bool;bool"),
        Opcode.CALL(";/lang/shogoth/v0/bootstrap/and;bool,bool;bool"),
        Opcode.IF(target=6),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        # !B && A
        Opcode.ROT(2),
        Opcode.CALL(";/lang/shogoth/v0/bootstrap/not;bool;bool"),
        Opcode.CALL(";/lang/shogoth/v0/bootstrap/and;bool,bool;bool"),
        Opcode.IF(target=12),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        Opcode.FALSE(),
        Opcode.RETURN(1),
    ],
)
