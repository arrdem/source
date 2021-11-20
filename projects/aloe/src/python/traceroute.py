"""A shitty traceroute wrapper."""

from datetime import timedelta
import re
from subprocess import (
    CalledProcessError,
    check_call,
    check_output,
    DEVNULL,
)
from typing import Iterator, List, NamedTuple


class TraceElem(NamedTuple):
    hostname: str
    ip: str
    latency: timedelta
    rank: int


_LINE = re.compile(r"\*|(((?P<hostname>[-_\w\d\.]*)\s+\((?P<ip>[a-f\d\.:]*)\)\s+)?(?P<latency>[\d\.]*) ms)")


def _parse_traceroute(lines: List[str]) -> Iterator[TraceElem]:
    for rank, l in zip(range(1, 1<<64), lines):
        ip = None
        hostname = None
        for m in re.finditer(_LINE, l):
            if m.group("latency"):
                ip = m.group("ip") or ip
                hostname = m.group("hostname") or hostname
                yield TraceElem(hostname, ip, timedelta(milliseconds=float(m.group("latency"))), rank)


def traceroute(host: str, icmp=True, timeout=timedelta(seconds=5)) -> Iterator[TraceElem]:
    # FIXME: Make ICMP mode an option, not on always
    yield from _parse_traceroute(
        check_output(["traceroute",
                      # Set wait; note use of total_seconds which is "real" valued.
                      "-w", str(timeout.total_seconds()),
                      # Use ICMP probes same as PING.
                      # This means all probed hosts will be pingable/ping compliant.
                      # May miss parts of the topology as a result.
                      "-I",
                      host],
                     stderr=DEVNULL,)
        .decode("utf-8")
        .splitlines())
