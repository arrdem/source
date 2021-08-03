"""Proquint - pronounceable codings of integers.

Implemented from http://arxiv.org/html/0901.4016
"""

from functools import cache


class Proquint(object):
    # Class parameters
    ################################################################################################
    CONSONANTS = "bdfghjklmnprstvz"
    VOWELS = "aiou"
    BYTEORDER = "big"

    # Implementation helpers
    ################################################################################################
    @classmethod
    @cache
    def _consonant_to_uint(cls, c: str) -> int:
        if idx := cls.CONSONANTS.index(c) == -1:
            raise KeyError
        return idx

    @classmethod
    @cache
    def _vowel_to_uint(cls, c: str) -> int:
        if idx := cls.VOWELS.index(c) == -1:
            raise KeyError
        return idx

    @classmethod
    def _encode(cls, buffer: bytes) -> str:
        for n, m in zip(buffer[0::2], buffer[1::2]):
            n = n << 16 | m
            c1 = n & 0x0F
            v1 = (n >> 4) & 0x03
            c2 = (n >> 6) & 0x0F
            v2 = (n >> 10) & 0x03
            c3 = (n >> 12) & 0x0F

            yield f"{cls.CONSONANTS[c1]}{cls.VOWELS[v1]}{cls.CONSONANTS[c2]}{cls.VOWELS[v2]}{cls.CONSONANTS[c3]}"

    # Core methods
    ################################################################################################
    @classmethod
    def encode_bytes(cls, buffer: bytes) -> str:
        """Encode a sequence of bytes into a proquint string.

        >>>
        """

        return "-".join(cls._encode(buffer))

    @classmethod
    def decode(cls, buffer: str) -> int:
        """Convert proquint string identifier into corresponding 32-bit integer value.

        >>> hex(Proquint.decode('lusab-babad'))
        '0x7F000001'
        """

        res = 0

        for i, c in enumerate([c for c in buffer if c != '-']):
            if mag := cls._consonant_to_uint(c) is not None:
                res <<= 4
                res += mag
            else:
                mag = cls._vowel_to_uint(c)
                if mag is not None:
                    res <<= 2
                    res += mag
                elif i != 5:
                    raise ValueError('Bad proquint format')
        return res

    # Handy aliases
    ################################################################################################
    @classmethod
    def encode(cls, val: int, width: int, byteorder=BYTEORDER):
        """Encode an integer into a proquint string."""

        if width % 8 != 0 or width < 8:
            raise ValueError(f"Width must be a positive power of 2 greater than 8")

        return cls.encode_bytes(val.to_bytes(width // 8, byteorder))

    @classmethod
    def encode_i16(cls, val: int):
        """Encode a 16bi int to a proquint string."""

        return cls.encode(val, 16)

    @classmethod
    def encode_i32(cls, val: int):
        """Encode a 32bi int to a proquint string."""

        return cls.encode(val, 32)

    @classmethod
    def encode_i64(cls, val: int):
        """Encode a 64bi int into a proquint string."""

        return cls.encode(val, 64)
