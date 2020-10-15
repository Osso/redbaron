from collections import UserList
from fnmatch import fnmatch
import inspect
from itertools import dropwhile
import re
import sys

import baron
import baron.path
from baron.render import nodes_rendering_order

from .node_mixin import NodeMixin
from .syntax_highlight import (help_highlight,
                               python_highlight)
from .utils import (display_property_atttributeerror_exceptions,
                    in_a_shell,
                    in_ipython,
                    indent,
                    redbaron_classname_to_baron_type,
                    truncate)

NODES_RENDERING_ORDER = nodes_rendering_order
NODES_RENDERING_ORDER["root"] = [('list', 'value', True)]
NODE_TYPE_MAPPING = {}


class NodeList(UserList, NodeMixin):
    def __init__(self, node_list=None, parent=None, on_attribute=None):
        for node in node_list:
            node.parent = self

        super().__init__(node_list)

        self.parent = parent
        self.on_attribute = on_attribute

    @classmethod
    def from_fst(cls, node_list, parent, on_attribute=None):
        assert isinstance(parent, Node)
        nodes = [parent.from_fst(n) for n in node_list]
        return cls(nodes, parent=parent, on_attribute=on_attribute)

    @classmethod
    def from_str(cls, value, parent, on_attribute=None):
        return cls.from_fst(baron.parse(value), parent=parent,
                            on_attribute=on_attribute)

    def from_str_el(self, value):
        node = self.parent.from_str(value, on_attribute=self.on_attribute)
        node.parent = self
        return node

    def __setitem__(self, key, value):
        if isinstance(value, str):
            value = self.from_str_el(value)

        self.data[key] = value

    def find_iter(self, identifier, *args, **kwargs):
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
        for num, i in enumerate(self.data):
            sys.stdout.write(str(num) + " -----------------------------------------------------\n")
            i.help(deep=deep, with_formatting=with_formatting)

    def __help__(self, deep=2, with_formatting=False):
        return [x.__help__(deep=deep, with_formatting=with_formatting) for x in self.data]

    def copy(self):
        return self.__class__(list(self))

    def deep_copy(self):
        return self.__class__([node.copy() for node in self])

    def filter(self, function):
        return self.replace_data([x for x in self.data if function(x)])

    def replace_data(self, new_data):
        self.data = new_data

    def _generate_nodes_in_rendering_order(self):
        previous = None
        for node in self:
            for _node in node._iter_in_rendering_order():
                if _node is previous:
                    continue
                previous = _node
                yield _node

    def get_absolute_bounding_box_of_attribute(self, index):
        if not 0 < index <= len(self.data):
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
        return self.index(value)

    def get_from_baron_index(self, index):
        return self[index]

    @property
    def node_list(self):
        return self


class Node(NodeMixin):
    _other_identifiers = []
    _default_test_value = "value"
    first_formatting = None
    second_formatting = None
    third_formatting = None

    def __init__(self, fst=None, parent=None, on_attribute=None):
        if fst is None:
            fst = self._default_fst()

        self.init = True
        self.parent = parent
        self.on_attribute = on_attribute
        self._str_keys = ["type"]
        self._list_keys = []
        self._dict_keys = []
        self.type = fst["type"]
        self.indent = ""

        for kind, key, _ in self._render():
            if kind == "constant":
                continue

            if kind == "key":
                if fst[key]:
                    value = self.from_fst(fst[key], on_attribute=key)
                else:
                    value = None
                setattr(self, key, value)
                self._dict_keys.append(key)
            elif kind in ("bool", "string"):
                setattr(self, key, fst[key])
                self._str_keys.append(key)
            elif kind in ("list", "formatting"):
                value = self.nodelist_from_fst(fst[key], on_attribute=key)
                setattr(self, key, value)
                self._list_keys.append(key)
            else:
                raise Exception(str((fst["type"], kind, key)))

        self.init = False

    def from_fst(self, node, on_attribute=None):
        cls = NODE_TYPE_MAPPING[node['type']]
        return cls(node, parent=self, on_attribute=on_attribute)

    def nodelist_from_fst(self, node_list, on_attribute=None):
        return NodeList.from_fst(node_list, parent=self,
                                 on_attribute=on_attribute)

    def from_str(self, value, on_attribute=None):
        assert isinstance(value, str)
        value = baron.parse(value)[0]
        return self.from_fst(value, on_attribute=on_attribute)

    def nodelist_from_str(self, value, on_attribute=None):
        assert isinstance(value, str)
        return NodeList.from_fst(value, parent=self.parent,
                                 on_attribute=on_attribute)

    @property
    def neighbors(self):
        neighbors = self.on_attribute_node
        if isinstance(neighbors, NodeList):
            return neighbors
        return []

    @property
    def next_neighbors(self):
        neighbors = dropwhile(lambda x: x is not self, self.neighbors)
        next(neighbors)
        return neighbors

    @property
    def next(self):
        return next(self.next_neighbors, None)

    @property
    def next_intuitive(self):
        next_node = self.next

        if next_node and next_node.type == "ifelseblock":
            return next_node.find("if")

        return next_node

    @property
    @display_property_atttributeerror_exceptions
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
    def next_recursive(self):
        target = self
        while not target.next:
            if not target.parent:
                break
            target = target.parent
        return target.next

    @property
    def previous_neighbors(self):
        neighbors = dropwhile(lambda x: x is not self,
                              reversed(self.neighbors))
        next(neighbors)
        return neighbors

    @property
    def previous(self):
        return next(self.previous_neighbors, None)

    @property
    def previous_intuitive(self):
        previous_ = self.previous

        if previous_ and previous_.type == "ifelseblock":
            return previous_.value[-1]

        elif previous_ and previous_.type == "try":
            if previous_.finally_:
                return previous_.finally_

            if previous_.else_:
                return previous_.else_

            if previous_.excepts:
                return previous_.excepts[-1]

        elif previous_ and previous_.type in ("for", "while"):
            if previous_.else_:
                return previous_.else_

        return previous_

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
    def previous_recursive(self):
        target = self
        while not target.previous:
            if not target.parent:
                break
            target = target.parent
        return target.previous

    def __getattr__(self, key):
        if key.endswith("_") and key[:-1] in self._dict_keys + self._list_keys + self._str_keys:
            return getattr(self, key[:-1])

        if key != "value" and hasattr(self, "value"):
            return getattr(self.value, key)

        raise AttributeError("%s not found" % key)

    def find_iter(self, identifier, *args, recursive=True, **kwargs):
        if self._node_match_query(self, identifier, *args, **kwargs):
            yield self

        if recursive:
            for kind, key, _ in self._render():
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
        return sorted(set(map(lambda x: x.lower(), [
            redbaron_classname_to_baron_type(cls.__name__),
            cls.__name__,
            cls.__name__.replace("Node", ""),
            redbaron_classname_to_baron_type(cls.__name__) + "_"
        ] + cls._other_identifiers)))

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
            to_return[key] = [node.fst() for node in getattr(self, key).node_list]
        for key in self._dict_keys:
            value = getattr(self, key)
            to_return[key] = value.fst() if value else {}
        return to_return

    def help(self, deep=2, with_formatting=False):
        if in_ipython():
            help_msg = self.__help__(deep=deep,
                                     with_formatting=with_formatting)
            sys.stdout.write(help_highlight(help_msg + "\n"))
        else:
            sys.stdout.write(help_msg + "\n")

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
            to_join += ["%s ->\n    %s" % (key, indent(
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
                        "  * " + indent(i.__help__(deep=new_deep,
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
                        "  * " + indent(i.__help__(deep=new_deep,
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
        if name == "init" or self.init:
            return super(Node, self).__setattr__(name, value)

        # convert "async_" to "async"
        # (but we don't want to mess with "__class__" for example)
        if name.endswith("_") and not name.endswith("__"):
            name = name[:-1]

        if name in self._str_keys:
            assert isinstance(value, str)

        elif name in self._dict_keys:
            if isinstance(value, str):
                value = self.from_str(value, on_attribute=name)
            assert isinstance(value, dict)

        elif name in self._list_keys:
            if isinstance(value, str):
                value = self.nodelist_from_str(value, on_attribute=name)

        return super(Node, self).__setattr__(name, value)

    def _render(self):
        return nodes_rendering_order[self.type]

    def _generate_nodes_in_rendering_order(self):
        previous = None
        for j in self._iter_in_rendering_order():
            if j is previous:
                continue
            previous = j
            yield j

    def has_render_key(self, target_key):
        for _, _, key in baron.render.render(self.fst()):
            if key == target_key:
                return True
        return False

    def get_absolute_bounding_box_of_attribute(self, attribute):
        if not self.has_render_key(attribute):
            raise KeyError()
        path = self.path().to_baron_path() + [attribute]
        return baron.path.path_to_bounding_box(self.root.fst(), path)

    def increase_indentation(self, number_of_spaces):
        self.indent += number_of_spaces * " "

    def decrease_indentation(self, number_of_spaces):
        self.indent = self.indent[:-len(number_of_spaces)]

    def insert_before(self, value, offset=0):
        self.parent.insert(self.index_on_parent - offset, value)

    def insert_after(self, value, offset=0):
        self.parent.insert(self.index_on_parent + 1 + offset, value)

    def __bool__(self):
        return True

    @property
    def node_list(self):
        return self


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


class CodeBlockNode(IterableNode):
    def nodelist_from_str(self, value, on_attribute=None):
        assert isinstance(value, str)

        if on_attribute.endswith("_formatting"):
            return super().nodelist_from_str(value, on_attribute=on_attribute)

        raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        from .proxy_list import CodeProxyList, LineProxyList

        if key == "value":
            if isinstance(value, str):
                value = CodeProxyList.from_str(value, parent=self,
                                               on_attribute=key)
            elif isinstance(value, NodeList):
                value = CodeProxyList(value, parent=self, on_attribute=key)

            assert isinstance(value, CodeProxyList)

        elif key == "decorators":
            if isinstance(value, str):
                value = LineProxyList.from_str(value, parent=self,
                                               on_attribute=key)
            if isinstance(value, NodeList):
                value = LineProxyList(value, parent=self, on_attribute=key)

        super().__setattr__(key, value)


class IfElseBlockSiblingNode(CodeBlockNode):
    @property
    @display_property_atttributeerror_exceptions
    def next_intuitive(self):
        next_ = super(IfElseBlockSiblingNode, self).next

        if next_ is None and self.parent:
            next_ = self.parent.next

        return next_

    @property
    @display_property_atttributeerror_exceptions
    def previous_intuitive(self):
        previous_ = super(IfElseBlockSiblingNode, self).previous

        if previous_ is None and self.parent:
            previous_ = self.parent.previous

        return previous_
