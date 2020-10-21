from redbaron.utils import (in_a_shell,
                            truncate)

from .base_nodes import (Node,
                         NodeList)


class ProxyList(NodeList):
    needs_separator = True
    middle_separator = None

    def __init__(self, node_list, parent=None, on_attribute="value",
                 trailing_separator=False):
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)
        self.header = []
        self.trailing_separator = trailing_separator
        self._data = self._node_list_to_data(node_list)
        assert isinstance(self._data, list)

    def _node_list_to_data(self, node_list):
        data = []
        leftover_indent = ""
        separator_type = type(self.middle_separator)

        def consume_leftover():
            nonlocal leftover_indent
            r = leftover_indent
            leftover_indent = ''
            return r

        for node in node_list:
            if isinstance(node, separator_type):
                if not data:
                    empty_el = self.make_empty_el()
                    if empty_el:
                        self.header.append(node)
                        continue
                    else:
                        raise Exception("node_list starts with separator "
                                        "for %s" % self.__class__.__name__)
                elif data[-1][1] is not None:
                    empty_el = self.make_empty_el()
                    if empty_el:
                        data.append([empty_el, node])
                    else:
                        raise Exception("node_list has two successive separators "
                                        "for %s" % self.__class__.__name__)
                else:
                    data[-1][1] = node
                assert isinstance(node.indentation, str)
                if node.second_formatting:
                    leftover_indent = node.second_formatting[0].indent
                    node.second_formatting[0].indent = ""

            else:
                if data and data[-1][1] is None and self.needs_separator:
                    raise Exception("node_list is missing separator "
                                    "for %s" % self.__class__.__name__)
                node.indentation += consume_leftover()
                data.append([node, None])

        return data

    def _data_to_node_list(self, data):
        from .nodes import SpaceNode
        expected_list = []

        for el in self.header:
            expected_list.append(el)

        for node, sep in data:
            if node.indentation:
                expected_list.append(SpaceNode.make(node.indentation,
                                                    parent=self))
            expected_list.append(node)
            if sep is not None:
                expected_list.append(sep)

        return expected_list

    def make_separator(self):
        separator = self.middle_separator.copy()
        separator.parent = self
        separator.on_attribute = self.on_attribute
        return separator

    def make_empty_el(self, value=""):
        return None

    def _synchronise(self):
        if not self.trailing_separator and self._data:
            self._data[-1][1] = None
        self.data = self._data_to_node_list(self._data)

    def __len__(self):
        return len(self._data)

    def _insert(self, index, item):
        value = Node.generic_from_str(item, parent=self)
        self._check_for_separator(index)
        self._data.insert(index, [value, self.make_separator()])

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

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            self.__setslice__(index.start, index.stop, value)
        else:
            self._data[index][0] = self.parent.from_str(value)
        self._synchronise()

    def __setslice__(self, i, j, value):
        _nodes = self.from_str(value)
        self._check_for_separator(i)
        self._data[i:j] = ([node, self.make_separator()] for node in _nodes)
        self._synchronise()

    def _check_for_separator(self, index):
        if index > 0 and self._data[index-1][1] is None:
            self._data[index-1][1] = self.make_separator()

    def __delslice__(self, i, j):
        del self._data[i:j]
        self._synchronise()

    def __getslice__(self, i, j):
        to_return = [self._item_from_data_tuple(el) for el in self._data[i:j]]
        return self.__class__(to_return)

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
        new_list = self.copy()
        new_list.replace_data([node for node, sep in self._data
                               if function(node)])

    def replace_data(self, new_data):
        self._data = new_data
        self._synchronise()


class SpaceProxyList(ProxyList):
    def __init__(self, node_list, parent=None, on_attribute="value"):
        from .nodes import SpaceNode
        self.middle_separator = SpaceNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)


class CommaProxyList(ProxyList):
    def __init__(self, node_list, parent=None, on_attribute="value"):
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
    needs_separator = False

    def __init__(self, node_list, parent=None, on_attribute="value"):
        from .nodes import DotNode
        self.middle_separator = DotNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)


class LineProxyList(ProxyList):
    needs_separator = False

    def __init__(self, node_list, parent=None, on_attribute="value"):
        from .nodes import EndlNode
        self.middle_separator = EndlNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute,
                         trailing_separator=True)

    def make_empty_el(self, value=""):
        from .nodes import SpaceNode
        return SpaceNode.make(value, parent=self)


class CodeProxyList(LineProxyList):
    def __init__(self, node_list, parent=None, on_attribute="value",
                 trailing_separator=False):
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)
        self._synchronise()

    def _node_list_to_data(self, node_list):
        from .nodes import SpaceNode, EmptyLineNode

        def _make_empty_el_and_consume_leftover():
            if leftover_indent:
                empty_line = SpaceNode.make(consume_leftover(), parent=self)
            else:
                empty_line = EmptyLineNode(parent=self)

            return empty_line

        def consume_leftover():
            nonlocal leftover_indent
            r = leftover_indent
            leftover_indent = ''
            return r

        data = []
        leftover_indent = ''
        for node in node_list:
            if node.type == "endl":
                if not data:
                    if leftover_indent:
                        self.header.append(_make_empty_el_and_consume_leftover())
                    self.header.append(node)
                else:
                    if data[-1][1] is not None:
                        empty_line = _make_empty_el_and_consume_leftover()
                        data.append([empty_line, node])
                    else:
                        data[-1][1] = node
                leftover_indent = node.indent
                node.indent = ''
            else:
                node.indentation += consume_leftover()
                data.append([node, None])
                leftover_indent = node.consume_leftover_indentation()
                for el in node.consume_leftover_endl():
                    el[0].parent = self
                    if el[1] is not None:
                        el[1].parent = self
                    data.append(el)

        if leftover_indent:
            data.append([SpaceNode.make(leftover_indent, parent=self), None])

        return data

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
