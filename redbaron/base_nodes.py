from collections import UserList
from fnmatch import fnmatch
import inspect
from itertools import dropwhile
import re

import baron
import baron.path
from baron.render import nodes_rendering_order

from .node_path import Path
from .node_property import (NodeListProperty,
                            NodeProperty,
                            set_name_for_node_properties)
from .syntax_highlight import (help_highlight,
                               python_highlight)
from .utils import (in_a_shell,
                    in_ipython,
                    indent_str,
                    redbaron_classname_to_baron_type,
                    squash_successive_duplicates,
                    truncate)

NODES_RENDERING_ORDER = nodes_rendering_order
NODES_RENDERING_ORDER["root"] = [('list', 'value', True)]
NODES_RENDERING_ORDER["empty_line"] = []


class BaseNode:
    """
    Abstract class for Node and NodeList that contains methods
    that are used by both.
    """
    def __init__(self, parent, on_attribute):
        self.parent = parent
        self.on_attribute = on_attribute

    @property
    def bounding_box(self):
        return baron.path.node_to_bounding_box(self.fst())

    @property
    def absolute_bounding_box(self):
        path = self.path().to_baron_path()
        return baron.path.path_to_bounding_box(self.root.fst(), path)

    def find_by_position(self, position):
        path = baron.path.position_to_path(self.fst()['value'], position) or []
        return self.find_by_path(path)

    def at(self, line_no):
        if not 0 < line_no <= self.absolute_bounding_box.bottom_right.line:
            raise IndexError(f"Line number {line_no} is outside of the file")

        node = self.find_by_position((line_no, 1))
        if not node:
            return None

        if node.absolute_bounding_box.top_left.line > line_no:
            for n in self._iter_in_rendering_order():
                if n.absolute_bounding_box.top_left.line == line_no:
                    return n
            return node

        while node.parent and node.parent.absolute_bounding_box.top_left.line == line_no:
            node = node.parent

        while node.previous_nodelist and \
                node.previous_nodelist.absolute_bounding_box.top_left.line == line_no:
            node = node.previous_nodelist

        if node.type == 'endl':
            _next = node.next_nodelist
            if _next and _next.type != 'endl':
                node = _next

        return node

    @property
    def root(self):
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    @property
    def on_attribute_node(self):
        if self.on_attribute == "root":
            return self

        if self.on_attribute:
            return getattr(self.parent, self.on_attribute)

        return None

    @on_attribute_node.setter
    def set_on_attribute_node(self, node):
        setattr(self.parent, self.on_attribute, node)

    def find_by_path(self, path):
        return Path.from_baron_path(self, path).node

    def path(self):
        return Path(self)

    def fst(self):
        raise NotImplementedError()

    def dumps(self):
        return baron.dumps(self.fst())

    def find_all(self, identifier, *args, **kwargs):
        return list(self.find_iter(identifier, *args, **kwargs))

    def find_iter(self, identifier, *args, recursive=True, **kwargs):
        raise NotImplementedError()

    def find(self, identifier, *args, **kwargs):
        return next(self.find_iter(identifier, *args, **kwargs), None)

    def from_str(self, value: str, on_attribute=None):
        raise NotImplementedError()

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

    def _iter_in_rendering_order(self):
        raise NotImplementedError()

    def _generate_nodes_in_rendering_order(self):
        yield from squash_successive_duplicates(self._iter_in_rendering_order())

    @property
    def neighbors(self):
        return self.parent if isinstance(self.parent, NodeList) else []

    @property
    def neighbors_nodelist(self):
        return self.parent.node_list if isinstance(self.parent, NodeList) else []

    @property
    def next_neighbors(self):
        neighbors = self.neighbors
        if not neighbors:
            return iter([])

        neighbors = dropwhile(lambda x: x is not self, neighbors)
        next(neighbors)
        return neighbors

    @property
    def next_neighbors_nodelist(self):
        neighbors = self.neighbors_nodelist
        if not neighbors:
            return iter([])

        neighbors = dropwhile(lambda x: x is not self, neighbors)
        next(neighbors)
        return neighbors

    @property
    def previous_neighbors(self):
        neighbors = list(reversed(self.neighbors))
        if not neighbors:
            return iter([])

        neighbors = dropwhile(lambda x: x is not self, neighbors)
        next(neighbors)
        return neighbors

    @property
    def previous_neighbors_nodelist(self):
        neighbors = list(reversed(self.neighbors_nodelist))
        if not neighbors:
            return iter([])

        neighbors = dropwhile(lambda x: x is not self, neighbors)
        next(neighbors)
        return neighbors

    @property
    def next(self):
        return next(self.next_neighbors, None)

    @property
    def next_nodelist(self):
        return next(self.next_neighbors_nodelist, None)

    @property
    def previous(self):
        return next(self.previous_neighbors, None)

    @property
    def previous_nodelist(self):
        return next(self.previous_neighbors_nodelist, None)


class IndentationMixin:
    def __init__(self, indent):
        self.indent = NodeConstant(indent, parent=self, on_attribute="indent")

    @property
    def indentation(self):
        return self.indent.value

    @indentation.setter
    def indentation(self, value):
        self.indent.value = value

    @property
    def indentation_unit(self):
        if self.parent:
            indentation = self.parent.indentation_unit
            if indentation is None:
                raise Exception("node is not attached to ")
            return indentation

        try:
            indentation = self._indentation_unit
        except AttributeError:
            indentation = 4 * " "
        return indentation


class NodeList(UserList, BaseNode, IndentationMixin):
    def __init__(self, node_list, parent=None, on_attribute=None):
        for node in node_list:
            node.parent = self

        UserList.__init__(self, node_list)
        BaseNode.__init__(self, parent=parent, on_attribute=on_attribute)
        IndentationMixin.__init__(self, getattr(node_list, "indentation", ""))

    @classmethod
    def generic_from_fst(cls, fst_list, parent=None, on_attribute=None):
        assert isinstance(parent, Node)
        nodes = [parent.from_fst(n) for n in fst_list]
        return cls(nodes, parent=parent, on_attribute=on_attribute)

    @classmethod
    def generic_from_str(cls, value: str, parent=None, on_attribute=None):
        assert isinstance(parent, Node)
        return cls.generic_from_fst(baron.parse(value), parent=parent,
                                    on_attribute=on_attribute)

    def from_str(self, value: str, on_attribute=None):
        return self.generic_from_str(value, parent=self,
                                     on_attribute=on_attribute)

    def __setitem__(self, key, value):
        if isinstance(value, str):
            value = Node.generic_from_str(value)
        elif isinstance(value, dict):
            value = Node.generic_from_fst(value)

        value.parent = self
        value.on_attribute = None
        self.data[key] = value

    def find_iter(self, identifier, *args, recursive=True, **kwargs):
        for node in self.data:
            for matched_node in node.find_iter(identifier, *args, **kwargs):
                yield matched_node

    def fst(self):
        return [x.fst() for x in self.node_list]

    def __repr__(self):
        if in_a_shell():
            return self.__str__()

        return "<%s %s, \"%s\" %s, on %s %s>" % (
            self.__class__.__name__,
            self.path().to_baron_path(),
            truncate(self.dumps().replace("\n", "\\n"), 20),
            id(self),
            self.parent.__class__.__name__,
            id(self.parent)
        )

    def __str__(self):
        to_return = ""
        for number, value in enumerate(self.data):
            to_return += ("%-3s " % number) + "\n    ".join(value.__repr__().split("\n"))
            to_return += "\n"
        return to_return

    def help(self, deep=2, with_formatting=False):
        for index, node in enumerate(self.data):
            print(f"{index} -------------------------------------------------")
            node.help(deep=deep, with_formatting=with_formatting)

    def __help__(self, deep=2, with_formatting=False):
        return [x.__help__(deep=deep, with_formatting=with_formatting)
                for x in self.data]

    def copy(self):
        return type(self)(list(self))

    def deep_copy(self):
        return type(self)([node.copy() for node in self])

    def filter(self, function):
        self.data = [x for x in self.data if function(x)]

    def replace_data(self, new_data):
        for el in new_data:
            el.parent = self
            el.on_attribute = None
        self.data = new_data

    def _iter_in_rendering_order(self):
        for node in self:
            yield from node._iter_in_rendering_order()

    def get_absolute_bounding_box_of_attribute(self, index):
        if not 0 <= index < len(self.data):
            raise IndexError("invalid index")

        path = self[index].path().to_baron_path()
        return baron.path.path_to_bounding_box(self.root.fst(), path)

    def increase_indentation(self, number_of_spaces):
        for node in self:
            node.increase_indentation(number_of_spaces)

    def decrease_indentation(self, number_of_spaces):
        for node in self:
            node.decrease_indentation(number_of_spaces)

    def baron_index(self, value):
        return self.data.index(value)

    def get_from_baron_index(self, index):
        return self.data[index]

    @property
    def node_list(self):
        return self

    def insert(self, i, item):
        item.parent = self
        item.on_attribute = None
        super().insert(i, item)

    def append(self, item):
        item.parent = self
        item.on_attribute = None
        super().append(item)

    def extend(self, other):
        for node in other:
            node.parent = self
            node.on_attribute = None
        super().extend(other)


class NodeRegistration(type):
    node_type_mapping = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if name not in ("Node", "IterableNode"):
            baron_type = redbaron_classname_to_baron_type(name)
            NodeRegistration.register_type(baron_type, cls)
            if baron_type in NODES_RENDERING_ORDER:
                cls.define_attributes_from_baron(baron_type)  # pylint: disable=no-value-for-parameter
        set_name_for_node_properties(cls)  # pylint: disable=no-value-for-parameter

    def define_attributes_from_baron(cls, baron_type):
        cls.type = baron_type

        cls._str_keys = ["type"]
        cls._list_keys = []
        cls._dict_keys = []

        for kind, key, _ in cls._baron_attributes():
            if kind == "constant":
                pass
            elif kind in ("bool", "string"):
                cls._str_keys.append(key)
            elif kind == "key":
                if not hasattr(cls, key):
                    setattr(cls, key, NodeProperty())
                cls._dict_keys.append(key)
            elif kind in ("list", "formatting"):
                if not hasattr(cls, key):
                    setattr(cls, key, NodeListProperty(NodeList))
                cls._list_keys.append(key)
            else:
                raise Exception(f"Invalid kind {kind} for {baron_type}.{key}")

    @classmethod
    def register_type(mcs, baron_type, node_class):
        mcs.node_type_mapping[baron_type] = node_class

    @classmethod
    def class_from_baron_type(mcs, baron_type):
        return mcs.node_type_mapping[baron_type]

    @classmethod
    def all_types(mcs):
        return mcs.node_type_mapping


class Node(BaseNode, IndentationMixin, metaclass=NodeRegistration):
    _other_identifiers = []
    _default_test_value = "value"
    first_formatting = NodeListProperty(NodeList)
    second_formatting = NodeListProperty(NodeList)
    third_formatting = NodeListProperty(NodeList)
    fourth_formatting = NodeListProperty(NodeList)
    fifth_formatting = NodeListProperty(NodeList)
    sixth_formatting = NodeListProperty(NodeList)
    formatting = NodeListProperty(NodeList)

    def __init__(self, fst=None, parent=None, on_attribute=None):
        if fst is None:
            fst = self._default_fst()

        BaseNode.__init__(self, parent=parent, on_attribute=on_attribute)
        IndentationMixin.__init__(self, getattr(fst, "indentation", ""))
        self.set_attributes_from_fst(fst)

    def set_attributes_from_fst(self, fst):
        for kind, key, _ in self._baron_attributes():
            if kind == "constant":
                setattr(self, key, NodeConstant(getattr(fst, key, ""),
                                                parent=self,
                                                on_attribute=key))
                continue

            # if key in fst:
            setattr(self, key, fst[key])

            if kind == "key" and fst[key]:
                new_value = getattr(self, key)
                assert isinstance(getattr(self, key), Node), \
                    f"invalid {new_value} for {type(self).__name__}.{key}"
            elif kind in ("list", "formatting"):
                new_value = getattr(self, key)
                assert isinstance(new_value, NodeList), \
                    f"invalid {new_value} for {type(self).__name__}.{key}"

    @staticmethod
    def generic_from_fst(fst, parent=None, on_attribute=None):
        cls = NodeRegistration.class_from_baron_type(fst['type'])
        return cls(fst, parent=parent, on_attribute=on_attribute)

    def from_fst(self, fst, on_attribute=None):
        return Node.generic_from_fst(fst, parent=self,
                                     on_attribute=on_attribute)

    # def nodelist_from_fst(self, node_list, on_attribute=None):
    #     return NodeList.generic_from_fst(node_list, parent=self,
    #                                      on_attribute=on_attribute)

    @staticmethod
    def generic_from_str(value: str, parent=None, on_attribute=None):
        assert isinstance(value, str)
        value = baron.parse(value)[0]
        return Node.generic_from_fst(value, parent=parent,
                                     on_attribute=on_attribute)

    def from_str(self, value: str, on_attribute=None):
        return Node.generic_from_str(value, parent=self,
                                     on_attribute=on_attribute)

    # def nodelist_from_str(self, value: str, on_attribute=None):
    #     assert isinstance(value, str)
    #     fst = baron.parse(value)
    #     return self.nodelist_from_fst(fst, on_attribute=on_attribute)

    @property
    def next_intuitive(self):
        next_node = self.next

        if next_node and next_node.type == "ifelseblock":
            return next_node.find("if")

        return next_node

    @property
    def previous_intuitive(self):
        previous_ = self.previous

        if previous_ and previous_.type == "ifelseblock":
            return previous_.value[-1]

        elif previous_ and previous_.type == "try":
            if previous_.find("finally"):
                return previous_.find("finally")

            if previous_.find("else"):
                return previous_.find("else")

            if previous_.find("excepts"):
                return previous_.excepts[-1]

        elif previous_ and previous_.type in ("for", "while"):
            if previous_.find("else"):
                return previous_.find("else")

        return previous_

    @property
    def next_rendered(self):
        previous = None
        target = self.parent
        while target is not None:
            for i in reversed(target._generate_nodes_in_rendering_order()):
                if i is self and previous is not None:
                    return previous
                previous = i

            previous = None
            target = target.parent

    @property
    def previous_rendered(self):
        previous = None
        target = self.parent
        while target is not None:
            for i in target._generate_nodes_in_rendering_order():
                if i is self:
                    return previous
                previous = i

            target = target.parent

    @property
    def next_recursive(self):
        target = self
        while not target.next:
            if not target.parent:
                break
            target = target.parent
        return target.next

    @property
    def previous_recursive(self):
        target = self
        while not target.previous:
            if not target.parent:
                break
            target = target.parent
        return target.previous

    def __getattr__(self, key):
        if key.endswith("_") and \
                key[:-1] in self._dict_keys + self._list_keys + self._str_keys:
            return getattr(self, key[:-1])

        if key not in ("value", "_value"):
            value = getattr(self, "value", None)
            if value:
                return getattr(self.value, key)

        raise AttributeError("%s not found" % key)

    def find_iter(self, identifier, *args, recursive=True, **kwargs):
        if self._node_match_query(self, identifier, *args, **kwargs):
            yield self

        if recursive:
            for kind, key, _ in self._baron_attributes():
                if kind == "key":
                    node = getattr(self, key)
                    if hasattr(node, "find_iter"):
                        for matched_node in node.find_iter(identifier,
                                                           *args, **kwargs):
                            yield matched_node
                elif kind in ("list", "formatting"):
                    nodes = getattr(self, key)
                    for node in nodes:
                        for matched_node in node.find_iter(identifier, *args, **kwargs):
                            yield matched_node

    def parent_find(self, identifier, *args, **kwargs):
        current = self
        while current.parent and current.on_attribute != 'root':
            if self._node_match_query(current.parent, identifier, *args, **kwargs):
                return current.parent

            current = current.parent
        return None

    def _node_match_query(self, node, identifier, *args, **kwargs):
        if isinstance(identifier, str) and not identifier.startswith("re:"):
            identifier = identifier.lower()
        if not self._attribute_match_query(node.generate_identifiers(),
                                           identifier):
            return False

        all_my_keys = node._str_keys + node._list_keys + node._dict_keys

        if args and isinstance(args[0], (str, re._pattern_type, list, tuple)):
            if not self._attribute_match_query([getattr(node, node._default_test_value)], args[0]):
                return False
            args = args[1:]

        for arg in args:
            if not arg(node):
                return False

        for key, value in kwargs.items():
            if key not in all_my_keys:
                return False

            if not self._attribute_match_query([getattr(node, key)], value):
                return False

        return True

    def _attribute_match_query(self, attribute_names, query):
        """
        Take a list/tuple of attributes that can match and a query, return True
        if any of the attributes match the query.
        """
        assert isinstance(attribute_names, (list, tuple))

        if isinstance(query, str) and query.startswith("re:"):
            query = re.compile(query[3:])

        for attribute in attribute_names:
            if callable(query):
                if query(attribute):
                    return True

            elif isinstance(query, str) and query.startswith("g:"):
                if fnmatch(attribute, query[2:]):
                    return True

            elif isinstance(query, re._pattern_type):
                if query.match(attribute):
                    return True

            elif isinstance(query, (list, tuple)):
                if attribute in query:
                    return True
            else:
                if attribute == query:
                    return True

        return False

    @classmethod
    def generate_identifiers(cls):
        ids = [
            redbaron_classname_to_baron_type(cls.__name__),
            redbaron_classname_to_baron_type(cls.__name__) + "_",
            cls.__name__,
            cls.__name__.replace("Node", ""),
        ]
        ids += cls._other_identifiers
        return sorted(set(map(lambda x: x.lower(), ids)))

    def _get_helpers(self):
        not_helpers = set([
            'at',
            'copy',
            'decrease_indentation',
            'dumps',
            'edit',
            'find',
            'find_all',
            'findAll',
            'find_by_path',
            'find_by_position',
            'find_iter',
            'from_fst',
            'fst',
            'fst',
            'generate_identifiers',
            'get_absolute_bounding_box_of_attribute',
            'get_indentation_node',
            'get_indentation_node',
            'has_render_key',
            'help',
            'help',
            'increase_indentation',
            'indentation_node_is_direct',
            'indentation_node_is_direct',
            'index_on_parent',
            'index_on_parent_raw',
            'insert_after',
            'insert_before',
            'next_neighbors',
            'next_neighbors',
            'parent_find',
            'parent_find',
            'parse_code_block',
            'parse_decorators',
            'path',
            'path',
            'previous_neighbors',
            'previous_neighbors',
            'replace',
            'to_python',
        ])
        return [x for x in dir(self) if not x.startswith("_") and
                x not in not_helpers and inspect.ismethod(getattr(self, x))]

    def fst(self):
        to_return = {}
        for key in self._str_keys:
            to_return[key] = getattr(self, key)
        for key in self._list_keys:
            to_return[key] = getattr(self, key).fst()
        for key in self._dict_keys:
            value = getattr(self, key)
            to_return[key] = value.fst() if value else {}
        return to_return

    def help(self, deep=2, with_formatting=False):
        help_msg = self.__help__(deep=deep, with_formatting=with_formatting)

        if in_ipython():
            help_msg = help_highlight(help_msg)

        print(help_msg)

    def __help__(self, deep=2, with_formatting=False):
        new_deep = deep - 1 if not isinstance(deep, bool) else deep

        to_join = ["%s()" % self.__class__.__name__]

        if not deep:
            to_join[-1] += " ..."
        else:
            to_join.append("# identifiers: %s" % ", ".join(self.generate_identifiers()))
            if self._get_helpers():
                to_join.append("# helpers: %s" % ", ".join(self._get_helpers()))
            if self._default_test_value != "value":
                to_join.append("# default test value: %s" % self._default_test_value)
            to_join += ["%s=%s" % (key, repr(getattr(self, key))) for key in self._str_keys if
                        key != "type" and "formatting" not in key]
            to_join += ["%s ->\n    %s" % (key, indent_str(
                getattr(self, key).__help__(deep=new_deep,
                                            with_formatting=with_formatting),
                "    ").lstrip() if getattr(self, key) else getattr(self, key))
                        for key in self._dict_keys if "formatting" not in key]
            # need to do this otherwise I end up with stacked quoted list
            # example: value=[\'DottedAsNameNode(target=\\\'None\\\',
            #    as=\\\'False\\\', value=DottedNameNode(
            #         value=["NameNode(value=\\\'pouet\\\')"])]
            for key in filter(lambda x: "formatting" not in x, self._list_keys):
                to_join.append(("%s ->" % key))
                for i in getattr(self, key):
                    to_join.append(
                        "  * " + indent_str(i.__help__(deep=new_deep,
                                                       with_formatting=with_formatting),
                                            "      ").lstrip())

        if deep and with_formatting:
            to_join += ["%s=%s" % (key, repr(getattr(self, key))) for key in self._str_keys if
                        key != "type" and "formatting" in key]
            to_join += ["%s=%s" % (key, getattr(self, key).__help__(deep=new_deep,
                                                                    with_formatting=with_formatting)
                                   if getattr(self, key) else getattr(self, key))
                        for key in self._dict_keys if "formatting" in key]

            for key in filter(lambda x: "formatting" in x, self._list_keys):
                to_join.append(("%s ->" % key))
                for i in getattr(self, key):
                    to_join.append(
                        "  * " + indent_str(i.__help__(deep=new_deep,
                                                       with_formatting=with_formatting),
                                            "      ").lstrip())

        return "\n  ".join(to_join)

    def __repr__(self):
        if in_a_shell():
            return self.__str__()

        return "<%s path=%s, \"%s\" %s, on %s %s>" % (
            self.__class__.__name__,
            self.path().to_baron_path(),
            truncate(self.dumps().replace("\n", "\\n"), 20),
            id(self),
            self.parent.__class__.__name__,
            id(self.parent)
        )

    def __str__(self):
        if in_ipython():
            return python_highlight(self.dumps()).decode("utf-8")
        return self.dumps()

    def copy(self):
        # not very optimised but at least very simple
        return self.from_fst(self.fst(), on_attribute=self.on_attribute)

    def __setattr__(self, name, value):
        # convert "async_" to "async"
        # (but we don't want to mess with "__class__" for example)
        if name.endswith("_") and not name.endswith("__"):
            name = name[:-1]

        return super().__setattr__(name, value)

    @classmethod
    def _baron_attributes(cls):
        return NODES_RENDERING_ORDER[cls.type]

    def has_render_key(self, target_key):
        for _, _, key in baron.render.render(self.fst()):
            if key == target_key:
                return True
        return False

    def get_absolute_bounding_box_of_attribute(self, attribute):
        if not self.has_render_key(attribute):
            raise KeyError(f"{attribute} not found in {self}")
        path = self.path().to_baron_path() + [attribute]
        return baron.path.path_to_bounding_box(self.root.fst(), path)

    def increase_indentation(self, number_of_units):
        self.indentation += number_of_units * self.indentation_unit

    def decrease_indentation(self, number_of_units):
        self.indentation = self.indentation[:-len(self.indentation_unit)*number_of_units]

    def insert_before(self, value, offset=0):
        self.parent.insert(self.index_on_parent - offset, value)

    def insert_after(self, value, offset=0):
        self.parent.insert(self.index_on_parent + 1 + offset, value)

    def __bool__(self):
        return True

    @property
    def node_list(self):
        return self

    def _iter_in_rendering_order(self):
        for kind, key, display in self._baron_attributes():
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


class IterableNode(Node):
    def __len__(self):
        return len(self.value)

    def __getitem__(self, key):
        return self.value[key]

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


class NodeConstant(BaseNode):
    def __init__(self, value, parent, on_attribute):
        super().__init__(parent=parent, on_attribute=on_attribute)
        self.value = value

    def fst(self):
        return self.value

    def find_iter(self, identifier, *args, recursive=True, **kwargs):
        if self.on_attribute == self.value:
            return self
        return None

    def from_str(self, value: str, on_attribute=None):
        return NodeConstant(value, parent=self.parent,
                            on_attribute=on_attribute)

    def _iter_in_rendering_order(self):
        yield self
