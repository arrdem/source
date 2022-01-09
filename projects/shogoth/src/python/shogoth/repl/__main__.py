"""A testing REPL."""

import sys

from shogoth.parser import parse
from shogoth.reader import Reader


if __name__ == "__main__":
    reader = Reader()
    while (line := input(">>> ")):
        read = reader.read(line)
        print(read, type(read))
