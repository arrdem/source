#!/usr/bin/env python3

"""The Ichor VM implementation.

The whole point of Shoggoth is that program executions are checkpointable and restartable. This requires that rather than
using a traditional recursive interpreter which is difficult to snapshot, interpretation in shoggoth occur within a
context (a virtual machine) which DOES have an easily introspected and serialized representation.

"""


from copy import deepcopy

from ichor.isa import Opcode
from ichor.typing import Closure, FunctionRef, Identifier


def rotate(l):
    return [l[-1]] + l[:-1]


class Stackframe(object):
    def __init__(self, stack=None, name=None, ip=None, parent=None, depth=0):
        self.stack = stack or []
        self.name = name or ";unknown;;"
        self.ip = ip or 0
        self.parent = parent
        self.depth = depth

    def push(self, obj):
        self.stack.insert(0, obj)

    def pop(self):
        return self.stack.pop(0)

    def call(self, signature: FunctionRef, ip) -> "Stackframe":
        self.ip += 1
        nargs = len(signature.args)
        args, self.stack = self.stack[:nargs], self.stack[nargs:]
        return Stackframe(
            stack=args,
            name=signature.raw,
            ip=ip,
            parent=self,
            depth=self.depth+1
        )

    def ret(self, nargs) -> "Stackframe":
        self.parent.stack = self.stack[:nargs] + self.parent.stack
        return self.parent

    def dup(self, nargs):
        self.stack = self.stack[:nargs] + self.stack

    def drop(self, nargs):
        self.stack = self.stack[nargs:]

    def rot(self, nargs):
        self.stack = rotate(self.stack[:nargs]) + self.stack[nargs:]

    def __getitem__(self, key):
        return self.stack.__getitem__(key)

    def __len__(self):
        return len(self.stack)


class InterpreterError(Exception):
    """An error raised by the interpreter when something goes awry."""

    def __init__(self, module, stack, message=None):
        self.module = module
        self.stack = stack
        super().__init__(message)


class Interpreter(object):
    """A shit simple instruction pointer based interpreter."""
    def __init__(self, bootstrap_module):
        self.bootstrap = bootstrap_module

    def run(self, opcodes, stack=[]):
        """Directly interpret some opcodes in the configured environment."""

        stackframe = Stackframe(stack=stack)
        mod = self.bootstrap.copy()
        stackframe.ip = mod.functions[mod.define_function(";<main>;;", opcodes)]

        print(mod)

        def _error(msg=None):
            # Note this is pretty expensive because we have to snapshot the stack BEFORE we do anything
            # And the stack object isn't immutable or otherwise designed for cheap snapshotting
            raise InterpreterError(mod, deepcopy(stackframe), msg)

        while True:
            op = mod.opcodes[stackframe.ip]
            print("{0}{1: <50} {2}: {3}".format("  " * stackframe.depth, str(stackframe.stack), stackframe.ip, op))

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
                        stackframe.ip = target
                        continue

                case Opcode.GOTO(n):
                    if (n < 0):
                        _error("Illegal branch target")

                    stackframe.ip = n
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
                    if (n > len(stackframe.stack) - 1):
                        _error("SLOT reference out of range")
                    stackframe.push(stackframe.stack[len(stackframe) - n - 1])

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
                    if n != len(sig.args):
                        _error("CALLF target violation; argument count missmatch")
                    if n > len(stackframe):
                        _error("Stack size violation")

                    try:
                        ip = mod.functions[sig.raw]
                    except KeyError:
                        _error("Unknown target")

                    stackframe = stackframe.call(sig, ip)
                    continue

                case Opcode.RETURN(n):
                    if (n > len(stackframe)):
                        _error("Stack size violation")

                    if stackframe.depth == 0:
                        return stackframe[:n]

                    sig = FunctionRef.parse(stackframe.name)
                    if (len(sig.ret) != n):
                        _error("Signature violation")

                    stackframe = stackframe.ret(n)
                    continue

                case Opcode.CLOSUREF(n):
                    sig = stackframe.pop()
                    if not isinstance(sig, FunctionRef):
                        _error("CLOSUREF requires a funref at top of stack")
                    if not n <= len(sig.args):
                        _error("CLOSUREF target violation; too many parameters provided")
                    if n > len(stackframe):
                        _error("Stack size violation")

                    c = Closure(
                        sig,
                        stackframe.stack[:n]
                    )
                    stackframe.drop(n)
                    stackframe.push(c)

                case Opcode.CLOSUREC(n):
                    c = stackframe.pop()
                    if not isinstance(c, Closure):
                        _error("CLOSUREC requires a closure at top of stack")
                    if n + len(c.frag) > len(c.funref.args):
                        _error("CLOSUREC target violation; too many parameters provided")
                    if n > len(stackframe):
                        _error("Stack size violation")

                    c = Closure(
                        c.funref,
                        stackframe.stack[:n] + c.frag
                    )
                    stackframe.drop(n)
                    stackframe.push(c)

                case Opcode.CALLC(n):
                    c = stackframe.pop()
                    if not isinstance(c, Closure):
                        _error("CALLC requires a closure at top of stack")
                    if n + len(c.frag) != len(c.funref.args):
                        _error("CALLC target vionation; argument count missmatch")
                    if n > len(stackframe):
                        _error("Stack size violation")

                    # Extract the function signature
                    sig = c.funref

                    # Push the closure's stack fragment
                    stackframe.stack = c.frag + stackframe.stack

                    # Perform a "normal" funref call
                    try:
                        ip = mod.functions[sig.raw]
                    except KeyError:
                        _error("Unknown target")

                    stackframe = stackframe.call(sig, ip)
                    continue

                case _:
                    raise Exception(f"Unhandled interpreter state {op}")

            stackframe.ip += 1
