"""The instruction set for Shogoth."""


from typing import NamedTuple


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


class FunctionSignature(NamedTuple):
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
