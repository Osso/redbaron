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
        assert not self.node_list
        assert not self.data
        self.extend_node_list(node_list or [])

    def can_be_in_header(self, node):
        return True

    def _node_list_to_data(self):
        from .nodes import (LeftParenthesisNode, RightParenthesisNode,
                            SpaceNode, EndlNode)

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
                        # e.g. , a, starts with separator, invalid code
                        raise Exception("node_list starts with separator "
                                        "for %s" % self.__class__.__name__)
                    elif self.can_be_in_header(node):
                        # e.g. def fun():\n pass body starts with new line
                        self.append_leftover_indent_to_header(consume_leftover(),
                                                              self.header)
                        self.header.append(node)
                    else:
                        # e.g. def fun():\n\n pass body starts with new lines
                        empty_el = self.make_empty_el(consume_leftover())
                        data.append([empty_el, node])
                elif data[-1][1] is None:
                    # e.g. (a, b) normal case
                    data[-1][1] = node
                elif isinstance(data[-1][1], self.separator_type):
                    if self.strict_separator:
                        # e.g. (a,,) 2 separators in a row
                        # Ignore extra separator
                        continue
                    # e.g. def fun():\n\n 2 separators in a row
                    empty_el = self.make_empty_el(consume_leftover())
                    data.append([empty_el, node])
                elif isinstance(data[-1][1], EndlNode):
                    # can only happen if self.separtor_type is not a new line
                    # e.g. (a\n, b) new line before separator
                    endl = data[-1][1]
                    data[-1][1] = node
                    data[-1][1].first_formatting.append(endl)
                    data[-1][1].extend(endl.second_formatting)
                    del endl.second_formatting[:]
                else:
                    raise Exception("unhandled separator location")
            elif isinstance(node, EndlNode):
                # can only happen if self.separtor_type is not a new line
                if not data:
                    self.header.append(node)
                elif data[-1][1] is None:
                    data[-1][1] = node
                else:
                    data[-1][1].second_formatting.append(node)
            elif isinstance(node, SpaceNode):
                # Space is emptied by consume_leftover_indentation()
                pass
            else:
                if (data and data[-1][1] is None  # no separator
                        and self.strict_separator):
                    raise Exception("node_list is missing separator after "
                                    f"{data[-1][0].dumps()!r} "
                                    f"for {self.__class__.__name__}")
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
            if node.hidden:
                continue
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
        from .nodes import EndlNode, CommentNode

        for el in self._data:
            if el[0].on_new_line:
                el[0].indentation = self.el_indentation
            else:
                el[0].indentation = ""

            if not el[1]:
                el[1] = self.make_separator()
            elif isinstance(el[1], EndlNode) and not isinstance(el[0],
                                                                CommentNode):
                el[1] = self.make_separator()
                el[1].second_formatting = ["\n"]

        if self._data:
            if not self.trailing_separator or not self[-1].endl:
                self._data[-1][1] = None

    def _synchronise(self):
        if self.auto_separator:
            self.reformat()

        self._data_to_node_list()

    def __len__(self):
        return len(self._data)

    def _insert(self, index, item):
        value = self.el_to_node_with_indentation(item)

        self._add_separator_if_needed(index)
        sep = self.make_separator_if_strict() if index < len(self) else None
        self._data.insert(index, [value, sep])

    def insert(self, i, item):
        self._insert(i, item)
        self._synchronise()

    def put_on_new_line(self, item, indentation=None):
        from .nodes import EndlNode

        item.indentation = indentation if indentation is not None \
                                                       else self.el_indentation

        if item.on_new_line:
            return

        previous = item.displayable_previous
        if not previous:
            self.header.append(EndlNode())
        else:
            data = self.find_in_data(previous)
            if data[1]:
                data[1].second_formatting = ["\n"]
            else:
                data[1] = EndlNode()

        self._synchronise()

    def put_on_same_line(self, item):
        from .nodes import EndlNode

        if not item.on_new_line:
            return

        i = self.index(item)
        if i == 0:
            assert isinstance(self.header[-1], EndlNode)
            self.header.pop()
        else:
            if self._data[i-1][1]:
                assert isinstance(self._data[i-1][1].second_formatting[-1], EndlNode)
                self._data[i-1][1].second_formatting = " "
            else:
                assert isinstance(self._data[i-1][1], EndlNode)
                self._data[i-1][1] = None

        self._synchronise()

    def insert_on_new_line(self, i, item):
        self._insert(i, item)
        if not self[i].on_new_line:
            self.put_on_new_line(self[i])
            # put_on_new_line() calls self._synchronise()
        else:
            self.add_endl(self[i])
            self._synchronise()

    def insert_with_new_line(self, i, item):
        self._insert(i, item)
        self.add_endl(self[i])

    def add_endl(self, item):
        from .nodes import EndlNode

        i = self.index(item)

        if self._data[i][1]:
            self._data[i][1].second_formatting = ["\n"]
        else:
            self._data[i][1] = EndlNode()

        self._synchronise()

    def append(self, item):
        self.insert(len(self), item)

    def append_on_new_line(self, item):
        self.insert_on_new_line(len(self), item)

    def append_with_new_line(self, item):
        self.insert_with_new_line(len(self), item)

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

        self._add_separator_if_needed(min(key.start, len(self._data)))

        nodes = [[self.el_to_node_with_indentation(el),
                  self.make_separator_if_strict()]
                 for el in value]
        for (_, sep), node in zip(self._data[key], nodes):
            node[1] = sep
        self._data[key] = nodes

        self._synchronise()

    def _add_separator_if_needed(self, index):
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
        for el, sep in new_data:
            el.parent = self
            el.on_attribute = None
            if sep is not None:
                sep.parent = self
                sep.on_attribute = None
        self._data = list(new_data)
        self._synchronise()

    def extend_node_list(self, new_node_list):
        self.set_parent_and_on_attribute(new_node_list)
        self.data += list(new_node_list)
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

    def clear(self):
        self._data.clear()
        self._synchronise()

    def associated_sep(self, item):
        data_tuple = self.find_in_data(item)
        sep = self._sep_from_data_tuple(data_tuple)
        if sep is item:
            raise ValueError("Invalid Item: %r" % item)
        return sep

    def set_associated_sep(self, item, value):
        data_tuple = self.find_in_data(item)
        if item is data_tuple[1]:
            raise ValueError("Invalid Item: %r" % item)
        data_tuple[1] = value
        self._synchronise()

    def find_in_data(self, item):
        for data_tuple in self._data:
            if (self._el_from_data_tuple(data_tuple) is item or
                    self._sep_from_data_tuple(data_tuple) is item):
                return data_tuple

        raise ValueError("Invalid Item: %r" % item)

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
        self.header.insert(0, LeftParenthesisNode())
        self.footer.append(RightParenthesisNode())
        self._synchronise()

    def remove_brackets(self):
        if not self.has_brackets():
            return

        del self.header[0]
        del self.footer[-1]
        self._synchronise()

    def detect_one_per_line(self):
        for _, sep in self._data:
            if sep and not sep.second_formatting.find("endl"):
                return False
        return True

    def is_multiline(self):
        return bool(self.find("endl"))

    @property
    def el_indentation(self):
        from .nodes import LeftParenthesisNode

        if self:
            # First element that is not inline, we have an indent reference
            for el, _ in self._data:
                if el.on_new_line:
                    return el.indentation

            # Compute indent from parent + header length
            header_len = 0
            if self.header and isinstance(self.header[-1], LeftParenthesisNode):
                header_len = 1
            return (header_len + self.box.top_left.column - 1) * " "

        # If list is empty, then first element will be inline
        return ""

    def hide(self, item):
        super().hide(item)
        self._synchronise()

    def move_after(self, el, to):
        """Keeps new lines"""
        old_index = self.index(el)
        new_index = self.index(to)
        self._data.insert(new_index+1, self._data[old_index])
        del self._data[old_index]
        self._synchronise()


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
    def can_be_in_header(self, node):
        if self.header:
            return False
        return isinstance(node, self.separator_type)

    def consume_leftover_indentation(self):
        if not self.footer:
            return ""

        if self.footer[-1].baron_type == 'space':
            leftover = self.footer.pop().value
            self._synchronise()
            return leftover

        return ""

    def consume_leftover_endl(self):
        if not self._data:
            return []

        leftover_endl = []
        while self._data[-1][0].type in ('empty_line', 'space'):
            leftover_endl.append(self._data.pop())

        self._synchronise()

        return reversed(leftover_endl)

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
        from .nodes import EmptyLineNode
        if isinstance(el, str):
            el = self.parent._parse_value(el)

        if isinstance(el, (dict, list)):
            code_list = type(self).generic_from_fst(el, parent=self)
            data = [[self.make_empty_el(), endl] for endl in code_list.header]
            data.extend(code_list._data)
            return data

        el.parent = self

        if isinstance(el, self.separator_type):
            return [[EmptyLineNode(parent=self), el]]

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

    def hide(self, item):
        from .nodes import CommentNode
        from .node_mixin import CodeBlockMixin

        super().hide(item)

        # Handle inline comments
        if item.previous and not item.previous.associated_sep:
            if isinstance(item, CommentNode):
                item.previous.associated_sep = item.associated_sep
            else:
                isinstance(item.previous, CodeBlockMixin)

    def make_code_block(self, start, length):
        try:
            start_index = self.index(start)
        except ValueError as e:
            raise ValueError("Invalid start %r" % start) from e
        code_block = self.deep_copy()
        code_block._data[:] = code_block._data[start_index:start_index+length]
        code_block._synchronise()
        return code_block


class DictProxyList(CommaProxyList):
    def el_to_node(self, el):
        from .base_nodes import BaseNode

        if isinstance(el, BaseNode):
            return Node.generic_to_node(el, parent=self)

        fst = baron.parse("{%s}" % el)[0]['value'][0]
        return Node.generic_from_fst(fst, parent=self)

    def _node_list_to_data(self):
        from .nodes import DictitemNode, EndlNode

        super()._node_list_to_data()

        # Workaround parser bug indentation in second formatting
        if self and self.parent.second_formatting:
            self[0].indentation += self.parent.second_formatting[-1].indent
            self.parent.second_formatting[-1].indent = ""

        # Workaround parser bug putting new lines in dict values
        for item in self._data:
            assert isinstance(item[0], DictitemNode)
            endl = item[0].value.endl
            if isinstance(endl, EndlNode):
                item[0].value.remove_endl()
                if item[1]:
                    item[1].second_formatting.append(endl)
                else:
                    item[1] = endl


class ImportsProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("from m import %s" % el)[0]['targets'][0]
        return Node.generic_from_fst(fst, parent=self)

    @property
    def el_indentation(self):
        from .nodes import LeftParenthesisNode

        if self:
            # Compute indent from parent + header length
            header_len = 0
            if self.header and isinstance(self.header[-1], LeftParenthesisNode):
                header_len = 1
            return (header_len + self.box.top_left.column - 1) * " "

        # If list is empty, then first element will be inline
        return ""


class ArgsProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("a(%s)" % el)[0]['value'][1]['value'][0]
        return Node.generic_from_fst(fst, parent=self)

    def _node_list_to_data(self):
        if self.parent and self.parent.second_formatting:
            self.data = list(self.parent.second_formatting) + self.data
            self.parent.second_formatting.clear()
        super()._node_list_to_data()


class DefArgsProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("def a(%s): pass" % el)[0]["arguments"][0]
        return Node.generic_from_fst(fst, parent=self)

    def _node_list_to_data(self):
        if self.parent and self.parent.third_formatting:
            self.data = list(self.parent.third_formatting) + self.data
            self.parent.third_formatting.clear()
        super()._node_list_to_data()


class ContextsProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("with %s:\n pass" % el)[0]['contexts'][0]
        return Node.generic_from_fst(fst, parent=self)


class DecoratorsProxyList(LineProxyList):
    auto_separator = True

    def el_to_node(self, el):
        # We add @pre decorator in case el is a comment
        fst = baron.parse("@pre\n%s\ndef a():\n pass" % el)[0]['decorators'][2]
        return Node.generic_from_fst(fst, parent=self)

    def _data_to_node_list(self):
        # Remove indentation as it is always handled by the def node
        for el, _ in self._data:
            el.indentation = ""
        self.footer.clear()

        super()._data_to_node_list()
