"""Tests based off of round-tripping randomly generated examples."""

from hypothesis import given
from hypothesis.strategies import integers
import proquint


@given(integers(min_value=0, max_value=1 << 16))
def test_round_trip_16(val):
    assert proquint.Proquint.decode(proquint.Proquint.encode(val, 16)) == val


@given(integers(min_value=0, max_value=1 << 32))
def test_round_trip_32(val):
    assert proquint.Proquint.decode(proquint.Proquint.encode(val, 32)) == val


@given(integers(min_value=0, max_value=1 << 64))
def test_round_trip_64(val):
    assert proquint.Proquint.decode(proquint.Proquint.encode(val, 64)) == val


@given(integers(min_value=0, max_value=1 << 512))
def test_round_trip_512(val):
    assert proquint.Proquint.decode(proquint.Proquint.encode(val, 512)) == val
