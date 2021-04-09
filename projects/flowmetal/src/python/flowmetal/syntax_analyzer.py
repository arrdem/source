"""
The parser just parses and tokenizes.

The [syntax] syntax_analyzer interprets a parse sequence into a syntax tree which can be checked, type inferred and compiled.
"""

from abc import ABC, abstractmethod
from io import StringIO
from typing import NamedTuple, List, Union, Any, IO, Tuple
from enum import Enum

import flowmetal.parser as p


### Types
## We are not, in fact, sponsored by Typelevel LLC.
class TypeLevelExpr(object):
    """A base class for type-level expressions."""
    pass


class GenericExpr(TypeLevelExpr, NamedTuple):
    """'invocation' (application) of a generic type to Type[Level]Exprs."""
    pass


class TypeExpr(TypeLevelExpr, NamedTuple):
    """A bound (or yet to be bound) type level symbol."""
    pass


class BuiltinType(TypeLevelExpr, Enum):
    """Built in types for atoms."""
    BOOLEAN = 'Boolean'
    SYMBOL = 'Symbol'
    KEYWORD = 'Keyword'
    STRING = 'String'
    INTEGER = 'Integer'
    FRACTION = 'Fraction'
    FLOAT = 'Float'


class ConstraintExpr(TypeLevelExpr, NamedTuple):
    """A value-level constraint (predicate) as a type."""


## Terms
# Now down to reality
class ValueLevelExpr(object):
    """A base class for value-level expressions."""


class TriviallyTypedExpr(ValueLevelExpr):
    """And some of those expressions have trivial types."""
    @property
    def type(self) -> TypeExpr:
        """The type of an expression."""


class AscribeExpr(TriviallyTypedExpr, NamedTuple):
    value: ValueLevelExpr
    type: TypeLevelExpr


class ConstExpr(TriviallyTypedExpr, NamedTuple):
    """Constant expressions. Keywords, strings, numbers, that sort of thing."""

    token: p.ConstTokenBase

    @property
    def data(self) -> Any:
        """The value of the constant."""
        # The parser gives us this data
        return self.token.data

    @abstractmethod
    def type(self):
        raise NotImplementedError()


class BooleanExpr(ConstExpr):
    @property
    def type(self):
        return BuiltinType.BOOLEAN


class IntegerExpr(ConstExpr):
    @property
    def type(self):
        return BuiltinType.INTEGER


class FractionExpr(ConstExpr):
    @property
    def type(self):
        return BuiltinType.FRACTION


class FloatExpr(ConstExpr):
    @property
    def type(self):
        return BuiltinType.FLOAT


class KeywordExpr(ConstExpr):
    @property
    def type(self):
        return BuiltinType.KEYWORD


class StringExpr(ConstExpr):
    @property
    def type(self):
        return BuiltinType.STRING


class ListExpr(ValueLevelExpr, NamedTuple):
    elements: List[ValueLevelExpr]


## 'real' AST nodes
class DoExpr(ValueLevelExpr, NamedTuple):
    effect_exprs: List[ValueLevelExpr]
    ret_expr: ValueLevelExpr


class LetExpr(ValueLevelExpr, NamedTuple):
    binding_exprs: List[Tuple]
    ret_expr: DoExpr


class FnExpr(ValueLevelExpr, NamedTuple):
    arguments: List
    ret_type: TypeExpr
    ret_expr: DoExpr


## Syntax analysis implementation
class AnalyzerBase(ABC):
    """Analyzer interface."""

    @classmethod
    @abstractmethod
    def analyze(cls, token: p.TokenBase) -> ValueLevelExpr:
        """Analyze a token tree, returning an expr tree."""


def _t(txt):
    return p.SymbolToken(txt, txt, None)


class Analyzer(AnalyzerBase):
    """A reference Analyzer implementation.

    Walks a parsed token tree, building up a syntax tree.
    """
    TACK0 = _t('⊢')
    TACK1 = _t('|-')
    TACK2 = p.KeywordToken(":-", None, None)
    LET = _t('let')
    DO = _t('do')
    FN = _t('fn')
    LIST = _t('list')
    QUOTE = _t('quote')

    @classmethod
    def _tackp(cls, t):
        return t in [cls.TACK0, cls.TACK1, cls.TACK2]

    @classmethod
    def _nows(cls, tokens):
        return [t for t in tokens if not isinstance(t, p.WhitespaceToken)]

    @classmethod
    def _chomp(cls, tokens):
        """'chomp' an expression and optional ascription off the tokens, returning an expression and the remaining tokens."""

        if len(tokens) == 1:
            return cls.analyze(tokens[0]), []
        elif cls._tackp(tokens[1]):
            if len(tokens) >= 3:
                return (
                    AscribeExpr(
                        cls.analyze(tokens[0]),
                        cls.analyze(tokens[2])),
                    tokens[3:],
                )
            else:
                raise SyntaxError(f"Analyzing tack at {tokens[1].pos}, did not find following type ascription!")
        else:
            return cls.analyze(tokens[0]), tokens[1::]

    @classmethod
    def _terms(cls, tokens):
        terms = []
        tokens = cls._nows(tokens)
        while tokens:
            term, tokens = cls._chomp(tokens)
            terms.append(term)
        return terms

    @classmethod
    def analyze(cls, token: p.TokenBase):
        if isinstance(token, p.BooleanToken):
            return BooleanExpr(token)

        if isinstance(token, p.KeywordToken):
            return KeywordExpr(token)

        if isinstance(token, p.IntegerToken):
            return IntegerExpr(token)

        if isinstance(token, p.FractionToken):
            return FractionExpr(token)

        if isinstance(token, p.FloatToken):
            return FloatExpr(token)

        if isinstance(token, p.StringToken):
            return StringExpr(token)

        if isinstance(token, p.SymbolToken):
            return token

        if isinstance(token, p.ListToken):
            return cls.analyze_list(token)

    @classmethod
    def _do(cls, t, body: list):
        return p.ListToken([cls.DO] + body, t.raw, t.pos)

    @classmethod
    def analyze_list(cls, token: p.ListToken):
        """Analyze a list, for which there are several 'ground' forms."""

        # Expunge any whitespace tokens
        tokens = cls._nows(token.data)

        if len(tokens) == 0:
            return ListExpr([])

        if tokens[0] == cls.QUOTE:
            raise NotImplementedError("Quote isn't quite there!")

        if tokens[0] == cls.LIST:
            return ListExpr(cls._terms(tokens[1:]))

        if tokens[0] == cls.DO:
            return cls.analyze_do(token)

        if tokens[0] == cls.LET:
            return cls.analyze_let(token)

        if tokens[0] == cls.FN:
            return cls.analyze_fn(token)

        cls.analyze_invoke(tokens)

    @classmethod
    def analyze_let(cls, let_token):
        tokens = cls._nows(let_token.data[1:])
        assert len(tokens) >= 2
        assert isinstance(tokens[0], p.ListToken)
        bindings = []
        binding_tokens = cls._nows(tokens[0].data)
        tokens = tokens[1:]
        while binding_tokens:
            if isinstance(binding_tokens[0], p.SymbolToken):
                bindexpr = binding_tokens[0]
                binding_tokens = binding_tokens[1:]
            else:
                raise SyntaxError(f"Analyzing `let` at {let_token.pos}, got illegal binding expression {binding_tokens[0]}")

            if not binding_tokens:
                raise SyntaxError(f"Analyzing `let` at {let_token.pos}, got binding expression without subsequent value expression!")

            if cls._tackp(binding_tokens[0]):
                if len(binding_tokens) < 2:
                    raise SyntaxError(f"Analyzing `let` at {let_token.pos}, got `⊢` at {binding_tokens[0].pos} without type!")
                bind_ascription = cls.analyze(binding_tokens[1])
                binding_tokens = binding_tokens[2:]
                bindexpr = AscribeExpr(bindexpr, bind_ascription)

            if not binding_tokens:
                raise SyntaxError(f"Analyzing `let` at {let_token.pos}, got binding expression without subsequent value expression!")

            valexpr = binding_tokens[0]
            binding_tokens = cls.analyze(binding_tokens[1:])

            bindings.append((bindexpr, valexpr))

        # FIXME (arrdem 2020-07-18):
        #   This needs to happen with bindings
        tail = tokens[0] if len(tokens) == 1 else cls._do(let_token, tokens)
        return LetExpr(bindings, cls.analyze(tail))

    @classmethod
    def analyze_do(cls, do_token):
        tokens = cls._nows(do_token.data[1:])
        exprs = cls._terms(tokens)
        if exprs[:-1]:
            return DoExpr(exprs[:-1], exprs[-1])
        else:
            return exprs[-1]

    @classmethod
    def analyze_fn(cls, fn_token):
        tokens = cls._nows(fn_token.data[1:])
        assert len(tokens) >= 2
        assert isinstance(tokens[0], p.ListToken)

        args = []
        arg_tokens = cls._nows(tokens[0].data)
        while arg_tokens:
            argexpr, arg_tokens = cls._chomp(arg_tokens)
            args.append(argexpr)

        ascription = None
        if cls._tackp(tokens[1]):
            ascription = cls.analyze(tokens[2])
            tokens = tokens[2:]
        else:
            tokens = tokens[1:]

        # FIXME (arrdem 2020-07-18):
        #   This needs to happen with bindings
        body = cls.analyze(cls._do(fn_token, tokens))
        return FnExpr(args, ascription, body)


## Analysis interface
def analyzes(buff: str,
             syntax_analyzer: AnalyzerBase = Analyzer,
             parser: p.SexpParser = p.Parser,
             source_name = None):
    """Parse a single s-expression from a string, returning its token tree."""

    return analyze(StringIO(buff), syntax_analyzer, parser, source_name or f"<string {id(buff):x}>")


def analyzef(path: str,
             syntax_analyzer: AnalyzerBase = Analyzer,
             parser: p.SexpParser = p.Parser):
    """Parse a single s-expression from the file named by a string, returning its token tree."""

    with open(path, "r") as f:
        return analyze(f, syntax_analyzer, parser, path)


def analyze(file: IO,
            syntax_analyzer: AnalyzerBase = Analyzer,
            parser: p.SexpParser = p.Parser,
            source_name = None):
    """Parse a single sexpression from a file-like object, returning its token tree."""

    return syntax_analyzer.analyze(p.parse(file, parser, source_name))
