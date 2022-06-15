#!/usr/bin/env python3

"""The Ichor VM implementation.

The whole point of Shoggoth is that program executions are checkpointable and restartable. This requires that rather than
using a traditional recursive interpreter which is difficult to snapshot, interpretation in shoggoth occur within a
context (a virtual machine) which DOES have an easily introspected and serialized representation.

"""


from copy import deepcopy
import typing as t

from ichor.isa import Opcode
from ichor.state import Closure, FunctionRef, Identifier, Module, Function


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
        self._stack = stack or []
        self._parent = parent

    def push(self, obj):
        self._stack.insert(0, obj)

    def pop(self):
        return self._stack.pop(0)

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
        self._parent._stack = self._stack[:nargs] + self._parent._stack
        return self._parent

    def dup(self, nargs):
        self._stack = self._stack[:nargs] + self._stack

    def drop(self, nargs):
        self._stack = self._stack[nargs:]

    def rot(self, nargs):
        self._stack = rotate(self._stack[:nargs]) + self._stack[nargs:]

    def slot(self, n):
        self.push(self._stack[len(self) - n - 1])

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


class InterpreterError(Exception):
    """An error raised by the interpreter when something goes awry."""

    def __init__(self, module, stack, message=None):
        self.module = module
        self.stack = stack
        super().__init__(message)


class Interpreter(object):
    """A shit simple instruction pointer based interpreter."""
    def __init__(self, bootstrap_module: Module):
        self.bootstrap = bootstrap_module

    def run(self, opcodes, stack=[]):
        """Directly interpret some opcodes in the configured environment."""

        mod = self.bootstrap.copy()
        main = mod.define_function(";<main>;;", opcodes)
        main_fun = mod.functions[main]
        main_ip = mod.labels[main]
        stackframe = Stackframe(main_fun, main_ip, stack)

        print(mod)

        def _error(msg=None):
            # Note this is pretty expensive because we have to snapshot the stack BEFORE we do anything
            # And the stack object isn't immutable or otherwise designed for cheap snapshotting
            raise InterpreterError(mod, deepcopy(stackframe), msg)

        while True:
            op = mod.codepage[stackframe._ip]
            print("{0}{1: <50} {2}: {3}".format("  " * stackframe.depth, str(stackframe._stack), stackframe._ip, op))

            match op:
                case Opcode.TRUE():
                    stackframe.push(True)

                case Opcode.FALSE():
                    stackframe.push(False)

                case Opcode.IF(target):
                    if len(stackframe) < 1:
                        _error("Stack size violation")

                    val = stackframe.pop()
                    if val not in [True, False]:
                        _error("Type violation")

                    if val is False:
                        stackframe.goto(target)
                        continue

                case Opcode.GOTO(n):
                    if (n < 0):
                        _error("Illegal branch target")
                    stackframe.goto(n)
                    continue

                case Opcode.DUP(n):
                    if (n > len(stackframe)):
                        _error("Stack size violation")

                    stackframe.dup(n)

                case Opcode.ROT(n):
                    if (n > len(stackframe)):
                        _error("Stack size violation")

                    stackframe.rot(n)

                case Opcode.DROP(n):
                    if (n > len(stackframe)):
                        _error("Stack size violation")

                    stackframe.drop(n)

                case Opcode.SLOT(n):
                    if (n < 0):
                        _error("SLOT must have a positive reference")
                    if (n > len(stackframe) - 1):
                        _error("SLOT reference out of range")
                    stackframe.slot(n)

                case Opcode.IDENTIFIERC(name):
                    if not (name in mod.functions or name in mod.types):
                        _error("IDENTIFIERC references unknown entity")

                    stackframe.push(Identifier(name))

                case Opcode.FUNREF():
                    id = stackframe.pop()
                    if not isinstance(id, Identifier):
                        _error("FUNREF consumes an IDENTIFIER")
                    try:
                        # FIXME: Verify this statically
                        stackframe.push(FunctionRef.parse(id.name))
                    except:
                        _error("Invalid function ref")

                case Opcode.CALLF(n):
                    sig = stackframe.pop()
                    if not isinstance(sig, FunctionRef):
                        _error("CALLF requires a funref at top of stack")
                    fun = mod.functions[sig.name]
                    if n != len(fun.arguments):
                        _error("CALLF target violation; argument count missmatch")
                    if n > len(stackframe):
                        _error("Stack size violation")

                    try:
                        ip = mod.labels[fun.signature]
                    except KeyError:
                        _error("Unknown target")

                    stackframe = stackframe.call(fun, ip)
                    continue

                case Opcode.RETURN(n):
                    if (n > len(stackframe)):
                        _error("Stack size violation")

                    if stackframe.depth == 0:
                        return stackframe[:n]

                    if (len(stackframe._fun.returns) != n):
                        _error("Signature violation")

                    stackframe = stackframe.ret(n)
                    continue

                case Opcode.CLOSUREF(n):
                    sig = stackframe.pop()
                    if not isinstance(sig, FunctionRef):
                        _error("CLOSUREF requires a funref at top of stack")
                    fun = mod.functions[sig.name]
                    if not n <= len(fun.arguments):
                        _error("CLOSUREF target violation; too many parameters provided")
                    if n > len(stackframe):
                        _error("Stack size violation")

                    c = Closure(
                        sig,
                        stackframe._stack[:n]
                    )
                    stackframe.drop(n)
                    stackframe.push(c)

                case Opcode.CLOSUREC(n):
                    c = stackframe.pop()
                    if not isinstance(c, Closure):
                        _error("CLOSUREC requires a closure at top of stack")
                    fun = mod.functions[c.funref.name]
                    if n + len(c.frag) > len(fun.arguments):
                        _error("CLOSUREC target violation; too many parameters provided")
                    if n > len(stackframe):
                        _error("Stack size violation")

                    c = Closure(
                        c.funref,
                        stackframe._stack[:n] + c.frag
                    )
                    stackframe.drop(n)
                    stackframe.push(c)

                case Opcode.CALLC(n):
                    c = stackframe.pop()
                    if not isinstance(c, Closure):
                        _error("CALLC requires a closure at top of stack")
                    fun = mod.functions[c.funref.name]
                    if n + len(c.frag) != len(fun.arguments):
                        _error("CALLC target vionation; argument count missmatch")
                    if n > len(stackframe):
                        _error("Stack size violation")

                    # Extract the function signature

                    # Push the closure's stack fragment
                    stackframe._stack = c.frag + stackframe._stack

                    # Perform a "normal" funref call
                    try:
                        ip = mod.labels[fun.signature]
                    except KeyError:
                        _error("Unknown target")

                    stackframe = stackframe.call(fun, ip)
                    continue

                case _:
                    raise Exception(f"Unhandled interpreter state {op}")

            stackframe._ip += 1
