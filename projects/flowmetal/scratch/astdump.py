"""
A (toy) tool for emitting Python ASTs as YAML formatted data.
"""

import ast
import optparse
import sys

import yaml


def propnames(node):
    """return names of attributes specific for the current node"""

    props = {x for x in dir(node) if not x.startswith("_")}

    if isinstance(node, ast.Module):
        props -= {"body"}

    if isinstance(node, (ast.Expr, ast.Attribute)):
        props -= {"value"}

    if isinstance(node, ast.Constant):
        props -= {"n", "s"}

    if isinstance(node, ast.ClassDef):
        props -= {"body"}

    return props


# Note that ast.NodeTransformer exists for mutations.
# This is just for reads.
class TreeDumper(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self._stack = []

    def dump(self, node):
        self.visit(node)

    def visit(self, node):
        # nodetype = type(node)
        nodename = node.__class__.__name__
        indent = " " * len(self._stack) * 2
        print(indent + nodename)
        for n in propnames(node):
            print(indent + "%s: %s" % (n, node.__dict__[n]))

        self._stack.append(node)
        self.generic_visit(node)
        self._stack.pop()


class YAMLTreeDumper(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self._stack = []

    def node2yml(self, node):
        try:
            # nodetype = type(node)
            nodename = node.__class__.__name__
            return {
                "op": nodename,
                "props": {n: node.__dict__[n] for n in propnames(node)},
                "children": [],
            }
        except Exception:
            print(repr(node), propnames(node), dir(node))

    def visit(self, node):
        yml_node = self.node2yml(node)
        self._stack.append(yml_node)
        old_stack = self._stack
        self._stack = yml_node["children"]
        self.generic_visit(node)
        self._stack = old_stack
        return yml_node


if __name__ == "__main__":
    parser = optparse.OptionParser(usage="%prog [options] <filename.py>")
    opts, args = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        sys.exit(-1)
    filename = args[0]

    with open(filename) as f:
        root = ast.parse(f.read(), filename)

    print(yaml.dump(YAMLTreeDumper().visit(root), default_flow_style=False, sort_keys=False))
