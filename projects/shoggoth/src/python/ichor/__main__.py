#!/usr/bin/env python3

"""
ichor entrypoint
"""

from . import Opcode, Interpreter, BOOTSTRAP, XOR3


def main():
    vm = Interpreter(BOOTSTRAP)
    ret = vm.run(
        [
            Opcode.IDENTIFIERC(XOR3),
            Opcode.FUNREF(),
            Opcode.CLOSUREF(1),
            Opcode.CLOSUREC(1),
            Opcode.CALLC(1),
            Opcode.RETURN(1),
        ],
        stack = [True, True, False]
    )
    print(ret)


if __name__ == "__main__":
    main()
