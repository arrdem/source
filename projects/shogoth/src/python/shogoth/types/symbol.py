import typing as t


class Symbol(t.NamedTuple):
    name: str
    namespace: t.Optional[str] = None

    def qualify(self, ns: str):
        return Symbol(self.name, ns)

    def unqualified(self):
        if not self.namespace:
            return self
        else:
            return Symbol(self.name)

    def __str__(self):
        if self.namespace:
            return f"{self.namespace}/{self.name}"
        else:
            return self.name
