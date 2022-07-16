#!/usr/bin/env python3

from random import choices
from string import ascii_lowercase, digits
from typing import List, Optional, Sequence, Union

from ichor import isa


def gensym(prefix = None) -> isa.Label:
    frag = "".join(choices(ascii_lowercase + digits, k=8))
    return isa.Label(f"{prefix or 'gensym'}_{frag}")


class FuncBuilder(object):
    def __init__(self) -> None:
        self._opcodes = []

    def _write(self, op):
        self._opcodes.append(op)

    def write(self, op: Union[isa.Opcode, isa.Label, Sequence[isa.Opcode]]):

        def flatten(o):
            for e in o:
                if isinstance(e, (isa.Opcode, isa.Label)):
                    yield e
                else:
                    yield from flatten(e)

        if isinstance(op, (isa.Opcode, isa.Label)):
            self._opcodes.append(op)
        else:
            for e in op:
                self.write(e)

    def make_label(self, prefix: Optional[str] = ""):
        return gensym(prefix)

    def build(self) -> List[isa.Opcode]:
        """Assemble the written body into fully resolved opcodes."""

        # The trivial two-pass assembler. First pass removes labels from the
        # opcode stream, marking where they occurred.

        labels = {}
        unassembled = []
        for op in self._opcodes:
            match op:
                case isa.Label(_) as l:
                    assert l not in labels  # isa.Label marks must be unique.
                    labels[l] = len(unassembled)
                case o:
                    unassembled.append(o)

        # Second pass rewrites instructions (which can reference forwards OR
        # backwards labels) with real targets instead of labels.
        assembled = []
        for op in unassembled:
            match op:
                case isa.GOTO(isa.Label(_) as l):
                    assembled.append(isa.GOTO(labels[l]))

                case isa.VTEST(isa.Label(_) as l):
                    assembled.append(isa.VTEST(labels[l]))

                case o:
                    assembled.append(o)

        return assembled


def assemble(builder_cls=FuncBuilder, /, **opcodes: List[isa.Opcode]) -> List[isa.Opcode]:
    builder = builder_cls()
    for o in opcodes:
        builder.write(o)
    return builder.build()


class LocalBuilder(FuncBuilder):
    def __init__(self):
        super().__init__()
        self._stack = 0
        self._labels = {}

    def _write(self, op):
        pass

    def write_local(self, label: isa.Label):
        pass

    def get_local(self, label: isa.Label):
        pass
