from collections import defaultdict
import re


class TreeNode(object):
    def __init__(self, text, offset, elements=None):
        self.text = text
        self.offset = offset
        self.elements = elements or []

    def __iter__(self):
        for el in self.elements:
            yield el


class TreeNode1(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode1, self).__init__(text, offset, elements)
        self.clause = elements[0]


class TreeNode2(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode2, self).__init__(text, offset, elements)
        self.ws = elements[2]
        self.clauses = elements[3]


class TreeNode3(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode3, self).__init__(text, offset, elements)
        self.clause = elements[0]


class TreeNode4(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode4, self).__init__(text, offset, elements)
        self.ws = elements[1]
        self.clauses = elements[2]


class TreeNode5(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode5, self).__init__(text, offset, elements)
        self.word = elements[1]
        self.terms = elements[3]


class TreeNode6(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode6, self).__init__(text, offset, elements)
        self.term = elements[0]


class TreeNode7(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode7, self).__init__(text, offset, elements)
        self.ws = elements[1]
        self.terms = elements[2]


class TreeNode8(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode8, self).__init__(text, offset, elements)
        self.clause = elements[0]


class TreeNode9(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode9, self).__init__(text, offset, elements)
        self.ws = elements[2]
        self.clauses = elements[3]


class ParseError(SyntaxError):
    pass


FAILURE = object()


class Grammar(object):
    REGEX_1 = re.compile("^[A-Z]")
    REGEX_2 = re.compile("^[a-z0-9-_=<>]")
    REGEX_3 = re.compile("^[a-z0-9-_=<>]")
    REGEX_4 = re.compile("^[^']")
    REGEX_5 = re.compile('^[^\\"]')
    REGEX_6 = re.compile("^[^\\n]")
    REGEX_7 = re.compile("^[ \\t\\n]")

    def _read_dataset(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["dataset"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        remaining0, index1, elements0, address1 = 0, self._offset, [], True
        while address1 is not FAILURE:
            index2 = self._offset
            address1 = self._read_rule()
            if address1 is FAILURE:
                self._offset = index2
                address1 = self._read_comment()
                if address1 is FAILURE:
                    self._offset = index2
                    address1 = self._read_whitespace()
                    if address1 is FAILURE:
                        self._offset = index2
            if address1 is not FAILURE:
                elements0.append(address1)
                remaining0 -= 1
        if remaining0 <= 0:
            address0 = self._actions.make_dataset(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        else:
            address0 = FAILURE
        self._cache["dataset"][index0] = (address0, self._offset)
        return address0

    def _read_rule(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["rule"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_clause()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2 = self._offset
            index3, elements1 = self._offset, []
            address3 = FAILURE
            address3 = self._read_ws()
            if address3 is not FAILURE:
                elements1.append(address3)
                address4 = FAILURE
                chunk0 = None
                if self._offset < self._input_size:
                    chunk0 = self._input[self._offset : self._offset + 2]
                if chunk0 == ":-":
                    address4 = TreeNode(
                        self._input[self._offset : self._offset + 2], self._offset
                    )
                    self._offset = self._offset + 2
                else:
                    address4 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('":-"')
                if address4 is not FAILURE:
                    elements1.append(address4)
                    address5 = FAILURE
                    address5 = self._read_ws()
                    if address5 is not FAILURE:
                        elements1.append(address5)
                        address6 = FAILURE
                        address6 = self._read_clauses()
                        if address6 is not FAILURE:
                            elements1.append(address6)
                        else:
                            elements1 = None
                            self._offset = index3
                    else:
                        elements1 = None
                        self._offset = index3
                else:
                    elements1 = None
                    self._offset = index3
            else:
                elements1 = None
                self._offset = index3
            if elements1 is None:
                address2 = FAILURE
            else:
                address2 = TreeNode2(
                    self._input[index3 : self._offset], index3, elements1
                )
                self._offset = self._offset
            if address2 is FAILURE:
                address2 = TreeNode(self._input[index2:index2], index2)
                self._offset = index2
            if address2 is not FAILURE:
                elements0.append(address2)
                address7 = FAILURE
                chunk1 = None
                if self._offset < self._input_size:
                    chunk1 = self._input[self._offset : self._offset + 1]
                if chunk1 == ".":
                    address7 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address7 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('"."')
                if address7 is not FAILURE:
                    elements0.append(address7)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_rule(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        self._cache["rule"][index0] = (address0, self._offset)
        return address0

    def _read_clauses(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["clauses"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_clause()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2 = self._offset
            index3, elements1 = self._offset, []
            address3 = FAILURE
            chunk0 = None
            if self._offset < self._input_size:
                chunk0 = self._input[self._offset : self._offset + 1]
            if chunk0 == ",":
                address3 = TreeNode(
                    self._input[self._offset : self._offset + 1], self._offset
                )
                self._offset = self._offset + 1
            else:
                address3 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append('","')
            if address3 is not FAILURE:
                elements1.append(address3)
                address4 = FAILURE
                address4 = self._read_ws()
                if address4 is not FAILURE:
                    elements1.append(address4)
                    address5 = FAILURE
                    address5 = self._read_clauses()
                    if address5 is not FAILURE:
                        elements1.append(address5)
                    else:
                        elements1 = None
                        self._offset = index3
                else:
                    elements1 = None
                    self._offset = index3
            else:
                elements1 = None
                self._offset = index3
            if elements1 is None:
                address2 = FAILURE
            else:
                address2 = TreeNode4(
                    self._input[index3 : self._offset], index3, elements1
                )
                self._offset = self._offset
            if address2 is FAILURE:
                address2 = TreeNode(self._input[index2:index2], index2)
                self._offset = index2
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_clauses(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        self._cache["clauses"][index0] = (address0, self._offset)
        return address0

    def _read_clause(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["clause"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        address1 = self._read_negation()
        if address1 is FAILURE:
            address1 = TreeNode(self._input[index2:index2], index2)
            self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            address2 = self._read_word()
            if address2 is not FAILURE:
                elements0.append(address2)
                address3 = FAILURE
                chunk0 = None
                if self._offset < self._input_size:
                    chunk0 = self._input[self._offset : self._offset + 1]
                if chunk0 == "(":
                    address3 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address3 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('"("')
                if address3 is not FAILURE:
                    elements0.append(address3)
                    address4 = FAILURE
                    address4 = self._read_terms()
                    if address4 is not FAILURE:
                        elements0.append(address4)
                        address5 = FAILURE
                        chunk1 = None
                        if self._offset < self._input_size:
                            chunk1 = self._input[self._offset : self._offset + 1]
                        if chunk1 == ")":
                            address5 = TreeNode(
                                self._input[self._offset : self._offset + 1],
                                self._offset,
                            )
                            self._offset = self._offset + 1
                        else:
                            address5 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append('")"')
                        if address5 is not FAILURE:
                            elements0.append(address5)
                        else:
                            elements0 = None
                            self._offset = index1
                    else:
                        elements0 = None
                        self._offset = index1
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_clause(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        self._cache["clause"][index0] = (address0, self._offset)
        return address0

    def _read_negation(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["negation"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset : self._offset + 1]
        if chunk0 == "~":
            address0 = TreeNode(
                self._input[self._offset : self._offset + 1], self._offset
            )
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"~"')
        self._cache["negation"][index0] = (address0, self._offset)
        return address0

    def _read_terms(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["terms"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_term()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2 = self._offset
            index3, elements1 = self._offset, []
            address3 = FAILURE
            chunk0 = None
            if self._offset < self._input_size:
                chunk0 = self._input[self._offset : self._offset + 1]
            if chunk0 == ",":
                address3 = TreeNode(
                    self._input[self._offset : self._offset + 1], self._offset
                )
                self._offset = self._offset + 1
            else:
                address3 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append('","')
            if address3 is not FAILURE:
                elements1.append(address3)
                address4 = FAILURE
                address4 = self._read_ws()
                if address4 is not FAILURE:
                    elements1.append(address4)
                    address5 = FAILURE
                    address5 = self._read_terms()
                    if address5 is not FAILURE:
                        elements1.append(address5)
                    else:
                        elements1 = None
                        self._offset = index3
                else:
                    elements1 = None
                    self._offset = index3
            else:
                elements1 = None
                self._offset = index3
            if elements1 is None:
                address2 = FAILURE
            else:
                address2 = TreeNode7(
                    self._input[index3 : self._offset], index3, elements1
                )
                self._offset = self._offset
            if address2 is FAILURE:
                address2 = TreeNode(self._input[index2:index2], index2)
                self._offset = index2
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_terms(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        self._cache["terms"][index0] = (address0, self._offset)
        return address0

    def _read_term(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["term"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        address0 = self._read_string()
        if address0 is FAILURE:
            self._offset = index1
            address0 = self._read_lvar()
            if address0 is FAILURE:
                self._offset = index1
                address0 = self._read_word()
                if address0 is FAILURE:
                    self._offset = index1
        self._cache["term"][index0] = (address0, self._offset)
        return address0

    def _read_lvar(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["lvar"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset : self._offset + 1]
        if chunk0 is not None and Grammar.REGEX_1.search(chunk0):
            address1 = TreeNode(
                self._input[self._offset : self._offset + 1], self._offset
            )
            self._offset = self._offset + 1
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append("[A-Z]")
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            remaining0, index2, elements1, address3 = 0, self._offset, [], True
            while address3 is not FAILURE:
                chunk1 = None
                if self._offset < self._input_size:
                    chunk1 = self._input[self._offset : self._offset + 1]
                if chunk1 is not None and Grammar.REGEX_2.search(chunk1):
                    address3 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address3 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append("[a-z0-9-_=<>]")
                if address3 is not FAILURE:
                    elements1.append(address3)
                    remaining0 -= 1
            if remaining0 <= 0:
                address2 = TreeNode(
                    self._input[index2 : self._offset], index2, elements1
                )
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_symbol(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        self._cache["lvar"][index0] = (address0, self._offset)
        return address0

    def _read_word(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["word"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        remaining0, index1, elements0, address1 = 0, self._offset, [], True
        while address1 is not FAILURE:
            chunk0 = None
            if self._offset < self._input_size:
                chunk0 = self._input[self._offset : self._offset + 1]
            if chunk0 is not None and Grammar.REGEX_3.search(chunk0):
                address1 = TreeNode(
                    self._input[self._offset : self._offset + 1], self._offset
                )
                self._offset = self._offset + 1
            else:
                address1 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append("[a-z0-9-_=<>]")
            if address1 is not FAILURE:
                elements0.append(address1)
                remaining0 -= 1
        if remaining0 <= 0:
            address0 = self._actions.make_word(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        else:
            address0 = FAILURE
        self._cache["word"][index0] = (address0, self._offset)
        return address0

    def _read_string(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["string"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        address0 = self._read_sq_string()
        if address0 is FAILURE:
            self._offset = index1
            address0 = self._read_dq_string()
            if address0 is FAILURE:
                self._offset = index1
        self._cache["string"][index0] = (address0, self._offset)
        return address0

    def _read_sq_string(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["sq_string"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset : self._offset + 1]
        if chunk0 == "'":
            address1 = TreeNode(
                self._input[self._offset : self._offset + 1], self._offset
            )
            self._offset = self._offset + 1
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"\'"')
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            remaining0, index2, elements1, address3 = 0, self._offset, [], True
            while address3 is not FAILURE:
                chunk1 = None
                if self._offset < self._input_size:
                    chunk1 = self._input[self._offset : self._offset + 1]
                if chunk1 is not None and Grammar.REGEX_4.search(chunk1):
                    address3 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address3 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append("[^']")
                if address3 is not FAILURE:
                    elements1.append(address3)
                    remaining0 -= 1
            if remaining0 <= 0:
                address2 = TreeNode(
                    self._input[index2 : self._offset], index2, elements1
                )
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                chunk2 = None
                if self._offset < self._input_size:
                    chunk2 = self._input[self._offset : self._offset + 1]
                if chunk2 == "'":
                    address4 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address4 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('"\'"')
                if address4 is not FAILURE:
                    elements0.append(address4)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_string(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        self._cache["sq_string"][index0] = (address0, self._offset)
        return address0

    def _read_dq_string(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["dq_string"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset : self._offset + 1]
        if chunk0 == '"':
            address1 = TreeNode(
                self._input[self._offset : self._offset + 1], self._offset
            )
            self._offset = self._offset + 1
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"\\""')
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            remaining0, index2, elements1, address3 = 0, self._offset, [], True
            while address3 is not FAILURE:
                chunk1 = None
                if self._offset < self._input_size:
                    chunk1 = self._input[self._offset : self._offset + 1]
                if chunk1 is not None and Grammar.REGEX_5.search(chunk1):
                    address3 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address3 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('[^\\"]')
                if address3 is not FAILURE:
                    elements1.append(address3)
                    remaining0 -= 1
            if remaining0 <= 0:
                address2 = TreeNode(
                    self._input[index2 : self._offset], index2, elements1
                )
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                chunk2 = None
                if self._offset < self._input_size:
                    chunk2 = self._input[self._offset : self._offset + 1]
                if chunk2 == '"':
                    address4 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address4 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('"\\""')
                if address4 is not FAILURE:
                    elements0.append(address4)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_string(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        self._cache["dq_string"][index0] = (address0, self._offset)
        return address0

    def _read_ws(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["ws"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        remaining0, index1, elements0, address1 = 1, self._offset, [], True
        while address1 is not FAILURE:
            index2 = self._offset
            address1 = self._read_comment()
            if address1 is FAILURE:
                self._offset = index2
                address1 = self._read_whitespace()
                if address1 is FAILURE:
                    self._offset = index2
            if address1 is not FAILURE:
                elements0.append(address1)
                remaining0 -= 1
        if remaining0 <= 0:
            address0 = TreeNode(self._input[index1 : self._offset], index1, elements0)
            self._offset = self._offset
        else:
            address0 = FAILURE
        self._cache["ws"][index0] = (address0, self._offset)
        return address0

    def _read_comment(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["comment"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset : self._offset + 1]
        if chunk0 == "%":
            address1 = TreeNode(
                self._input[self._offset : self._offset + 1], self._offset
            )
            self._offset = self._offset + 1
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"%"')
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            remaining0, index2, elements1, address3 = 0, self._offset, [], True
            while address3 is not FAILURE:
                chunk1 = None
                if self._offset < self._input_size:
                    chunk1 = self._input[self._offset : self._offset + 1]
                if chunk1 is not None and Grammar.REGEX_6.search(chunk1):
                    address3 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address3 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append("[^\\n]")
                if address3 is not FAILURE:
                    elements1.append(address3)
                    remaining0 -= 1
            if remaining0 <= 0:
                address2 = TreeNode(
                    self._input[index2 : self._offset], index2, elements1
                )
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                chunk2 = None
                if self._offset < self._input_size:
                    chunk2 = self._input[self._offset : self._offset + 1]
                if chunk2 == "\n":
                    address4 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address4 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('"\\n"')
                if address4 is not FAILURE:
                    elements0.append(address4)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_comment(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        self._cache["comment"][index0] = (address0, self._offset)
        return address0

    def _read_whitespace(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["whitespace"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        remaining0, index1, elements0, address1 = 1, self._offset, [], True
        while address1 is not FAILURE:
            chunk0 = None
            if self._offset < self._input_size:
                chunk0 = self._input[self._offset : self._offset + 1]
            if chunk0 is not None and Grammar.REGEX_7.search(chunk0):
                address1 = TreeNode(
                    self._input[self._offset : self._offset + 1], self._offset
                )
                self._offset = self._offset + 1
            else:
                address1 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append("[ \\t\\n]")
            if address1 is not FAILURE:
                elements0.append(address1)
                remaining0 -= 1
        if remaining0 <= 0:
            address0 = self._actions.make_ws(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        else:
            address0 = FAILURE
        self._cache["whitespace"][index0] = (address0, self._offset)
        return address0

    def _read_command(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache["command"].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_clause()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2 = self._offset
            index3, elements1 = self._offset, []
            address3 = FAILURE
            address3 = self._read_ws()
            if address3 is not FAILURE:
                elements1.append(address3)
                address4 = FAILURE
                chunk0 = None
                if self._offset < self._input_size:
                    chunk0 = self._input[self._offset : self._offset + 2]
                if chunk0 == ":-":
                    address4 = TreeNode(
                        self._input[self._offset : self._offset + 2], self._offset
                    )
                    self._offset = self._offset + 2
                else:
                    address4 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('":-"')
                if address4 is not FAILURE:
                    elements1.append(address4)
                    address5 = FAILURE
                    address5 = self._read_ws()
                    if address5 is not FAILURE:
                        elements1.append(address5)
                        address6 = FAILURE
                        address6 = self._read_clauses()
                        if address6 is not FAILURE:
                            elements1.append(address6)
                        else:
                            elements1 = None
                            self._offset = index3
                    else:
                        elements1 = None
                        self._offset = index3
                else:
                    elements1 = None
                    self._offset = index3
            else:
                elements1 = None
                self._offset = index3
            if elements1 is None:
                address2 = FAILURE
            else:
                address2 = TreeNode9(
                    self._input[index3 : self._offset], index3, elements1
                )
                self._offset = self._offset
            if address2 is FAILURE:
                address2 = TreeNode(self._input[index2:index2], index2)
                self._offset = index2
            if address2 is not FAILURE:
                elements0.append(address2)
                address7 = FAILURE
                index4 = self._offset
                chunk1 = None
                if self._offset < self._input_size:
                    chunk1 = self._input[self._offset : self._offset + 1]
                if chunk1 == ".":
                    address7 = TreeNode(
                        self._input[self._offset : self._offset + 1], self._offset
                    )
                    self._offset = self._offset + 1
                else:
                    address7 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('"."')
                if address7 is FAILURE:
                    self._offset = index4
                    chunk2 = None
                    if self._offset < self._input_size:
                        chunk2 = self._input[self._offset : self._offset + 1]
                    if chunk2 == "?":
                        address7 = TreeNode(
                            self._input[self._offset : self._offset + 1], self._offset
                        )
                        self._offset = self._offset + 1
                    else:
                        address7 = FAILURE
                        if self._offset > self._failure:
                            self._failure = self._offset
                            self._expected = []
                        if self._offset == self._failure:
                            self._expected.append('"?"')
                    if address7 is FAILURE:
                        self._offset = index4
                        chunk3 = None
                        if self._offset < self._input_size:
                            chunk3 = self._input[self._offset : self._offset + 1]
                        if chunk3 == "!":
                            address7 = TreeNode(
                                self._input[self._offset : self._offset + 1],
                                self._offset,
                            )
                            self._offset = self._offset + 1
                        else:
                            address7 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append('"!"')
                        if address7 is FAILURE:
                            self._offset = index4
                if address7 is not FAILURE:
                    elements0.append(address7)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_command(
                self._input, index1, self._offset, elements0
            )
            self._offset = self._offset
        self._cache["command"][index0] = (address0, self._offset)
        return address0


class Parser(Grammar):
    def __init__(self, input, actions, types):
        self._input = input
        self._input_size = len(input)
        self._actions = actions
        self._types = types
        self._offset = 0
        self._cache = defaultdict(dict)
        self._failure = 0
        self._expected = []

    def parse(self):
        tree = self._read_dataset()
        if tree is not FAILURE and self._offset == self._input_size:
            return tree
        if not self._expected:
            self._failure = self._offset
            self._expected.append("<EOF>")
        raise ParseError(format_error(self._input, self._failure, self._expected))


def format_error(input, offset, expected):
    lines, line_no, position = input.split("\n"), 0, 0
    while position <= offset:
        position += len(lines[line_no]) + 1
        line_no += 1
    message, line = (
        "Line " + str(line_no) + ": expected " + ", ".join(expected) + "\n",
        lines[line_no - 1],
    )
    message += line + "\n"
    position -= len(line) + 1
    message += " " * (offset - position)
    return message + "^"


def parse(input, actions=None, types=None):
    parser = Parser(input, actions, types)
    return parser.parse()
