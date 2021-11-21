#!/usr/bin/env python3

import logging
from time import sleep

from icmplib import Hop
from icmplib.exceptions import (
    ICMPLibError,
    TimeExceeded,
)
from icmplib.models import Hop, ICMPRequest
from icmplib.sockets import (
    ICMPv4Socket,
    ICMPv6Socket,
)
from icmplib.utils import *


log = logging.getLogger(__name__)


def urping(address: str, hops: int, via: str, family=None, count=3, fudge=4, interval=0.05, timeout=2, source=None, **kwargs) -> Hop:
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
    hop = Hop(address, 0, [])
    packets_sent = 0

    with _Socket(source) as sock:
        for _ in range(count * fudge):
            request = ICMPRequest(
                destination=via,
                # Note that we act like this is a new stream with a new ID and sequence each time to try and fool multipathing.
                id=unique_identifier(),
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

            except TimeExceeded:
                sleep(interval)

            except ICMPLibError as e:
                log.exception(e)
                break

            if not reply:
                log.debug(f"got no reply from {address}")
            else:
                # Because the default repr() is crap
                reply_str = "ICMPReply({})".format(", ".join(slot + "=" + str(getattr(reply, slot)) for slot in reply.__slots__))
                log.debug(f"Pinging {address} (distance {hops}) via {via} got reply {reply_str}")

            if reply and reply.source != address:
                continue

            elif reply:
                hop._packets_sent += 1
                hop._rtts.append(rtt)

            if hop and hop._packets_sent >= count:
                break

    return hop
