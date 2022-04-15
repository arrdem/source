"""The instruction set for Shogoth."""


from typing import NamedTuple

from shogoth.types import Function, FunctionSignature


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

        Executing a `CALL` pushes the name and module path of the current function.
        """

        funref: str

    class RETURN(NamedTuple):
        """(*) -> ()
        Return to the source of the last `CALL`.
        The returnee will see the top `nargs` values of the present stack appended to theirs.
        All other values on the stack will be discarded.

        Executing a `RETURN` pops (restores) the name and module path of the current function back to that of the caller.

        If the call stack is empty, `RETURN` will exit the interpreter.
        """

        nargs: int

    class GOTO(NamedTuple):
        """() -> ()
        Branch to another point within the same bytecode segment.
        The target MUST be within the same module range as the current function.
        Branching does NOT update the name or module of the current function.
        """

        target: int
        anywhere: bool = False

    class STRUCT(NamedTuple):
        """(*) -> (T)
        Consume the top N items of the stack, producing a struct of the type `structref`.

        The name and module path of the current function MUST match the name and module path of `structref`.
        """

        structref: str
        nargs: int

    class FIELD(NamedTuple):
        """(A) -> (B)
        Consume the struct reference at the top of the stack, producing the value of the referenced field.
        """

        fieldref: str


class Module(NamedTuple):
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
    def translate(offset: int, i: "Opcode"):
        match i:
            case Opcode.IF(t):
                return Opcode.IF(t + offset)
            case Opcode.GOTO(t, anywhere=False):
                return Opcode.GOTO(t + offset)
            case _:
                return i

    def define_function(self, name, opcodes):
        # FIXME: This is way way WAAAAAAY too minimal. Lots of other stuff goes on a "function."
        # For instance how to install handlers?
        # How to consume capabilities?

        try:
            sig = FunctionSignature.parse(name)
            assert sig.name
        except:
            raise ValueError("Illegal name provided")

        start = len(self.opcodes)
        self.functions[name] = start
        for op in opcodes:
            self.opcodes.append(self.translate(start, op))
        return name

    def define_struct(self, name, signature):
        # FIXME: What in TARNATION is this going to do
        pass
