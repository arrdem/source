"""Shogoth bootstrap code.

Some utterly trivial functions and types that allow me to begin testing the VM.
Hopefully no "real" interpreter ever uses this code, since it's obviously replaceable.
"""

from .isa import Module, Opcode


BOOTSTRAP = Module()

NOT = BOOTSTRAP.define_function(
    ";/lang/shogoth/v0/bootstrap/not;bool;bool",
    [
        Opcode.IF(target=3),
        Opcode.FALSE(),
        Opcode.RETURN(1),
        Opcode.TRUE(),
        Opcode.RETURN(1),
    ],
)

OR = BOOTSTRAP.define_function(
    ";/lang/shogoth/v0/bootstrap/or;bool,bool;bool",
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

AND = BOOTSTRAP.define_function(
    ";/lang/shogoth/v0/bootstrap/and;bool,bool;bool",
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

XOR = BOOTSTRAP.define_function(
    ";/lang/shogoth/v0/bootstrap/xor;bool,bool;bool",
    [
        Opcode.DUP(nargs=2),
        # !A && B
        Opcode.CALL(NOT),
        Opcode.CALL(AND),
        Opcode.IF(target=6),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        # !B && A
        Opcode.ROT(2),
        Opcode.CALL(NOT),
        Opcode.CALL(AND),
        Opcode.IF(target=12),
        Opcode.TRUE(),
        Opcode.RETURN(1),
        Opcode.FALSE(),
        Opcode.RETURN(1),
    ],
)
