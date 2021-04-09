"""
Tests covering the Flowmetal analyzer.
"""

import flowmetal.parser as p
import flowmetal.syntax_analyzer as a

import pytest


@pytest.mark.parametrize('txt, exprtype', [
    # Booleans
    ('true', a.ConstExpr),
    ('false', a.BooleanExpr),
    # Integers
    ('1', a.ConstExpr),
    ('1', a.IntegerExpr),
    # Fractions
    ('1/2', a.ConstExpr),
    ('1/2', a.FractionExpr),
    # Floats
    ('1.0', a.ConstExpr),
    ('1.0', a.FloatExpr),
    # Keywords
    (':foo', a.ConstExpr),
    (':foo', a.KeywordExpr),
    # Strings
    ('"foo"', a.ConstExpr),
    ('"foo"', a.StringExpr),
])
def test_analyze_constants(txt, exprtype):
    """Make sure the analyzer can chew on constants."""
    assert isinstance(a.analyzes(txt), exprtype)


@pytest.mark.parametrize('txt', [
    '()',
    '(list)',
    '(list 1)',
    '(do 1)',
    '(do foo bar 1)',
    '(let [a 1, b 2] 1)',
    '(fn [] 1)',
    '(fn [] ⊢ integer? x)',
    '(fn [] x |- integer?)',
    '(fn [] x :- integer?)',
])
def test_analyze(txt):
    """Make sure that do exprs work."""
    assert a.analyzes(txt)
