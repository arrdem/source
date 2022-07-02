#!/usr/bin/env python3

from dataclasses import dataclass


@dataclass
class Symbol(object):
    name: str
    namespace: "Symbol" = None

    def __hash__(self):
        return hash(self.name)

    def qualify(self, name: str) -> "Symbol":
        return Symbol(
            name = self.name,
            namespace = Symbol(name)
        )

    def unqualified(self):
        return Symbol(self.name)


class Keyword(Symbol):

    def qualify(self, name: str) -> "Keyword":
        return Keyword(
            name = self.name,
            namespace = Keyword(name)
        )

    def unqualified(self):
        return Keyword(self.name)


class List(list):
    pass


class Vec(list):
    pass
