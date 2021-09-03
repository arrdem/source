"""Proquint - pronounceable codings of integers.

Implemented from http://arxiv.org/html/0901.4016

Quoting -

    we propose encoding a 16-bit string as a proquint of alternating consonants and vowels as follows.

    Four-bits as a consonant:

        0 1 2 3 4 5 6 7 8 9 A B C D E F
        b d f g h j k l m n p r s t v z

    Two-bits as a vowel:

        0 1 2 3
        a i o u

    Whole 16-bit word, where "con" = consonant, "vo" = vowel:

         0 1 2 3 4 5 6 7 8 9 A B C D E F
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |con    |vo |con    |vo |con    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    Separate proquints using dashes, which can go un-pronounced or be pronounced "eh". The suggested optional magic number prefix to a sequence of proquints is "0q-".

    Here are some IP dotted-quads and their corresponding proquints.

        127.0.0.1       lusab-babad
        63.84.220.193   gutih-tugad
        63.118.7.35     gutuk-bisog
        140.98.193.141  mudof-sakat
        64.255.6.200    haguz-biram
        128.30.52.45    mabiv-gibot
        147.67.119.2    natag-lisaf
        212.58.253.68   tibup-zujah
        216.35.68.215   tobog-higil
        216.68.232.21   todah-vobij
        198.81.129.136  sinid-makam
        12.110.110.204  budov-kuras

"""

from functools import cache


class Proquint(object):
    # Class parameters
    ################################################################################################
    CONSONANTS = "bdfghjklmnprstvz"
    VOWELS = "aiou"

    # Implementation helpers
    ################################################################################################
    @classmethod
    @cache
    def _consonant_to_uint(cls, c: str) -> int:
        try:
            return cls.CONSONANTS.index(c)
        except ValueError:
            return

    @classmethod
    @cache
    def _vowel_to_uint(cls, c: str) -> int:
        try:
            return cls.VOWELS.index(c)
        except ValueError:
            return

    @classmethod
    def _encode(cls, buffer: bytes) -> str:
        # This is a bit tricky.
        # Proquints are encoded not out of 8bi quantities but out of 16bi quantities.
        #
        # Example from the proposal:
        #
        #      0 1 2 3 4 5 6 7 8 9 A B C D E F
        #      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #      |con    |vo |con    |vo |con    |
        #      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #
        # Now, while this is the bit-order interpretation, note it's left-to-right not right-to-left
        # as english is written. This means that the highest order bits in RTL will be written
        # first, so the chunks are 0xC, 0xA, 0x6, 0x4, 0x0
        for n, m in zip(buffer[0::2], buffer[1::2]):
            # Rebuild the two 8bi pairs into a 16bi chunk
            val = n << 8 | m

            # This is slightly un-idiomatic, but it precisely captures the coding definition
            yield "".join(
                [
                    dict[val >> shift & mask]
                    for dict, shift, mask in [
                        (cls.CONSONANTS, 0xC, 0xF),
                        (cls.VOWELS, 0xA, 0x3),
                        (cls.CONSONANTS, 0x6, 0xF),
                        (cls.VOWELS, 0x4, 0x3),
                        (cls.CONSONANTS, 0x0, 0xF),
                    ]
                ]
            )

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

        for i, c in enumerate([c for c in buffer if c != "-"]):
            if (mag := cls._consonant_to_uint(c)) is not None:
                res <<= 4
                res += mag
            else:
                mag = cls._vowel_to_uint(c)
                if mag is not None:
                    res <<= 2
                    res += mag
                elif i != 5:
                    raise ValueError("Bad proquint format")
        return res

    # Handy aliases
    ################################################################################################
    @classmethod
    def encode(cls, val: int, width: int):
        """Encode an integer into a proquint string."""

        if width % 8 != 0 or width < 8:
            raise ValueError("Width must be a positive power of 2 greater than 8")

        return cls.encode_bytes(val.to_bytes(width // 8, "big"))

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
