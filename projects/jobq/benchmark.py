"""
Benchmarking the jobq.
"""

from contextlib import contextmanager
from time import perf_counter_ns
from abc import abstractclassmethod
import os
from random import randint, choice
import string
from statistics import mean, median, stdev
import tempfile
import logging

from jobq import JobQueue


def randstr(len):
    return ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(len))


class Timing(object):
    def __init__(self, start):
        self.start = start
        self.end = None

    @property
    def duration(self):
        if self.end:
            return self.end - self.start


@contextmanager
def timing():
    """A context manager that produces a semi-mutable timing record."""

    obj = Timing(perf_counter_ns())
    yield obj
    obj.end = perf_counter_ns()


def bench(callable, reps):
    timings = []
    with timing() as run_t:
        for _ in range(reps):
            with timing() as t:
                callable()
            timings.append(t.duration)
    print(f"""Ran {callable.__name__!r} {reps} times, total time {run_t.duration / 1e9} (s)
  mean: {mean(timings) / 1e9} (s)
  median: {median(timings) / 1e9} (s)
  stddev: {stdev(timings) / 1e9} (s)
  test overhead: {(run_t.duration - sum(timings)) / reps / 1e9} (s)
""")


def test_insert(q, reps):
    # Measuring insertion time
    jobs = [
        {"user_id": randint(0, 1<<32), "msg": randstr(256)}
        for _ in range(reps)
    ]
    jobs_i = iter(jobs)

    def insert():
        q.create(next(jobs_i), new_state=["CREATED"])

    bench(insert, reps)


def test_poll(q, reps):

    def poll():
        q.poll([["=", "json_extract(j.state, '$[0]')", "'CREATED'"]], ["POLLED"])

    bench(poll, reps)


def test_append(q, reps):
    def append_event():
        q.append_event(randint(1, reps), {"foo": "bar"})

    bench(append_event, reps)


if __name__ == "__main__":
    # No logs
    logging.getLogger().setLevel(logging.WARN)

    # Test params
    reps = 10000
    path = "/tmp/jobq-bench.sqlite3"

    # Ensuring a clean-ish run env.
    if os.path.exists(path):
        os.remove(path)

    # And the tests
    print(f"Testing with {path}")
    q = JobQueue(path)
    test_insert(q, reps)
    test_poll(q, reps)
    test_append(q, reps)

    print(f"Testing with :memory:")
    q = JobQueue(":memory:")
    test_insert(q, reps)
    test_poll(q, reps)
    test_append(q, reps)
