import ast

import baron
import baron.path

from .base_nodes import (BaseNode,
                         NodeList)
from .node_property import (NodeListProperty,
                            NodeProperty,
                            conditional_formatting_property,
                            nodelist_property)
from .proxy_list import (CodeProxyList,
                         DecoratorsProxyList)
from .utils import indent_str


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


class DecoratorsMixin:
    @nodelist_property(DecoratorsProxyList)
    def decorators(self, value):
        assert value.lstrip()[0] == '@'

        def _detect_indentation(s):
            return s.index("@")
        indentation = _detect_indentation(value)

        code = "%s\n%sdef a(): pass" % (value, indentation)
        return baron.parse(code)[0]["decorators"]


class AnnotationMixin:
    @NodeProperty
    def annotation(self, value):
        return baron.parse("a: %s = a" % value)[0]["annotation"]

    @conditional_formatting_property(NodeList, [" "], [])
    def annotation_first_formatting(self):
        return self.annotation

    @conditional_formatting_property(NodeList, [" "], [])
    def annotation_second_formatting(self):
        return self.annotation


class ReturnAnnotationMixin:
    @NodeProperty
    def return_annotation(self, value):
        if not value:
            return None

        code = "def a() -> %s: pass" % value
        return baron.parse(code)[0]["return_annotation"]

    @conditional_formatting_property(NodeList, [" "], [])
    def return_annotation_first_formatting(self):
        return self.return_annotation

    @conditional_formatting_property(NodeList, [" "], [])
    def return_annotation_second_formatting(self):
        return self.return_annotation


class ValueIterableMixin:
    def __len__(self):
        return len(self.value)

    def __getitem__(self, index):
        return self.value[index]

    def __getslice__(self, i, j):
        return self.value.__getslice__(i, j)

    def __setitem__(self, key, value):
        self.value[key] = value

    def __setslice__(self, i, j, value):
        return self.value.__setslice__(i, j, value)

    def __delitem__(self, key):
        del self.value[key]

    def __delslice__(self, i, j):
        self.value.__delslice__(i, j)

    def index(self, item):
        return self.value.index(item)

    def insert(self, i, item):
        self.value.insert(i, item)

    def append(self, item):
        self.value.append(item)

    def extend(self, other):
        self.value.extend(other)

    def pop(self, index=-1):
        return self.value.pop(index)

    def remove(self, item):
        return self.value.remove(item)

    def count(self, item):
        return self.value.count(item)


class CodeBlockMixin(ValueIterableMixin):
    default_indent = ""

    @nodelist_property(CodeProxyList)
    def value(self, value):
        return self._parse_value(value, replace=True)

    def _parse_value(self, value, replace=False):
        if self.el_indentation or value.startswith(" "):
            fst = self._parse_indented(value)
        else:
            fst = self._parse_not_indented(value)
        return fst

    def _parse_indented(self, value):
        value = indent_str(value, self.el_indentation)
        # First line is on the same line with def/class element
        # we do not want to the el_indentation there
        # e.g def f(): {value}
        if value.startswith(" ") and value.lstrip(" ").startswith("\n"):
            value = value[len(self.el_indentation):]
        fst = baron.parse("while a:\n%s" % value)[0]['value']
        fst[0] = {"type": "space", "value": fst[0]['indent']}
        return fst

    def _parse_not_indented(self, value):
        return baron.parse(value)

    @property
    def leftover_indentation(self):
        return self.value.leftover_indentation

    @leftover_indentation.setter
    def leftover_indentation(self, value):
        self.value._leftover_indentation = value

    @property
    def leftover_endl(self):
        return self.value.leftover_endl

    @leftover_endl.setter
    def leftover_endl(self, value):
        self.value._leftover_endl = value

    def consume_leftover_indentation(self):
        return super().consume_leftover_indentation() + \
               self.value.consume_leftover_indentation()

    def consume_leftover_endl(self):
        yield from super().consume_leftover_endl()
        yield from self.value.consume_leftover_endl()

    def increase_indentation(self, indent):
        super().increase_indentation(indent)
        self.value.increase_indentation(indent)

    def decrease_indentation(self, indent):
        super().decrease_indentation(indent)
        self.value.decrease_indentation(indent)

    def _find_first_el_indentation(self):
        return self.value[0].indentation

    @property
    def el_indentation(self):
        if not self.value:
            return self.indentation + self.default_indent

        return self._find_first_el_indentation() or self.default_indent


class IndentedCodeBlockMixin(CodeBlockMixin):
    default_indent = BaseNode.indent_unit

    @nodelist_property(CodeProxyList)
    def value(self, value):
        return self._parse_value(value, replace=True)

    def _parse_value(self, value, replace=False):
        if replace:
            if value.lstrip(" ").startswith("\n"):
                fst = self._parse_indented(value)
            else:
                fst = self._parse_not_indented(value)
        else:
            if self.value.header:
                fst = self._parse_indented(value)
            else:
                fst = self._parse_not_indented(value)
        return fst

    def _parse_not_indented(self, value):
        fst = baron.parse("while a: %s" % value)
        if len(fst) > 1:
            raise ValueError("inline code can't have multiple lines")
        fst = fst[0]
        indent = fst['third_formatting'][0]['value'][1:]
        fst['value'].insert(0, {"type": "space", "value": indent})
        return fst['value']


class IfElseBlockSiblingMixin:
    @property
    def next_intuitive(self):
        next_ = super().next

        if next_ is None and self.parent and self.parent.parent:
            next_ = self.parent.parent.next

        return next_

    @property
    def previous_intuitive(self):
        previous_ = super().previous

        if previous_ is None and self.parent and self.parent.parent:
            previous_ = self.parent.parent.previous

        return previous_

    def increase_indentation(self, indent):
        self.value.increase_indentation(indent)

    def decrease_indentation(self, indent):
        self.value.decrease_indentation(indent)

    @property
    def el_indentation(self):
        return self.parent.parent.indentation + self.indent_unit


class SeparatorMixin:
    def consume_leftover_indentation(self):
        from .nodes import EndlNode

        if not self.second_formatting:
            return ""

        node = self.second_formatting[-1]
        if isinstance(node, EndlNode):
            indent = node.indent
            node.indent = ""
            return indent

        return ""
