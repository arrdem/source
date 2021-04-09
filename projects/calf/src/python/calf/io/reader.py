"""
Various Reader class instances.
"""


class Position(object):
    def __init__(self, offset, line, column):
        self.offset = offset
        self.line = line
        self.column = column

    def __repr__(self):
        return "<Pos %r (%r:%r)>" % (self.offset, self.line, self.column)

    def __str__(self):
        return self.__repr__()


class PosReader(object):
    """A wrapper for anything that can be read from. Tracks offset, line and column information."""

    def __init__(self, reader):
        self.reader = reader
        self.offset = 0
        self.line = 1
        self.column = 0

    def read(self, n=1):
        """
        Returns a pair (position, text) where position is the position of the first character in the
        returned text. Text is a string of length up to or equal to `n` in length.
        """
        p = self.position

        if n == 1:
            chr = self.reader.read(n)

            if chr != "":
                self.offset += 1
                self.column += 1

            if chr == "\n":
                self.line += 1
                self.column = 0

            return (
                p,
                chr,
            )

        else:
            return (
                p,
                "".join(self.read(n=1)[1] for i in range(n)),
            )

    @property
    def position(self):
        """The position of the last character read."""
        return Position(self.offset, self.line, self.column)


class PeekPosReader(PosReader):
    """A wrapper for anything that can be read from. Provides a way to peek the next character."""

    def __init__(self, reader):
        self.reader = reader if isinstance(reader, PosReader) else PosReader(reader)
        self._peek = None

    def read(self, n=1):
        """
        Same as `PosReader.read`.  Returns a pair (pos, text) where pos is the position of the first
        read character and text is a string of length up to `n`.  If a peeked character exists, it
        is consumed by this operation.
        """
        if self._peek and n == 1:
            a = self._peek
            self._peek = None
            return a

        else:
            p, t = self._peek or (None, "")

            if self._peek:
                self._peek = None

            p_, t_ = self.reader.read(n=(n if not t else n - len(t)))
            p = p or p_

            return (p, t + t_)

    def peek(self):
        """Returns the (pos, text) pair which would be read next by read(n=1)."""
        if self._peek is None:
            self._peek = self.reader.read(n=1)
        return self._peek

    @property
    def position(self):
        """The position of the last character read."""
        return self.reader.position
