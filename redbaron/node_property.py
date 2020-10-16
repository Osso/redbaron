from functools import partial

import baron

from .base_nodes import NodeList


class NodeProperty:
    def __init__(self, name, str_to_fst=None):
        if isinstance(name, str):
            self.name = name
            self.str_to_fst = str_to_fst if str_to_fst else baron.parse
        else:  # assumed fun
            self.name = name.__name__
            self.str_to_fst = name

    @property
    def attr_name(self):
        return "_" + self.name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        return getattr(obj, self.attr_name)

    def __set__(self, obj, value):
        print(f"Setting {type(obj)}.{self.attr_name} to {value}")
        if isinstance(value, str):
            value = self.str_to_fst(value)

        if isinstance(value, (dict, list)):
            value = self.fst_to_value(obj, value)

        setattr(obj, self.attr_name, value)

    def fst_to_value(self, obj, value):
        if not value:
            return None
        return obj.from_fst(value, on_attribute=self.name)


def node_property():
    return NodeProperty


def nodelist_property(name=None, list_type=NodeList):
    attr = partial(NodeListProperty, list_type=list_type)

    if name:
        assert isinstance(name, str)
        return attr(name)

    return attr


class NodeListProperty(NodeProperty):
    def __init__(self, name, str_to_fst=None, list_type=NodeList):
        self.list_type = list_type
        super().__init__(name, str_to_fst=str_to_fst)

    def fst_to_value(self, obj, value):
        return self.list_type([obj.from_fst(el) for el in value],
                              parent=obj, on_attribute=self.name)
