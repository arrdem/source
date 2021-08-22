"""The Lilith runner."""

import argparse
from importlib.resources import read_text as resource_text
import sys
import traceback

from lilith.interpreter import Bindings, eval, Runtime
from lilith.parser import Apply, Args, parse_expr, Symbol
from lilith.reader import Import, Module, read_buffer, read_file
from prompt_toolkit import print_formatted_text, prompt, PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
import yaml


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


def repl(opts, args, runtime):
    """Run an interactive Lilith repl, supporting only the Lilith language itself."""

    session = PromptSession(history=FileHistory(".lilith.history"))
    module = Module(
        "__repl__",
        {},
    )

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
            traceback.print_exc()
            continue

        try:
            result = eval(runtime, module, Bindings("__root__", None), expr)
            print_([("class:result", f"⇒ {result!r}")], style=STYLE)
        except Exception as e:
            traceback.print_exc()
            continue


def batch(opts, args, runtime):
    """Run a Lilith program 'for real' in non-interactive batch mode."""

    if opts.file:
        mod = read_file(opts.file)
        main = "main"
    elif opts.main:
        mod, main = opts.main.split(":") if ":" in opts.main else opts.main, "main"
        dirmod, rname = ".".join(mod.split(".")[:-1]), mod.split(".")[-1] + ".lil"
        mod = read_buffer(resource_text(dirmod, rname), mod)

    main = Symbol(main)

    # Register
    runtime.modules.update({mod.name: mod})

    print("DEBUG: batch mode")
    print(
        yaml.dump(
            {
                "type": "runtime",
                "name": runtime.name.name,
                "modules": {
                    m.name.name: {
                        "defs": {dname.name: repr(d) for dname, d in m.defs.items()}
                    }
                    for m in runtime.modules.values()
                },
            },
            default_flow_style=False,
            sort_keys=False,
        )
    )

    if main in mod.defs:
        eval(runtime, mod, Bindings(main, None), mod.defs.get(main))
    else:
        raise NameError(f"entry point {main} not found in {mod.name.name}")


parser = argparse.ArgumentParser()
parser.add_argument(
    "-m", "--main", default="main", help="The name of an entry point eg <module>:<name>"
)
parser.add_argument(
    "-p",
    "--path",
    default=[],
    action="append",
    help="Append something to the module path.",
)
parser.add_argument(
    "--prelude", default="lilith.prelude", help="Select a module prelude."
)
parser.add_argument("file", nargs="?", help="A file to start executing from")


if __name__ == "__main__":
    opts, args = parser.parse_known_args()

    # Bash anything the user says is the path onto the PYTHONPATH so we can use importlib for our loading machinery.
    for e in opts.path:
        for _e in e.split(":"):
            sys.path.insert(0, _e)

    # Building up a bootstrap interface for going out to many Python features.
    runtime = Runtime(Symbol("__runtime__"), Symbol(opts.prelude), {})

    def _lil(runtime=None,
             module=None,
             body=None,
             name=None):
        """The implementation of the Lilith lang as an eval type."""
        expr = parse_expr(body)
        return eval(runtime, module, Bindings(), expr)

    bootstrap = Module(
        Symbol("lilith.bootstrap"),
        [],
        {
            # The foundational meaning of lang[]
            Symbol("lang"): lambda evaluator, body=None: evaluator(body),
            # The Python FFI escape hatch
            Symbol("py"): lambda *args, body=None, **kwargs: eval(body),
            # The Lilith self-interpreter
            Symbol("lilith"): _lil,
         },
    )
    runtime.modules[Symbol(bootstrap.name)] = bootstrap
    prelude_mod = read_buffer(
        resource_text(
            ".".join(opts.prelude.split(".")[:-1]), opts.prelude.split(".")[-1] + ".lil"
        ),
        opts.prelude,
    )
    runtime.modules[prelude_mod.name] = prelude_mod

    if (opts.path and opts.main) or opts.file:
        batch(opts, args, runtime)
    else:
        repl(opts, args, runtime)
