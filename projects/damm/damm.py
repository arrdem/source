"""
An implementation of Damm check digits.
"""

import re
from typing import NamedTuple


class DammException(Exception):
    """Base class for all exceptions in the module."""


class CheckDigitException(DammException):
    """Thrown when a string did not check when decoding a supposedly checked string."""


class NoMatchException(DammException):
    """Thrown when a string did not match."""


class Damm(NamedTuple):
    """A Damm coded number."""

    MATRIX = (
        (0, 3, 1, 7, 5, 9, 8, 6, 4, 2),
        (7, 0, 9, 2, 1, 5, 4, 8, 6, 3),
        (4, 2, 0, 6, 8, 7, 1, 3, 5, 9),
        (1, 7, 5, 0, 9, 8, 3, 4, 2, 6),
        (6, 1, 2, 3, 0, 4, 5, 9, 7, 8),
        (3, 6, 7, 4, 2, 0, 9, 5, 8, 1),
        (5, 8, 6, 9, 7, 2, 0, 1, 3, 4),
        (8, 9, 4, 5, 3, 6, 2, 0, 1, 7),
        (9, 4, 3, 8, 6, 1, 7, 2, 0, 5),
        (2, 5, 8, 1, 4, 3, 6, 7, 9, 0),
    )

    DAMM_PATTERN = re.compile(r"(?P<value>\d+)-?(?P<check>\d)")

    value: int

    def __str__(self):
        return f"{self.value}-{self.encode(self.value)}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value}, {self.encode(self.value)})"

    @classmethod
    def encode(cls, value):
        state = 0
        for digit in str(value):
            state = cls.MATRIX[state][int(digit)]
        return state

    @classmethod
    def verify(cls, value: str) -> bool:
        """Verify a Damm encoded number, returning its value if valid.

        The core Damm encoding property is that the LAST digit is ALWAYS the check. When the rest of
        the string is correctly Damm encoded, the Damm of the entire string will be 0.

        """
        return cls.encode(int(value.replace("-", ""))) == 0

    @classmethod
    def from_str(cls, value: str) -> "Damm":
        """Verify a Damm coded string, and return its decoding."""
        if match := re.fullmatch(cls.DAMM_PATTERN, value):
            given_value = match.group("value")
            computed_code = cls.encode(given_value)
            given_code = int(match.group("check"))
            if computed_code == given_code:
                return Damm(int(given_value))
            else:
                raise CheckDigitException(
                    f"Value {value!r} had check digit {given_code!r}, but computed check was {computed_code!r}"
                )
        else:
            raise NoMatchException(f"Input {value!r} was not a valid decimal number")
