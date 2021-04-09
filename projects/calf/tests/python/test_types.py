"""
Tests covering the Calf types.
"""

from calf import types as t


def test_maps_check():
    assert isinstance(t.Map.of([(1, 2)]), t.Map)


def test_vectors_check():
    assert isinstance(t.Vector.of([(1, 2)]), t.Vector)


def test_sets_check():
    assert isinstance(t.Set.of([(1, 2)]), t.Set)
