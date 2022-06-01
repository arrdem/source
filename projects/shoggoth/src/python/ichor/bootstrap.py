"""Shogoth bootstrap code.

Some utterly trivial functions and types that allow me to begin testing the VM.
Hopefully no "real" interpreter ever uses this code, since it's obviously replaceable.
"""

from .isa import Module, Opcode

from .typing import ProductExpr, SumExpr


BOOTSTRAP = Module()

NOT1 = BOOTSTRAP.define_function(
    ";/lang/shoggoth/v0/bootstrap/not;bool;bool",
    [
        Opcode.IF(target=3),
        Opcode.FALSE(),
        Opcode.RETURN(1),
        Opcode.TRUE(),
        Opcode.RETURN(1),
    ],
)

OR2 = BOOTSTRAP.define_function(
    ";/lang/shoggoth/v0/bootstrap/or;bool,bool;bool",
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

OR3 = BOOTSTRAP.define_function(
    ";/lang/shoggoth/v0/bootstrap/or;bool,bool,bool;bool",
    [
        # A B C
        Opcode.CALLS(OR2),   # A|B C
        Opcode.CALLS(OR2),   # A|B|C
        Opcode.RETURN(1),
    ]
)

AND2 = BOOTSTRAP.define_function(
    ";/lang/shoggoth/v0/bootstrap/and;bool,bool;bool",
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

AND3 = BOOTSTRAP.define_function(
    ";/lang/shoggoth/v0/bootstrap/and;bool,bool,bool;bool",
    [
        # A B C
        Opcode.CALLS(AND2),  # A&B C
        Opcode.CALLS(AND2),  # A&B&C
        Opcode.RETURN(1),
    ],
)

XOR2 = BOOTSTRAP.define_function(
    ";/lang/shoggoth/v0/bootstrap/xor;bool,bool;bool",
    [
        Opcode.DUP(nargs=2),
        # !A && B
        Opcode.CALLS(NOT1),
        Opcode.CALLS(AND2),
        Opcode.IF(target=6),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        # !B && A
        Opcode.ROT(2),
        Opcode.CALLS(NOT1),
        Opcode.CALLS(AND2),
        Opcode.IF(target=12),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        Opcode.FALSE(),

        Opcode.RETURN(1),
    ],
)

XOR3 = BOOTSTRAP.define_function(
    ";/lang/shoggoth/v0/bootstrap/xor;bool,bool,bool;bool",
    [
                                # A B C
        Opcode.ROT(nargs=3),    # C A B
        Opcode.ROT(nargs=3),    # B C A
        Opcode.DUP(nargs=1),    # B B C A
        Opcode.ROT(nargs=4),    # A B B C
        Opcode.CALLS(XOR2),     # A^B B C
        Opcode.ROT(nargs=3),    # C A^B B
        Opcode.ROT(nargs=3),    # B C A^B
        Opcode.CALLS(XOR2),     # B^C A^B
        Opcode.CALLS(OR2),      # A^B|B^C
        Opcode.RETURN(1),
    ]
)

TRUE = BOOTSTRAP.define_type(
    "/lang/shoggoth/v0/true",
    ProductExpr([]),
)

FALSE = BOOTSTRAP.define_type(
    "/lang/shoggoth/v0/false",
    ProductExpr([]),
)

BOOL = BOOTSTRAP.define_type(
    "/lang/shoggoth/v0/bool",
    SumExpr([TRUE, FALSE])
)
