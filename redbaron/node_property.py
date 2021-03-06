from functools import partial
from typing import Callable

import baron


class BaseProperty:
    @property
    def attr_name(self):
        return "_" + self.name


class NodeProperty(BaseProperty):
    _after_set: Callable
    name = None

    def __init__(self, str_to_fst=None):
        self.str_to_fst = str_to_fst if str_to_fst else self.default_str_to_fst
        self._after_set = lambda obj, value: None

    def default_str_to_fst(self, obj, value):  # pylint: disable=unused-argument
        return baron.parse(value)[0]

    def __get__(self, obj, objtype=None):  # pylint: disable=method-hidden
        if not obj:
            return self

        return getattr(obj, self.attr_name, None)

    def setter(self, fun):
        new_property = self.copy()
        new_property._set = fun
        return new_property

    def _set(self, obj, value):
        setattr(obj, self.attr_name, self.to_value(obj, value))

    def __set__(self, obj, value):
        self._set(obj, value)
        self._after_set(obj, value)

    def to_value(self, obj, value):
        from .base_nodes import BaseNode

        if isinstance(value, str):
            value = self.str_to_fst(obj, value)
            assert value is None or isinstance(value, (dict, list, BaseNode))

        if isinstance(value, (dict, list)):
            value = self.fst_to_node(obj, value)

        if value is not None:
            value.parent = obj
            value.on_attribute = self.name

        return value

    def fst_to_node(self, obj, value):
        from .base_nodes import Node
        assert isinstance(obj, Node)
        assert isinstance(value, dict)
        if not value:
            return None

        return Node.generic_from_fst(value, parent=obj)

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

    def default_str_to_fst(self, obj, value):  # pylint: disable=unused-argument
        return baron.parse(value)

    def fst_to_node(self, obj, value):
        from .base_nodes import Node

        def _convert(el):
            if isinstance(el, str):
                return Node.generic_from_str(el, parent=node_list)
            if isinstance(el, list):
                assert len(el) == 1
                el = el[0]
            if isinstance(el, dict):
                return Node.generic_from_fst(el, parent=node_list)

            el.parent = node_list
            el.on_attribute = None
            return el

        node_list = self.list_type([], parent=obj, on_attribute=self.name)
        node_list.replace_node_list([_convert(el) for el in value])
        return node_list

    def __get__(self, obj, objtype=None):
        if not obj:
            return self

        try:
            value = getattr(obj, self.attr_name)
        except AttributeError:
            setattr(obj, self.name, [])
            value = getattr(obj, self.attr_name)

        return value

    def copy(self):
        new_property = type(self)(self.list_type)
        new_property.__dict__ = self.__dict__.copy()
        return new_property


class ConditionalFormattingProperty(NodeListProperty):
    _default = None

    def __init__(self, condition, list_type, default_true, default_false,
                 allow_set=True):
        super().__init__(list_type=list_type, str_to_fst=None)
        self.condition = condition
        self._default_true = default_true
        self._default_false = default_false
        self._allow_set = allow_set

    def __get__(self, obj, objtype=None):
        if not obj:
            return self

        user_defined_value = getattr(obj, self.attr_name, None)
        if user_defined_value:
            return user_defined_value

        attr_name_for_default = self.attr_name + "_default"
        default = getattr(obj, attr_name_for_default, None)
        if default is None:
            default = {
                True: self.to_value(obj, self._default_true),
                False: self.to_value(obj, self._default_false),
            }
            setattr(obj, attr_name_for_default, default)

        return default[bool(self.condition(obj))]

    def __set__(self, obj, value):
        if self._allow_set:
            super().__set__(obj, value)

    def copy(self):
        new_property = type(self)(condition=self.condition,
                                  list_type=self.list_type,
                                  default_true=self._default_true,
                                  default_false=self._default_false)
        new_property.__dict__ = self.__dict__.copy()
        return new_property


def node_property():
    return NodeProperty


def nodelist_property(list_type):
    return partial(NodeListProperty, list_type)


def conditional_formatting_property(list_type, default_true, default_false,
                                    allow_set=True):
    return partial(ConditionalFormattingProperty,
                   list_type=list_type, default_true=default_true,
                   default_false=default_false, allow_set=allow_set)


def set_name_for_node_properties(cls):
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if isinstance(attr, BaseProperty):
            attr.name = attr_name


class AliasProperty(BaseProperty):
    def __init__(self, aliased_name):
        self.aliased_name = aliased_name

    def __get__(self, obj, objtype=None):
        if not obj:
            return self
        return getattr(obj, self.aliased_name)

    def __set__(self, obj, value):
        setattr(obj, self.aliased_name, value)
