#!/usr/bin/env python3

"""The Ichor VM implementation.

The whole point of Shoggoth is that program executions are checkpointable and restartable. This requires that rather than
using a traditional recursive interpreter which is difficult to snapshot, interpretation in shoggoth occur within a
context (a virtual machine) which DOES have an easily introspected and serialized representation.

"""


from copy import deepcopy
import typing as t
from textwrap import indent

from ichor import isa
from ichor.state import Closure, FunctionRef, Identifier, Module, Function, Type, TypeRef, VariantRef, Variant, Stackframe


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
        clock: int = 0

        print(mod)

        def _error(msg=None):
            # Note this is pretty expensive because we have to snapshot the stack BEFORE we do anything
            # And the stack object isn't immutable or otherwise designed for cheap snapshotting
            raise InterpreterError(mod, deepcopy(stackframe), msg)

        def _debug():
            b = []
            b.append(f"clock {clock}:")
            b.append("  stack:")
            for offset, it in zip(range(0, len(stackframe), 1), stackframe):
                b.append(f"    {offset: <3} {it}")
            b.append(f"  op: {op}")
            print(indent("\n".join(b), "  " * stackframe.depth))


        while True:
            op = mod.codepage[stackframe._ip]
            _debug()
            clock += 1

            match op:
                case isa.IDENTIFIERC(name):
                    if not (name in mod.functions
                            or name in mod.types
                            or any(name in t.constructors for t in mod.types.values())):
                        _error("IDENTIFIERC references unknown entity")

                    stackframe.push(Identifier(name))

                case isa.TYPEREF():
                    id = stackframe.pop()
                    if not isinstance(id, Identifier):
                        _error("TYPEREF consumes an identifier")
                    if not id.name in mod.types:
                        _error("TYPEREF must be given a valid type identifier")

                    stackframe.push(TypeRef(id.name))

                case isa.VARIANTREF():
                    id: Identifier = stackframe.pop()
                    if not isinstance(id, Identifier):
                        _error("VARIANTREF consumes an identifier and a typeref")

                    t: TypeRef = stackframe.pop()
                    if not isinstance(t, TypeRef):
                        _error("VARIANTREF consumes an identifier and a typeref")

                    type = mod.types[t.name]
                    if id.name not in type.constructors:
                        _error(f"VARIANTREF given {id.name!r} which does not name a constructor within {type!r}")

                    stackframe.push(VariantRef(t, id.name))

                case isa.VARIANT(n):
                    armref: VariantRef = stackframe.pop()
                    if not isinstance(armref, VariantRef):
                        _error("VARIANT must be given a valid constructor reference")

                    ctor = mod.types[armref.type.name].constructors[armref.arm]
                    if n != len(ctor):
                        _error("VARIANT given n-args inconsistent with the type constructor")

                    if n > len(stackframe):
                        _error("Stack size violation")

                    # FIXME: Where does type variable to type binding occur?
                    # Certainly needs to be AT LEAST here, where we also need to be doing some typechecking
                    v = Variant(armref.type.name, armref.arm, tuple(stackframe[:n]))
                    stackframe.drop(n)
                    stackframe.push(v)

                case isa.VTEST(n):
                    armref: VariantRef = stackframe.pop()
                    if not isinstance(armref, VariantRef):
                        _error("VTEST must be given a variant reference")

                    inst: Variant = stackframe.pop()
                    if not isinstance(inst, Variant):
                        _error("VTEST must be given an instance of a variant")

                    if inst.type == armref.type.name and inst.variant == armref.arm:
                        stackframe.goto(n)
                        continue

                case isa.GOTO(n):
                    if (n < 0):
                        _error("Illegal branch target")
                    stackframe.goto(n)
                    continue

                case isa.DUP(n):
                    if (n > len(stackframe)):
                        _error("Stack size violation")

                    stackframe.dup(n)

                case isa.ROT(n):
                    if (n > len(stackframe)):
                        _error("Stack size violation")

                    stackframe.rot(n)

                case isa.DROP(n):
                    if (n > len(stackframe)):
                        _error("Stack size violation")

                    stackframe.drop(n)

                case isa.SLOT(n):
                    if (n < 0):
                        _error("SLOT must have a positive reference")
                    if (n > len(stackframe) - 1):
                        _error("SLOT reference out of range")
                    stackframe.slot(n)

                case isa.FUNREF():
                    id = stackframe.pop()
                    if not isinstance(id, Identifier):
                        _error("FUNREF consumes an IDENTIFIER")
                    try:
                        # FIXME: Verify this statically
                        stackframe.push(FunctionRef.parse(id.name))
                    except:
                        _error("Invalid function ref")

                case isa.CALLF(n):
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

                case isa.RETURN(n):
                    if (n > len(stackframe)):
                        _error("Stack size violation")

                    if stackframe.depth == 0:
                        return stackframe[:n]

                    if (len(stackframe._fun.returns) != n):
                        _error("Signature violation")

                    stackframe = stackframe.ret(n)
                    continue

                case isa.CLOSUREF(n):
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
                        stackframe[:n]
                    )
                    stackframe.drop(n)
                    stackframe.push(c)

                case isa.CLOSUREC(n):
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
                        stackframe[:n] + c.frag
                    )
                    stackframe.drop(n)
                    stackframe.push(c)

                case isa.CALLC(n):
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
