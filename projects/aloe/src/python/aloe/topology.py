"""
A model of a (radial) network topology.
"""

from collections import defaultdict
import logging
from typing import List

import graphviz
from icmplib import Hop
import requests


log = logging.getLogger(__name__)


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
