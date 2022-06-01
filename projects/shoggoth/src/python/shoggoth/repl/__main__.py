"""A testing REPL."""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from shoggoth.analyzer import (
    Analyzer,
    GLOBALS,
    Namespace,
    SPECIALS,
)
from shoggoth.reader import Reader
from shoggoth.types import Symbol
from yaspin import Spinner, yaspin


STYLE = Style.from_dict(
    {
        # User input (default text).
        "": "",
        "prompt": "ansigreen",
        "time": "ansiyellow",
    }
)

SPINNER = Spinner("|/-\\", 200)


def main():
    reader = Reader()
    analyzer = Analyzer(SPECIALS, GLOBALS)
    ns = Namespace(Symbol("user"), {})

    session = PromptSession(history=FileHistory(".shoggoth.history"))

    while True:
        try:
            line = session.prompt([("class:prompt", ">>> ")], style=STYLE)
        except (KeyboardInterrupt):
            continue
        except EOFError:
            break

        with yaspin(SPINNER):
            read = reader.read(line)
        print(read, type(read))

        with yaspin(SPINNER):
            expr = analyzer.analyze(ns, read)
        print("analyze ]", expr, type(expr))


if __name__ == "__main__":
    main()
