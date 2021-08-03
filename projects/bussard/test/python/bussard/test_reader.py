"""
Tests of the Bussard reader.
"""

import bussard.reader as t
from bussard.reader import Actions, Parser, read, read1


def parse_word(input):
    return Parser(input, Actions(), None)._read_word()


def test_parse_name():
    assert "foo" == parse_word("foo")
    assert "foo" == parse_word("foo bar")
    assert "foo" == parse_word("foo	bar")
    assert "foo-bar" == parse_word("foo-bar")
    assert "*" == parse_word("*")
    assert "*.foo" == parse_word("*.foo")


def test_read_ttl():
    assert isinstance(
        read1(
            """$TTL 300
"""
        ),
        t.TTL,
    )


def test_read_origin():
    assert isinstance(
        read1(
            """$ORIGIN foobar.org
"""
        ),
        t.ORIGIN,
    )


def test_read_soa():
    """Test a couple of SOA cases, exercising both parsing and formatting."""

    # Basically no formatting.
    assert isinstance(
        read1(
            """@ IN SOA ns1. root. (2020012301 60 90 1w 60)
"""
        ),
        t.SOA,
    )

    # With a TTL
    assert isinstance(
        read1(
            """@ 300 IN SOA ns1. root. (2020012301 60 90 1w 60)
"""
        ),
        t.SOA,
    )

    # Some meaningful formatting.
    assert isinstance(
        read1(
            """@ IN SOA ns1. root. (
   2020012301 ; comment
   60 ; comment
   90 ; comment
   1w ; comment
   60 ; comment
)
"""
        ),
        t.SOA,
    )


def test_read_a():
    """Test that some A records parse."""

    assert isinstance(
        read1(
            """@ IN A 127.0.0.1
"""
        ),
        t.A,
    )

    # With a TTL
    assert isinstance(
        read1(
            """@ 300 IN A 127.0.0.1
"""
        ),
        t.A,
    )

    # With a TTL & comment
    assert isinstance(
        read1(
            """@ 300 IN A 127.0.0.1; comment
"""
        ),
        t.A,
    )

    # With a TTL & comment & whitespace
    assert isinstance(
        read1(
            """@ 300 IN A 127.0.0.1  	; comment
"""
        ),
        t.A,
    )


def test_read_aaaa():
    """Test that some quad-a records parse"""

    assert isinstance(
        read1(
            """foo IN AAAA ::1
"""
        ),
        t.AAAA,
    )

    # With a TTL
    assert isinstance(
        read1(
            """foo 300 IN AAAA ::1
"""
        ),
        t.AAAA,
    )

    # With a TTL & comment
    assert isinstance(
        read1(
            """foo 300 IN AAAA ::1; comment
"""
        ),
        t.AAAA,
    )

    # With a TTL & whitespace & comment
    assert isinstance(
        read1(
            """foo 300 IN AAAA ::1  	; comment
"""
        ),
        t.AAAA,
    )


def test_read_cname():
    """Test some CNAME cases."""

    assert isinstance(
        read1(
            """bar IN CNAME qux.
"""
        ),
        t.CNAME,
    )

    assert isinstance(
        read1(
            """bar IN CNAME bar-other
"""
        ),
        t.CNAME,
    )

    # With TTL
    assert isinstance(
        read1(
            """bar 300 IN CNAME bar-other.
"""
        ),
        t.CNAME,
    )

    # With TTL & comment
    assert isinstance(
        read1(
            """bar 300 IN CNAME bar-other.; comment
"""
        ),
        t.CNAME,
    )

    # With TTL & comment
    assert isinstance(
        read1(
            """bar 300 IN CNAME bar-other.  	; comment
"""
        ),
        t.CNAME,
    )


def test_read_mx():
    """Some MX record examples."""

    assert isinstance(
        read1(
            """@ IN MX 10 mx1.
"""
        ),
        t.MX,
    )

    # With TTL
    assert isinstance(
        read1(
            """@ 300 IN MX 10 mx1.
"""
        ),
        t.MX,
    )

    # With TTL & comment
    assert isinstance(
        read1(
            """@ 300 IN MX 10 mx1.;bar
"""
        ),
        t.MX,
    )

    # With TTL & comment
    assert isinstance(
        read1(
            """@ 300 IN MX 10 mx1. ; bar
"""
        ),
        t.MX,
    )


def test_read_repeated():
    """Test t=support for repetition."""

    assert all(
        isinstance(e, t.A)
        for e in read(
            """foo IN A 10.0.0.1
  IN A 10.0.0.2; comment
  IN A 10.0.0.3 ; with whitespace
"""
        )
    )

    # Note that comments and newlines become raw strings
    assert all(
        list(
            isinstance(e, (t.A, str))
            for e in read(
                """foo IN A 10.0.0.1
; comment
  IN A 10.0.0.2; comment

  IN A 10.0.0.3 ; with whitespace
"""
            )
        )
    )
