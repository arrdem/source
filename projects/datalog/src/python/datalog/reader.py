"""
A datalog reader.
"""

from collections import defaultdict
from itertools import chain

from datalog.parser import FAILURE, Grammar
from datalog.types import Constant, Dataset, LVar, Rule


class Actions(object):
    def __init__(self, db_cls=None):
        self._db_cls = db_cls or Dataset

    def make_dataset(self, input, start, end, elements):
        # Group the various terms
        rules = []
        tuples = []
        for e in elements:
            if e:
                if isinstance(e, Rule):
                    rules.append(e)
                else:
                    tuples.append(e)

        return self._db_cls(tuples, rules)

    def make_symbol(self, input, start, end, elements):
        return LVar("".join(e.text for e in elements),)

    def make_word(self, input, start, end, elements):
        return Constant("".join(e.text for e in elements),)

    def make_string(self, input, start, end, elements):
        return Constant(elements[1].text,)

    def make_comment(self, input, start, end, elements):
        return None

    def make_ws(self, input, start, end, elements=None):  # watf?
        pass

    def make_rule(self, input, start, end, elements):
        if elements[1].elements:
            return Rule(elements[0], elements[1].elements[3][1])
        else:
            return elements[0]

    def make_clause(self, input, start, end, elements):
        if elements[0].text == "~":
            return ("not", (elements[1], *elements[3][1]))
        else:
            return (elements[1], *elements[3][1])

    def make_terms(self, input, start, end, elements):
        return self._make("terms", elements)

    def make_clauses(self, input, start, end, elements):
        return self._make("clauses", elements)

    def _make(self, tag, elements):
        if len(elements) == 1:
            return (
                tag,
                [elements[0]],
            )
        elif elements[1].elements:
            return (tag, [elements[0]] + elements[1].elements[2][1])
        else:
            return (tag, [elements[0]])

    def make_command(self, input, start, end, elements):
        op = elements[-1].text
        val = self.make_rule(input, start, end, elements)
        if op == ".":
            val = self.make_dataset(input, start, end, [val])
        return op, val


class Parser(Grammar):
    """Implementation detail.

  A slightly hacked version of the Parser class canopy generates, which lets us control what the
  parsing entry point is. This lets me play games with having one parser and one grammar which is
  used both for the command shell and for other things.

  """

    def __init__(self, input, actions, types):
        self._input = input
        self._input_size = len(input)
        self._actions = actions
        self._types = types
        self._offset = 0
        self._cache = defaultdict(dict)
        self._failure = 0
        self._expected = []

    def parse(self, meth):
        tree = meth()
        if tree is not FAILURE and self._offset == self._input_size:
            return tree
        if not self._expected:
            self._failure = self._offset
            self._expected.append("<EOF>")
            raise ParseError(format_error(self._input, self._failure, self._expected))


def format_error(input, offset, expected):
    lines, line_no, position = input.split("\n"), 0, 0
    while position <= offset:
        position += len(lines[line_no]) + 1
        line_no += 1
        message, line = (
            "Line " + str(line_no) + ": expected " + ", ".join(expected) + "\n",
            lines[line_no - 1],
        )
        message += line + "\n"
        position -= len(line) + 1
        message += " " * (offset - position)
    return message + "^"


def read_dataset(text: str, db_cls=None):
    """Read a string of text, returning a whole Datalog dataset."""

    parser = Parser(text, Actions(db_cls=db_cls), None)
    return parser.parse(parser._read_dataset)


def read_command(text: str, db_cls=None):
    """Read a string of text, returning a whole Datalog dataset."""

    actions = Actions(db_cls=db_cls)
    parser = Parser(text, actions, None)
    return parser.parse(parser._read_command)


read = read_dataset


def pr_clause(e):
    if len(e) == 2 and e[0] == "not":
        return "~" + pr_str(e[1])
    else:
        return pr_str(e)


def pr_str(e):
    if isinstance(e, str):
        return e

    elif isinstance(e, Rule):
        return (
            pr_str(e.pattern)
            + " :- "
            + ", ".join([pr_clause(c) for c in e.clauses])
            + "."
        )

    elif isinstance(e, Constant):
        return repr(e.value)

    elif isinstance(e, LVar):
        return e.name

    elif isinstance(e, list):
        return "[{}]".format(", ".join(pr_str(_e) for _e in e))

    elif isinstance(e, tuple):
        return e[0].value + "(" + ", ".join(pr_str(_e) for _e in e[1:]) + ")"
