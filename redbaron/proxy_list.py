from redbaron.utils import (in_a_shell,
                            truncate)

import baron

from .base_nodes import (Node,
                         NodeList)


class ProxyList(NodeList):
    strict_separator = True
    auto_separator = True
    middle_separator = None

    def __init__(self, node_list=None, parent=None, on_attribute=None,
                 trailing_separator=False):
        super().__init__(parent=parent, on_attribute=on_attribute)
        self.header = []
        self.footer = []
        self._data = []
        self.trailing_separator = trailing_separator
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

        self.append_leftover_indent_to_data(leftover_indent, data)
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

    def append_leftover_indent_to_data(self, leftover_indent, data):
        if leftover_indent:
            data.append([self.make_empty_el(leftover_indent), None])

    def _data_to_node_list(self):
        expected_list = []

        def _append_el(el):
            if not el:
                return
            if el.indentation:
                expected_list.append(self.make_empty_el(el.indentation))
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

    def _synchronise(self):
        if not self.trailing_separator and self._data:
            self._data[-1][1] = None
        self._data_to_node_list()

    def __len__(self):
        return len(self._data)

    def _insert(self, index, item):
        value = self.el_to_node(item)
        self._check_for_separator(index)
        sep = self.make_separator_if_strict()
        self._data.insert(index, [value, sep])

    def insert(self, i, item):
        self._insert(i, item)
        self._synchronise()

    def append(self, item):
        self.insert(len(self), item)

    def extend(self, other):
        for value in other:
            self._insert(len(self), value)
        self._synchronise()

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

    def _item_from_data_tuple(self, el):
        node, _ = el
        return node

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.__getslice__(index.start, index.stop)
        return self._item_from_data_tuple(self._data[index])

    def get_from_baron_index(self, index):
        return self.node_list[index]

    def __contains__(self, item):
        return self.index(item) is not None

    def __iter__(self):
        for el in self._data:
            yield self._item_from_data_tuple(el)

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

        nodes = ([self.el_to_node(el), self.make_separator_if_strict()]
                 for el in value)
        self._data[key] = nodes

        # delta = key.start - len(self._data)
        # if delta > 0:
        #     key = slice(key.start - delta, key.stop - delta, key.step)

        # values_iter = iter(value)
        # index = key.start
        # # First replace values in slice
        # for index, el in zip(range(key.stop)[key], values_iter):
        #     self._data[index][0] = self.el_to_node(el)
        # # Second, append the remaining values
        # for el in values_iter:
        #     index += 1
        #     self._insert(index, el)
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
        new_list = type(self)()
        new_list.replace_data(self._data[i:j])
        return new_list

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

    def _get_separator_indentation(self):
        if self._data:
            return self._data[0].indentation
        return self.parent.indentation + "    "

    def filter(self, function):
        new_list = type(self)()
        new_list.extend([node.copy() for node in filter(function, self)])
        return new_list

    def replace_data(self, new_data):
        self._data = list(new_data)
        self.set_parent_and_on_attribute(self)
        self._synchronise()

    def replace_node_list(self, new_node_list):
        self.data = list(new_node_list)
        self._node_list_to_data()
        self._synchronise()

    def copy(self):
        new_list = type(self)()
        new_list.replace_data(self)
        return new_list

    def deep_copy(self):
        new_list = type(self)()
        new_list.replace_data([node.copy() for node in self])
        return new_list

    def el_to_node(self, el):
        return Node.generic_to_node(el, parent=self)


class SpaceProxyList(ProxyList):
    def __init__(self, node_list=None, parent=None, on_attribute=None):
        from .nodes import SpaceNode
        self.middle_separator = SpaceNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)


class CommaProxyList(ProxyList):
    def __init__(self, node_list=None, parent=None, on_attribute=None):
        from .nodes import CommaNode
        self.style = "flat"
        self.middle_separator = CommaNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)

    def make_indented(self):
        self.style = "indented"
        self.middle_separator.second_formatting = NodeList([{
            "type": "endl",
            "indent": self._get_separator_indentation(),
            "formatting": [],
            "value": "\n"}])


class DotProxyList(ProxyList):
    strict_separator = False
    auto_separator = True

    def __init__(self, node_list=None, parent=None, on_attribute=None):
        from .nodes import DotNode
        self.middle_separator = DotNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)

    def _synchronise(self):
        from .nodes import CallNode, TupleNode, ListNode

        for index, (el, _) in enumerate(self._data):
            if index and isinstance(el, (CallNode, TupleNode, ListNode)):
                self._data[index - 1][1] = None

        super()._synchronise()


class LineProxyList(ProxyList):
    strict_separator = False
    auto_separator = False

    def __init__(self, node_list=None, parent=None, on_attribute=None):
        from .nodes import EndlNode
        self.middle_separator = EndlNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute,
                         trailing_separator=True)


class CodeProxyList(LineProxyList):
    def __init__(self, node_list=None, parent=None, on_attribute=None,
                 trailing_separator=False):
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)
        self._synchronise()

    def move_indentation_to_leftover(self):
        if not self._data or not self.parent:
            return

        if self._data[-1][0].type == 'space' and self._data[-1][1] is None:
            self.leftover_indentation = self._data.pop()[0].value

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
        if isinstance(item, str):
            code_list = self.to_node(item)
            for endl in code_list.header:
                self._data.insert(index, [self.make_empty_el(), endl])
                index += 1
            for el in code_list._data:
                self._data.insert(index, el)
                index += 1
        elif isinstance(item, self.separator_type):
            self._data.insert(index, [self.make_empty_el(), item])
        else:
            self._data.insert(index, [item, None])


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


class ContextsProxyList(CommaProxyList):
    def el_to_node(self, el):
        fst = baron.parse("with %s:\n pass" % el)[0]['contexts'][0]
        return Node.generic_from_fst(fst, parent=self)
