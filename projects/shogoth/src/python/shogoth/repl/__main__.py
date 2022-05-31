"""A testing REPL."""

from shogoth.reader import Reader
from shogoth.types import Symbol
from shogoth.analyzer import Analyzer, SPECIALS, GLOBALS, Namespace

from prompt_toolkit import (
    print_formatted_text,
    PromptSession,
)
from prompt_toolkit.formatted_text import (
    FormattedText,
)
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
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

    session = PromptSession(history=FileHistory(".shogoth.history"))

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
        print('analyze ]', expr, type(expr))


if __name__ == "__main__":
    main()
