"""
A parser for s-expressions.
"""

from abc import ABC, abstractmethod
from enum import Enum
from io import StringIO, BufferedReader
from typing import IO, NamedTuple, Any
from fractions import Fraction
import re


## Types
class Position(NamedTuple):
    """An encoding for the location of a read token within a source."""
    source: str
    line: int
    col: int
    offset: int

    @staticmethod
    def next_pos(pos: "Position"):
        return Position(pos.source, pos.line, pos.col + 1, pos.offset + 1)

    @staticmethod
    def next_line(pos: "Position"):
        return Position(pos.source, pos.line + 1, 1, pos.offset + 1)


class TokenBase(object):
    """The shared interface to tokens."""

    @property
    @abstractmethod
    def pos(self):
        """The position of the token within its source."""

    @property
    @abstractmethod
    def raw(self):
        """The raw token as scanned."""


class ConstTokenBase(TokenBase, NamedTuple):
    """The shared interface for constant tokens"""
    data: Any
    raw: str
    pos: Position

    # Hash according to data
    def __hash__(self):
        return hash(self.data)

    # And make sure it's orderable
    def __eq__(self, other):
        return self.data == other

    def __lt__(self, other):
        return self.data < other

    def __gt__(self, other):
        return self.data > other


class BooleanToken(ConstTokenBase):
    """A read boolean."""


class IntegerToken(ConstTokenBase):
    """A read integer, including position."""


class FractionToken(ConstTokenBase):
    """A read fraction, including position."""


class FloatToken(ConstTokenBase):
    """A read floating point number, including position."""


class SymbolToken(ConstTokenBase):
    """A read symbol, including position."""


class KeywordToken(ConstTokenBase):
    """A read keyword."""


class StringToken(ConstTokenBase):
    """A read string, including position."""


class ListType(Enum):
    """The supported types of lists."""
    ROUND = ("(", ")")
    SQUARE = ("[", "]")


class ListToken(NamedTuple, TokenBase):
    """A read list, including its start position and the paren type."""
    data: list
    raw: str
    pos: Position
    paren: ListType = ListType.ROUND


class SetToken(NamedTuple, TokenBase):
    """A read set, including its start position."""
    data: list
    raw: str
    pos: Position


class MappingToken(NamedTuple, TokenBase):
    """A read mapping, including its start position."""
    data: list
    raw: str
    pos: Position


class WhitespaceToken(NamedTuple, TokenBase):
    """A bunch of whitespace with no semantic value."""
    data: str
    raw: str
    pos: Position


class CommentToken(WhitespaceToken):
    """A read comment with no semantic value."""


## Parser implementation
class PosTrackingBufferedReader(object):
    """A slight riff on BufferedReader which only allows for reads and peeks of a
    char, and tracks positions.

    Perfect for implementing LL(1) parsers.
    """

    def __init__(self, f: IO, source_name=None):
        self._next_pos = self._pos = Position(source_name, 1, 1, 0)
        self._char = None
        self._f = f

    def pos(self):
        return self._pos

    def peek(self):
        if self._char is None:
            self._char = self._f.read(1)
        return self._char

    def read(self):
        # Accounting for lookahead(1)
        ch = self._char or self._f.read(1)
        self._char = self._f.read(1)

        # Accounting for the positions
        self._pos = self._next_pos
        if ch == "\r" and self.peek() == "\n":
            super.read(1)  # Throw out a character
            self._next_pos = Position.next_line(self._next_pos)
        elif ch == "\n":
            self._next_pos = Position.next_line(self._next_pos)
        else:
            self._next_pos = Position.next_pos(self._next_pos)

        return ch


class ReadThroughBuffer(PosTrackingBufferedReader):
    """A duck that quacks like a PosTrackingBufferedReader."""

    def __init__(self, ptcr: PosTrackingBufferedReader):
        self._reader = ptcr
        self._buffer = StringIO()

    def pos(self):
        return self._reader.pos()

    def peek(self):
        return self._reader.peek()

    def read(self):
        ch = self._reader.read()
        self._buffer.write(ch)
        return ch

    def __str__(self):
        return self._buffer.getvalue()

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        pass


class SexpParser(ABC):
    @classmethod
    @abstractmethod
    def parse(cls, f: PosTrackingBufferedReader) -> TokenBase:
        """Parse an s-expression, returning a parsed token tree."""

    def read(cls, f: PosTrackingBufferedReader):
        """Parse to a token tree and read to values returning the resulting values."""

        return cls.parse(f).read()


class Parser(SexpParser):
    """A basic parser which knows about lists, symbols and numbers.

    Intended as a base class / extension point for other parsers.
    """

    @classmethod
    def parse(cls, f: PosTrackingBufferedReader):
        if not f.peek():
            raise SyntaxError(f"Got end of file ({f.pos()}) while parsing")
        elif cls.ispunct(f.peek()):
            if f.peek() == "(":
                return cls.parse_list(f)
            elif f.peek() == "[":
                return cls.parse_sqlist(f)
            elif f.peek() == '"':
                return cls.parse_str(f)
            elif f.peek() == ";":
                return cls.parse_comment(f)
            else:
                raise SyntaxError(f"Got unexpected punctuation {f.read()!r} at {f.pos()} while parsing")
        elif cls.isspace(f.peek()):
            return cls.parse_whitespace(f)
        else:
            return cls.parse_symbol(f)

    @classmethod
    def isspace(cls, ch: str):
        """An extension point allowing for a more expansive concept of whitespace."""
        return ch.isspace() or ch == ','

    @classmethod
    def ispunct(cls, ch: str):
        return ch in (
            '"'
            ';'   # Semicolon
            '()'  # Parens
            '⟮⟯'   # 'flat' parens
            '[]'  # Square brackets
            '⟦⟧'  # 'white' square brackets
            '{}'  # Curly brackets
            '⟨⟩'  # Angle brackets
            '《》'  # Double angle brackets
            '⟪⟫'  # Another kind of double angle brackets
        )

    @classmethod
    def parse_delimeted(cls, f: PosTrackingBufferedReader, openc, closec, ctor):
        with ReadThroughBuffer(f) as rtb:
            pos = None
            for c in openc:
                pos = pos or rtb.pos()
                assert rtb.read() == c  # Discard the leading delimeter
            pos = rtb.pos()
            acc = []
            while f.peek() != closec:
                if not f.peek():
                    raise SyntaxError(f"Got end of file while parsing {openc!r}...{closec!r} starting at {pos}")
                try:
                    acc.append(cls.parse(rtb))
                except SyntaxError as e:
                    raise SyntaxError(f"While parsing {openc!r}...{closec!r} starting at {pos},\n{e}")

            assert rtb.read() == closec  # Discard the trailing delimeter
            return ctor(acc, str(rtb), pos)

    # FIXME (arrdem 2020-07-18):
    #   Break this apart and make the supported lists composable features somehow?
    @classmethod
    def parse_list(cls, f: PosTrackingBufferedReader):
        return cls.parse_delimeted(f, "(", ")", lambda *args: ListToken(*args, ListType.ROUND))

    @classmethod
    def parse_sqlist(cls, f: PosTrackingBufferedReader):
        return cls.parse_delimeted(f, "[", "]", lambda *args: ListToken(*args, ListType.SQUARE))

    # FIXME (arrdem 2020-07-18):
    #   Break this apart into middleware or composable features somehow?
    @classmethod
    def handle_symbol(cls, buff, pos):
        def _sign(m, idx):
            if m.group(idx) == '-':
                return -1
            else:
                return 1

        # Parsing integers with bases
        if m := re.fullmatch(r"([+-]?)(\d+)r([a-z0-9_]+)", buff):
            return IntegerToken(
                _sign(m, 1) * int(m.group(3).replace("_", ""),
                                  int(m.group(2))),
                buff,
                pos,
            )

        # Parsing hex numbers
        if m := re.fullmatch(r"([+-]?)0[xX]([A-Fa-f0-9_]*)", buff):
            val = m.group(2).replace("_", "")
            return IntegerToken(_sign(m, 1) * int(val, 16), buff, pos)

        # Parsing octal numbers
        if m := re.fullmatch(r"([+-]?)0([\d_]*)", buff):
            val = m.group(2).replace("_", "")
            return IntegerToken(_sign(m, 1) * int(val, 8), buff, pos)

        # Parsing integers
        if m := re.fullmatch(r"([+-]?)\d[\d_]*", buff):
            return IntegerToken(int(buff.replace("_", "")), buff, pos)

        # Parsing fractions
        if m := re.fullmatch(r"([+-]?)(\d[\d_]*)/(\d[\d_]*)", buff):
            return FractionToken(
                Fraction(
                    int(m.group(2).replace("_", "")),
                    int(m.group(3).replace("_", ""))),
                buff,
                pos,
            )

        # Parsing floats
        if re.fullmatch(r"([+-]?)\d[\d_]*(\.\d[\d_]*)?(e[+-]?\d[\d_]*)?", buff):
            return FloatToken(float(buff), buff, pos)

        # Booleans
        if buff == "true":
            return BooleanToken(True, buff, pos)

        if buff == "false":
            return BooleanToken(False, buff, pos)

        # Keywords
        if buff.startswith(":"):
            return KeywordToken(buff, buff, pos)

        # Default behavior
        return SymbolToken(buff, buff, pos)

    @classmethod
    def parse_symbol(cls, f: PosTrackingBufferedReader):
        with ReadThroughBuffer(f) as rtb:
            pos = None
            while rtb.peek() and not cls.isspace(rtb.peek()) and not cls.ispunct(rtb.peek()):
                pos = pos or rtb.pos()
                rtb.read()
            buff = str(rtb)
            return cls.handle_symbol(buff, pos)

    @classmethod
    def parse_whitespace(cls, f: PosTrackingBufferedReader):
        with ReadThroughBuffer(f) as rtb:
            pos = None
            while rtb.peek() and cls.isspace(rtb.peek()):
                pos = pos or rtb.pos()
                ch = rtb.read()
                if ch == "\n":
                    break
            buff = str(rtb)
            return WhitespaceToken(buff, buff, pos)

    @classmethod
    def parse_comment(cls, f: PosTrackingBufferedReader):
        with ReadThroughBuffer(f) as rtb:
            pos = None
            while rtb.read() not in ["\n", ""]:
                pos = pos or rtb.pos()
                continue
            buff = str(rtb)
            return CommentToken(buff, buff, pos)


    @classmethod
    def handle_escape(cls, ch: str):
        if ch == 'n':
            return "\n"
        elif ch == 'r':
            return "\r"
        elif ch == 'l':
            return "\014"  # form feed
        elif ch == 't':
            return "\t"
        elif ch == '"':
            return '"'

    @classmethod
    def parse_str(cls, f: PosTrackingBufferedReader):
        with ReadThroughBuffer(f) as rtb:
            assert rtb.read() == '"'
            pos = rtb.pos()
            content = []

            while True:
                if not rtb.peek():
                    raise

                # Handle end of string
                elif rtb.peek() == '"':
                    rtb.read()
                    break

                # Handle escape sequences
                elif rtb.peek() == '\\':
                    rtb.read()  # Discard the escape leader
                    # Octal escape
                    if rtb.peek() == '0':
                        rtb.read()
                        buff = []
                        while rtb.peek() in '01234567':
                            buff.append(rtb.read())
                        content.append(chr(int(''.join(buff), 8)))

                    # Hex escape
                    elif rtb.peek() == 'x':
                        rtb.read()  # Discard the escape leader
                        buff = []
                        while rtb.peek() in '0123456789abcdefABCDEF':
                            buff.append(rtb.read())
                        content.append(chr(int(''.join(buff), 16)))

                    else:
                        content.append(cls.handle_escape(rtb.read()))

                else:
                    content.append(rtb.read())

        buff = str(rtb)
        return StringToken(content, buff, pos)


## Parsing interface
def parses(buff: str,
           parser: SexpParser = Parser,
           source_name=None):
    """Parse a single s-expression from a string, returning its token tree."""

    return parse(StringIO(buff), parser, source_name or f"<string {id(buff):x}>")


def parsef(path: str,
           parser: SexpParser = Parser):
    """Parse a single s-expression from the file named by a string, returning its token tree."""

    with open(path, "r") as f:
        return parse(f, parser, path)


def parse(file: IO,
          parser: SexpParser = Parser,
          source_name=None):
    """Parse a single sexpression from a file-like object, returning its token tree."""

    return parser.parse(
        PosTrackingBufferedReader(
            file,
            source_name=source_name
        )
    )


## Loading interface
def loads(buff: str,
          parser: SexpParser = Parser,
          source_name=None):
    """Load a single s-expression from a string, returning its object representation."""

    return load(StringIO(buff), parser, source_name or f"<string {id(buff):x}>")


def loadf(path: str,
          parser: SexpParser = Parser):
    """Load a single s-expression from the file named by a string, returning its object representation."""

    with open(path, "r") as f:
        return load(f, parser, path)


def load(file: IO,
         parser: SexpParser = Parser,
         source_name=None):
    """Load a single sexpression from a file-like object, returning its object representation."""

    return parser.load(
        PosTrackingBufferedReader(
            file,
            source_name=source_name
        )
    )


## Dumping interface
def dump(file: IO, obj):
    """Given an object, dump its s-expression coding to the given file-like object."""

    raise NotImplementedError()


def dumps(obj):
    """Given an object, dump its s-expression coding to a string and return that string."""

    with StringIO("") as f:
        dump(f, obj)
        return str(f)
