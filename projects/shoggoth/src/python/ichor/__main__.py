#!/usr/bin/env python3

"""
ichor entrypoint
"""

from . import *


def main():
    vm = Interpreter(BOOTSTRAP)
    ret = vm.run(
        [
            Opcode.FUNREF(XOR2),
            Opcode.CLOSUREF(1),
            Opcode.CALLC(1),
            Opcode.RETURN(1),
        ],
        stack = [True, False]
    )
    print(ret)


if __name__ == "__main__":
    main()
