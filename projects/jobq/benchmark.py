"""
Benchmarking the jobq.
"""

from contextlib import contextmanager
import json
import logging
import os
from random import choice, randint
from statistics import mean, median, stdev
import string
import tempfile
from time import perf_counter_ns

from jobq import JobQueue


def randstr(len):
    return "".join(choice(string.ascii_uppercase + string.digits) for _ in range(len))


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


def timer(val: float) -> str:
    """Given a time in NS, convert it to integral NS/MS/S such that the non-decimal part is integral."""

    for factor, unit in [
            (1e9, "s"),
            (1e6, "ms"),
            (1e3, "us"),
            (1, "ns"),
    ]:
        scaled_val = val / factor
        if 1e4 > scaled_val > 1.0:
            return f"{scaled_val} {unit}"


def bench(callable, reps):
    timings = []
    with timing() as run_t:
        for _ in range(reps):
            with timing() as t:
                callable()
            timings.append(t.duration)
    print(f"""Ran {callable.__name__!r} {reps} times, total time {timer(run_t.duration)}
  mean: {timer(mean(timings))}
  median: {timer(median(timings))}
  stddev: {timer(stdev(timings))}
  test overhead: {timer((run_t.duration - sum(timings)) / reps)}
""")


def test_reference_json(reps):
    """As a reference benchmark, test just appending to a file."""

    jobs = [
        {"user_id": randint(0, 1<<32), "msg": randstr(256)}
        for _ in range(reps)
    ]
    jobs_i = iter(jobs)

    def naive_serialize():
        json.dumps([next(jobs_i), ["CREATED"]])

    bench(naive_serialize, reps)


def test_reference_fsync(reps):
    """As a reference benchmark, test just appending to a file."""

    jobs = [
        {"user_id": randint(0, 1<<32), "msg": randstr(256)}
        for _ in range(reps)
    ]
    jobs_i = iter(jobs)

    handle, path = tempfile.mkstemp()
    os.close(handle)
    with open(path, "w") as fd:
        def naive_fsync():
            fd.write(json.dumps([next(jobs_i), ["CREATED"]]))
            fd.flush()
            os.fsync(fd.fileno())

        bench(naive_fsync, reps)


def test_insert(q, reps):
    """Benchmark insertion time to a given SQLite DB."""

    jobs = [
        {"user_id": randint(0, 1<<32), "msg": randstr(256)}
        for _ in range(reps)
    ]
    jobs_i = iter(jobs)

    def insert():
        q.create(next(jobs_i), new_state=["CREATED"])

    bench(insert, reps)


def test_poll(q, reps):
    """Benchmark query/update time on a given SQLite DB."""

    def poll():
        q.poll("json_extract(j.state, '$[0]') = 'CREATED'", ["POLLED"])

    bench(poll, reps)


def test_append(q, reps):
    """Benchmark adding an event on a given SQLite DB."""

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

    print("Getting a baseline")
    test_reference_json(reps)
    test_reference_fsync(reps)

    # And the tests
    print(f"Testing with {path}")
    q = JobQueue(path)
    test_insert(q, reps)
    test_poll(q, reps)
    test_append(q, reps)

    print("Testing with :memory:")
    q = JobQueue(":memory:")
    test_insert(q, reps)
    test_poll(q, reps)
    test_append(q, reps)
