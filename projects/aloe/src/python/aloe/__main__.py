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
import queue
import sys
from typing import List

import graphviz
from icmplib import Hop, ping, traceroute
from icmplib.utils import *
import requests


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


def compute_topology(hostlist, topology=None):
    """Walk a series of traceroute tuples, computing a 'worst expected latency' topology from them."""

    topology = topology or Topology()
    for h in hostlist:
        trace = traceroute(h)
        # Restrict the trace to hosts which ICMP ping
        trace = [e for e in trace if ping(e.address, count=1).is_alive]
        topology.add_traceroute(trace)

    return topology


def pinger(host, id, queue):
    # Mokney patch the RTT tracking
    host._rtts = deque(host._rtts, maxlen=100)
    while True:
        timeout = h.avg_rtt * 2 / 1000.0  # rtt is in ms but timeout is in sec.
        start = datetime.now()
        res = ping(host.address, id=id, timeout=timeout, count=3)
        queue.put((start, res))
        if res.is_alive:
            host._rtts.extend(res._rtts)
            host._packets_sent += res._packets_sent


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    opts, args = parser.parse_known_args()

    now = start = datetime.now()
    reconfigure_delay = timedelta(minutes=5)
    configure_at = now - reconfigure_delay
    flush_delay = timedelta(seconds=5)
    flush_at = now + flush_delay

    recovered_duration = timedelta(seconds=5)
    dead_duration = timedelta(minutes=30)

    topology = None
    id = unique_identifier()

    q = Queue()
    workers = {}
    last_seen = {}

    spinner = cycle("|/-\\")

    with open("incidents.txt", "a") as fp:
        fp.write("RESTART\n")
        while True:
            now = datetime.now()

            if flush_at <= now:
                fp.flush()
                flush_at = now + flush_delay

            if configure_at <= now:
                log.info("Attempting to reconfigure network topology...")
                topology = compute_topology(opts.hosts, topology)
                configure_at = now + reconfigure_delay
                log.info("Graph -\n" + topology.render())

                for h in topology:
                    if h.distance == 0:
                        continue

                    if h.address in workers:
                        continue

                    else:
                        p = workers[h.address] = Process(target=pinger, args=(h, id, q))
                        p.start()

            try:
                timestamp, res = q.get(timeout=0.1)
                last = last_seen.get(res.address)
                delta = timestamp - last if last else None

                if res.address not in workers:
                    pass

                elif res.is_alive:
                    last_seen[res.address] = timestamp
                    if last and delta > recovered_duration:
                        fp.write(
                            f"RECOVERED\t{res.address}\t{timestamp.isoformat()}\t{delta.total_seconds()}\n"
                        )
                    elif not last:
                        fp.write(f"UP\t{res.address}\t{timestamp.isoformat()}\n")

                elif not res.is_alive:
                    if last and delta > dead_duration:
                        workers[h.address].terminate()
                        del workers[h.address]
                        del topology[h.address]
                        del last_seen[h.address]
                        fp.write(
                            f"DEAD\t{res.address}\t{timestamp.isoformat()}\t{delta.total_seconds()}\n"
                        )

                    elif last and delta < recovered:
                        fp.write(f"WARN\t{res.address}\t{timestamp.isoformat()}\n")

                    elif last and delta > recovered:
                        fp.write(f"DOWN\t{res.address}\t{timestamp.isoformat()}\n")

            except queue.Empty:
                sys.stderr.write("\r" + next(spinner))
                sys.stderr.flush()
