#!/usr/bin/env python3

"""A reader, integrating the generated parser and types.

Integrates the generated parser with the types, providing a reasonable way to interface with both
zonefiles through the parser.

"""

from types import LambdaType

from bussard.gen.parser import (  # noqa
    parse as _parse,
    Parser,
)
from bussard.gen.types import *  # noqa


def _merge(d1, d2):
    res = {}
    for k, v in d1.items():
        res[k] = v
    for k, v in d2.items():
        if v is not None:
            res[k] = v
    return res


class PrintableLambda(object):
    def __init__(self, fn, **kwargs):
        self._target = fn
        self._kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self._target(*args, **_merge(kwargs, self._kwargs))

    def __repr__(self):
        return f"lambda ({self._target!r}, **{self._kwargs!r})"


class Actions:
    @staticmethod
    def make_zone(_input, _index, _offset, elements):
        """Zones are just a sequence of entries. For now."""
        origin = "@"  # Preserve the default unless we get an explicit origin
        ttl = None

        for e in elements:
            # $ORIGIN and $TTL set global defaults
            if isinstance(e, ORIGIN):
                if origin != "@":
                    raise RuntimeError("$ORIGIN occurs twice!")
                origin = e.name
                yield e

            elif isinstance(e, TTL):
                if ttl:
                    raise RuntimeError("$TTL occurs twice!")
                ttl = e.ttl
                yield e

            # apply bindings to emit records
            elif isinstance(e, list):
                for fn in e:
                    if isinstance(fn, (LambdaType, PrintableLambda)):
                        yield fn(name=origin, ttl=ttl)
                    else:
                        yield fn

    @staticmethod
    def make_origin(_input, _index, _offset, elements):
        return ORIGIN(elements[2])

    @staticmethod
    def make_ttl(_input, _index, _offset, elements):
        return TTL(elements[2])

    @staticmethod
    def make_records(_input, _index, _offset, elements):
        name, repetitions = elements
        if name == "@":
            # We allow make_zone to bind @ to $ORIGIN if present
            name = None
        return [
            PrintableLambda(e, name=name) if isinstance(e, PrintableLambda) else e
            for e in repetitions
        ]

    @staticmethod
    def make_repeat(input, _index, _offset, elements):
        _, record, _, comment = elements
        return PrintableLambda(record, comment=comment)

    @staticmethod
    def make_record_ttl(_input, _index, _offset, elements):
        ttl, _, record = elements
        return PrintableLambda(record, ttl=ttl)

    @staticmethod
    def make_record_type(_input, _index, _offset, elements):
        type, _, record = elements
        return PrintableLambda(record, type=type.text)

    ##################################################
    @staticmethod
    def make_a(_input, _index, _offset, elements):
        _, _, address = elements
        return PrintableLambda(A, address=address)

    @staticmethod
    def make_aaaa(_input, _index, _offset, elements):
        _, _, address = elements
        return PrintableLambda(AAAA, address=address)

    @staticmethod
    def make_cname(_input, _index, _offset, elements):
        _, _, cname = elements
        return PrintableLambda(CNAME, cname=cname)

    @staticmethod
    def make_mx(_input, _index, _offset, elements):
        _, _, preference, _, mx = elements
        return PrintableLambda(MX, preference=preference, exchange=mx)

    @staticmethod
    def make_ns(_input, _index, _offset, elements):
        _, _, ns = elements
        return PrintableLambda(NS, nsdname=ns)

    @staticmethod
    def make_soa(_input, _index, _offset, elements):
        (
            _,
            _,
            mname,
            _,
            rname,
            _,
            _,
            _,
            serial,
            _,
            refresh,
            _,
            retry,
            _,
            expire,
            _,
            minimum,
            _,
            _,
        ) = elements
        return PrintableLambda(
            SOA,
            mname=mname,
            rname=rname,
            serial=serial,
            refresh=refresh,
            retry=retry,
            expire=expire,
            minimum=minimum,
        )

    @staticmethod
    def make_srv(_input, _index, _offset, elements):
        _, _, priority, _, weight, _, port, _, target = elements
        return PrintableLambda(
            SRV, priority=priority, weight=weight, port=port, target=target
        )

    @staticmethod
    def make_txt(_input, _index, _offset, elements):
        _, _, txt_data = elements
        return PrintableLambda(TXT, txt_data=txt_data)

    @staticmethod
    def make_ptr(_input, _index, _offset, elements):
        _, _, ptrdname = elements
        return PrintableLambda(PTR, ptrdname=ptrdname)

    @staticmethod
    def make_rp(_input, _index, _offset, elements):
        _, _, mbox_dname, _, txt_dname = elements
        return PrintableLambda(RP, mbox_dname=mbox_dname, txt_dname=txt_dname)

    @staticmethod
    def make_string(input, start, end, _elements):
        return input[start + 1 : end - 1]

    ##################################################
    @staticmethod
    def make_word(_input, _index, _offset, elements):
        """Words have many elements, but we want their whole text."""
        return "".join(e.text for e in elements).lower()  # Uppercase is a lie in DNS

    @staticmethod
    def make_num(input, start, end, _elements):
        return int(input[start:end], 10)

    @staticmethod
    def make_seconds(_input, _, _end, elements):
        base = elements[0]
        factor = 1
        unit = elements[1].text.lower()
        if len(elements) == 2 and unit:
            factor = {
                "s": 1,
                "m": 60,
                "h": 60 * 60,
                "d": 24 * 60 * 60,
                "w": 7 * 24 * 60 * 60,
            }[unit]

        return base * factor

    @staticmethod
    def make_v4(input, start, end, _elements):
        return input[start:end]

    @staticmethod
    def make_v6(input, start, end, _elements):
        return input[start:end]

    @staticmethod
    def make_blank(input, start, end, *_):
        return input[start:end]


def read(input):
    """Read an entire zonefile, returning an AST for it which contains formatting information."""
    return _parse(input, actions=Actions())


def read1(input):
    """Read a single record as if it were part or a zonefile.

    Really just for testing.
    """
    return next(read(input))
