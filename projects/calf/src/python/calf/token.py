"""
Tokens.

The philosophy here is that to the greatest extent possible we want to preserve lexical (source)
information about indentation, position and soforth.  That we have to do so well mutably is just a
pain in the ass and kinda unavoidable.

Consequently, this file defines classes which wrap core Python primitives, providing all the usual
bits in terms of acting like values, while preserving fairly extensive source information.
"""


class CalfToken:
    """
    Token object.

    The result of reading a token from the source character feed.
    Encodes the source, and the position in the source from which it was read.
    """

    def __init__(self, type, value, source, start_position, more):
        self.type = type
        self.value = value
        self.source = source
        self.start_position = start_position
        self.more = more if more is not None else {}

    def __repr__(self):
        return "<%s:%s %r %s %r>" % (
            type(self).__name__,
            self.type,
            self.value,
            self.loc(),
            self.more,
        )

    def loc(self):
        return "%r@%r:%r" % (
            self.source,
            self.line,
            self.column,
        )

    def __str__(self):
        return self.value

    @property
    def offset(self):
        if self.start_position is not None:
            return self.start_position.offset

    @property
    def line(self):
        if self.start_position is not None:
            return self.start_position.line

    @property
    def column(self):
        if self.start_position is not None:
            return self.start_position.column


class CalfBlockToken(CalfToken):
    """
    (Block) Token object.

    The base result of parsing a token with a start and an end position.
    """

    def __init__(self, type, value, source, start_position, end_position, more):
        CalfToken.__init__(self, type, value, source, start_position, more)
        self.end_position = end_position


class CalfListToken(CalfBlockToken, list):
    """
    (list) Token object.

    The final result of reading a parens list through the Calf lexer stack.
    """

    def __init__(self, type, value, source, start_position, end_position):
        CalfBlockToken.__init__(
            self, type, value, source, start_position, end_position, None
        )
        list.__init__(self, value)


class CalfDictToken(CalfBlockToken, dict):
    """
    (dict) Token object.

    The final(ish) result of reading a braces list through the Calf lexer stack.
    """

    def __init__(self, type, value, source, start_position, end_position):
        CalfBlockToken.__init__(
            self, type, value, source, start_position, end_position, None
        )
        dict.__init__(self, value)


class CalfIntegerToken(CalfToken, int):
    """
    (int) Token object.


    The final(ish) result of reading an integer.
    """

    def __new__(cls, value):
        return int.__new__(cls, value.value)

    def __init__(self, value):
        CalfToken.__init__(
            self,
            value.type,
            value.value,
            value.source,
            value.start_position,
            value.more,
        )


class CalfFloatToken(CalfToken, float):
    """
    (int) Token object.


    The final(ish) result of reading a float.
    """

    def __new__(cls, value):
        return float.__new__(cls, value.value)

    def __init__(self, value):
        CalfToken.__init__(
            self,
            value.type,
            value.value,
            value.source,
            value.start_position,
            value.more,
        )


class CalfStrToken(CalfToken, str):
    """
    (str) Token object.


    The final(ish) result of reading a string.
    """

    def __new__(cls, token, buff):
        return str.__new__(cls, buff)

    def __init__(self, token, buff):
        CalfToken.__init__(
            self,
            token.type,
            buff,
            token.source,
            token.start_position,
            token.more,
        )
        str.__init__(self)


class CalfSymbolToken(CalfToken):
    """A symbol."""

    def __init__(self, token):
        CalfToken.__init__(
            self,
            token.type,
            token.value,
            token.source,
            token.start_position,
            token.more,
        )


class CalfKeywordToken(CalfToken):
    """A keyword."""

    def __init__(self, token):
        CalfToken.__init__(
            self,
            token.type,
            token.value,
            token.source,
            token.start_position,
            token.more,
        )


class CalfMetaToken(CalfToken):
    """A ^ meta token."""

    def __init__(self, token, meta, value):
        CalfToken.__init__(
            self,
            token.type,
            value,
            token.source,
            token.start_position,
            token.more,
        )
        self.meta = meta


class CalfDispatchToken(CalfToken):
    """A # macro dispatch token."""

    def __init__(self, token, tag, value):
        CalfToken.__init__(
            self,
            token.type,
            value,
            token.source,
            token.start_position,
            token.more,
        )
        self.tag = tag


class CalfQuoteToken(CalfToken):
    """A ' quotation."""

    def __init__(self, token, quoted):
        CalfToken.__init__(
            self,
            token.type,
            quoted,
            token.source,
            token.start_position,
            token.more,
        )
