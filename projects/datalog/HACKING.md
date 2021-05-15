# Hacking on datalog

Datalog uses the [canopy](https://github.com/jcoglan/canopy) PEG
parser generator, the grammar for which is `src/datalog.peg`.

The included `Makefile` contains appropriate rules to build a Python 3
virtual environment, install the canopy compiler locally, build the
grammar, install pytest and run the test suite. All you should have to
do is `make test`, and away it all goes.

The `datalog.parser` module is generated code emitted by canopy and
should not be edited. It will be rebuilt as needed.

The parser is tested in `test/test_datalog_parser.py` which attempts
to provide coverage for the basic cases of the grammar itself. As of
v0.0.3 (and earlier) this coverage is somewhat incomplete.

The `datalog.core` module contains pretty much everything besides the
codegen'd parser. Particularly, it contains an `Actions` class which
uses hooks in the datalog PEG grammar (noted by the `%foo` ends of
lines) to construct a database AST for every *whole file* read.

The `datalog.core` module also implements evaluation of queries
against databases. This comes in the `evaluate` function and its
mutually recursive helper `join`. `join` is an implementation detail,
whereas `evaluate` is an intentionally exposed entry point. Future
versions of datalog may hide `join`.
