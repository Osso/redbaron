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

    @node_property()
    def annotation(self, value):
        return baron.parse("a: %s = a" % value)[0]["annotation"]

    @annotation.after_set
    def annotation_after_set(self, value):
        if not value:
            self.annotation_first_formatting = []
            self.annotation_second_formatting = []
        else:
            if not self.annotation_first_formatting:
                self.annotation_first_formatting = [" "]

            if not self.annotation_second_formatting:
                self.annotation_second_formatting = [" "]


class ReturnAnnotationMixin:
    return_annotation_first_formatting = nodelist_property("return_annotation_first_formatting")
    return_annotation_second_formatting = nodelist_property("return_annotation_second_formatting")

    @node_property()
    def return_annotation(self, value):
        code = "def a() -> %s: pass" % value
        return baron.parse(code)[0]["return_annotation"]

    @return_annotation.after_set
    def return_annotation_after_set(self, value):
        if not value:
            self.return_annotation_first_formatting = []
            self.return_annotation_second_formatting = []
        else:
            if not self.return_annotation_first_formatting:
                self.return_annotation_first_formatting = [" "]

            if not self.return_annotation_second_formatting:
                self.return_annotation_second_formatting = [" "]
