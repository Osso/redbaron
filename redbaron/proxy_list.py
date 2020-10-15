from redbaron.utils import (in_a_shell,
                            truncate)


class ProxyList:
    needs_separator = True

    def __init__(self, node_list, on_attribute="value",
                 trailing_separator=False):
        self.node_list = node_list
        self.heading_formatting = []
        self.on_attribute = on_attribute
        self.trailing_separator = trailing_separator
        self.data = self._node_list_to_data(node_list)
        assert isinstance(self.data, list)

    @classmethod
    def from_str(cls, value, parent, on_attribute=None):
        from .base_nodes import NodeList
        node_list = NodeList.from_str(value, parent=parent,
                                      on_attribute=on_attribute)
        return cls(node_list, on_attribute=on_attribute)

    def nodelist_from_str(self, value):
        parent = self.node_list.parent
        return parent.nodelist_from_str(value, self.on_attribute)

    def _node_list_to_data(self, node_list):
        data = []
        separator_type = type(self.middle_separator)

        for i in node_list:
            if isinstance(i, separator_type):
                if not data:
                    empty_el = self.make_empty_el()
                    if empty_el:
                        data.append([empty_el, i])
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
        expected_list = self.heading_formatting.copy()

        for el in data:
            expected_list.append(el[0])
            if el[1]:
                expected_list.append(el[1])

        return expected_list

    def make_separator(self):
        separator = self.middle_separator.copy()
        separator.parent = self.node_list
        separator.on_attribute = self.on_attribute
        return separator

    def make_empty_el(self):
        return None

    def _synchronise(self):
        if not self.trailing_separator:
            self.data[-1][1] = None
        self.node_list.data = self._data_nodelist_from_str(self.data)

    def __len__(self):
        return len(self.data)

    def insert(self, index, value, synchronise=True):
        value = self.parent.from_str(value)
        self._check_for_separator(index)
        self.data.insert(index, [value, self.make_separator()])
        if synchronise:
            self._synchronise()

    def append(self, value, synchronise=True):
        self.insert(len(self), value, synchronise)

    def extend(self, values):
        for value in values:
            self.append(value, synchronise=False)
        self._synchronise()

    def pop(self, index=None):
        if index is not None:
            self.data.pop(index)
        else:
            self.data.pop()
        self._synchronise()

    def remove(self, value):
        self.pop(self.index(value))

    def __delitem__(self, index):
        if isinstance(index, slice):
            self.__delslice__(index.start, index.stop)
        else:
            self.pop(index)

    def index(self, value):
        for position, el in enumerate(self.data):
            if el[0] is value:
                return position
        return None

    def baron_index(self, value):
        return self.node_list.index(value)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.__getslice__(index.start, index.stop)
        return self.data[index][0]

    def get_from_baron_index(self, index):
        return self.node_list[index]

    def __contains__(self, item):
        return self.index(item) is not None

    def __iter__(self):
        for el in self.data:
            yield el[0]

    def count(self, value):
        return [x[0] for x in self.data].count(value)

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            self.__setslice__(index.start, index.stop, value)
        else:
            self.data[index][0] = self.parent.from_str(value)
        self._synchronise()

    def __setslice__(self, i, j, value):
        _nodes = self.nodelist_from_str(value)
        self._check_for_separator(i)
        self.data[i:j] = ([node, self.make_separator()] for node in _nodes)
        self._synchronise()

    def _check_for_separator(self, index):
        if index > 0 and self.data[index-1][1] is None:
            self.data[index-1][1] = self.make_separator()

    def __delslice__(self, i, j):
        del self.data[i:j]
        self._synchronise()

    def __getslice__(self, i, j):
        from .base_nodes import NodeList
        to_return = map(lambda x: x[0], self.data[i:j])
        return self.__class__(NodeList(to_return))

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

    def _bytes_repr_html_(self):
        def __repr_html(self):
            # string addition is slow (and makes copies)
            yield b"<table>"
            yield b"<tr><th>Index</th><th>node</th></tr>"
            for num, item in enumerate(self):
                yield b"<tr>"
                yield b"<td>"
                yield str(num).encode("Utf-8")
                yield b"</td>"
                yield b"<td>"
                yield item._bytes_repr_html_()
                yield b"</td>"
                yield b"</tr>"
            yield b"</table>"

        return b''.join(__repr_html(self))

    def _repr_html_(self):
        return self._bytes_repr_html_().decode("Utf-8")

    def __str__(self):
        to_return = ""
        for number, value in enumerate(self.data):
            value = value[0]
            to_return += (("%-3s " % number) + "\n    ".join(value.__repr__().split("\n")))
            to_return += "\n"
        return to_return

    def __getattr__(self, key):
        return getattr(self.node_list, key)

    def _get_separator_indentation(self):
        if self.data:
            return self.data[0].indentation
        return self.parent.indentation + "    "

    @property
    def parent(self):
        return self.node_list.parent


class SpaceProxyList(ProxyList):
    def __init__(self, node_list, on_attribute="value"):
        from .nodes import SpaceNode
        self.middle_separator = SpaceNode()
        super().__init__(node_list, on_attribute=on_attribute)


class CommaProxyList(ProxyList):
    def __init__(self, node_list, on_attribute="value"):
        from .nodes import CommaNode
        self.style = "flat"
        self.middle_separator = CommaNode()
        super().__init__(node_list, on_attribute=on_attribute)

    def make_indented(self):
        from .base_nodes import NodeList
        self.style = "indented"
        self.middle_separator.second_formatting = NodeList([{
            "type": "endl",
            "indent": self._get_separator_indentation(),
            "formatting": [],
            "value": "\n"}])


class DotProxyList(ProxyList):
    needs_separator = False

    def __init__(self, node_list, on_attribute="value"):
        from .nodes import DotNode
        self.middle_separator = DotNode()
        super().__init__(node_list, on_attribute=on_attribute)

    def nodelist_from_str(self, value):
        if value.startswith(("(", "[")):
            value = "a%s" % value
        else:
            value = "a.%s" % value

        node_list = self.node_list.parent.nodelist_from_str(
            value, on_attribute=self.on_attribute)
        return node_list.filtered()


class LineProxyList(ProxyList):
    needs_separator = False

    def __init__(self, node_list, on_attribute="value"):
        from .nodes import EndlNode
        self.middle_separator = EndlNode()
        super().__init__(node_list, on_attribute=on_attribute)

    def make_empty_el(self):
        from .nodes import EmptyLine
        return EmptyLine()

    # def get_absolute_bounding_box_of_attribute(self, index):
    #     if index >= len(self.data) or index < 0:
    #         raise IndexError()
    #     index = self[index].index_on_parent_raw
    #     path = self.path().to_baron_path() + [index]
    #     return baron.path.path_to_bounding_box(self.root.fst(), path)


class CodeProxyList(LineProxyList):
    def _node_list_to_data(self, node_list):
        from .nodes import EmptyLine
        from .base_nodes import NodeList

        def current_line_to_el(current_line):
            if not current_line:
                el = EmptyLine()
            elif len(current_line) == 1:
                el = current_line[0]
            else:
                el = NodeList(current_line)
            return el

        data = []
        current_line = []
        for node in node_list:
            if node.type == "endl":
                data.append([current_line_to_el(current_line), [node]])
            else:
                current_line.append(node)
        if current_line:
            data.append([current_line_to_el(current_line), []])

        return data
