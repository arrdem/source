"""Shogoth bootstrap code.

Some utterly trivial functions and types that allow me to begin testing the VM.
Hopefully no "real" interpreter ever uses this code, since it's obviously replaceable.
"""

from ichor.isa import Opcode
from ichor.state import Module


BOOTSTRAP = Module()

BOOL = BOOTSTRAP.define_type(
    ";bool;true(),false()",
)

NOT1 = BOOTSTRAP.define_function(
    f";not;{BOOL};{BOOL}",
    [
        Opcode.IF(target=3),
        Opcode.FALSE(),
        Opcode.RETURN(1),
        Opcode.TRUE(),
        Opcode.RETURN(1),
    ],
)

OR2 = BOOTSTRAP.define_function(
    f";or;{BOOL},{BOOL};{BOOL}",
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
    f";or;{BOOL},{BOOL},{BOOL};{BOOL}",
    [
        # A B C
        Opcode.IDENTIFIERC(OR2),
        Opcode.FUNREF(),
        # FIXME: This could be tightened by using ROT maybe...
        Opcode.SLOT(0),
        Opcode.SLOT(1),
        Opcode.SLOT(3),
        Opcode.CALLF(2),   # A|B
        Opcode.SLOT(2),
        Opcode.SLOT(3),
        Opcode.CALLF(2),   # A|B|C
        Opcode.RETURN(1),
    ]
)

AND2 = BOOTSTRAP.define_function(
    f";and;{BOOL},{BOOL};{BOOL}",
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
    f";and;{BOOL},{BOOL},{BOOL};{BOOL}",
    [
        # A B C
        Opcode.IDENTIFIERC(AND2),
        Opcode.FUNREF(),
        Opcode.SLOT(0),   # C <and2> A B C
        Opcode.SLOT(1),   # B C <and2> A B C
        Opcode.SLOT(3),   # <and2> B C <and2> A B C
        Opcode.CALLF(2),  # B&C <and2> A B C
        Opcode.SLOT(2),   # A B&C <and2> A B C
        Opcode.SLOT(3),   # <and2> A B&C <and2> A B C
        Opcode.CALLF(2),  # A&B&C <and2> A B C
        Opcode.RETURN(1),
    ],
)

XOR2 = BOOTSTRAP.define_function(
    f";xor;{BOOL},{BOOL};{BOOL}",
    [
        Opcode.IDENTIFIERC(AND2),
        Opcode.FUNREF(),
        Opcode.IDENTIFIERC(NOT1),
        Opcode.FUNREF(),

        Opcode.SLOT(0),
        Opcode.SLOT(1),
        Opcode.DUP(nargs=2),

        # !A && B
        Opcode.SLOT(3),  # not
        Opcode.CALLF(1),
        Opcode.SLOT(2),  # and
        Opcode.CALLF(2),
        Opcode.IF(target=14),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        # !B && A
        Opcode.ROT(2),
        Opcode.SLOT(3),  # not
        Opcode.CALLF(1),
        Opcode.SLOT(2),  # and
        Opcode.CALLF(2),
        Opcode.IF(target=22),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        Opcode.FALSE(),

        Opcode.RETURN(1),
    ],
)

XOR3 = BOOTSTRAP.define_function(
    f";xor;{BOOL},{BOOL},{BOOL};{BOOL}",
    [
        Opcode.IDENTIFIERC(XOR2),
        Opcode.FUNREF(),
        Opcode.IDENTIFIERC(OR2),
        Opcode.FUNREF(),

        Opcode.SLOT(0),
        Opcode.SLOT(1),
        Opcode.SLOT(2),
                                # A B C
        Opcode.ROT(nargs=3),    # C A B
        Opcode.ROT(nargs=3),    # B C A
        Opcode.DUP(nargs=1),    # B B C A
        Opcode.ROT(nargs=4),    # A B B C
        Opcode.SLOT(3),
        Opcode.CALLF(2),     # A^B B C
        Opcode.ROT(nargs=3),    # C A^B B
        Opcode.ROT(nargs=3),    # B C A^B
        Opcode.SLOT(3),
        Opcode.CALLF(2),     # B^C A^B
        Opcode.SLOT(4),
        Opcode.CALLF(2),      # A^B|B^C
        Opcode.RETURN(1),
    ]
)
