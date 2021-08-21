"""A simple Lilith shell."""

from lilith.interpreter import Bindings, eval, Runtime
from lilith.parser import Apply, Args, parse_expr
from lilith.reader import Module

from prompt_toolkit import print_formatted_text, prompt, PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style


STYLE = Style.from_dict(
    {
        # User input (default text).
        "": "",
        "prompt": "ansigreen",
        "time": "ansiyellow",
        "result": "ansiblue",
    }
)

def print_(fmt, **kwargs):
    print_formatted_text(FormattedText(fmt), **kwargs)


if __name__ == "__main__":
    session = PromptSession(history=FileHistory(".lilith.history"))
    runtime = Runtime("test", dict())
    module = Module("__repl__", {
        "print": print,
        "int": int,
        "string": str,
        "float": float,
    })

    while True:
        try:
            line = session.prompt([("class:prompt", ">>> ")], style=STYLE)
        except (KeyboardInterrupt):
            continue
        except EOFError:
            break

        try:
            expr = parse_expr(line)
        except Exception as e:
            print(e)
            continue

        try:
            result = eval(
                runtime, module,
                Bindings("__root__", None),
                expr
            )
            print_([("class:result", f"⇒ {result!r}")], style=STYLE)
        except Exception as e:
            print(e)
            continue
