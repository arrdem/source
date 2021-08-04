"""Tests based off of known examples."""

import proquint
import pytest


examples = [
    # Various single-bit data
    (1, 32, "babab-babad"),
    (2, 32, "babab-babaf"),
    (4, 32, "babab-babah"),
    (8, 32, "babab-babam"),
    (16, 32, "babab-babib"),
    (32, 32, "babab-babob"),
    (64, 32, "babab-badab"),
    (128, 32, "babab-bafab"),
    (256, 32, "babab-bahab"),
    (512, 32, "babab-bamab"),
    (1024, 32, "babab-bibab"),
    (2048, 32, "babab-bobab"),
    (4096, 32, "babab-dabab"),
    (8192, 32, "babab-fabab"),
    (16384, 32, "babab-habab"),
    (32768, 32, "babab-mabab"),
    (65536, 32, "babad-babab"),
    (131072, 32, "babaf-babab"),
    (262144, 32, "babah-babab"),
    (524288, 32, "babam-babab"),
    (1048576, 32, "babib-babab"),
    (2097152, 32, "babob-babab"),
    (4194304, 32, "badab-babab"),
    (8388608, 32, "bafab-babab"),
    (16777216, 32, "bahab-babab"),
    (33554432, 32, "bamab-babab"),
    (67108864, 32, "bibab-babab"),
    (134217728, 32, "bobab-babab"),
    (268435456, 32, "dabab-babab"),
    (536870912, 32, "fabab-babab"),
    (1073741824, 32, "habab-babab"),
    (2147483648, 32, "mabab-babab"),

    # A random value
    (3232235536, 32, "safom-babib"),
]


@pytest.mark.parametrize("val,width,qint", examples)
def test_decode_examples(val, width, qint):
    assert proquint.Proquint.decode(qint) == val, f"qint {qint} did not decode"


@pytest.mark.parametrize("val,width,qint", examples)
def test_encode_examples(val, width, qint):
    encoded_qint = proquint.Proquint.encode(val, width)
    decoded_val = proquint.Proquint.decode(encoded_qint)
    assert encoded_qint == qint, f"did not encode {val} to {qint}; got {encoded_qint} ({decoded_val})"
