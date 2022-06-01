"""The instruction set for Shogoth."""


import typing as t

from .typing import *


class Opcode:
    ####################################################################################################
    # Logic
    ####################################################################################################
    class TRUE(t.NamedTuple):
        """() -> (bool)
        Push the constant TRUE onto the stack.
        """

    class FALSE(t.NamedTuple):
        """() -> (bool)
        Push the constant FALSE onto the stack.
        """

    class IF(t.NamedTuple):
        """(bool) -> ()
        Branch to another point if the top item of the stack is TRUE.
        Otherwise fall through.
        """

        target: int

    # not, and, or, xor etc. can all be functions given if.

    ####################################################################################################
    # Stack manipulation
    ####################################################################################################
    class DUP(t.NamedTuple):
        """(A, B, ...) -> (A, B, ...)
        Duplicate the top N items of the stack.
        """

        nargs: int = 1

    class ROT(t.NamedTuple):
        """(A, B, ... Z) -> (Z, A, B, ...)
        Rotate the top N elements of the stack.
        """

        nargs: int = 2

    class DROP(t.NamedTuple):
        """(*) -> ()
        Drop the top N items of the stack.
        """

        nargs: int = 1

    ####################################################################################################
    # Functional abstraction
    ####################################################################################################
    class CALLS(t.NamedTuple):
        """(... A) -> (... B)
        Call [static]

        Branch to `target` pushing the current point onto the call stack.
        The callee will see a stack containg only the provided `nargs`.
        A subsequent RETURN will return execution to the next point.

        Executing a `CALL` pushes the name and module path of the current function.

        .. note::

           CALLS is equvalent to `FUNREF; CALLF`
        """

        funref: str

    class RETURN(t.NamedTuple):
        """(... A) -> ()
        Return to the source of the last `CALL`.
        The returnee will see the top `nargs` values of the present stack appended to theirs.
        All other values on the stack will be discarded.

        Executing a `RETURN` pops (restores) the name and module path of the current function back to that of the caller.

        If the call stack is empty, `RETURN` will exit the interpreter.
        """

        nargs: int

    class GOTO(t.NamedTuple):
        """() -> ()
        Branch to another point within the same bytecode segment.
        The target MUST be within the same module range as the current function.
        Branching does NOT update the name or module of the current function.
        """

        target: int
        anywhere: bool = False

    class FUNREF(t.NamedTuple):
        """() -> (`FUNREF<... A to ... B>`)
        Construct a reference to a static codepoint.
        """

        funref: str

    class CALLF(t.NamedTuple):
        """(`FUNREF<... A to ... B>`, ... A) -> (... B)
        Call [funref]

        Make a dynamic call to the function reference at the top of stack.
        The callee will see a stack containg only the provided `nargs`.
        A subsequent RETURN will return execution to the next point.

        Executing a `CALL` pushes the name and module path of the current function.
        """

        nargs: int = 0

    class CLOSUREF(t.NamedTuple):
        """(`FUNREF<A, ... B to ... C>`, A) -> (`CLOSURE<... B to ... C>`)
        Construct a closure over the function reference at the top of the stack.
        This may produce nullary closures.
        """
        nargs: int = 0

    class CLOSUREC(t.NamedTuple):
        """(`CLOSURE<A, ... B to ... C>`, A) -> (`CLOSURE<... B to ... C>`)
        Further close over the closure at the top of the stack.
        This may produce nullary closures.
        """
        nargs: int = 0

    class CALLC(t.NamedTuple):
        """(`CLOSURE<... A to ... B>`, ... A) -> (... B)
        Call [closure]

        Make a dynamic call to the closure at the top of stack.
        The callee will see a stack containg only the provided `nargs` and closed-overs.
        A subsequent RETURN will return execution to the next point.

        Executing a `CALL` pushes the name and module path of the current function.
        """

        nargs: int = 0

    ####################################################################################################
    # Structures
    ####################################################################################################
    class STRUCT(t.NamedTuple):
        """(*) -> (T)
        Consume the top N items of the stack, producing a struct of the type `structref`.

        The name and module path of the current function MUST match the name and module path of `structref`.
        """

        structref: str
        nargs: int

    class FLOAD(t.NamedTuple):
        """(A) -> (B)
        Consume the struct reference at the top of the stack, producing the value of the referenced field.
        """

        fieldref: str

    class FSTORE(t.NamedTuple):
        """(A) -> (B)
        Consume the struct reference at the top of the stack, producing the value of the referenced field.
        """

        fieldref: str

    ####################################################################################################
    # Arrays
    ####################################################################################################
    class ARRAY(t.NamedTuple):
        """(*) -> (ARRAY<Y>)
        Consume the top N items of the stack, producing an array of the type `typeref`.
        """

        typeref: str
        nargs: int

    class ALOAD(t.NamedTuple):
        """(NAT, ARRAY<T>) -> (T)
        Consume a reference to an array and an index, producing the value at that index.
        FIXME: Or a fault/signal.
        """

    class ASTORE(t.NamedTuple):
        """(T, NAT, ARRAY<T>) -> (ARRAY<T>)
        Consume a value T, storing it at an index in the given array.
        Produces the updated array as the top of stack.
        """

    ####################################################################################################
    # Naturals
    ####################################################################################################

    ####################################################################################################
    # Integers
    ####################################################################################################

    ####################################################################################################
    # Ratios
    ####################################################################################################


class Module(t.NamedTuple):
    opcodes: list = []
    functions: dict = {}
    types: dict = {}
    constants: dict = {}

    def copy(self):
        return Module(
            self.opcodes.copy(),
            self.functions.copy(),
            self.types.copy(),
            self.constants.copy(),
        )

    @staticmethod
    def translate(start: int, end: int, i: "Opcode"):
        # FIXME: Consolidate bounds checks somehow
        match i:
            case Opcode.IF(t):
                d = t + start
                assert start <= d < end
                return Opcode.IF(d)

            case Opcode.GOTO(t, anywhere=False):
                d = t + start
                assert start <= d < end
                return Opcode.GOTO(d)

            case _:
                return i

    def define_function(self, name, opcodes):
        # FIXME: This is way way WAAAAAAY too minimal. Lots of other stuff goes on a "function."
        # For instance how to install handlers?
        # How to consume capabilities?

        try:
            sig = FunctionRef.parse(name)
            assert sig.name
        except:
            raise ValueError("Illegal name provided")

        start = len(self.opcodes)
        self.functions[name] = start
        for op in opcodes:
            self.opcodes.append(self.translate(start, start + len(opcodes), op))
        return name

    def define_type(self, name, signature):
        # FIXME: What in TARNATION is this going to do
        pass

    def __str__(self):
        b = []
        marks = {v: k for k, v in self.functions.items()}
        for i, o in zip(range(1<<64), self.opcodes):
            if(i in marks):
                b.append(f"{marks[i]}:")
            b.append(f"{i: >10}: {o}")
        return "\n".join(b)
