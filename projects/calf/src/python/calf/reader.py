"""The Calf reader

Unlike the lexer and parser which are mostly information preserving, the reader
is designed to be a somewhat pluggable structure for implementing transforms and
discarding information.

"""

from typing import *

from calf.lexer import lex_buffer, lex_file
from calf.parser import parse_stream
from calf.token import *
from calf.types import *


class CalfReader(object):
    def handle_keyword(self, t: CalfToken) -> Any:
        """Convert a token to an Object value for a symbol.

        Implementations could convert kws to strings, to a dataclass of some
        sort, use interning, or do none of the above.

        """

        return Keyword.of(t.more.get("name"), t.more.get("namespace"))

    def handle_symbol(self, t: CalfToken) -> Any:
        """Convert a token to an Object value for a symbol.

        Implementations could convert syms to strings, to a dataclass of some
        sort, use interning, or do none of the above.

        """

        return Symbol.of(t.more.get("name"), t.more.get("namespace"))

    def handle_dispatch(self, t: CalfDispatchToken) -> Any:
        """Handle a #foo <> dispatch token.

        Implementations may choose how dispatch is mapped to values, for
        instance by imposing a static mapping or by calling out to runtime state
        or other data sources to implement this hook. It's intended to be an
        open dispatch mechanism, unlike the others which should have relatively
        defined behavior.

        The default implementation simply preserves the dispatch token.

        """

        return t

    def handle_meta(self, t: CalfMetaToken) -> Any:
        """Handle a ^<> <> so called 'meta' token.

        Implementations may choose how to process metadata, discarding it or
        consuming it somehow.

        The default implementation simply discards the tag value.

        """

        return self.read1(t.value)

    def make_quote(self):
        """Factory. Returns the quote or equivalent symbol. May use `self.make_symbol()` to do so."""

        return Symbol.of("quote")

    def handle_quote(self, t: CalfQuoteToken) -> Any:
        """Handle a 'foo quote form."""

        return Vector.of([self.make_quote(), self.read1(t.value)])

    def read1(self, t: CalfToken) -> Any:
        # Note: 'square' and 'round' lists are treated the same. This should be
        # a hook. Should {} be a "list" too until it gets reader hooked into
        # being a mapping or a set?
        if isinstance(t, CalfListToken):
            return Vector.of(self.read(t.value))

        elif isinstance(t, CalfDictToken):
            return Map.of([(self.read1(k), self.read1(v)) for k, v in t.items()])

        # Magical pairwise stuff
        elif isinstance(t, CalfQuoteToken):
            return self.handle_quote(t)

        elif isinstance(t, CalfMetaToken):
            return self.handle_meta(t)

        elif isinstance(t, CalfDispatchToken):
            return self.handle_dispatch(t)

        # Stuff with real factories
        elif isinstance(t, CalfKeywordToken):
            return self.handle_keyword(t)

        elif isinstance(t, CalfSymbolToken):
            return self.handle_symbol(t)

        # Terminals
        elif isinstance(t, CalfStrToken):
            return str(t)

        elif isinstance(t, CalfIntegerToken):
            return int(t)

        elif isinstance(t, CalfFloatToken):
            return float(t)

        else:
            raise ValueError(f"Unsupported token type {t!r} ({type(t)})")

    def read(self, stream):
        """Given a sequence of tokens, read 'em."""

        for t in stream:
            yield self.read1(t)


def read_stream(stream, reader: CalfReader = None):
    """Read from a stream of parsed tokens."""

    reader = reader or CalfReader()
    yield from reader.read(stream)


def read_buffer(buffer):
    """Read from a buffer, producing a lazy sequence of all top level forms."""

    yield from read_stream(parse_stream(lex_buffer(buffer)))


def read_file(file):
    """Read from a file, producing a lazy sequence of all top level forms."""

    yield from read_stream(parse_stream(lex_file(file)))


def main():
    """A CURSES application for using the reader."""

    from calf.cursedrepl import curse_repl

    def handle_buffer(buff, count):
        return list(
            read_stream(parse_stream(lex_buffer(buff, source=f"<Example {count}>")))
        )

    curse_repl(handle_buffer)
