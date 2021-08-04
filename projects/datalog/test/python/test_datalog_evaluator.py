"""Query evaluation unit tests."""

from datalog.easy import read, select
from datalog.types import (
  CachedDataset,
  Constant,
  Dataset,
  LVar,
  PartlyIndexedDataset,
  Rule,
  TableIndexedDataset
)

import pytest


DBCLS = [Dataset, CachedDataset, TableIndexedDataset, PartlyIndexedDataset]


@pytest.mark.parametrize("db_cls,", DBCLS)
def test_id_query(db_cls):
    """Querying for a constant in the dataset."""

    ab = (
        Constant("a"),
        Constant("b"),
    )
    assert not select(
        db_cls([], []),
        (
            "a",
            "b",
        ),
    )
    assert select(db_cls([ab], []), ("a", "b",)) == [
        (
            (("a", "b"),),
            {},
        )
    ]


@pytest.mark.parametrize("db_cls,", DBCLS)
def test_lvar_query(db_cls):
    """Querying for a binding in the dataset."""

    d = read("""a(b). a(c).""", db_cls=db_cls)

    assert select(d, ("a", "X")) == [
        ((("a", "b"),), {"X": "b"}),
        ((("a", "c"),), {"X": "c"}),
    ]


@pytest.mark.parametrize("db_cls,", DBCLS)
def test_lvar_unification(db_cls):
    """Querying for MATCHING bindings in the dataset."""

    d = read("""edge(b, c). edge(c, c).""", db_cls=db_cls)

    assert (
        select(
            d,
            (
                "edge",
                "X",
                "X",
            ),
        )
        == [((("edge", "c", "c"),), {"X": "c"})]
    )


@pytest.mark.parametrize("db_cls,", DBCLS)
def test_rule_join(db_cls):
    """Test a basic join query - the parent -> grandparent relation."""

    child = Constant("child")
    gc = Constant("grandchild")

    d = read(
        """
child(a, b).
child(b, c).
child(b, d).
child(b, e).

grandchild(A, B) :-
  child(A, C),
  child(C, B).
""",
        db_cls=db_cls,
    )

    assert select(d, ("grandchild", "a", "X",)) == [
        ((("grandchild", "a", "c"),), {"X": "c"}),
        ((("grandchild", "a", "d"),), {"X": "d"}),
        ((("grandchild", "a", "e"),), {"X": "e"}),
    ]


@pytest.mark.parametrize("db_cls,", DBCLS)
def test_antijoin(db_cls):
    """Test a query containing an antijoin."""

    d = read(
        """
a(foo, bar).
b(foo, bar).
a(baz, qux).
% matching b(baz, qux). is our antijoin test

no-b(X, Y) :-
  a(X, Y),
  ~b(X, Z).
""",
        db_cls=db_cls,
    )

    assert select(d, ("no-b", "X", "Y")) == [
        ((("no-b", "baz", "qux"),), {"X": "baz", "Y": "qux"})
    ]


@pytest.mark.parametrize("db_cls,", DBCLS)
def test_nested_antijoin(db_cls):
    """Test a query which negates a subquery which uses an antijoin.

    Shouldn't exercise anything more than `test_antjoin` does, but it's an interesting case since you
    actually can't capture the same semantics using a single query. Antijoins can't propagate positive
    information (create lvar bindings) so I'm not sure you can express this another way without a
    different evaluation strategy.

    """

    d = read(
        """
a(foo, bar).
b(foo, bar).
a(baz, qux).
b(baz, quack).

b-not-quack(X, Y) :-
  b(X, Y),
  ~=(Y, quack).

a-no-nonquack(X, Y) :-
  a(X, Y),
  ~b-not-quack(X, Y).
""",
        db_cls=db_cls,
    )

    assert select(d, ("a-no-nonquack", "X", "Y")) == [
        ((("a-no-nonquack", "baz", "qux"),), {"X": "baz", "Y": "qux"})
    ]


@pytest.mark.parametrize("db_cls,", DBCLS)
def test_alternate_rule(db_cls):
    """Testing that both recursion and alternation work."""

    d = read(
        """
edge(a, b).
edge(b, c).
edge(c, d).
edge(d, e).
edge(e, f).

path(A, B) :-
  edge(A, B).

path(A, B) :-
  edge(A, C),
  path(C, B).
""",
        db_cls=db_cls,
    )

    # Should be able to recurse to this one.
    assert select(d, ("path", "a", "f")) == [((("path", "a", "f"),), {})]


# FIXME (arrdem 2019-06-13):
#
#   This test is BROKEN for the simple dataset.  In order for left-recursive production rules to
#   work, they have to ground out somewhere.  Under the naive, cache-less datalog this is an
#   infinite left recursion.  Under the cached versions, the right-recursion becomes iteration over
#   an incrementally realized list which ... is weird but does work because the recursion grounds
#   out in iterating over an empty list on the 2nd round then falls through to the other production
#   rule which generates ground tuples and feeds everything.
#
#   It's not clear how to make this work with the current (lack of) query planner on the naive db as
#   really fixing this requires some amount of insight into the data dependency structure and may
#   involve reordering rules.
@pytest.mark.parametrize("db_cls,", DBCLS)
def test_alternate_rule_lrec(db_cls):
    """Testing that both recursion and alternation work."""

    if db_cls == Dataset:
        pytest.xfail("left-recursive rules aren't supported with a trivial store and no planner")

    d = read(
        """
edge(a, b).
edge(b, c).
edge(c, d).
edge(d, e).
edge(e, f).

path(A, B) :-
  edge(A, B).

path(A, B) :-
  path(A, C),
  edge(C, B).
""",
        db_cls=db_cls,
    )

    # Should be able to recurse to this one.
    assert select(d, ("path", "a", "f")) == [((("path", "a", "f"),), {})]


@pytest.mark.parametrize("db_cls,", DBCLS)
def test_cojoin(db_cls):
    """Tests that unification occurs correctly."""

    d = read(
        """
edge(a, b).
edge(b, c).
edge(c, d).
edge(d, e).
edge(e, f).
edge(c, q).

two_path(A, B, C) :- edge(A, B), edge(B, C).
""",
        db_cls=db_cls,
    )

    # Should be able to recurse to this one.
    assert [t for t, _ in select(d, ("two_path", "A", "B", "C"))] == [
        (("two_path", "a", "b", "c"),),
        (("two_path", "b", "c", "d"),),
        (("two_path", "b", "c", "q"),),
        (("two_path", "c", "d", "e"),),
        (("two_path", "d", "e", "f"),),
    ]
