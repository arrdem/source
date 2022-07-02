#!/usr/bin/env python3

from dataclasses import dataclass
from random import choices
from string import ascii_lowercase, digits
from typing import List

from ichor.isa import Opcode


@dataclass
class Label(object):
    name: str

    def __hash__(self):
        return hash(self.name)

class FuncBuilder(object):
    def __init__(self) -> None:
        self._opcodes = []

    def write(self, op: Opcode):
        self._opcodes.append(op)

    def make_label(self, prefix=""):
        frag = ''.join(choices(ascii_lowercase + digits, k=8))
        return Label(f"{prefix or 'gensym'}_{frag}")

    def set_label(self, label: Label):
        self._opcodes.append(label)

    def build(self) -> List[Opcode]:
        """Assemble the written body into fully resolved opcodes."""

        # The trivial two-pass assembler. First pass removes labels from the
        # opcode stream, marking where they occurred.

        labels = {}
        unassembled = []
        for op in self._opcodes:
            match op:
                case Label(_) as l:
                    assert l not in labels  # Label marks must be unique.
                    labels[l] = len(unassembled)
                case o:
                    unassembled.append(o)

        # Second pass rewrites instructions (which can reference forwards OR
        # backwards labels) with real targets instead of labels.
        assembled = []
        for op in unassembled:
            match op:
                case Opcode.GOTO(Label(_) as l):
                    assembled.append(Opcode.GOTO(labels[l]))

                case Opcode.VTEST(Label(_) as l):
                    assembled.append(Opcode.VTEST(labels[l]))

                case o:
                    assembled.append(o)

        return assembled
