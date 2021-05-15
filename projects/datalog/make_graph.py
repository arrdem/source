"""
For benchmarking the datalog.

Generates a large graph, which will be expensive to enumerate 2-edges over and paths through.
"""

from random import choice
from uuid import uuid4 as uuid


with open("graph.dtl", "w") as f:
    nodes = []

    # Generate 10k edges
    for i in range(10000):
        if nodes:
            from_node = choice(nodes)
        else:
            from_node = uuid()

        to_node = uuid()

        nodes.append(to_node)

        f.write(f"edge({str(from_node)!r}, {str(to_node)!r}).\n")
