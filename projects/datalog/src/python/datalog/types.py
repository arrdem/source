#!/usr/bin/env python3

"""
The core IR types for datalog.
"""

from collections import namedtuple
from typing import Sequence, Tuple, Union


class Constant(namedtuple("Constant", ["value"])):
    """Representation of a constant for interpreter dispatching."""


class LVar(namedtuple("LVar", ["name"])):
    """Representation of an LVar for interpreter dispatching."""


class Rule(namedtuple("Rule", ["pattern", "clauses"])):
    """Representation of an Rule for the interpreter."""

    def __new__(cls, pattern, clauses):
        return super(cls, Rule).__new__(cls, pattern, tuple(clauses))

    @property
    def used_vars(self):
        return {e for e in self.pattern if isinstance(e, LVar)}

    @property
    def bound_vars(self):
        return {e for c in self.clauses for e in c if isinstance(e, LVar)}

    @property
    def free_vars(self):
        return {v for v in self.used_vars if v not in self.bound_vars}


# Logical type for 'Tuple' as we're gonna use it for the rest of the thing.
LTuple = Tuple[Union[Constant, LVar]]
CTuple = Tuple[Constant]


class Dataset(object):
    """A set of tuples and rules which can be queried."""

    def __init__(self, tuples: Sequence[CTuple], rules: Sequence[Rule]):
        self.__tuples = tuples
        self.__rules = rules

    def tuples(self) -> Sequence[CTuple]:
        for t in self.__tuples:
            yield t

    def rules(self) -> Sequence[Rule]:
        for r in self.__rules:
            yield r

    def merge(self, other: "Dataset") -> "Dataset":
        """Merge two datasets together, returning a new one."""

        return type(self)(
            list({*self.tuples(), *other.tuples()}), [*self.rules(), *other.rules()]
        )


class CachedDataset(Dataset):
    """An extension of the dataset which features a cache of rule produced tuples.

  Note that this cache is lost when merging datasets - which ensures correctness.
  """

    # Inherits tuples, rules, merge

    def __init__(self, tuples, rules):
        super(__class__, self).__init__(tuples, rules)
        # The cache is a mapping from a Rule to tuples produced by it.
        self.__cache = {}

    def scan_cache(self, rule_tuple):
        if rule_tuple in self.__cache:
            return iter(self.__cache.get(rule_tuple))

    def cache_tuple(self, rule_tuple, tuple: CTuple):
        coll = self.__cache.get(rule_tuple, list())
        self.__cache[rule_tuple] = coll
        if tuple not in coll:
            coll.append(tuple)


class TableIndexedDataset(CachedDataset):
    """An extension of the Dataset type which features both a cache and an index by table & length.

  The index allows more efficient scans by maintaining 'table' style partitions.
  It does not support user-defined indexing schemes.

  Note that index building is delayed until an index is scanned.
  """

    # From Dataset:
    #   tuples, rules, merge
    # from CachedDataset:
    #   cache_tuple, scan_cache

    @staticmethod
    def __key(t: LTuple) -> str:
        assert isinstance(t[0], Constant)
        return f"{t[0].value}_{len(t)}"

    def __init__(self, tuples, rules):
        super(__class__, self).__init__(tuples, rules)
        self.__index = {}

    def __build_indices(self):
        if not self.__index:
            for t in self.tuples():
                key = self.__key(t)
                # FIXME: Walrus operator???
                coll = self.__index[key] = self.__index.get(key, list())
                coll.append(t)

    def scan_index(self, t: LTuple) -> Sequence[CTuple]:
        self.__build_indices()
        for t in self.__index.get(self.__key(t), []):
            yield t


class PartlyIndexedDataset(TableIndexedDataset):
    """An extension of the Dataset type which features both a cache and and a full index by table,
  length, tuple index and value.

  The index allows extremely efficient scans when elements of the tuple are known.

  """

    # From Dataset:
    #   tuples, rules, merge
    # from CachedDataset:
    #   cache_tuple, scan_cache
    # from IndexedDataset / TableIndexedDataset:
    #   scan_index

    @staticmethod
    def __key(t: LTuple, i: int) -> str:
        assert isinstance(t[0], Constant)
        return (f"{t[0].value}_{len(t)}_{i}", t[i])

    def __init__(self, tuples, rules, index_prefix=999):
        super(__class__, self).__init__(tuples, rules)
        self.__index_prefix = index_prefix
        self.__index = {}

    def __build_indices(self):
        if not self.__index:
            self.__index = index = {}
            # Index by single value
            for t in self.tuples():
                for e, i in zip(t, range(self.__index_prefix)):
                    key = self.__key(t, i)
                    # FIXME: Walrus operator???
                    coll = index[key] = index.get(key, list())
                    coll.append(t)

    def scan_index(self, t: LTuple) -> Sequence[CTuple]:
        self.__build_indices()

        default_key = self.__key(t, 0)
        column_indices = []
        for e, i in zip(t, range(self.__index_prefix)):
            if isinstance(e, Constant):
                _k = self.__key(t, i)
                v = self.__index.get(_k)
                if v:
                    column_indices.append((_k, v))
                else:
                    # If there's no such index, then there's no such tuple. Abort.
                    return iter([])

        if column_indices:
            sorted(column_indices, key=lambda x: len(x[1]))
            key, l = column_indices[-1]
        else:
            key = default_key
            l = self.__index[key] = self.__index.get(key, list())

        return iter(l)
