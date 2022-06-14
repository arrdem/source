"""The instruction set for Shogoth."""


import typing as t


class Opcode:
    ####################################################################################################
    # Logic
    ####################################################################################################

    # FIXME: This should become an instantiation of the BOOL enum
    class TRUE(t.NamedTuple):
        """() -> (bool)

        Push the constant TRUE onto the stack.

        """

    # FIXME: This should become an instantiation of the BOOL enum
    class FALSE(t.NamedTuple):
        """() -> (bool)

        Push the constant FALSE onto the stack.

        """

    # FIXME: This should become a `VTEST` macro ... or may be replaceable
    class IF(t.NamedTuple):
        """(bool) -> ()

        Branch to another point if the top item of the stack is TRUE. Otherwise fall through.

        """

        target: int

    # not, and, or, xor etc. can all be functions given if.

    class GOTO(t.NamedTuple):
        """() -> ()

        Branch to another point within the same bytecode segment. The target MUST be within the same module range as the
        current function. Branching does NOT update the name or module of the current function.

        """

        target: int

    ####################################################################################################
    # Stack manipulation
    ####################################################################################################
    # https://wiki.laptop.org/go/Forth_stack_operators
    # https://www.forth.com/starting-forth/2-stack-manipulation-operators-arithmetic/
    # https://docs.oracle.com/javase/specs/jvms/se18/html/jvms-6.html#jvms-6.5.swap

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

    class SLOT(t.NamedTuple):
        """(..., A) -> (A, ..., A)

        Copy the Nth (counting up from 0 at the bottom of the stack) item to the top of the stack.
        Intended to allow users to emulate (immutable) frame local slots for reused values.

        """

        target: int

    ####################################################################################################
    # Functional abstraction
    ####################################################################################################

    class IDENTIFIERC(t.NamedTuple):
        """() -> (IDENTIFIER)

        An inline constant which produces an identifier to the stack.

        Identifiers name functions, fields and types but are not strings.
        They are a VM-internal naming structure with reference to the module.

        """

        val: str

    class FUNREF(t.NamedTuple):
        """(IDENTIFIER) -> (`FUNREF<... A to ... B>`)

        Construct a reference to a static codepoint.

        """

    class CALLF(t.NamedTuple):
        """(`FUNREF<... A to ... B>`, ... A) -> (... B)

        Call [funref]

        Make a dynamic call to the function reference at the top of stack.
        The callee will see a stack containg only the provided `nargs`.
        A subsequent RETURN will return execution to the next point.

        Executing a `CALL` pushes the name and module path of the current function.

        """

        nargs: int = 0

    class RETURN(t.NamedTuple):
        """(... A) -> ()

        Return to the source of the last `CALL`. The returnee will see the top `nargs` values of the present stack
        appended to theirs. All other values on the stack will be discarded.

        Executing a `RETURN` pops (restores) the name and module path of the current function back to that of the caller.

        If the call stack is empty, `RETURN` will exit the interpreter.

        """

        nargs: int


    class CLOSUREF(t.NamedTuple):
        """(`FUNREF<A, ... B to ... C>`, A) -> (`CLOSURE<... B to ... C>`)

        Construct a closure over the function reference at the top of the stack. This may produce nullary closures.

        """

        nargs: int = 0

    class CLOSUREC(t.NamedTuple):
        """(`CLOSURE<A, ... B to ... C>`, A) -> (`CLOSURE<... B to ... C>`)

        Further close over the closure at the top of the stack. This may produce nullary closures.

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

    # FIXME: This lacks any sort of way to do dynamic type/field references

    class TYPEREF(t.NamedTuple):
        """(IDENTIFIER) -> (TYPEREF)

        Produces a TYPEREF to the type named by the provided IDENTIFIER.

        """

    class VARIANTREF(t.NamedTuple):
        """(IDENTIFIER, TYPEREF) -> (VARIANTREF)

        Produce a VARIANTREF to an 'arm' of the given variant type.

        """

    class VARIANT(t.NamedTuple):
        """(VARIANTREF<a ⊢ A ⊂ B>, ...) -> (B)

        Construct an instance of an 'arm' of a variant.
        The type of the 'arm' is considered to be the type of the whole variant.

        The name and module path of the current function MUST match the name and module path of `VARIANTREF`.
        The arity of this opcode MUST match the arity of the arm.
        The signature of the arm MUST match the signature fo the top N of the stack.
        """

        nargs: int = 0

    class VTEST(t.NamedTuple):
        """(VARIANTREF<a ⊢ A ⊂ B>, B) -> (bool)

        Test whether B is a given arm of a variant A .

        """

    class VLOAD(t.NamedTuple):
        """(VARIANTREF<a ⊢ A ⊂ B>, B) -> (A)

        Load the value of the variant arm.
        VLOAD errors (undefined) if B is not within the variant.
        VLOAD errors (undefined) if the value in B is not an A - use VTEST as needed.

        """

    class BREAK(t.NamedTuple):
        """Abort the interpreter."""
        pass
