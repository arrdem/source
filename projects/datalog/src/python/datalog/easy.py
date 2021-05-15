"""
Easy datalog.

Takes the core datalog engine and wraps it up so it's a little nicer to work with.

Easy because it's closer to hand, but no simpler.
"""

from typing import Sequence, Tuple

from datalog.evaluator import join as __join, select as __select
from datalog.reader import read as __read
from datalog.types import Constant, Dataset, LTuple, LVar, PartlyIndexedDataset


def read(text: str, db_cls=PartlyIndexedDataset):
    """A helper for reading Datalog text into a well-supported dataset."""

    return __read(text, db_cls=db_cls)


def q(t: Tuple[str]) -> LTuple:
    """Helper for writing terse queries.

  Takes a tuple of strings, and interprets them as a logic tuple.
  So you don't have to write the logic tuple out by hand.
  """

    def _x(s: str):
        if s[0].isupper():
            return LVar(s)
        else:
            return Constant(s)

    return tuple(_x(e) for e in t)


def __mapv(f, coll):
    return [f(e) for e in coll]


def __result(results_bindings):
    results, bindings = results_bindings
    return (
        tuple(tuple(c.value for c in e) for e in results),
        {var.name: c.value for var, c in bindings.items()},
    )


def select(db: Dataset, query: Tuple[str], bindings=None) -> Sequence[Tuple]:
    """Helper for interpreting tuples of strings as a query, and returning simplified results.

  Executes your query, returning matching full tuples.
  """

    return __mapv(__result, __select(db, q(query), bindings=bindings))


def join(db: Dataset, query: Sequence[Tuple[str]], bindings=None) -> Sequence[dict]:
    """Helper for interpreting a bunch of tuples of strings as a join query, and returning simplified
results.

  Executes the query clauses as a join, returning a sequence of tuples and binding mappings such
  that the join constraints are simultaneously satisfied.


  >>> db = read('''
  ... edge(a, b).
  ... edge(b, c).
  ... edge(c, d).
  ... ''')
  >>> join(db, [
  ...   ('edge', 'A', 'B'),
  ...   ('edge', 'B', 'C')
  ... ])
  [((('edge', 'a', 'b'),
     ('edge', 'b', 'c')),
    {'A': 'a', 'B': 'b', 'C': 'c'}),
   ((('edge', 'b', 'c'),
     ('edge', 'c', 'd')),
    {'A': 'b', 'B': 'c', 'C': 'd'}),
   ((('edge', 'c', 'd'),
     ('edge', 'd', 'f')),
    {'A': 'c', 'B': 'd', 'C': 'f'})]
  """

    return __mapv(__result, __join(db, [q(c) for c in query], bindings=bindings))
