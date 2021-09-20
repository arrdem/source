"""
Datalog (py)
============

An interactive datalog interpreter with commands and persistence

Commands
~~~~~~~~
  .help      (this message)
  .all       display all tuples
  .quit      to exit the REPL

To exit, use control-c or control-d

The interpreter
~~~~~~~~~~~~~~~

The interpreter reads one line at a time from stdin.
Lines are either
 - definitions (ending in .),
 - queries (ending in ?)
 - retractions (ending in !)

A definition may contain arbitrarily many datalog tuples and rules.

   edge(a, b). edge(b, c).  % A pair of definitions
   ⇒ edge(a, b). % The REPL's response that it has been committed
   ⇒ edge(b, c).

A query may contain definitions, but they exist only for the duration of the query.

   edge(X, Y)? % A query which will enumerate all 2-edges
   ⇒ edge(a, b).
   ⇒ edge(b, c).

   edge(c, d). edge(X, Y)? % A query with a local tuple
   ⇒ edge(a, b).
   ⇒ edge(b, c).
   ⇒ edge(c, d).

A retraction may contain only one tuple or clause, which will be expunged.

   edge(a, b)!   % This tuple is in our dataset
   ⇒ edge(a, b)  % So deletion succeeds

   edge(a, b)!   % This tuple is no longer in our dataset
   ⇒ Ø           % So deletion fails

"""

import argparse
import logging
import sys

from datalog.debris import Timing
from datalog.evaluator import select
from datalog.reader import (
    pr_str,
    read_command,
    read_dataset,
)
from datalog.types import (
    CachedDataset,
    Dataset,
    LVar,
    PartlyIndexedDataset,
    Rule,
    TableIndexedDataset,
)

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

SPINNER = Spinner(["|", "/", "-", "\\"], 200)


class InterpreterInterrupt(Exception):
    """An exception used to break the prompt or evaluation."""


def print_(fmt, **kwargs):
    print_formatted_text(FormattedText(fmt), **kwargs)


def print_db(db):
    """Render a database for debugging."""

    for e in db.tuples():
        print(f"⇒ {pr_str(e)}")

    for r in db.rules():
        print(f"⇒ {pr_str(r)}")


def main(args):
    """REPL entry point."""

    if args.db_cls == "simple":
        db_cls = Dataset
    elif args.db_cls == "cached":
        db_cls = CachedDataset
    elif args.db_cls == "table":
        db_cls = TableIndexedDataset
    elif args.db_cls == "partly":
        db_cls = PartlyIndexedDataset

    print(f"Using dataset type {db_cls}")

    session = PromptSession(history=FileHistory(".datalog.history"))
    db = db_cls([], [])

    if args.dbs:
        for db_file in args.dbs:
            try:
                with open(db_file, "r") as f:
                    db = db.merge(read_dataset(f.read()))
                    print(f"Loaded {db_file} ...")
            except Exception as e:
                print(f"Internal error - {e}\nUnable to load db {db_file}, skipping")

    while True:
        try:
            line = session.prompt([("class:prompt", ">>> ")], style=STYLE)
        except (InterpreterInterrupt, KeyboardInterrupt):
            continue
        except EOFError:
            break

        if line == ".all":
            op = ".all"
        elif line == ".dbg":
            op = ".dbg"
        elif line == ".quit":
            break

        elif line in {".help", "help", "?", "??", "???"}:
            print(__doc__)
            continue

        elif line.split(" ")[0] == ".log":
            op = ".log"

        else:
            try:
                op, val = read_command(line)
            except Exception:
                print("Got an unknown command or a syntax error, can't tell which")
                continue

        # Definition merges on the DB
        if op == ".all":
            print_db(db)

        # .dbg drops to a debugger shell so you can poke at the instance objects (database)
        elif op == ".dbg":
            import pdb

            pdb.set_trace()

        # .log sets the log level - badly
        elif op == ".log":
            level = line.split(" ")[1].upper()
            try:
                ch.setLevel(getattr(logging, level))
            except BaseException:
                print(f"Unknown log level {level}")

        elif op == ".":
            # FIXME (arrdem 2019-06-15):
            #   Syntax rules the parser doesn't impose...
            try:
                for rule in val.rules():
                    assert (
                        not rule.free_vars
                    ), f"Rule contains free variables {rule.free_vars!r}"

                for tuple in val.tuples():
                    assert not any(
                        isinstance(e, LVar) for e in tuple
                    ), f"Tuples cannot contain lvars - {tuple!r}"

            except BaseException as e:
                print(f"Error: {e}")
                continue

            db = db.merge(val)
            print_db(val)

        # Queries execute - note that rules as queries have to be temporarily merged.
        elif op == "?":
            # In order to support ad-hoc rules (joins), we have to generate a transient "query" database
            # by bolting the rule on as an overlay to the existing database. If of course we have a join.
            #
            # `val` was previously assumed to be the query pattern. Introduce `qdb`, now used as the
            # database to query and "fix" `val` to be the temporary rule's pattern.
            #
            # We use a new db and db local so that the ephemeral rule doesn't persist unless the user
            # later `.` defines it.
            #
            # Unfortunately doing this merge does nuke caches.
            qdb = db
            if isinstance(val, Rule):
                qdb = db.merge(db_cls([], [val]))
                val = val.pattern

            with yaspin(SPINNER):
                with Timing() as t:
                    try:
                        results = list(select(qdb, val))
                    except KeyboardInterrupt:
                        print(f"Evaluation aborted after {t}")
                        continue

            # It's kinda bogus to move sorting out but oh well
            sorted(results)

            for _results, _bindings in results:
                _result = _results[0]  # select only selects one tuple at a time
                print(f"⇒ {pr_str(_result)}")

            # So we can report empty sets explicitly.
            if not results:
                print("⇒ Ø")

            print_([("class:time", f"Elapsed time - {t}")], style=STYLE)

        # Retractions try to delete, but may fail.
        elif op == "!":
            if val in db.tuples() or val in [r.pattern for r in db.rules()]:
                db = db_cls(
                    [u for u in db.tuples() if u != val],
                    [r for r in db.rules() if r.pattern != val],
                )
                print(f"⇒ {pr_str(val)}")
            else:
                print("⇒ Ø")


parser = argparse.ArgumentParser()

# Select which dataset type to use
parser.add_argument(
    "--db-type",
    choices=["simple", "cached", "table", "partly"],
    help="Choose which DB to use (default partly)",
    dest="db_cls",
    default="partly",
)

parser.add_argument(
    "--load-db", dest="dbs", action="append", help="Datalog files to load first."
)

if __name__ == "__main__":
    args = parser.parse_args(sys.argv[1:])
    logger = logging.getLogger("arrdem.datalog")
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    main(args)
