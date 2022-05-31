#!/usr/bin/env python3

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


import sys


assert sys.version_info > (3, 10, 0), "`match` support is required"

from copy import deepcopy

from .isa import FunctionRef, Opcode


def rotate(l):
    return [l[-1]] + l[:-1]


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

    def call(self, signature: FunctionRef, ip):
        print(signature)
        nargs = len(signature.args)
        args, self.stack = self.stack[:nargs], self.stack[nargs:]
        return Stackframe(
                stack=args,
                name=signature.raw,
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
        mod.define_function(";<entry>;;", opcodes)
        stack.ip = mod.functions[";<entry>;;"]

        def _error(msg=None):
            # Note this is pretty expensive because we have to snapshot the stack BEFORE we do anything
            # And the stack object isn't immutable or otherwise designed for cheap snapshotting
            raise InterpreterError(mod, deepcopy(stack), msg)

        while True:
            op = mod.opcodes[stack.ip]
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

                    if stack.parent:
                        sig = FunctionRef.parse(stack.name)
                        if (len(sig.ret) != n):
                            _error("Signature violation")

                        stack = stack.ret(n)
                    else:
                        return stack[:n]

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
                    if not n == len(sig.args):
                        _error("CALLF target violation; not enough arguments provided")
                    if n > len(stack):
                        _error("Stack size violation")

                    try:
                        ip = mod.functions[sig.raw]
                    except KeyError:
                        _error("Unknown target")

                    stack = stack.call(sig, ip)
                    continue

                case _:
                    raise Exception(f"Unhandled interpreter state {op}")

            stack.ip += 1
