from functools import partial
from typing import Callable

import baron


class NodeProperty:
    _after_set: Callable = lambda obj, value: None
    name = None

    def __init__(self, str_to_fst=None):
        self.str_to_fst = str_to_fst if str_to_fst else self.default_str_to_fst

    def default_str_to_fst(self, value):
        return baron.parse(value)[0]

    @property
    def attr_name(self):
        return "_" + self.name

    def __get__(self, obj, objtype=None):  # pylint: disable=method-hidden
        return getattr(obj, self.attr_name)

    def getter(self, fun):
        new_property = self.copy()
        new_property.__get__ = fun
        return self

    def __set__(self, obj, value):
        setattr(obj, self.attr_name, self.to_value(obj, value))
        self._after_set(self, value)

    def to_value(self, obj, value):
        if isinstance(value, str):
            value = self.str_to_fst(value)
            assert isinstance(value, (dict, list))

        if isinstance(value, (dict, list)):
            value = self.fst_to_node(obj, value)

        return value

    def fst_to_node(self, obj, value):
        if not value:
            return None

        assert value["type"] == obj.type, f"{value['type']} != {obj.type}"

        return obj.from_fst(value, on_attribute=self.name)

    def after_set(self, after_set):
        new_property = self.copy()
        new_property._after_set = after_set
        return new_property

    def copy(self):
        new_property = type(self)()
        new_property.__dict__ = self.__dict__.copy()
        return new_property


class NodeListProperty(NodeProperty):
    def __init__(self, list_type, str_to_fst=None):
        super().__init__(str_to_fst=str_to_fst)
        self.list_type = list_type

    def default_str_to_fst(self, value):
        return baron.parse(value)

    def fst_to_value(self, obj, value):
        nodes = [obj.from_fst(el) if isinstance(el, dict) else el
                 for el in value]
        return self.list_type(nodes, parent=obj, on_attribute=self.name)

    def __get__(self, obj, objtype=None):
        try:
            value = getattr(obj, self.attr_name)
        except AttributeError:
            setattr(obj, self.name, [])
            value = getattr(obj, self.attr_name)

        return value


class ConditionalFormattingProperty(NodeListProperty):
    def __init__(self, condition, list_type, default_true, default_false):
        super().__init__(list_type=list_type, str_to_fst=None)
        self.condition = condition
        self.default = {
            True: self.to_value(self, default_true),
            False: self.to_value(self, default_false),
        }

    def __get__(self, obj, objtype=None):
        try:
            return getattr(obj, self.attr_name)
        except AttributeError:
            return self.default[bool(self.condition())]


def node_property():
    return NodeProperty


def nodelist_property(list_type):
    return partial(NodeListProperty, list_type)


def conditional_formatting_property(list_type, default_true, default_false):
    return partial(ConditionalFormattingProperty,
                   list_type=list_type, default_true=default_true,
                   default_false=default_false)
