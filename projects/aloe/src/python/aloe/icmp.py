"""Tools sitting between aloe and icmplib."""

from datetime import datetime, timedelta
from itertools import islice as take
import logging
import queue
from random import randint
from threading import Event, Lock
from time import sleep as _sleep

from icmplib.exceptions import (
    ICMPLibError,
    ICMPSocketError,
    TimeoutExceeded,
)
from icmplib.models import (
    Hop,
    Host,
    ICMPReply,
    ICMPRequest,
)
from icmplib.sockets import ICMPv4Socket
from icmplib.utils import is_hostname, resolve


log = logging.getLogger(__name__)


def better_repr(self):
    elems = ", ".join(f"{slot}={getattr(self, slot)}" for slot in self.__slots__)
    return f"<{type(self).__name__} ({elems})>"


ICMPRequest.__repr__ = better_repr
ICMPReply.__repr__ = better_repr


def sleep(event, duration, interval=0.1):
    total = 0
    while total < duration:
        if event.is_set():
            raise SystemExit()
        else:
            _sleep(interval)
            total += interval


class ICMPRequestResponse(object):
    """A thread-safe request/response structure for pinging a host."""

    PENDING = object()
    TIMEOUT = object()

    def __init__(self, address, request: ICMPRequest, timeout: timedelta):
        _timeout = datetime.now() + timeout
        self._address = address
        self._request = request
        self._timeout = _timeout
        self._lock = Lock()
        self._response = self.PENDING

    def ready(self):
        """Determine if this request is still waiting."""
        return self.get() is not self.PENDING

    def get(self):
        """Get the response, unless the timeout has passed in which case return a timeout."""

        with self._lock:
            if self._response is not self.PENDING:
                return self._response
            elif self._timeout < datetime.now():
                return self.TIMEOUT
            else:
                return self._response

    def set(self, response):
        """Set the response, unless the timeout has passed in which case set a timeout."""

        if isinstance(response, ICMPReply):
            with self._lock:
                if self._timeout < datetime.now():
                    self._response = self.TIMEOUT
                else:
                    # rtt = (reply.time - request.time) * 1000
                    self._response = response


def icmp_worker(shutdown: Event, q: queue.Queue):
    """A worker thread which processes ICMP requests; sending packets and listening for matching responses."""

    state = {}

    with ICMPv4Socket(None, True) as sock:
        while not shutdown.is_set():
            # Send one
            try:
                item = q.get(block=False, timeout=0.001)
                request = item._request
                state[(request._id, request._sequence)] = item
                # log.info(f"Sending request {item._request!r}")
                sock.send(item._request)
            except (ICMPLibError, ICMPSocketError, queue.Empty):
                pass

            # Recieve one
            try:
                if response := sock.receive(None, 0.001):
                    key = (response.id, response.sequence)
                    if key in state:
                        # log.info(f"Got response {response!r}")
                        state[key].set(response)
                        del state[key]
                    else:
                        # log.warning(f"Recieved non-matching response {response!r}")
                        pass
            except (ICMPLibError, ICMPSocketError):
                pass

            # GC one
            if key := next(iter(state.keys()), None):
                if state[key].ready():
                    del state[key]

            # Sleep one
            sleep(shutdown, 0.001)


def traceroute(q: queue.Queue,
               address: str,
               first_hop: int = 1,
               max_hops: int = 32,
               count: int = 3,
               id: int = None,
               family: int = None):
    if is_hostname(address):
        address = resolve(address, family)[0]

    mask = ((1<<16) - 1)
    id = id or randint(1, mask) & 0xFFFF
    ttl = first_hop
    host_reached = False
    hops = []

    while not host_reached and ttl <= max_hops:
        reply = None
        packets_sent = 0
        rtts = []

        for sequence in range(count):
            request = ICMPRequestResponse(
                address,
                ICMPRequest(
                    destination=address,
                    id=id,
                    sequence=sequence,
                    ttl=ttl
                ),
                timedelta(seconds=1),
            )

            q.put(request)
            while not request.ready():
                _sleep(0.1)

            _reply = request.get()
            if _reply is ICMPRequestResponse.TIMEOUT:
                _sleep(0.1)
                continue

            elif _reply:
                reply = reply or _reply
                try:
                    reply.raise_for_status()
                    host_reached = True
                except ICMPLibError:
                    pass

                rtt = (reply.time - request._request.time) * 1000
                rtts.append(rtt)

        if reply:
            hops.append(
                Hop(
                    address=reply.source,
                    packets_sent=packets_sent,
                    rtts=rtts,
                    distance=ttl
                )
            )

        ttl += 1

    return hops


def request_sequence(hostname: str,
                     timeout: timedelta,
                     id: int = None,
                     family: int = None):
    """Generate a sequence of requests monitoring a specific, usable as a request source for a ping."""

    if is_hostname(hostname):
        destination = resolve(hostname, family)[0]
    else:
        destination = hostname

    mask = ((1<<16) - 1)
    id = id or randint(1, mask) & 0xFFFF
    sequence = 1

    while True:
        yield ICMPRequestResponse(
            hostname,
            ICMPRequest(
                destination=destination,
                id=id,
                sequence=sequence & mask,
            ),
            timeout
        )
        sequence += 1


def _ping(q: queue.Queue, request: ICMPRequestResponse):
        q.put(request)
        while not request.ready():
            _sleep(0.1)

        _response = request.get()
        if _response is not ICMPRequestResponse.TIMEOUT:
            return _response


def ping(q: queue.Queue,
         address: str,
         count: int = 3,
         id: int = None,
         family: int = None) -> Host:
    """Ping a host N times."""

    rtts = []
    for request in take(request_sequence(address, timedelta(seconds=1)), count):
        if reply := _ping(q, request):
            rtt = (reply.time - request._request.time) * 1000
            rtts.append(rtt)

    return Host(
        address=address,
        packets_sent=count,
        rtts=rtts,
    )
