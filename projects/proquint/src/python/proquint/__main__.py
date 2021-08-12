"""A CLI program for interacting with proquints."""

import argparse
from secrets import randbits
import uuid

from proquint import Proquint


parser = argparse.ArgumentParser()
g = parser.add_mutually_exclusive_group()
g.add_argument("-g", "--generate", dest="generate", default=False, action="store_true")
g.add_argument("-p", "--predictable", dest="predictable", default=False, action="store_true")
g.add_argument("-d", "--decode", dest="decode", default=False, action="store_true")
g.add_argument("-e", "--encode", dest="encode", default=False, action="store_true")
parser.add_argument("-w", "--width", dest="width", type=int, default=32)


def main():
    opts, args = parser.parse_known_args()

    if opts.generate:
        print(Proquint.encode(randbits(opts.width), opts.width))
    elif opts.predictable:
        print(Proquint.encode(uuid.getnode(), 32))
    elif opts.encode:
        print(Proquint.encode(int(args[0]), opts.width))
    elif opts.decode:
        print(Proquint.decode(args[0]))


if __name__ == "__main__":
    main()
