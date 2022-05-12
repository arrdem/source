"""A testing REPL."""


from shogoth.reader import Reader

import prompt_toolkit
import yaspin

if __name__ == "__main__":
    reader = Reader()
    while (line := input(">>> ")):
        read = reader.read(line)
        print(read, type(read))
