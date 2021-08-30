"""The Lilith runner."""

import argparse
from importlib.resources import read_text as resource_text
import logging
import sys
import traceback

from lilith.interpreter import Bindings, eval as lil_eval, Runtime
from lilith.parser import parse_expr, Symbol
from lilith.reader import Def, Module, read_buffer, read_file
from prompt_toolkit import print_formatted_text, PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
import yaml


log = logging.getLogger(__name__)


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
        [],
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
        except Exception:
            traceback.print_exc()
            continue

        try:
            result = lil_eval(runtime, module, Bindings("__root__", None), expr)
            print_([("class:result", f"⇒ {result!r}")], style=STYLE)
        except Exception:
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

    log.debug(
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
        lil_eval(runtime, mod, Bindings(main, None), mod.defs.get(main).block)
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
parser.add_argument("-v", "--verbose", action="count", default=0)
parser.add_argument("file", nargs="?", help="A file to start executing from")


def main():
    opts, args = parser.parse_known_args()

    if opts.verbose == 0:
        level = logging.WARN
    elif opts.verbose == 1:
        level = logging.INFO
    elif opts.verbose > 1:
        level = 0

    logging.basicConfig(level=level)

    # Bash anything the user says is the path onto the PYTHONPATH so we can use importlib for our loading machinery.
    for e in opts.path:
        for _e in e.split(":"):
            sys.path.insert(0, _e)

    # Building up a bootstrap interface for going out to many Python features.
    runtime = Runtime(Symbol("__runtime__"), Symbol(opts.prelude), {})

    def py(runtime=None, module=None, expr=None, body=None, name=None):
        """The implementation of the Python lang as an eval type."""
        globs = globals().copy()
        locs = {}
        body = (
            "def _shim():\n"
            + "\n".join("  " + line for line in body.splitlines())
            + "\n\n_escape = _shim()"
        )
        exec(body, globs, locs)
        return locs["_escape"]

    def lil(runtime=None, module=None, expr=None, body=None, name=None):
        """The implementation of the Lilith lang as an eval type."""
        expr = parse_expr(body)
        return lil_eval(runtime, module, Bindings(), expr)

    bootstrap = Module(
        Symbol("lilith.bootstrap"),
        [],
        {
            # The Python FFI escape hatch
            Symbol("py"): Def(None, py),
            # The Lilith self-interpreter
            Symbol("lil"): Def(None, lil),
        },
    )
    runtime.modules[bootstrap.name] = bootstrap
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


if __name__ == "__main__":
    main()
