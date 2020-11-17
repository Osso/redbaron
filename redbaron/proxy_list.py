from redbaron.utils import (in_a_shell,
                            truncate)

import baron

from .base_nodes import (Node,
                         NodeList)


class ProxyList(NodeList):
    strict_separator = True
    auto_separator = True
    middle_separator = None
    trailing_separator = False

    def __init__(self, node_list=None, parent=None, on_attribute=None):
        super().__init__(parent=parent, on_attribute=on_attribute)
        self.header = []
        self.footer = []
        self._data = []
        self.separator_type = type(self.middle_separator)
        self.replace_node_list(node_list or [])

    def _node_list_to_data(self):
        from .nodes import LeftParenthesisNode, RightParenthesisNode, SpaceNode

        data = []
        self.header = []
        self.footer = []
        leftover_indent = ""

        def consume_leftover():
            nonlocal leftover_indent
            r = leftover_indent
            leftover_indent = ''
            return r

        for node in self.node_list:
            if isinstance(node, LeftParenthesisNode):
                assert node is self.node_list[0]
                self.header.append(node)
            elif isinstance(node, RightParenthesisNode):
                assert node is self.node_list[-1]
                self.footer.append(node)
            elif isinstance(node, self.separator_type):
                if not data:
                    if self.strict_separator:
                        raise Exception("node_list starts with separator "
                                        "for %s" % self.__class__.__name__)
                    self.append_leftover_indent_to_header(consume_leftover(),
                                                          self.header)
                    self.header.append(node)
                elif data[-1][1] is not None:
                    if self.strict_separator:
                        raise Exception("node_list has two successive separators "
                                        "for %s" % self.__class__.__name__)
                    empty_el = self.make_empty_el(consume_leftover())
                    data.append([empty_el, node])
                else:
                    data[-1][1] = node
            elif isinstance(node, SpaceNode):
                pass
            else:
                if data and data[-1][1] is None and self.strict_separator:
                    raise Exception("node_list is missing separator "
                                    "for %s" % self.__class__.__name__)
                node.indentation += consume_leftover()
                data.append([node, None])

            leftover_indent = node.consume_leftover_indentation()
            self.append_leftover_endl_to_data(node, data)

        self.append_leftover_indent_to_footer(leftover_indent, self.footer)
        self._data = data

    def append_leftover_endl_to_data(self, node, data):
        from .nodes import EndlNode

        if isinstance(self.middle_separator, EndlNode):
            for el in node.consume_leftover_endl():
                el[0].parent = self
                if el[1] is not None:
                    el[1].parent = self
                data.append(el)

    def append_leftover_indent_to_header(self, leftover_indent, header):
        if leftover_indent:
            header.append(self.make_empty_el(leftover_indent))

    def append_leftover_indent_to_footer(self, leftover_indent, footer):
        if leftover_indent:
            footer.append(self.make_empty_el(leftover_indent))

    def _data_to_node_list(self):
        from .nodes import IndentationNode

        expected_list = []

        def _append_el(el):
            if not el:
                return
            if el.indentation:
                expected_list.append(IndentationNode(el, parent=self))
            expected_list.append(el)

        for el in self.header:
            _append_el(el)

        for node, sep in self._data:
            _append_el(node)
            _append_el(sep)

        for el in self.footer:
            _append_el(el)

        self.data = expected_list

    def make_separator(self):
        separator = self.middle_separator.copy()
        separator.parent = self
        return separator

    def make_separator_if_strict(self):
        return self.make_separator() if self.auto_separator else None

    def make_empty_el(self, value=""):
        from .nodes import SpaceNode, EmptyLineNode

        if value:
            el = SpaceNode.make(value, parent=self)
        else:
            el = EmptyLineNode(parent=self)

        return el

    def reformat(self):
        for el in self._data:
            if el[0].on_new_line:
                el[0].indentation = self.el_indentation
            else:
                el[0].indentation = ""

            if not el[1]:
                el[1] = self.make_separator()

        if not self.trailing_separator and self._data:
            self._data[-1][1] = None

    def _synchronise(self):
        if self.auto_separator:
            self.reformat()

        self._data_to_node_list()

    def __len__(self):
        return len(self._data)

    def _insert(self, index, item):
        value = self.el_to_node_with_indentation(item)

        self._check_for_separator(index)
        sep = self.make_separator_if_strict()
        self._data.insert(index, [value, sep])

    def insert(self, i, item):
        self._insert(i, item)
        self._synchronise()

    def put_on_new_line(self, item):
        from .nodes import EndlNode

        i = self.index(item)
        if i == 0:
            if not self[0].on_new_line:
                self.header.append(EndlNode())
            else:
                # sep was just created, we know it doesn't have a new line
                self._data[i][1].second_formatting = ["\n"]
        else:
            if not self[i].on_new_line:
                self._data[i-1][1].second_formatting = ["\n"]
            else:
                self._data[i][1].second_formatting = ["\n"]

    def insert_on_new_line(self, i, item):
        self._insert(i, item)
        self.put_on_new_line(self[i])
        self._synchronise()

    def insert_with_new_line(self, i, item):
        self._insert(i, item)
        self._data[i][1].second_formatting = ["\n"]
        self._synchronise()

    def append(self, item):
        self.insert(len(self), item)

    def append_on_new_line(self, item):
        self.insert_on_new_line(len(self), item)

    def append_with_new_line(self, item):
        self.insert_on_new_line(len(self), item)

    def extend(self, other):
        self[len(self):] = other

    def pop(self, i=-1):
        self._data.pop(i)
        self._synchronise()

    def remove(self, item):
        self.pop(self.index(item))

    def __delitem__(self, index):
        if isinstance(index, slice):
            self.__delslice__(index.start, index.stop)
        else:
            self.pop(index)

    def index(self, item, *args):
        return list(self).index(item, *args)

    def baron_index(self, value):
        return self.node_list.index(value)

    def _el_from_data_tuple(self, el):
        node, _ = el
        return node

    def _sep_from_data_tuple(self, el):
        _, sep = el
        return sep

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.__getslice__(index.start, index.stop)
        return self._el_from_data_tuple(self._data[index])

    def get_from_baron_index(self, index):
        return self.node_list[index]

    def __contains__(self, item):
        try:
            self.index(item)
        except ValueError:
            return False
        return True

    def __iter__(self):
        for el in self._data:
            yield self._el_from_data_tuple(el)

    @property
    def node_list(self):
        return self.data

    def count(self, item):
        return list(self).count(item)

    def __setitem__(self, key, value):
        # Single element, make a one element slice
        if not isinstance(key, slice):
            key = slice(key, key + 1)
            value = [value]

        self._check_for_separator(min(key.start, len(self._data)))

        nodes = [[self.el_to_node_with_indentation(el),
                  self.make_separator_if_strict()]
                 for el in value]
        for (_, sep), node in zip(self._data[key], nodes):
            node[1] = sep
        self._data[key] = nodes

        self._synchronise()

    def _check_for_separator(self, index):
        if not self._data:
            return

        if index and self._data[index-1][1] is None and self.auto_separator:
            self._data[index-1][1] = self.make_separator()

    def __delslice__(self, i, j):
        del self._data[i:j]
        self._synchronise()

    def __getslice__(self, i, j):
        return [el for el, _ in self._data[i:j]]

    def __repr__(self):
        if in_a_shell():
            return self.__str__()

        return "<%s %s, \"%s\" %s, on %s %s>" % (
            self.__class__.__name__,
            self.path().to_baron_path(),
            truncate(self.dumps().replace("\n", "\\n"), 20),
            id(self),
            self.parent.__class__.__name__,
            id(self.parent)
        )

    def __str__(self):
        to_return = ""
        for number, value in enumerate(self._data):
            value = value[0]
            to_return += (("%-3s " % number) + "\n    ".join(value.__repr__().split("\n")))
            to_return += "\n"
        return to_return

    def filter(self, function):
        new_list = type(self)()
        new_list.extend([el.copy() for el in filter(function, self)])
        return new_list

    def replace_data(self, new_data):
        self._data = list(new_data)
        self.set_parent_and_on_attribute(self)
        self._synchronise()

    def replace_node_list(self, new_node_list):
        self.data = list(new_node_list)
        self._node_list_to_data()
        self.detect_trailing_sep()
        self._data_to_node_list()

    def detect_trailing_sep(self):
        if not self._data:
            return
        self.trailing_separator = bool(self._data[-1][1])

    def copy(self):
        new_list = type(self)()
        new_list.replace_data([el.copy() for el in self._data])
        return new_list

    def deep_copy(self):
        new_list = type(self)()
        new_list.replace_data([[node.copy(), sep.copy() if sep else None]
                               for node, sep in self._data])
        return new_list

    def el_to_node(self, el):
        return Node.generic_to_node(el, parent=self)

    def el_to_node_with_indentation(self, el):
        node = self.el_to_node(el)
        node.indentation = self.el_indentation
        return node

    def sort(self, key=None, reverse=False):  # pylint: disable=arguments-differ
        def wrapped_key(el):
            return key(el[0])

        self._data = sorted(self._data, key=wrapped_key, reverse=reverse)
        self._synchronise()

    def clear_data(self):
        self._data.clear()

    def associated_sep(self, item):
        return self._sep_from_data_tuple(self.find_in_data(item))

    def find_in_data(self, item):
        for data_tuple in self._data:
            if self._el_from_data_tuple(data_tuple) is item:
                return data_tuple
        return None

    def has_brackets(self):
        from .nodes import LeftParenthesisNode, RightParenthesisNode
        if self.header and isinstance(self.header[0], LeftParenthesisNode):
            assert isinstance(self.footer[-1], RightParenthesisNode)
            return True
        return False

    def add_brackets(self):
        if self.has_brackets():
            return

        from .nodes import LeftParenthesisNode, RightParenthesisNode
        self.data = [LeftParenthesisNode()] + \
                    self.data + \
                    [RightParenthesisNode()]
        self._node_list_to_data()

    def detect_one_per_line(self):
        for _, sep in self._data:
            if sep and not sep.second_formatting.find("endl"):
                return False
        return True

    def is_multiline(self):
        return bool(self.find("endl"))

    def _find_el_indentation(self):
        if len(self._data) > 1:
            return self._data[1][0].indentation

        return self._data[0][0].indentation

    @property
    def el_indentation(self):
        from .nodes import LeftParenthesisNode

        if self:
            # First element is not inline, we have an indent reference
            if self[0].on_new_line:
                return self._data[0][0].indentation

            # Compute indent from parent + header length
            header_len = 0
            if self.header and isinstance(self.header[-1], LeftParenthesisNode):
                header_len = 1
            return (header_len + self.box.top_left.column - 1) * " "

        # If list is empty, then first element will be inline
        return ""


class SpaceProxyList(ProxyList):
    def __init__(self, node_list=None, parent=None, on_attribute=None):
        from .nodes import SpaceNode
        self.middle_separator = SpaceNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)


class CommaProxyList(ProxyList):
    def __init__(self, node_list=None, parent=None, on_attribute=None):
        from .nodes import CommaNode
        self.middle_separator = CommaNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)


class DotProxyList(ProxyList):
    strict_separator = False
    auto_separator = True

    def __init__(self, node_list=None, parent=None, on_attribute=None):
        from .nodes import DotNode
        self.middle_separator = DotNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)

    def reformat(self):
        from .nodes import CallNode, TupleNode, ListNode

        super().reformat()
        for index, (el, _) in enumerate(self._data):
            if index and isinstance(el, (CallNode, TupleNode, ListNode)):
                self._data[index - 1][1] = None


class LineProxyList(ProxyList):
    strict_separator = False
    auto_separator = False
    trailing_separator = True

    def __init__(self, node_list=None, parent=None, on_attribute=None):
        from .nodes import EndlNode
        self.middle_separator = EndlNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)


class CodeProxyList(LineProxyList):
    def move_indentation_to_leftover(self):
        if not self.footer or not self.parent:
            return

        if self.footer[-1].baron_type == 'space':
            self.leftover_indentation = self.footer.pop().value

        self._synchronise()

    def move_endl_to_leftover(self):
        if not self._data or not self.parent:
            return

        index = len(self.leftover_endl)

        while self._data[-1][0].type in ('empty_line', 'space'):
            self.leftover_endl.insert(index, self._data.pop())

        self._synchronise()

    def consume_leftover_indentation(self):
        self.move_indentation_to_leftover()
        return super().consume_leftover_indentation()

    def consume_leftover_endl(self):
        self.move_endl_to_leftover()
        return super().consume_leftover_endl()

    @property
    def el_indentation(self):
        if not self.parent:
            return ""

        return self.parent.el_indentation

    def _insert(self, index, item):
        from .nodes import EmptyLineNode

        index = min(len(self._data), index)

        nodes = self.el_to_data(item)

        if nodes and index and self._data[index-1][1] is None and \
                isinstance(nodes[0][0], EmptyLineNode) and \
                isinstance(nodes[0][1], self.separator_type):
            self._data[index-1][1] = nodes.pop(0)[1]

        self._data[index:index] = nodes
        self._synchronise()

    def el_to_node(self, el):
        raise Exception("should not be used")

    def el_to_data(self, el):
        if isinstance(el, str):
            el = self.parent._parse_value(el)

        if isinstance(el, (dict, list)):
            code_list = type(self).generic_from_fst(el, parent=self)
            data = [[self.make_empty_el(), endl] for endl in code_list.header]
            data.extend(code_list._data)
            return data

        return [[el, None]]

    def __setitem__(self, key, value):
        # Single element, make a one element slice
        if not isinstance(key, slice):
            key = slice(key, key + 1)
            value = [value]

        nodes = []
        for node_list_to_convert in value:
            nodes += self.el_to_data(node_list_to_convert)

        self._data[key] = nodes
        self._synchronise()


class DictProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("{%s}" % el)[0]['value'][0]
        return Node.generic_from_fst(fst, parent=self)


class ImportsProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("from m import %s" % el)[0]['targets'][0]
        return Node.generic_from_fst(fst, parent=self)


class ArgsProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("a(%s)" % el)[0]['value'][1]['value'][0]
        return Node.generic_from_fst(fst, parent=self)


class DefArgsProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("def a(%s): pass" % el)[0]["arguments"][0]
        return Node.generic_from_fst(fst, parent=self)


class ContextsProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("with %s:\n pass" % el)[0]['contexts'][0]
        return Node.generic_from_fst(fst, parent=self)


class DecoratorsProxyList(LineProxyList):
    auto_separator = True

    def el_to_node(self, el):
        fst = baron.parse("%s\ndef a():\n pass" % el)[0]['decorators'][0]
        return Node.generic_from_fst(fst, parent=self)

    def reformat(self):
        super().reformat()
        # Handle indentation
        if self.parent:
            for el in self:
                el.indentation = self.parent.indentation
            if self:
                self[0].indentation = ""

    def _data_to_node_list(self):
        from . import node

        if self.parent:
            for el in self[1:]:
                el.indentation = self.parent.indentation
            if self.parent.indentation:
                self.footer = [node(self.parent.indentation)]
        super()._data_to_node_list()
