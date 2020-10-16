import ast

import baron
import baron.path

from .node_path import Path


class LiteralyEvaluableMixin:
    def to_python(self):
        try:
            return ast.literal_eval(self.dumps().strip())
        except ValueError as e:
            message = "to_python method only works on numbers, strings, " \
                      "list, tuple, dict, boolean and None. " \
                      "(using ast.literal_eval). The piece of code that you " \
                      "are trying to convert contains an illegale value, for" \
                      " example, a variable."
            e.message = message
            e.args = (message,)
            raise e


class NodeMixin:
    """
    Mixen top class for Node and NodeList that contains generic methods that are used by both.
    """
    @property
    def bounding_box(self):
        return baron.path.node_to_bounding_box(self.fst())

    @property
    def absolute_bounding_box(self):
        path = self.path().to_baron_path()
        return baron.path.path_to_bounding_box(self.root.fst(), path)

    def find_by_position(self, position):
        path = baron.path.position_to_path(self.fst(), position)
        return self.find_by_path(path)

    def at(self, line_no):
        if not 0 <= line_no <= self.absolute_bounding_box.bottom_right.line:
            raise IndexError(f"Line number {line_no} is outside of the file")

        node = self.find_by_position((line_no, 1))
        if not node:
            return None

        if node.absolute_bounding_box.top_left.line > line_no:
            for n in self._iter_in_rendering_order():
                if n.absolute_bounding_box.top_left.line == line_no:
                    return n
            return node

        # assumed node.absolute_bounding_box.top_left.line == line_no
        while node.parent and node.parent.absolute_bounding_box.top_left.line == line_no:
            # Don't break out of the self box
            if node.parent is self:
                break
            node = node.parent

        return node

    @property
    def root(self):
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def _iter_in_rendering_order(self):
        for kind, key, display in self._render():
            if display is not True:
                continue

            if kind == "constant":
                yield self
            elif kind == "string":
                if getattr(self, key) is not None:
                    yield self
            elif kind == "key":
                node = getattr(self, key)
                if node:
                    yield from node._iter_in_rendering_order()
            elif kind in ("list", "formatting"):
                for node in getattr(self, key):
                    yield from node._iter_in_rendering_order()

    @property
    def on_attribute_node(self):
        if self.on_attribute == "root":
            return self

        return getattr(self.parent, self.on_attribute)

    @on_attribute_node.setter
    def set_on_attribute_node(self, node):
        setattr(self.parent, self.on_attribute, node)

    def find_by_path(self, path):
        return Path.from_baron_path(self, path).node

    def path(self):
        return Path(self)

    def dumps(self):
        return baron.dumps(self.fst())

    def find_all(self, identifier, *args, **kwargs):
        return list(self.find_iter(identifier, *args, **kwargs))

    def find(self, identifier, *args, **kwargs):
        return next(self.find_iter(identifier, *args, **kwargs), None)

    def replace(self, new_node):
        new_node = self.from_str(new_node, on_attribute=self.on_attribute)
        if self is self.on_attribute_node:
            self.on_attribute_node = new_node
        else:
            index = self.on_attribute_node.index(self)
            self.on_attribute_node[index] = new_node

    @property
    def index_on_parent(self):
        if not self.parent:
            raise ValueError("no parent")

        return self.parent.index(self)

    @property
    def baron_index_on_parent(self):
        if not self.parent:
            raise ValueError("no parent")

        try:
            node_list = self.parent.node_list
        except AttributeError:
            raise ValueError("parent has no node list")

        return node_list.index(self)


class DecoratorsMixin:
    _decorators = None

    @property
    def decorators(self):
        return self._decorators

    @decorators.setter
    def decorators(self, value):
        from .proxy_list import LineProxyList
        if not isinstance(value, LineProxyList):
            if isinstance(value, str):
                value = self.parse_decorators(value)
            value = self.nodelist_from_fst(value, on_attribute="decorators")

        self._decorators = value


class ValueNodeMixin:
    _value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        from .base_nodes import Node
        if not isinstance(value, Node):
            if isinstance(value, str):
                value = baron.parse(value)
            value = self.from_fst(value, on_attribute="value")

        self._value = value


class ValueListMixin:
    _value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        from .base_nodes import Node
        if not isinstance(value, Node):
            if isinstance(value, str):
                value = baron.parse(value)
            value = self.nodelist_from_fst(value, on_attribute="value")

        self._value = value
