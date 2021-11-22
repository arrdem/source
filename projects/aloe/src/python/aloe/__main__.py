"""Aloe - A shitty weathermapping tool.

Periodically traceroutes the egress network, and then walks pings out the egress network recording times and hosts which
failed to respond. Expects a network in excess of 90% packet delivery, but with variable timings. Intended to probe for
when packet delivery latencies radically degrade and maintain a report file.

"""

import argparse
from collections import defaultdict, deque
from datetime import datetime, timedelta
from itertools import cycle
import logging
from multiprocessing import Process, Queue
from random import randint
import queue
import sys
from time import sleep
from typing import List

import graphviz
from icmplib import Hop, traceroute
from icmplib.utils import *
import requests
import pytz

from .urping import ping, urping

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("hosts", nargs="+")


class Topology(object):
    LOCALHOST = Hop("127.0.0.1", 1, [0.0], 0)

    def __init__(self):
        self._graph = defaultdict(set)
        self._nodes = {self.LOCALHOST.address: self.LOCALHOST}

    def next_hops(self, address: str) -> List[str]:
        return list(self._graph.get(address))

    def node(self, address: str) -> Hop:
        return self._nodes.get(address)

    def add_traceroute(self, trace):
        for e in trace:
            if e.address not in self._nodes:
                self._nodes[e.address] = e
            else:
                e0 = self._nodes[e.address]
                e0._packets_sent += e._packets_sent
                e0._rtts.extend(e.rtts)
                e0._distance = min(e.distance, e0.distance)

        hosts = [(self.LOCALHOST.address, self.LOCALHOST.distance)] + [
            (e.address, e.distance) for e in trace
        ]
        i1 = iter(hosts)
        i2 = iter(hosts)
        next(i2)

        for (parent, _), (child, _) in zip(i1, i2):
            self._graph[parent].add(child)

    def render(self):
        g = graphviz.Digraph()
        for n in sorted(self._nodes.values(), key=lambda n: n.distance):
            g.node(n.address)
            for next in self._graph[n.address]:
                g.edge(n.address, next)

        # Lol. Lmao.
        return requests.post(
            "https://dot-to-ascii.ggerganov.com/dot-to-ascii.php",
            params={"boxart": 1, "src": g.source},
        ).text

    def __iter__(self):
        return iter(sorted(self._nodes.values(), key=lambda n: n.distance))

    def __delitem__(self, key):
        del self._graph[key]
        del self._nodes[key]

INTERVAL = 0.5
Z = pytz.timezone("America/Denver")

def compute_topology(hostlist, topology=None):
    """Walk a series of traceroute tuples, computing a 'worst expected latency' topology from them."""

    topology = topology or Topology()
    for h in hostlist:
        trace = traceroute(h)
        # Restrict the trace to hosts which ICMP ping
        trace = [e for e in trace if ping(e.address, interval=INTERVAL, count=3).is_alive]
        topology.add_traceroute(trace)

    return topology


def pinger(host, queue, next=None):
    # Mokney patch the RTT tracking
    host._rtts = deque(host._rtts, maxlen=100)
    id = randint(1, 1<<16 - 1)
    sequence = 0

    while True:
        timeout = min(h.avg_rtt / 1000.0, 0.5)  # rtt is in ms but timeout is in sec.
        start = datetime.now(tz=Z)

        res = ping(host.address, timeout=timeout, interval=INTERVAL, count=3, id=id, sequence=sequence)
        sequence += res._packets_sent

        queue.put((start, res))
        sleep(INTERVAL)
        if res.is_alive:
            host._rtts.extend(res._rtts)
            host._packets_sent += res._packets_sent


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    opts, args = parser.parse_known_args()

    now = start = datetime.now(tz=Z)
    reconfigure_delay = timedelta(minutes=5)
    configure_at = now - reconfigure_delay
    flush_delay = timedelta(seconds=1)
    flush_at = now + flush_delay

    recovered_duration = timedelta(seconds=5)
    dead_duration = timedelta(minutes=30)

    topology = None

    q = Queue()
    workers = {}
    last_seen = {}
    state = {}

    spinner = cycle("|/-\\")

    with open("incidents.txt", "a") as fp:
        fp.write("RESTART\n")
        while True:
            now = datetime.now(tz=Z)

            if flush_at <= now:
                fp.flush()
                flush_at = now + flush_delay

            if configure_at <= now:
                log.info("Attempting to reconfigure network topology...")
                try:
                    topology = compute_topology(opts.hosts, topology)
                    configure_at = now + reconfigure_delay
                    log.info("Graph -\n" + topology.render())

                    for h in topology:
                        if h.distance == 0:
                            continue

                        if h.address in workers:
                            continue

                        else:
                            n = next(iter(topology.next_hops(h.address)), None)
                            p = workers[h.address] = Process(target=pinger, args=(h, q, n))
                            p.start()

                except Exception as e:
                    log.exception(e)

            try:
                # Revert to "logical now" of whenever the last ping results came in.
                now, res = q.get(timeout=0.1)
                last = last_seen.get(res.address)
                delta = now - last if last else None

                sys.stderr.write("\r" + next(spinner) + " " + f"ICMPResponse({res.address}, {res._rtts}, {res._packets_sent})" + " " * 20)
                sys.stderr.flush()

                if res.address not in workers:
                    pass

                elif res.is_alive:
                    last_seen[res.address] = now
                    if last and delta > recovered_duration:
                        state[res.address] = True
                        fp.write(
                            f"RECOVERED\t{res.address}\t{now.isoformat()}\t{delta.total_seconds()}\n"
                        )
                    elif not last:
                        state[res.address] = True
                        fp.write(f"UP\t{res.address}\t{now.isoformat()}\n")

                elif not res.is_alive:
                    if last and delta > dead_duration:
                        workers[res.address].terminate()
                        del workers[res.address]
                        del topology[res.address]
                        del last_seen[res.address]
                        del state[res.address]
                        fp.write(
                            f"DEAD\t{res.address}\t{now.isoformat()}\t{delta.total_seconds()}\n"
                        )

                    elif last and delta > recovered_duration and state[res.address]:
                        fp.write(f"DOWN\t{res.address}\t{now.isoformat()}\n")
                        state[res.address] = False

            except queue.Empty:
                sys.stderr.write("\r" + next(spinner))
                sys.stderr.flush()
