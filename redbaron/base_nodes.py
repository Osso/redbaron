from collections import UserList
from fnmatch import fnmatch
import inspect
from itertools import dropwhile
import re

import baron
import baron.path
from baron.render import nodes_rendering_order

from .node_path import Path
from .node_property import (AliasProperty,
                            NodeListProperty,
                            NodeProperty,
                            set_name_for_node_properties)
from .syntax_highlight import (help_highlight,
                               python_highlight)
from .utils import (baron_type_from_class,
                    deindent_str,
                    fix_baron_box,
                    in_a_shell,
                    in_ipython,
                    indent_str,
                    squash_successive_duplicates,
                    truncate)

NODES_RENDERING_ORDER = nodes_rendering_order
NODES_RENDERING_ORDER["root"] = [('list', 'value', True)]
NODES_RENDERING_ORDER["empty_line"] = []
RESERVED_KEYWORDS = ("async", "class", "finally", "except", "else",
                     "if", "elif", "while", "for", "is", "and", "or")


class NeighborsMixin:
    @property
    def neighbors(self):
        if not isinstance(self.parent, NodeList):
            return []

        if self not in self.parent:
            raise ValueError("Invalid node")

        return self.parent

    def _next_neighbors(self, neighbors):
        neighbors = dropwhile(lambda x: x is not self, neighbors)
        next(neighbors, None)
        return neighbors

    @property
    def next_neighbors(self):
        return self._next_neighbors(self.neighbors)

    @property
    def previous_neighbors(self):
        return self._next_neighbors(reversed(self.neighbors))

    @property
    def next(self):
        return next(self.next_neighbors, None)

    @property
    def previous(self):
        return next(self.previous_neighbors, None)

    @property
    def neighbors_nodelist(self):
        if not isinstance(self.parent, NodeList):
            return []

        if self not in self.parent.node_list:
            raise ValueError("Invalid node")

        return self.parent.node_list

    @property
    def next_neighbors_nodelist(self):
        return self._next_neighbors(self.neighbors_nodelist)

    @property
    def previous_neighbors_nodelist(self):
        return self._next_neighbors(reversed(self.neighbors_nodelist))

    @property
    def next_nodelist(self):
        return next(self.next_neighbors_nodelist, None)

    @property
    def previous_nodelist(self):
        return next(self.previous_neighbors_nodelist, None)


class BaseNode(NeighborsMixin):
    """
    Abstract class for Node and NodeList that contains methods
    that are used by both.
    """
    _leftover_indentation = ""
    indent_unit = 4 * " "

    def __init__(self, parent, on_attribute):
        self.parent = parent
        self.on_attribute = on_attribute

    @property
    def relative_box(self):
        box = baron.path.node_to_bounding_box(self.fst())
        return fix_baron_box(box)

    @classmethod
    def _baron_path_to_box(cls, fst, path):
        box = baron.path.path_to_bounding_box(fst, path)
        return fix_baron_box(box)

    @property
    def box(self):
        path = self.path().to_baron_path()
        return self._baron_path_to_box(self.root.fst(), path)

    def find_by_position(self, position):
        path = baron.path.position_to_path(self.fst(), position) or []
        return self.find_by_path(path)

    def at(self, line_no):
        if not 0 < line_no <= self.box.bottom_right.line:
            raise IndexError(f"Line number {line_no} is outside of the file")

        node = self.find_by_position((line_no, 1))
        if not node:
            return None

        if node.box.top_left.line > line_no:
            for n in self._iter_in_rendering_order():
                if n.box.top_left.line == line_no:
                    return n
            return node

        while node.parent and \
                node.parent.box.top_left.line == line_no:
            node = node.parent

        while node.previous_nodelist and \
                node.previous_nodelist.box.top_left.line == line_no:
            node = node.previous_nodelist

        while node.type in ('endl', 'space') and node.next_nodelist and \
                node.next_nodelist.box.top_left.line == line_no:
            node = node.next_nodelist

        return node

    @property
    def root(self):
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def set_on_attribute_node(self, node):
        if not self.parent:
            raise ValueError("Can't set on_attribute_node on root")

        assert self.on_attribute
        assert getattr(self.parent, self.on_attribute) is self

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

    def replace(self, new_node):
        self.set_on_attribute_node(new_node)

    @property
    def index_on_parent(self):
        if not self.parent:
            raise ValueError("No parent")

        if not isinstance(self.parent, NodeList):
            raise ValueError("Parent is not a node list")

        return self.parent.index(self)

    def _iter_in_rendering_order(self):
        raise NotImplementedError()

    def _generate_nodes_in_rendering_order(self):
        yield from squash_successive_duplicates(self._iter_in_rendering_order())

    @property
    def type(self):
        return self.baron_type

    def to_node(self, source_code: str):
        assert self.parent
        assert self.on_attribute
        node_property = getattr(type(self.parent), self.on_attribute)
        return node_property.to_value(self, source_code)

    @classmethod
    def generic_to_node(cls, value, parent=None, on_attribute=None):
        if isinstance(value, str):
            node = cls.generic_from_str(value, parent=parent,
                                        on_attribute=on_attribute)
        elif isinstance(value, dict):
            node = cls.generic_from_fst(value, parent=parent,
                                        on_attribute=on_attribute)
        elif isinstance(value, BaseNode):
            node = value
            node.parent = parent
            node.on_attribute = on_attribute
        else:
            raise ValueError(f"Invalid value {value} for to_node()")
        return node


class IndentationMixin:
    def __init__(self, indent):
        self.indent = indent
        self.leftover_endl = []

    @property
    def leftover_indentation(self):
        return self._leftover_indentation

    @leftover_indentation.setter
    def leftover_indentation(self, value):
        self._leftover_indentation = value

    def consume_leftover_indentation(self):
        r = self.leftover_indentation
        self.leftover_indentation = ""
        return r

    @property
    def leftover_endl(self):
        return self._leftover_endl

    @leftover_endl.setter
    def leftover_endl(self, value):
        self._leftover_endl = value

    def consume_leftover_endl(self):
        yield from self.leftover_endl
        self.leftover_endl.clear()


class NodeList(UserList, BaseNode, IndentationMixin):
    def __init__(self, node_list=None, parent=None, on_attribute=None):
        if node_list is None:
            node_list = []

        for node in node_list:
            node.parent = self

        UserList.__init__(self, node_list)
        BaseNode.__init__(self, parent=parent, on_attribute=on_attribute)
        IndentationMixin.__init__(self, getattr(node_list, "indentation", ""))

    @classmethod
    def generic_from_fst(cls, fst_list, parent=None, on_attribute=None):
        assert parent is None or isinstance(parent, BaseNode)
        nodes = [Node.generic_from_fst(n) for n in fst_list]
        return cls(nodes, parent=parent, on_attribute=on_attribute)

    @classmethod
    def generic_from_str(cls, value: str, parent=None, on_attribute=None):
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

    def _find_iter(self, identifier, *args, recursive=True, **kwargs):
        for node in self.data:
            for matched_node in node._find_iter(identifier, *args,
                                                recursive=recursive, **kwargs):
                yield matched_node

    def find_iter(self, identifier, *args, recursive=True, **kwargs):
        return self._find_iter(identifier, *args,
                               recursive=recursive, **kwargs)

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

    def set_parent_and_on_attribute(self, new_data):
        for el in new_data:
            el.parent = self
            el.on_attribute = None

    def _iter_in_rendering_order(self):
        for node in self:
            yield from node._iter_in_rendering_order()

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

    def increase_indentation(self, indent):
        indented_str = indent_str(self.dumps(), indent)
        if not self.parent:
            raise ValueError("Cannot indent detached node")

        self.replace(indented_str)

    def decrease_indentation(self, indent):
        indented_str = deindent_str(self.dumps(), indent)
        if not self.parent:
            raise ValueError("Cannot indent detached node")

        self.replace(indented_str)

    def replace_node_list(self, new_node_list):
        self.set_parent_and_on_attribute(new_node_list)
        self.data = new_node_list

    @property
    def indentation(self):
        if self.on_attribute:
            raise ValueError("Unhandled indentation on a node list attribute")

    @indentation.setter
    def indentation(self, value):
        if self.on_attribute:
            raise ValueError("Unhandled indentation on a node list attribute")

    @classmethod
    def generate_identifiers(cls):
        return [cls.__name__.lower()]


class NodeRegistration(type):
    node_type_mapping = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if name != "Node":
            cls.baron_type = getattr(cls, "baron_type",
                                     baron_type_from_class(cls))
            NodeRegistration.register_type(cls)
            if cls.baron_type in NODES_RENDERING_ORDER:
                cls.define_attributes_from_baron(cls.baron_type)  # pylint: disable=no-value-for-parameter
        set_name_for_node_properties(cls)  # pylint: disable=no-value-for-parameter

    def define_attributes_from_baron(cls, baron_type):
        cls._raw_keys = ["type"]
        cls._list_keys = []
        cls._dict_keys = []
        cls._constant_keys = []

        for kind, key, _ in cls._baron_attributes():
            orig_key = key
            if key in RESERVED_KEYWORDS:
                key += "_"
                if not hasattr(cls, orig_key):
                    setattr(cls, orig_key, AliasProperty(key))

            if kind == "constant":
                if orig_key not in cls._raw_keys:
                    cls._constant_keys.append(orig_key)
            elif kind in ("bool", "string"):
                cls._raw_keys.append(orig_key)
            elif kind == "key":
                if not hasattr(cls, key):
                    setattr(cls, key, NodeProperty())
                cls._dict_keys.append(orig_key)
            elif kind in ("list", "formatting"):
                if not hasattr(cls, key):
                    setattr(cls, key, NodeListProperty(NodeList))
                cls._list_keys.append(orig_key)
            else:
                raise Exception(f"Invalid kind {kind} for {baron_type}.{key}")

    @classmethod
    def register_type(mcs, node_class):
        mcs.node_type_mapping[node_class.baron_type] = node_class

    @classmethod
    def class_from_baron_type(mcs, baron_type):
        try:
            return mcs.node_type_mapping[baron_type]
        except IndexError:
            raise ValueError(f"Invalid baron type {baron_type}")

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
        assert self.type == fst["type"]

        for kind, key, _ in self._baron_attributes():
            if key == "type":
                continue

            if kind == "constant" and key not in fst:
                pass
            else:
                setattr(self, key, fst[key])

            # Checks
            if kind == "key" and fst[key]:
                assert isinstance(fst[key], dict)
                new_value = getattr(self, key)
                assert isinstance(getattr(self, key), Node), \
                    f"invalid {new_value} for {type(self).__name__}.{key}"
            elif kind in ("list", "formatting"):
                assert isinstance(fst[key], list)
                new_value = getattr(self, key)
                assert isinstance(new_value, NodeList), \
                    f"invalid {new_value} for {type(self).__name__}.{key}"

    @staticmethod
    def generic_from_fst(fst, parent=None, on_attribute=None):
        assert parent is None or isinstance(parent, BaseNode)
        assert 'type' in fst
        cls = NodeRegistration.class_from_baron_type(fst['type'])
        return cls(fst, parent=parent, on_attribute=on_attribute)

    @staticmethod
    def generic_from_str(source_code: str, parent=None, on_attribute=None):
        assert isinstance(source_code, str)
        fst = baron.parse(source_code)
        assert len(fst) == 1
        return Node.generic_from_fst(fst[0], parent=parent,
                                     on_attribute=on_attribute)

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

            if previous_.find("except"):
                return previous_.find_all("except")[-1]

        elif previous_ and previous_.type in ("for", "while"):
            if previous_.find("else"):
                return previous_.find("else")

        return previous_

    @property
    def next_rendered(self):
        previous = None
        target = self.parent
        while target is not None:
            for i in reversed(list(target._generate_nodes_in_rendering_order())):
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

    def _next_recursive(self, getter):
        target = self
        while not getter(target):
            if not target.parent:
                break
            target = target.parent
        return getter(target)

    @property
    def next_recursive(self):
        return self._next_recursive(lambda node: node.next)

    @property
    def previous_recursive(self):
        return self._next_recursive(lambda node: node.previous)

    def _find_iter(self, identifier, *args, recursive=True, **kwargs):
        if self._node_match_query(self, identifier, *args, **kwargs):
            yield self

        if recursive:
            for kind, key, _ in self._baron_attributes():
                if kind in ("key", "list", "formatting"):
                    node = getattr(self, key)
                    if node:
                        yield from node._find_iter(identifier, *args, **kwargs)

    def find_iter(self, identifier, *args, recursive=True, **kwargs):
        return dropwhile(lambda node: node is self,
                         self._find_iter(identifier, *args,
                                         recursive=recursive, **kwargs))

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

        all_my_keys = node._raw_keys + node._list_keys + node._dict_keys

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
            cls.baron_type,
            cls.baron_type + "_",
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
            'box_of_attribute',
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
            'consume_leftover_endl',
            'consume_leftover_indentation',
            'set_attributes_from_fst',
            'set_on_attribute_node',
            'to_node',
            'generic_to_node',
        ])
        return [x for x in dir(self) if not x.startswith("_") and
                x not in not_helpers and inspect.ismethod(getattr(self, x))]

    def fst(self):
        to_return = {}
        for key in self._constant_keys:
            try:
                to_return[key] = getattr(self, key).value
            except AttributeError:
                pass
        for key in self._raw_keys:
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
            to_join += ["%s=%s" % (key, repr(getattr(self, key))) for key in self._raw_keys if
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
            to_join += ["%s=%s" % (key, repr(getattr(self, key))) for key in self._raw_keys if
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
        return Node.generic_from_fst(self.fst())

    @classmethod
    def _baron_attributes(cls):
        return NODES_RENDERING_ORDER[cls.baron_type]

    def has_render_key(self, target_key):
        for _, _, key in baron.render.render(self.fst()):
            if key == target_key:
                return True
        return False

    def box_of_attribute(self, attribute):
        if not self.has_render_key(attribute):
            raise KeyError(f"{attribute} not found in {self}")
        path = self.path().to_baron_path() + [attribute]
        return self._baron_path_to_box(self.root.fst(), path)

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

    def set_on_attribute_node(self, node):
        if not self.parent:
            raise ValueError("Can't set on_attribute_node on root")

        assert self.parent[self.index_on_parent] is self
        self.parent[self.index_on_parent] = node

    def increase_indentation(self, indent):
        self.indentation += indent

    def decrease_indentation(self, indent):
        self.indentation = self.indentation[len(indent):]

    def dumps(self):
        return self.indentation + super().dumps()

    @property
    def indentation(self):
        return self.indent

    @indentation.setter
    def indentation(self, value):
        self.indent = value

    def get_from_baron_index(self, index):
        return getattr(self, index)
