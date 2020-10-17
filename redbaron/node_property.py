from functools import partial

import baron


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
        if isinstance(value, str):
            value = self.str_to_fst(value)

        if isinstance(value, (dict, list)):
            value = self.fst_to_value(obj, value)

        setattr(obj, self.attr_name, value)

    def fst_to_value(self, obj, value):
        if not value:
            return None
        return obj.from_fst(value, on_attribute=self.name)


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

    def fst_to_value(self, obj, value):
        nodes = [obj.from_fst(el) if isinstance(el, dict) else el
                 for el in value]
        return self.list_type(nodes, parent=obj, on_attribute=self.name)
