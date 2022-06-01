#!/usr/bin/env python3

"""
ichor entrypoint
"""

from . import *


def main():
    vm = Interpreter(BOOTSTRAP)
    ret = vm.run(
        [
            Opcode.CALLS(XOR3),
            Opcode.RETURN(1)
        ],
        stack = [True, False, False]
    )
    print(ret)


if __name__ == "__main__":
    main()
