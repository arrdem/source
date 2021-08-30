"""Debris."""

from random import shuffle

from datalog.types import LVar


def shuffled(seq):
    """Because random.shuffle() is in-place >.>"""
    s = seq.copy()
    shuffle(s)
    return s


def constexpr_p(expr):
    """Predicate. True of all terms of the expr are constants."""

    return all(isinstance(e, LVar) for e in expr)


class Timing(object):
    """
    A context manager object which records how long the context took.
    """

    def __init__(self):
        self.start = None
        self.end = None

    def __enter__(self):
        from datetime import datetime

        self.start = datetime.utcnow()
        return self

    def __exit__(self, type, value, traceback):
        from datetime import datetime

        self.end = datetime.utcnow()

    def __call__(self):
        """
        If the context is exited, return its duration. Otherwise return the duration "so far".
        """

        from datetime import datetime

        if self.start and self.end:
            return self.end - self.start
        else:
            return datetime.utcnow() - self.start

    def __str__(self):
        return str(self())
