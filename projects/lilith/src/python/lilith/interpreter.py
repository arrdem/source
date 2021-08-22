"""
A quick and dirty recursive interpreter for Lilith.
"""

import typing as t

from lilith.parser import Apply, Block, Symbol
from lilith.reader import Module


class Runtime(t.NamedTuple):
    name: str
    prelude: Symbol
    modules: t.Dict[Symbol, Module]


class BindingNotFound(KeyError):
    def __init__(self, msg, context):
        super().__init__(msg)
        self.context = context


class Bindings(object):
    def __init__(self, name=None, parent=None):
        self._name = None
        self._parent = None
        self._bindings = {}

    def get(self, key):
        if key in self._bindings:
            return self._bindings.get(key)
        elif self._parent:
            try:
                return self._parent.get(key)
            except BindingNotFound as e:
                raise BindingNotFound(str(e), self)
        else:
            raise BindingNotFound(f"No binding key {key}", self)


def lookup(runtime, mod, locals, name):
    """Implement resolving a name against multiple namespaces."""

    err = None
    try:
        return locals.get(name)
    except BindingNotFound as e:
        err = e

    if name in mod.defs:
        return mod.defs.get(name)

    raise err or KeyError

    # FIXME (arrdem 2021-08-21):
    #   How do we ever get references to stuff in other modules?
    #   !import / !require is probably The Way


def eval(ctx: Runtime, mod: Module, locals: Bindings, expr):
    """Eval.

    In the context of a given runtime and module which must exist within the
    given runtime, evaluate the given expression recursively.

    """

    # Pointedly not assert that the module is ACTUALLY in the runtime,
    # We're just going to assume this for convenience.

    if isinstance(expr, Symbol):
        return lookup(ctx, mod, locals, expr)

    elif isinstance(expr, Apply):
        # Evaluate the call target
        fun = eval(ctx, mod, locals, expr.target)
        # Evaluate the parameters
        args = eval(ctx, mod, locals, expr.args.positionals)
        kwargs = eval(ctx, mod, locals, expr.args.kwargs)
        # Use Python's __call__ protocol
        return fun(*args, **kwargs)

    elif isinstance(expr, (int, float, str)):
        return expr

    elif isinstance(expr, list):
        return [eval(ctx, mod, locals, i) for i in expr]

    elif isinstance(expr, tuple):
        return tuple(eval(ctx, mod, locals, i) for i in expr)

    elif isinstance(expr, dict):
        return {
            eval(ctx, mod, locals, k): eval(ctx, mod, locals, v)
            for k, v in expr.items()
        }

    else:
        raise RuntimeError(f"Can't eval {expr}")
