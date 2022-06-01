#!/usr/bin/env python3

"""The Ichor VM implementation.

The whole point of Shoggoth is that program executions are checkpointable and restartable. This requires that rather than
using a traditional recursive interpreter which is difficult to snapshot, interpretation in shoggoth occur within a
context (a virtual machine) which DOES have an easily introspected and serialized representation.

"""


import sys


assert sys.version_info > (3, 10, 0), "`match` support is required"

from copy import deepcopy

from .isa import Closure, FunctionRef, Opcode


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

    def call(self, signature: FunctionRef, ip):
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

    def ret(self, nargs):
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

        stack = Stackframe(stack=stack)
        mod = self.bootstrap.copy()
        stack.ip = mod.functions[mod.define_function(";<main>;;", opcodes)]

        print(mod)

        def _error(msg=None):
            # Note this is pretty expensive because we have to snapshot the stack BEFORE we do anything
            # And the stack object isn't immutable or otherwise designed for cheap snapshotting
            raise InterpreterError(mod, deepcopy(stack), msg)

        while True:
            op = mod.opcodes[stack.ip]
            print("{0}{1: <50} {2}: {3}".format("  " * stack.depth, str(stack.stack), stack.ip, op))

            match op:
                case Opcode.TRUE():
                    stack.push(True)

                case Opcode.FALSE():
                    stack.push(False)

                case Opcode.IF(target):
                    if len(stack) < 1:
                        _error("Stack size violation")

                    val = stack.pop()
                    if val not in [True, False]:
                        _error("Type violation")

                    if val is False:
                        stack.ip = target
                        continue

                case Opcode.DUP(n):
                    if (n > len(stack)):
                        _error("Stack size violation")

                    stack.dup(n)

                case Opcode.ROT(n):
                    if (n > len(stack)):
                        _error("Stack size violation")

                    stack.rot(n)

                case Opcode.DROP(n):
                    if (n > len(stack)):
                        _error("Stack size violation")

                    stack.drop(n)

                case Opcode.CALLS(dest):
                    try:
                        sig = FunctionRef.parse(dest)
                    except:
                        _error("Invalid target")

                    try:
                        ip = mod.functions[dest]
                    except KeyError:
                        _error("Unknown target")

                    stack = stack.call(sig, ip)
                    continue

                case Opcode.RETURN(n):
                    if (n > len(stack)):
                        _error("Stack size violation")

                    if stack.depth == 0:
                        return stack[:n]

                    sig = FunctionRef.parse(stack.name)
                    if (len(sig.ret) != n):
                        _error("Signature violation")

                    stack = stack.ret(n)
                    continue

                case Opcode.GOTO(n, _):
                    if (n < 0):
                        _error("Illegal branch target")

                    stack.ip = n
                    continue

                case Opcode.FUNREF(funref):
                    try:
                        # FIXME: Verify this statically
                        stack.push(FunctionRef.parse(funref))
                    except:
                        _error("Invalid function ref")

                case Opcode.CALLF(n):
                    sig = stack.pop()
                    if not isinstance(sig, FunctionRef):
                        _error("CALLF requires a funref at top of stack")
                    if n != len(sig.args):
                        _error("CALLF target violation; argument count missmatch")
                    if n > len(stack):
                        _error("Stack size violation")

                    try:
                        ip = mod.functions[sig.raw]
                    except KeyError:
                        _error("Unknown target")

                    stack = stack.call(sig, ip)
                    continue

                case Opcode.CLOSUREF(n):
                    sig = stack.pop()
                    if not isinstance(sig, FunctionRef):
                        _error("CLOSUREF requires a funref at top of stack")
                    if not n <= len(sig.args):
                        _error("CLOSUREF target violation; too many parameters provided")
                    if n > len(stack):
                        _error("Stack size violation")

                    c = Closure(
                        sig,
                        stack.stack[:n]
                    )
                    stack.drop(n)
                    stack.push(c)

                case Opcode.CLOSUREC(n):
                    c = stack.pop()
                    if not isinstance(c, Closure):
                        _error("CLOSUREC requires a closure at top of stack")
                    if n + len(c.frag) > len(c.funref.args):
                        _error("CLOSUREC target violation; too many parameters provided")
                    if n > len(stack):
                        _error("Stack size violation")

                    c = Closure(
                        c.funref,
                        stack.stack[:n] + c.frag
                    )
                    stack.drop(n)
                    stack.push(c)

                case Opcode.CALLC(n):
                    c = stack.pop()
                    if not isinstance(c, Closure):
                        _error("CALLC requires a closure at top of stack")
                    if n + len(c.frag) != len(c.funref.args):
                        _error("CALLC target vionation; argument count missmatch")
                    if n > len(stack):
                        _error("Stack size vionation")

                    # Extract the function signature
                    sig = c.funref

                    # Push the closure's stack fragment
                    stack.stack = c.frag + stack.stack

                    # Perform a "normal" funref call
                    try:
                        ip = mod.functions[sig.raw]
                    except KeyError:
                        _error("Unknown target")

                    stack = stack.call(sig, ip)
                    continue


                case _:
                    raise Exception(f"Unhandled interpreter state {op}")

            stack.ip += 1
