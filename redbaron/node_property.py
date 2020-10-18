from functools import partial
from typing import Callable

import baron


class NodeProperty:
    _after_set: Callable = lambda obj, value: None

    def __init__(self, name, str_to_fst=None):
        if isinstance(name, str):
            self.name = name
            self.str_to_fst = str_to_fst if str_to_fst else self.default_str_to_fst
        else:  # assumed fun
            self.name = name.__name__
            self.str_to_fst = name

    def default_str_to_fst(self, value):
        return baron.parse(value)[0]

    @property
    def attr_name(self):
        return "_" + self.name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        return getattr(obj, self.attr_name)

    def __set__(self, obj, value):
        if isinstance(value, str):
            value = self.str_to_fst(value)
            assert isinstance(value, (dict, list))

        if isinstance(value, (dict, list)):
            value = self.fst_to_value(obj, value)

        setattr(obj, self.attr_name, value)

        self._after_set(value)

    def fst_to_value(self, obj, value):
        if not value:
            return None

        assert value["type"] == obj.type, f"{value['type']} != {obj.type}"

        return obj.from_fst(value, on_attribute=self.name)

    def after_set(self, after_set):
        self._after_set = after_set
        return after_set


def node_property(name=None):
    attr = NodeProperty

    if name:
        assert isinstance(name, str)
        return attr(name)

    return attr


def nodelist_property(name=None, list_type=None):
    from .base_nodes import NodeList
    if list_type is None:
        list_type = NodeList

    attr = partial(NodeListProperty, list_type)

    if name:
        assert isinstance(name, str)
        return attr(name)

    return attr


class NodeListProperty(NodeProperty):
    def __init__(self, list_type, name, str_to_fst=None):
        self.list_type = list_type
        super().__init__(name, str_to_fst=str_to_fst)

    def default_str_to_fst(self, value):
        return baron.parse(value)

    def fst_to_value(self, obj, value):
        nodes = [obj.from_fst(el) if isinstance(el, dict) else el
                 for el in value]
        return self.list_type(nodes, parent=obj, on_attribute=self.name)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        try:
            value = getattr(obj, self.attr_name)
        except AttributeError:
            setattr(obj, self.name, [])
            value = getattr(obj, self.attr_name)

        return value
