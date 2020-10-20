from redbaron.utils import (in_a_shell,
                            truncate)

from .base_nodes import NodeList


class ProxyList(NodeList):
    needs_separator = True
    middle_separator = None

    def __init__(self, node_list, parent=None, on_attribute="value",
                 trailing_separator=False):
        self.header = []
        self.trailing_separator = trailing_separator
        self._data = self._node_list_to_data(node_list)
        assert isinstance(self._data, list)

        super().__init__(node_list, parent=parent, on_attribute=on_attribute)

    def nodelist_from_str(self, value):
        return self.parent.nodelist_from_str(value, self.on_attribute)

    def _node_list_to_data(self, node_list):
        data = []
        separator_type = type(self.middle_separator)

        for i in node_list:
            if isinstance(i, separator_type):
                if not data:
                    empty_el = self.make_empty_el()
                    if empty_el:
                        self.header.append(i)
                        continue
                    raise Exception("node_list starts with separator "
                                    "for %s" % self.__class__.__name__)
                if data[-1][1] is not None:
                    empty_el = self.make_empty_el()
                    if empty_el:
                        data.append([empty_el, i])
                        continue
                    raise Exception("node_list has two successive separators "
                                    "for %s" % self.__class__.__name__)
                data[-1][1] = i
            else:
                if data and data[-1][1] is None and self.needs_separator:
                    raise Exception("node_list is missing separator "
                                    "for %s" % self.__class__.__name__)
                data.append([i, None])

        return data

    def _data_nodelist_from_str(self, data):
        expected_list = []

        for el in self.header:
            expected_list.append(el)

        for el in data:
            expected_list.append(el[0])
            if el[1] is not None:
                expected_list.append(el[1])

        return expected_list

    def make_separator(self):
        separator = self.middle_separator.copy()
        separator.parent = self
        separator.on_attribute = self.on_attribute
        return separator

    def make_empty_el(self):
        return None

    def _synchronise(self):
        if not self.trailing_separator:
            self._data[-1][1] = None
        self._data = self._data_nodelist_from_str(self._data)

    def __len__(self):
        return len(self._data)

    def _insert(self, index, item):
        value = self.from_str_el(item)
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
        _nodes = self.nodelist_from_str(value)
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

    def nodelist_from_str(self, value):
        if value.startswith(("(", "[")):
            value = "a%s" % value
        else:
            value = "a.%s" % value

        node_list = self.parent.nodelist_from_str(
            value, on_attribute=self.on_attribute)
        return node_list.filtered()


class LineProxyList(ProxyList):
    needs_separator = False

    def __init__(self, node_list, parent=None, on_attribute="value"):
        from .nodes import EndlNode
        self.middle_separator = EndlNode()
        super().__init__(node_list, parent=parent, on_attribute=on_attribute)

    def make_empty_el(self):
        from .nodes import EmptyLine
        return EmptyLine()

    # def get_absolute_bounding_box_of_attribute(self, index):
    #     if index >= len(self._data) or index < 0:
    #         raise IndexError()
    #     index = self[index].index_on_parent_raw
    #     path = self.path().to_baron_path() + [index]
    #     return baron.path.path_to_bounding_box(self.root.fst(), path)


class CodeProxyList(LineProxyList):
    def _node_list_to_data(self, node_list):
        from .nodes import EmptyLine

        data = []
        leftover_indent = ''
        for node in node_list:
            if node.type == "endl":
                leftover_indent = node.indent
                node.indent = ''
                if not data:
                    self.header.append(node)
                elif data[-1][1] is not None:
                    data.append([EmptyLine(parent=self), node])
                else:
                    data[-1][1] = node
            else:
                data.append([node, None])

        return data

    def _item_from_data_tuple(self, el):
        return el[0]
