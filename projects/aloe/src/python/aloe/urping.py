#!/usr/bin/env python3

import logging
from time import sleep
import traceback
from textwrap import indent
from random import randint
import sys

from icmplib.exceptions import (
    ICMPLibError,
    TimeExceeded,
    TimeoutExceeded,
)
from icmplib.models import Host, Hop, ICMPRequest, ICMPReply
from icmplib.sockets import (
    ICMPv4Socket,
    ICMPv6Socket,
)
from icmplib.utils import *


log = logging.getLogger(__name__)


def better_repr(self):
    elems = ", ".join(f"{slot}={getattr(self, slot)}" for slot in self.__slots__)
    return f"<{type(self).__name__} ({elems})>"


ICMPRequest.__repr__ = better_repr
ICMPReply.__repr__ = better_repr


def urping(address: str,
           hops: int,
           via: str,
           family=None,
           count=3,
           fudge=4,
           id=None,
           interval=0.2,
           timeout=2,
           source=None,
           **kwargs) -> Hop:
    """Ur-ping by (ab)using ICMP TTLs.

    Craft an ICMP message which would go one (or more) hops FARTHER than the `address` host, routed towards `via`.
    Send `count * fudge` packets, looking for responses from `address`.
    Responses from `address` are considered; and a `Hop` is built from those results.
    Other responses from other hosts are discarded.

    """

    if is_hostname(via):
        via = resolve(via, family)[0]

    if is_hostname(address):
        address = resolve(address, falmiy)[0]

    if is_ipv6_address(via):
        _Socket = ICMPv6Socket
    else:
        _Socket = ICMPv4Socket

    ttl = hops
    hop = Hop(address, 0, [], hops)
    packets_sent = 0

    with _Socket(source) as sock:
        for _ in range(count * fudge):
            request = ICMPRequest(
                destination=via,
                # Note that we act like this is a new stream with a new ID and sequence each time to try and fool multipathing.
                id=id or unique_identifier(),
                sequence=0,
                ttl=ttl,
                **kwargs)

            try:
                sock.send(request)
                packets_sent += 1

                reply = None
                reply = sock.receive(request, timeout)
                rtt = (reply.time - request.time) * 1000

                reply.raise_for_status()

                assert reply.id == request.id
                assert reply.sequence == request.sequence
                assert reply.source == address

                hop._packets_sent += 1
                hop._rtts.append(rtt)

                if hop._packets_sent >= count:
                    break

            except AssertionError:
                log.warning("Got response from unexpected node %s (expected %s) %r for request %4", reply.source, address, reply, request)

            except (TimeoutExceeded, TimeExceeded):
                pass

            except ICMPLibError as e:
                log.exception(e)
                break

            sleep(interval)

    return hop


def ping(address, count=4, interval=1, timeout=2, id=None, source=None,
         family=None, privileged=True, sequence=0, **kwargs):
    """A simple, if paranoid, ping."""
    if is_hostname(address):
        address = resolve(address, family)[0]

    if is_ipv6_address(address):
        _Socket = ICMPv6Socket
    else:
        _Socket = ICMPv4Socket

    id = id or randint(1, 1<<16 - 1) & 0xFFFF
    packets_sent = 0
    rtts = []

    with _Socket(source, privileged) as sock:
        for base in range(count):
            sequence = (sequence + base) & 0xFFFF
            if base > 0:
                sleep(interval)

            request = ICMPRequest(
                destination=address,
                id=id,
                sequence=sequence,
                **kwargs)

            try:
                sock.send(request)
                packets_sent += 1

                reply = sock.receive(request, timeout)
                reply.raise_for_status()

                assert reply.id == request.id
                assert reply.sequence == request.sequence
                assert reply.source == address

                rtt = (reply.time - request.time) * 1000
                rtts.append(rtt)

            except AssertionError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                log.warning("Got erroneous response:\n  request: %r\n  reply: %r\n  err: |\n%s", request, reply, indent(traceback.format_exc(), "    "))

            except ICMPLibError:
                pass

    return Host(address, packets_sent, rtts)
