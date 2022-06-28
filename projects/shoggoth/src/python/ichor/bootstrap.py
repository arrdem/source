"""Shogoth bootstrap code.

Some utterly trivial functions and types that allow me to begin testing the VM.
Hopefully no "real" interpreter ever uses this code, since it's obviously replaceable.
"""

from ichor.isa import Opcode
from ichor.state import Module, Variant


BOOTSTRAP = Module()

BOOL = BOOTSTRAP.define_type(
    ";bool;true(),false()",
)

TRUE = Variant(BOOL, 'true', ())
FALSE = Variant(BOOL, 'false', ())

NOT1 = BOOTSTRAP.define_function(
    f";not;{BOOL};{BOOL}",
    [
        # a: Bool
        Opcode.IDENTIFIERC("bool"),
        Opcode.TYPEREF(),  # <typeref bool> a
        Opcode.DUP(),
        Opcode.IDENTIFIERC("true"),
        Opcode.VARIANTREF(), # <variantref true:bool> <typeref bool> a
        Opcode.DUP(),
        Opcode.SLOT(0),
        Opcode.ROT(2),
        Opcode.VTEST(11),

        Opcode.VARIANT(0),
        Opcode.RETURN(1),

        Opcode.DROP(1),
        Opcode.IDENTIFIERC("false"),
        Opcode.VARIANTREF(),
        Opcode.VARIANT(0),
        Opcode.RETURN(1),
    ],
)

OR2 = BOOTSTRAP.define_function(
    f";or;{BOOL},{BOOL};{BOOL}",
    [
        Opcode.BREAK(),
    ],
)

OR3 = BOOTSTRAP.define_function(
    f";or;{BOOL},{BOOL},{BOOL};{BOOL}",
    [
        Opcode.BREAK(),
    ]
)

AND2 = BOOTSTRAP.define_function(
    f";and;{BOOL},{BOOL};{BOOL}",
    [
        Opcode.BREAK(),
    ],
)

AND3 = BOOTSTRAP.define_function(
    f";and;{BOOL},{BOOL},{BOOL};{BOOL}",
    [
        Opcode.BREAK(),
    ],
)

XOR2 = BOOTSTRAP.define_function(
    f";xor;{BOOL},{BOOL};{BOOL}",
    [
        Opcode.BREAK(),
    ],
)

XOR3 = BOOTSTRAP.define_function(
    f";xor;{BOOL},{BOOL},{BOOL};{BOOL}",
    [
        # A^B|B^C
        Opcode.BREAK(),
    ]
)
