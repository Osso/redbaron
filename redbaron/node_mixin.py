import ast

import baron
import baron.path

from .node_property import (node_property,
                            nodelist_property)
from .proxy_list import LineProxyList


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
    @nodelist_property(list_type=LineProxyList)
    def decorators(self, value):
        assert value.lstrip()[0] == '@'

        def _detect_indentation(s):
            return s.index("@")
        indentation = _detect_indentation(value)

        code = "%s\n%sdef a(): pass" % (value, indentation)
        return baron.parse(code)[0]["decorators"]


class ValueMixin:
    value = node_property("value")


class AnnotationMixin:
    annotation_first_formatting = nodelist_property("annotation_first_formatting")
    annotation_second_formatting = nodelist_property("annotation_second_formatting")
