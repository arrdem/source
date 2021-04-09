"""The module analyzer chews modules using bindings.

Using the parser and syntax analyzer, this module chews on analyzed syntax trees doing the heavy lifting of working with
modules, namespaces and bindings. Gotta sort out all those symbols somewhere.
"""

from io import StringIO
from typing import IO, NamedTuple, Mapping
from abc import ABC, abstractmethod, abstractproperty

import flowmetal.parser as p
import flowmetal.syntax_analyzer as sa


class Namespace(NamedTuple):


## Syntax analysis implementation
class AnalyzerBase(ABC):
    """Analyzer interface."""

    @classmethod
    @abstractmethod
    def analyze(cls, token: sa.ValueLevelExpr):
        """Analyze an expr tree, returning a binding tree."""


class Analyzer(AnalyzerBase):
    @classmethod
    def analyze(cls,
                token: sa.ValueLevelExpr,
                environment = None):
        pass


## Analysis interface
def analyzes(buff: str,
             module_analyzer: AnalyzerBase = Analyzer,
             module_environment = None,
             syntax_analyzer: sa.AnalyzerBase = sa.Analyzer,
             parser: p.SexpParser = p.Parser,
             source_name = None):
    """Parse a single s-expression from a string, returning its token tree."""

    return analyze(StringIO(buff),
                   module_analyzer,
                   module_environment,
                   syntax_analyzer,
                   parser,
                   source_name or f"<string {id(buff):x}>")


def analyzef(path: str,
             module_analyzer: AnalyzerBase = Analyzer,
             module_environment = None,
             syntax_analyzer: sa.AnalyzerBase = sa.Analyzer,
             parser: p.SexpParser = p.Parser):
    """Parse a single s-expression from the file named by a string, returning its token tree."""

    with open(path, "r") as f:
        return analyze(f,
                       module_analyzer,
                       module_environment,
                       syntax_analyzer,
                       parser,
                       path)


def analyze(file: IO,
            module_analyzer: AnalyzerBase = Analyzer,
            module_environment = None,
            syntax_analyzer: sa.AnalyzerBase = sa.Analyzer,
            parser: p.SexpParser = p.Parser,
            source_name = None):
    """Parse a single sexpression from a file-like object, returning its token tree."""

    return module_analyzer.analyze(
        syntax_analyzer.analyze(
            p.parse(file, parser, source_name)),
        module_environment)
