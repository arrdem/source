#!/usr/bin/env python3

"""
ichor entrypoint
"""

from . import Opcode, Interpreter, BOOTSTRAP, XOR3, NOT1, TRUE, FALSE


def main():
    vm = Interpreter(BOOTSTRAP)
    ret = vm.run([
        Opcode.IDENTIFIERC(NOT1),
        Opcode.FUNREF(),
        Opcode.CALLF(1),
        Opcode.RETURN(1)
    ], stack = [TRUE])
    print(ret)


if __name__ == "__main__":
    main()
