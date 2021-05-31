"""
The Calf parser.
"""

from itertools import tee
import logging

from calf.grammar import MATCHING, WHITESPACE_TYPES
from calf.lexer import CalfLexer, lex_buffer, lex_file
from calf.token import *


log = logging.getLogger(__name__)


def mk_list(contents, open=None, close=None):
    return CalfListToken(
        "LIST", contents, open.source, open.start_position, close.start_position
    )


def mk_sqlist(contents, open=None, close=None):
    return CalfListToken(
        "SQLIST", contents, open.source, open.start_position, close.start_position
    )


def pairwise(l: list) -> iter:
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    return zip(l[::2], l[1::2])


def mk_dict(contents, open=None, close=None):
    # FIXME (arrdem 2021-03-14):
    #   Raise a real SyntaxError of some sort.
    assert len(contents) % 2 == 0, "Improper dict!"
    return CalfDictToken(
        "DICT",
        list(pairwise(contents)),
        open.source,
        open.start_position,
        close.start_position,
    )


def mk_str(token):
    buff = token.value

    if buff.startswith('"""') and not buff.endswith('"""'):
        raise ValueError("Unterminated tripple quote string")

    elif buff.startswith('"') and not buff.endswith('"'):
        raise ValueError("Unterminated quote string")

    elif not buff.startswith('"') or buff == '"' or buff == '"""':
        raise ValueError("Illegal string")

    if buff.startswith('"""'):
        buff = buff[3:-3]
    else:
        buff = buff[1:-1]

    buff = buff.encode("utf-8").decode("unicode_escape")  # Handle escape codes

    return CalfStrToken(token, buff)


CTORS = {
    "PAREN_LEFT": mk_list,
    "BRACKET_LEFT": mk_sqlist,
    "BRACE_LEFT": mk_dict,
    "STRING": mk_str,
    "INTEGER": CalfIntegerToken,
    "FLOAT": CalfFloatToken,
    "SYMBOL": CalfSymbolToken,
    "KEYWORD": CalfKeywordToken,
}


class CalfParseError(Exception):
    """
    Base class for representing errors encountered parsing.
    """

    def __init__(self, message: str, token: CalfToken):
        super(Exception, self).__init__(message)
        self.token = token

    def __str__(self):
        return f"Parse error at {self.token.loc()}: " + super().__str__()


class CalfUnexpectedCloseParseError(CalfParseError):
    """
    Represents encountering an unexpected close token.
    """

    def __init__(self, token, matching_open=None):
        msg = f"encountered unexpected closing {token!r}"
        if matching_open:
            msg += f" which appears to match {matching_open!r}"
        super(CalfParseError, self).__init__(msg, token)
        self.token = token
        self.matching_open = matching_open


class CalfMissingCloseParseError(CalfParseError):
    """
    Represents a failure to encounter an expected close token.
    """

    def __init__(self, expected_close_token, open_token):
        super(CalfMissingCloseParseError, self).__init__(
            f"expected {expected_close_token} starting from {open_token}, got end of file.",
            open_token,
        )
        self.expected_close_token = expected_close_token


def parse_stream(
    stream,
    discard_whitespace: bool = True,
    discard_comments: bool = True,
    stack: list = None,
):
    """Parses a token stream, producing a lazy sequence of all read top level forms.

    If `discard_whitespace` is truthy, then no WHITESPACE tokens will be emitted
    into the resulting parse tree. Otherwise, WHITESPACE tokens will be
    included. Whether WHITESPACE tokens are included or not, the tokens of the
    tree will reflect original source locations.

    """

    stack = stack or []

    def recur(_stack=None):
        yield from parse_stream(
            stream, discard_whitespace, discard_comments, _stack or stack
        )

    for token in stream:
        # Whitespace discarding
        if token.type == "WHITESPACE" and discard_whitespace:
            continue

        elif token.type == "COMMENT" and discard_comments:
            continue

        # Built in reader macros
        elif token.type == "META":
            try:
                meta_t = next(recur())
            except StopIteration:
                raise CalfParseError("^ not followed by meta value", token)

            try:
                value_t = next(recur())
            except StopIteration:
                raise CalfParseError("^ not followed by value", token)

            yield CalfMetaToken(token, meta_t, value_t)

        elif token.type == "MACRO_DISPATCH":
            try:
                dispatch_t = next(recur())
            except StopIteration:
                raise CalfParseError("# not followed by dispatch value", token)

            try:
                value_t = next(recur())
            except StopIteration:
                raise CalfParseError("^ not followed by value", token)

            yield CalfDispatchToken(token, dispatch_t, value_t)

        elif token.type == "SINGLE_QUOTE":
            try:
                quoted_t = next(recur())
            except StopIteration:
                raise CalfParseError("' not followed by quoted form", token)

            yield CalfQuoteToken(token, quoted_t)

        # Compounds
        elif token.type in MATCHING.keys():
            balancing = MATCHING[token.type]
            elements = list(recur(stack + [(balancing, token)]))
            # Elements MUST have at least the close token in it
            if not elements:
                raise CalfMissingCloseParseError(balancing, token)

            elements, close = elements[:-1], elements[-1]
            if close.type != MATCHING[token.type]:
                raise CalfMissingCloseParseError(balancing, token)

            yield CTORS[token.type](elements, token, close)

        elif token.type in MATCHING.values():
            # Case of matching the immediate open
            if stack and token.type == stack[-1][0]:
                yield token
                break

            # Case of maybe matching something else, but definitely being wrong
            else:
                matching = next(
                    reversed([t[1] for t in stack if t[0] == token.type]), None
                )
                raise CalfUnexpectedCloseParseError(token, matching)

        # Atoms
        elif token.type in CTORS:
            yield CTORS[token.type](token)

        else:
            yield token


def parse_buffer(buffer, discard_whitespace=True, discard_comments=True):
    """
    Parses a buffer, producing a lazy sequence of all parsed level forms.

    Propagates all errors.
    """

    yield from parse_stream(lex_buffer(buffer), discard_whitespace, discard_comments)


def parse_file(file):
    """
    Parses a file, producing a lazy sequence of all parsed level forms.
    """

    yield from parse_stream(lex_file(file))


def main():
    """A CURSES application for using the parser."""

    from calf.cursedrepl import curse_repl

    def handle_buffer(buff, count):
        return list(parse_stream(lex_buffer(buff, source=f"<Example {count}>")))

    curse_repl(handle_buffer)
