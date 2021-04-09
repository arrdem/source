#!/usr/bin/env python3

import argparse
import logging
import sys

from flowmetal.syntax_analyzer import analyzes

from prompt_toolkit import print_formatted_text, prompt, PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style


STYLE = Style.from_dict({
    # User input (default text).
    "": "",
    "prompt": "ansigreen",
    "time": "ansiyellow"
})


class InterpreterInterrupt(Exception):
    """An exception used to break the prompt or evaluation."""


def pp(t, indent=""):
    if isinstance(t, list):  # lists
        buff = ["["]
        for e in t:
            buff.append(f"{indent}  " + pp(e, indent+"  ")+",")
        return "\n".join(buff + [f"{indent}]"])

    elif hasattr(t, '_fields'):  # namedtuples
        buff = [f"{type(t).__name__}("]
        for field, value in zip(t._fields, t):
            buff.append(f"{indent}  {field}=" + pp(value, indent+"  ")+",")
        return "\n".join(buff + [f"{indent})"])

    elif isinstance(t, tuple):  # tuples
        buff = ["("]
        for e in t:
            buff.append(f"{indent}  " + pp(e, indent+"  ")+",")
        return "\n".join(buff + [f"{indent})"])

    else:
        return repr(t)

parser = argparse.ArgumentParser()

def main():
    """REPL entry point."""

    args = parser.parse_args(sys.argv[1:])
    logger = logging.getLogger("flowmetal")
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    session = PromptSession(history=FileHistory(".iflow.history"))
    line_no = 0

    while True:
        try:
            line = session.prompt([("class:prompt", ">>> ")], style=STYLE)
        except (InterpreterInterrupt, KeyboardInterrupt):
            continue
        except EOFError:
            break

        try:
            print(pp(analyzes(line, source_name=f"repl@{line_no}")))
        except Exception as e:
            print(e)
        finally:
            line_no += 1
