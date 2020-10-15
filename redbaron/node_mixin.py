import ast

import baron
import baron.path

from .utils import display_property_atttributeerror_exceptions


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


class GenericNodesMixin:
    """
    Mixen top class for Node and NodeList that contains generic methods that are used by both.
    """
    @property
    @display_property_atttributeerror_exceptions
    def bounding_box(self):
        return baron.path.node_to_bounding_box(self.fst())

    @property
    @display_property_atttributeerror_exceptions
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
    @display_property_atttributeerror_exceptions
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
