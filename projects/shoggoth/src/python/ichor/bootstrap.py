"""Shogoth bootstrap code.

Some utterly trivial functions and types that allow me to begin testing the VM.
Hopefully no "real" interpreter ever uses this code, since it's obviously replaceable.
"""

from ichor import isa
from ichor.state import Module, Variant
from ichor.assembler import FuncBuilder


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
        isa.IDENTIFIERC("bool"),
        isa.TYPEREF(),  # <typeref bool> a
        isa.DUP(),
        isa.IDENTIFIERC("true"),
        isa.VARIANTREF(), # <variantref true:bool> <typeref bool> a
        isa.DUP(),
        isa.SLOT(0),
        isa.ROT(2),
        isa.VTEST(11),

        isa.VARIANT(0),
        isa.RETURN(1),

        isa.DROP(1),
        isa.IDENTIFIERC("false"),
        isa.VARIANTREF(),
        isa.VARIANT(0),
        isa.RETURN(1),
    ],
)

OR2 = BOOTSTRAP.define_function(
    f";or;{BOOL},{BOOL};{BOOL}",
    [
        isa.BREAK(),
    ],
)

OR3 = BOOTSTRAP.define_function(
    f";or;{BOOL},{BOOL},{BOOL};{BOOL}",
    [
        isa.BREAK(),
    ]
)

AND2 = BOOTSTRAP.define_function(
    f";and;{BOOL},{BOOL};{BOOL}",
    [
        isa.BREAK(),
    ],
)

AND3 = BOOTSTRAP.define_function(
    f";and;{BOOL},{BOOL},{BOOL};{BOOL}",
    [
        isa.BREAK(),
    ],
)

XOR2 = BOOTSTRAP.define_function(
    f";xor;{BOOL},{BOOL};{BOOL}",
    [
        isa.BREAK(),
    ],
)

XOR3 = BOOTSTRAP.define_function(
    f";xor;{BOOL},{BOOL},{BOOL};{BOOL}",
    [
        # A^B|B^C
        isa.BREAK(),
    ]
)
