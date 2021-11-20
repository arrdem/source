"""Aloe - A shitty weathermapping tool.

Periodically traceroutes the egress network, and then walks pings out the egress network recording times and hosts which
failed to respond. Expects a network in excess of 90% packet delivery, but with variable timings. Intended to probe for
when packet delivery latencies radically degrade and maintain a report file.

"""

import sys
import argparse
import logging
from datetime import datetime, timedelta
from ping import ping
from traceroute import TraceElem, traceroute
from subprocess import CalledProcessError
from typing import NamedTuple
from collections import defaultdict


log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("hosts", nargs="+")


def distinct(iter):
    s = set()
    l = []
    for e in iter:
        if e in s:
            continue
        else:
            l.append(e)
            s.add(e)
    return l


class Host(NamedTuple):
    hostname: str
    ip: str
    rank: int
    latency: timedelta
    samples: int = 1

    def mean_latency(self):
        return self.latency / self.samples


class Topology(object):
    LOCALHOST = Host("localhost", "127.0.0.1", 0, timedelta(seconds=0.1))

    def __init__(self):
        self._graph = defaultdict(set) # Dict[ip, List[ip]]
        self._nodes = {self.LOCALHOST.ip: self.LOCALHOST} # Dict[ip, Host]

    def add_traceroute(self, trace):
        trace = list(trace)
        hosts = []
        newhosts = [self.LOCALHOST.ip]
        rank = 0
        for e in trace:
            if e.ip not in self._nodes:
                self._nodes[e.ip] = Host(e.hostname, e.ip, e.rank, e.latency, 1)
            else:
                self._nodes[e.ip] = Host(e.hostname, e.ip, e.rank, e.latency + self._nodes[e.ip].latency, self._nodes[e.ip].samples + 1)

            if e.rank > rank:
                if newhosts:
                    for h2 in newhosts:
                        for h1 in hosts:
                            self._graph[h1].add(h2)
                    hosts = newhosts
                    newhosts = []
                rank = e.rank

            if e.rank == rank:
                newhosts.append(e.ip)

    def render(self):
        for n in sorted(self._nodes.values(), key=lambda n: n.rank):
            print(f"{n.hostname} ({n.ip}) => {self._graph[n.ip]}")


def compute_topology(hostlist):
    """Walk a series of traceroute tuples, computing a 'worst expected latency' topology from them."""

    topology = Topology()
    for h in hostlist:
        topology.add_traceroute(traceroute(h))

    return sorted(topology._nodes.values(), key=lambda n: n.rank)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    opts, args = parser.parse_known_args()

    now = start = datetime.now()
    reconfigure_delay = timedelta(minutes=5)
    configure_at = now - reconfigure_delay

    topology = []

    with open("incidents.txt", "a") as fp:
        while True:
            now = datetime.now()

            if configure_at <= now:
                log.info("Attempting to reconfigure network topology...")
                try:
                    topology = compute_topology(opts.hosts)
                    configure_at = now + reconfigure_delay
                    for h in topology:
                        log.info(f"in topology {h}")
                except CalledProcessError:
                    pass

            for h in topology:
                if h.rank == 0:
                    continue

                fail = False
                try:
                    if ping(h.ip, timeout=h.mean_latency() * 2) != 0:
                        fail = True
                except Exception as e:
                    fail = True
                    log.exception(e)

                if fail:
                    msg = f"{datetime.now()} failed to reach {h.hostname} ({h.ip})"
                    log.warning(msg)
                    fp.write(msg + "\n")

                else:
                    sys.stderr.write('.')
                    sys.stderr.flush()
