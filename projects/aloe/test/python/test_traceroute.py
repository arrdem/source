#!/usr/bin/env python3

from typing import List
from traceroute import _parse_traceroute, TraceElem
from datetime import timedelta

import pytest


def parse_traceroute(lines):
    """Testing helper."""
    return list(_parse_traceroute(lines))


@pytest.mark.parametrize("example, expected", [
    # Basic case, one match
    ("3  10.60.142.2 (10.60.142.2)  117.502 ms",
     [TraceElem("10.60.142.2", "10.60.142.2", timedelta(milliseconds=117.502))]),
    # Multiple matches on one line
    ("3  10.60.142.2 (10.60.142.2)  117.502 ms 10.60.142.3 (10.60.142.3)  75.624 ms 10.60.142.2 (10.60.142.2)  117.709 ms",
     [TraceElem("10.60.142.2", "10.60.142.2", timedelta(milliseconds=117.502)),
      TraceElem("10.60.142.3", "10.60.142.3", timedelta(milliseconds=75.624)),
      TraceElem("10.60.142.2", "10.60.142.2", timedelta(milliseconds=117.709))]),
    # Context sensitive case - traceroute doesn't always print the host & IP.
    ("7  ae-501-ar01.denver.co.denver.comcast.net (96.216.22.130)  41.920 ms  41.893 ms  74.385 ms",
     [TraceElem("ae-501-ar01.denver.co.denver.comcast.net", "96.216.22.130", timedelta(milliseconds=41.920)),
      TraceElem("ae-501-ar01.denver.co.denver.comcast.net", "96.216.22.130", timedelta(milliseconds=41.893)),
      TraceElem("ae-501-ar01.denver.co.denver.comcast.net", "96.216.22.130", timedelta(milliseconds=74.385))]),
])
def test_examples(example: str, expected: List[TraceElem]):
    assert parse_traceroute(example.splitlines()) == expected
