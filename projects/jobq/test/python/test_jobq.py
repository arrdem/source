"""
Tests covering the jobq API
"""

import logging
from time import sleep

from jobq import Job, JobQueue
import pytest


logging.getLogger().setLevel(logging.DEBUG)


@pytest.fixture
def db():
    return JobQueue(":memory:")


@pytest.fixture
def payload():
    return "a basic payload"


def test_create(db, payload):
    """Assert that create does the thing."""

    j = db.create(payload)

    assert j
    assert isinstance(j, Job)
    assert j.id == 1
    assert j.payload == payload


def test_create_get(db, payload):
    """Assert that get-after-create returns the same value."""

    j = db.create(payload)

    assert j == db.get(j.id)


def test_poll(db):
    """Test that we can poll a job, and the oldest wins."""

    j1 = db.create("payload 1")
    j2 = db.create("payload 2")
    assert j1.modified == j2.modified, "Two within the second to force the `rowid` ASC"
    sleep(1)  # And a side-effect for the third one
    db.create("payload 3")

    j = db.poll("true", ["assigned"])

    assert isinstance(j, Job)
    assert j.id == j1.id, "j1 is the oldest in the system and should poll first."
    assert j.state == ["assigned"]


def test_poll_not_found(db):
    """Test that poll can return nothing."""

    db.create("payload 1")
    j = db.poll("false", ["assigned"])
    assert j is None


def test_append(db, payload):
    """Test that appending an event to the log does append and preserves invariants."""

    j = db.create(payload)
    sleep(1)  # side-effect so that sqlite3 gets a different commit timestamp
    j_prime = db.append_event(j.id, "some user-defined event")

    assert isinstance(j_prime, Job)
    assert j != j_prime
    assert j_prime.id == j.id
    assert j_prime.state == j.state
    assert j_prime.modified > j.modified
    assert j_prime.events != j.events
    assert j_prime.events[:-1] == j.events


def test_cas_ok(db):
    """Test that we can CAS a job from one state to the 'next'."""

    j = db.create("job2", ["state", 2])
    sleep(1)  # side-effect so that sqlite3 gets a different commit timestamp
    j_prime = db.cas_state(j.id, ["state", 2], ["state", 3])

    assert isinstance(j_prime, Job), "\n".join(db._db.iterdump())
    assert j != j_prime
    assert j_prime.id == j.id
    assert j_prime.state != j.state
    assert j_prime.modified > j.modified
    assert j_prime.events != j.events
    assert j_prime.events[:-1] == j.events


def test_cas_fail(db):
    """Test that if we have a 'stale' old state CAS fails."""

    j = db.create("job2", ["state", 2])
    j_prime = db.cas_state(j.id, ["state", 1], ["state", 2])

    assert j_prime is None
