from collections import UserList
from fnmatch import fnmatch
import inspect
import itertools
import os
import re
import sys

import baron
import baron.path
from baron.render import nodes_rendering_order

from . import (ALL_IDENTIFIERS,
               nodes)
from .node_mixin import GenericNodesMixin
from .node_path import Path
from .proxy_list import (DecoratorsLineProxyList,
                         LineProxyList,
                         ProxyList)
from .syntax_highlight import (help_highlight,
                               python_highlight,
                               python_html_highlight)
from .utils import (baron_type_to_redbaron_classname,
                    in_a_shell,
                    in_ipython,
                    indent,
                    redbaron_classname_to_baron_type,
                    truncate)


def display_property_atttributeerror_exceptions(function):
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except AttributeError:
            import traceback
            traceback.print_exc()
            raise

    return wrapper


class NodeList(UserList, GenericNodesMixin):
    # NodeList doesn't have a previous nor a next
    # avoid common bug in shell by providing None
    next = None
    previous = None

    def __init__(self, initlist=None, parent=None, on_attribute=None):
        super(NodeList, self).__init__(initlist)
        self.parent = parent
        self.on_attribute = on_attribute

    @classmethod
    def from_fst(cls, node_list, parent=None, on_attribute=None):
        return cls(map(lambda x: Node.from_fst(x, parent=parent,
                                               on_attribute=on_attribute),
                       node_list),
                   parent=parent, on_attribute=on_attribute)

    def find(self, identifier, *args, **kwargs):
        for i in self.data:
            candidate = i.find(identifier, *args, **kwargs)
            if candidate is not None:
                return candidate
        return None

    def __getattr__(self, key):
        if key not in ALL_IDENTIFIERS:
            raise AttributeError(
                "%s instance has no attribute '%s' and '%s' is not a valid "
                "identifier of another node" % (self.__class__.__name__,
                                                key, key))

        return self.find(key)

    def __setitem__(self, key, value):
        self.data[key] = self.to_node_object(value, parent=self.parent,
                                             on_attribute=self.on_attribute)

    def find_iter(self, identifier, *args, **kwargs):
        for node in self.data:
            for matched_node in node.find_iter(identifier, *args, **kwargs):
                yield matched_node

    def find_all(self, identifier, *args, **kwargs):
        return NodeList(list(self.find_iter(identifier, *args, **kwargs)))

    findAll = find_all
    __call__ = find_all

    def find_by_path(self, path):
        path = Path.from_baron_path(self, path)
        return path.node if path else None

    def path(self):
        return Path(self)

    def fst(self):
        return [x.fst() for x in self.data]

    def dumps(self):
        return baron.dumps(self.fst())

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

    def _bytes_repr_html_(self):
        def __repr_html(self):
            # string addition is slow (and makes copies)
            yield b"<table>"
            yield b"<tr><th>Index</th><th>node</th></tr>"
            for num, item in enumerate(self):
                yield b"<tr>"
                yield b"<td>"
                yield str(num).encode("Utf-8")
                yield b"</td>"
                yield b"<td>"
                yield item._bytes_repr_html_() if hasattr(item, "_repr_html_") else str(item).encode("Utf-8")
                yield b"</td>"
                yield b"</tr>"
            yield b"</table>"

        return b''.join(__repr_html(self))

    def _repr_html_(self):
        return self._bytes_repr_html_().decode("Utf-8")

    def help(self, deep=2, with_formatting=False):
        for num, i in enumerate(self.data):
            sys.stdout.write(str(num) + " -----------------------------------------------------\n")
            i.help(deep=deep, with_formatting=with_formatting)

    def __help__(self, deep=2, with_formatting=False):
        return [x.__help__(deep=deep, with_formatting=with_formatting) for x in self.data]

    def copy(self):
        # XXX not very optimised but at least very simple
        return NodeList(map(Node.from_fst, self.fst()))

    def next_generator(self):
        # similary, NodeList will never have next items
        # trick to return an empty generator
        # I wonder if I should not raise instead :/
        return

    def previous_generator(self):
        # similary, NodeList will never have next items
        # trick to return an empty generator
        # I wonder if I should not raise instead :/
        return

    def apply(self, function):
        for el in self.data:
            function(el)
        return self

    def map(self, function):
        return NodeList([function(x) for x in self.data])

    def filter(self, function):
        return NodeList([x for x in self.data if function(x)])

    def filtered(self):
        return tuple([x for x in self.data if
                      not isinstance(x, (nodes.EndlNode, nodes.CommaNode, nodes.DotNode))])

    def _generate_nodes_in_rendering_order(self):
        previous = None
        for i in self:
            for j in self._iter_in_rendering_order(i):
                if j is previous:
                    continue
                previous = j
                yield j

    def get_absolute_bounding_box_of_attribute(self, index):
        if index >= len(self.data) or index < 0:
            raise IndexError()
        path = self.path().to_baron_path() + [index]
        return baron.path.path_to_bounding_box(self.root.fst(), path)

    def increase_indentation(self, number_of_spaces):
        previous = None
        done = set()
        for i in self.data:
            for node in i._generate_nodes_in_rendering_order():
                if node.type != "endl" and previous is not None and previous.type == "endl" and previous not in done:
                    previous.indent += number_of_spaces * " "
                    done.add(previous)
                previous = node

    def decrease_indentation(self, number_of_spaces):
        previous = None
        done = set()
        for i in self.data:
            for node in i._generate_nodes_in_rendering_order():
                if node.type != "endl" and previous is not None and previous.type == "endl" and previous not in done:
                    previous.indent = previous.indent[number_of_spaces:]
                    done.add(previous)
                previous = node


class Node(GenericNodesMixin):
    _other_identifiers = []
    _default_test_value = "value"
    first_formatting = None
    second_formatting = None
    third_formatting = None

    def __init__(self, fst, parent=None, on_attribute=None):
        self.init = True
        self.parent = parent
        self.on_attribute = on_attribute
        self._str_keys = ["type"]
        self._list_keys = []
        self._dict_keys = []
        self.type = fst["type"]

        for kind, key, _ in filter(lambda x: x[0] != "constant", self._render()):
            if kind == "key":
                if fst[key]:
                    setattr(self, key, Node.from_fst(fst[key], parent=self, on_attribute=key))
                else:
                    setattr(self, key, None)
                self._dict_keys.append(key)

            elif kind in ("bool", "string"):
                setattr(self, key, fst[key])
                self._str_keys.append(key)

            elif kind in ("list", "formatting"):
                setattr(self, key, NodeList.from_fst(fst[key], parent=self, on_attribute=key))
                self._list_keys.append(key)

            else:
                raise Exception(str((fst["type"], kind, key)))

        self.init = False

    @classmethod
    def from_fst(cls, node, parent=None, on_attribute=None):
        class_name = baron_type_to_redbaron_classname(node["type"])
        return getattr(nodes, class_name)(node, parent=parent, on_attribute=on_attribute)

    @property
    @display_property_atttributeerror_exceptions
    def next(self):
        in_list = self._get_list_attribute_is_member_off()

        if in_list is None:
            return None

        next_node = list(itertools.dropwhile(lambda x: x is not self, in_list))[1:]
        return next_node[0] if next_node else None

    @property
    @display_property_atttributeerror_exceptions
    def next_intuitive(self):
        next_ = self.next

        if next_ and next_.type == "ifelseblock":
            return next_.if_

        return next_

    @property
    @display_property_atttributeerror_exceptions
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
    @display_property_atttributeerror_exceptions
    def next_recursive(self):
        target = self
        while not target.next:
            if not target.parent:
                break
            target = target.parent
        return target.next

    def next_generator(self):
        in_list = self._get_list_attribute_is_member_off()

        if in_list is None:
            return None

        generator = itertools.dropwhile(lambda x: x is not self, in_list)
        next(generator)
        return generator

    @property
    @display_property_atttributeerror_exceptions
    def previous(self):
        in_list = self._get_list_attribute_is_member_off()

        if in_list is None:
            return None

        next_node = list(itertools.dropwhile(lambda x: x is not self, reversed(in_list)))[1:]
        return next_node[0] if next_node else None

    @property
    @display_property_atttributeerror_exceptions
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
    @display_property_atttributeerror_exceptions
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
    @display_property_atttributeerror_exceptions
    def previous_recursive(self):
        target = self
        while not target.previous:
            if not target.parent:
                break
            target = target.parent
        return target.previous

    def previous_generator(self):
        in_list = self._get_list_attribute_is_member_off()

        if in_list is None:
            return None

        generator = itertools.dropwhile(lambda x: x is not self, reversed(in_list))
        next(generator)
        return generator

    def get_indentation_node(self):
        if self.type == "endl":
            # by convention, an endl node will always have this indentation
            return None

        if self.previous_rendered is None:
            return None

        if self.previous_rendered.type == "endl":
            return self.previous_rendered

        return self.previous_rendered.get_indentation_node()

    @property
    @display_property_atttributeerror_exceptions
    def indentation(self):
        endl_node = self.get_indentation_node()
        return endl_node.indent if endl_node is not None else ""

    def indentation_node_is_direct(self):
        if self.previous_rendered and self.previous_rendered.type == "endl":
            return True

        return False

    def _get_list_attribute_is_member_off(self):
        """
        Return the list attribute of the parent from which this node is a
        member.

        If this node isn't in a list attribute, return None.
        """
        if self.parent is None:
            return None

        if self.on_attribute == "root":
            in_list = self.parent
        elif self.on_attribute is not None:
            if isinstance(self.parent, NodeList):
                in_list = getattr(self.parent.parent, self.on_attribute)
            else:
                in_list = getattr(self.parent, self.on_attribute)
        else:
            return None

        if isinstance(in_list, ProxyList):
            return in_list.node_list

        if not isinstance(in_list, NodeList):
            return None

        return in_list

    def __getattr__(self, key):
        if key.endswith("_") and key[:-1] in self._dict_keys + self._list_keys + self._str_keys:
            return getattr(self, key[:-1])

        if key != "value" and hasattr(self, "value") and isinstance(self.value, ProxyList) and hasattr(self.value, key):
            return getattr(self.value, key)

        if key not in ALL_IDENTIFIERS:
            raise AttributeError(
                "%s instance has no attribute '%s' and '%s' is not a valid identifier of another node" % (
                    self.__class__.__name__, key, key))

        return self.find(key)

    def find_iter(self, identifier, *args, **kwargs):
        if "recursive" in kwargs:
            recursive = kwargs["recursive"]
            kwargs = kwargs.copy()
            del kwargs["recursive"]
        else:
            recursive = True

        if self._node_match_query(self, identifier, *args, **kwargs):
            yield self

        if recursive:
            for (kind, key, _) in self._render():
                if kind == "key":
                    node = getattr(self, key)
                    if not isinstance(node, Node):
                        continue
                    for matched_node in node.find_iter(identifier, *args, **kwargs):
                        yield matched_node
                elif kind in ("list", "formatting"):
                    _nodes = getattr(self, key)
                    if isinstance(_nodes, ProxyList):
                        _nodes = _nodes.node_list
                    for node in _nodes:
                        for matched_node in node.find_iter(identifier, *args, **kwargs):
                            yield matched_node

    def find(self, identifier, *args, **kwargs):
        return next(self.find_iter(identifier, *args, **kwargs), None)

    def find_all(self, identifier, *args, **kwargs):
        return NodeList(list(self.find_iter(identifier, *args, **kwargs)))

    findAll = find_all
    __call__ = find_all

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

    def find_by_path(self, path):
        path = Path(self, path).node
        return path.node if path else None

    def path(self):
        return Path(self)

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
            'next_generator',
            'next_generator',
            'parent_find',
            'parent_find',
            'parse_code_block',
            'parse_decorators',
            'path',
            'path',
            'previous_generator',
            'previous_generator',
            'replace',
            'to_python',
        ])
        return [x for x in dir(self) if
                not x.startswith("_") and x not in not_helpers and inspect.ismethod(getattr(self, x))]

    def fst(self):
        to_return = {}
        for key in self._str_keys:
            to_return[key] = getattr(self, key)
        for key in self._list_keys:
            # Proxy Lists overload __iter__ for a better user interface
            if isinstance(getattr(self, key), ProxyList):
                to_return[key] = [node.fst() for node in getattr(self, key).node_list]
            else:
                to_return[key] = [node.fst() for node in getattr(self, key)]
        for key in self._dict_keys:
            if getattr(self, key) not in (None, "", [], {}):
                to_return[key] = getattr(self, key).fst()
            else:
                to_return[key] = {}
        return to_return

    def dumps(self):
        return baron.dumps(self.fst())

    def help(self, deep=2, with_formatting=False):
        if in_ipython():
            sys.stdout.write(help_highlight(self.__help__(deep=deep, with_formatting=with_formatting) + "\n"))
        else:
            sys.stdout.write(self.__help__(deep=deep, with_formatting=with_formatting) + "\n")

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
                getattr(self, key).__help__(deep=new_deep, with_formatting=with_formatting),
                "    ").lstrip() if getattr(self, key) else getattr(self, key)) for key in self._dict_keys if
                        "formatting" not in key]
            # need to do this otherwise I end up with stacked quoted list
            # example: value=[\'DottedAsNameNode(target=\\\'None\\\', as=\\\'False\\\', value=DottedNameNode(value=["NameNode(value=\\\'pouet\\\')"])]
            for key in filter(lambda x: "formatting" not in x, self._list_keys):
                to_join.append(("%s ->" % key))
                for i in getattr(self, key):
                    to_join.append(
                        "  * " + indent(i.__help__(deep=new_deep, with_formatting=with_formatting), "      ").lstrip())

        if deep and with_formatting:
            to_join += ["%s=%s" % (key, repr(getattr(self, key))) for key in self._str_keys if
                        key != "type" and "formatting" in key]
            to_join += ["%s=%s" % (key, getattr(self, key).__help__(deep=new_deep,
                                                                    with_formatting=with_formatting) if getattr(self,
                                                                                                                key) else getattr(
                self, key)) for key in self._dict_keys if "formatting" in key]

            for key in filter(lambda x: "formatting" in x, self._list_keys):
                to_join.append(("%s ->" % key))
                for i in getattr(self, key):
                    to_join.append(
                        "  * " + indent(i.__help__(deep=new_deep, with_formatting=with_formatting), "      ").lstrip())

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
            return python_highlight(self.dumps()).decode("Utf-8")
        else:
            return self.dumps()

    def _bytes_repr_html_(self):
        return python_html_highlight(self.dumps())

    def _repr_html_(self):
        return self._bytes_repr_html_().decode("Utf-8")

    def copy(self):
        # XXX not very optimised but at least very simple
        return Node.from_fst(self.fst())

    def __setattr__(self, name, value):
        if name == "init" or self.init:
            return super(Node, self).__setattr__(name, value)

        # we don't want to mess with "__class__" for example but convert "async_" to "async"
        if name.endswith("_") and not name.endswith("__"):
            name = name[:-1]

        # FIXME I'm pretty sure that Bool should also be put in the isinstance for cases like with_parenthesis/as
        if name in self._str_keys and not isinstance(value, (str, int)):
            value = str(value)

        elif name in self._dict_keys:
            value = self.to_node_object(value, self, name)

        elif name in self._list_keys:
            value = self.to_node_object_list(value, self, name)

        return super(Node, self).__setattr__(name, value)

    def _render(self):
        return nodes_rendering_order[self.type]

    def replace(self, new_node):
        new_node = self.to_node_object(new_node, parent=None, on_attribute=None, generic=True)
        self.__class__ = new_node.__class__  # YOLO
        self.__init__(new_node.fst(), parent=self.parent, on_attribute=self.on_attribute)

    def edit(self, editor=None):
        if editor is None:
            editor = os.environ.get("EDITOR", "nano")

        base_path = os.path.join("/tmp", "baron_%s" % os.getpid())
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        temp_file_path = os.path.join(base_path, str(id(self)))

        self_in_string = self.dumps()
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(self_in_string)

        os.system("%s %s" % (editor, temp_file_path))

        with open(temp_file_path, "r") as temp_file:
            result = temp_file.read()

        if result != self_in_string:
            self.replace(result)

    @property
    @display_property_atttributeerror_exceptions
    def index_on_parent(self):
        if not self.parent:
            return None

        if not isinstance(getattr(self.parent, self.on_attribute), (NodeList, ProxyList)):
            return None

        return getattr(self.parent, self.on_attribute).index(self)

    @property
    @display_property_atttributeerror_exceptions
    def index_on_parent_raw(self):
        if not self.parent:
            return None

        if not isinstance(getattr(self.parent, self.on_attribute), (NodeList, ProxyList)):
            return None

        if isinstance(getattr(self.parent, self.on_attribute), ProxyList):
            return getattr(self.parent, self.on_attribute).node_list.index(self)

        return getattr(self.parent, self.on_attribute).index(self)

    def _generate_nodes_in_rendering_order(self):
        previous = None
        for j in self._iter_in_rendering_order(self):
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
        self.get_indentation_node().indent += number_of_spaces * " "

    def decrease_indentation(self, number_of_spaces):
        self.get_indentation_node().indent = self.get_indentation_node().indent[:-len(number_of_spaces * " ")]

    def insert_before(self, value, offset=0):
        self.parent.insert(self.index_on_parent - offset, value)

    def insert_after(self, value, offset=0):
        self.parent.insert(self.index_on_parent + 1 + offset, value)


class CodeBlockNode(Node):
    def _string_to_node_list(self, string, parent, on_attribute):
        if on_attribute == "value":
            return self.parse_code_block(string, parent=parent, on_attribute=on_attribute)

        elif on_attribute.endswith("_formatting"):
            return super(CodeBlockNode, self)._string_to_node_list(string, parent, on_attribute)

        else:
            raise Exception("Unhandled case")

    def parse_code_block(self, string, parent, on_attribute):
        # remove heading blanks lines
        clean_string = re.sub("^ *\n", "", string) if "\n" in string else string
        indentation = len(re.search("^ *", clean_string).group())
        target_indentation = len(self.indentation) + 4

        # putting this in the string template will fail, need at least some indent
        if indentation == 0:
            clean_string = "    " + "\n    ".join(clean_string.split("\n"))
            clean_string = clean_string.rstrip()

        fst = baron.parse("def a():\n%s\n" % clean_string)[0]["value"]

        result = NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        # set indentation to the correct level
        indentation = len(result[0].indent)
        if indentation > target_indentation:
            result.decrease_indentation(indentation - target_indentation)
        elif indentation < target_indentation:
            result.increase_indentation(target_indentation - indentation)

        endl_base_node = Node.from_fst({'formatting': [], 'indent': '',
                                        'type': 'endl', 'value': '\n'},
                                       on_attribute=on_attribute,
                                       parent=parent)

        if (self.on_attribute == "root" and self.next) or \
                (not self.next and self.parent and self.parent.next):
            # I need to finish with 3 endl nodes
            if not all(map(lambda x: x.type == "endl", result[-1:])):
                result.append(endl_base_node.copy())
            elif not all(map(lambda x: x.type == "endl", result[-2:])):
                result.append(endl_base_node.copy())
                result.append(endl_base_node.copy())
            elif not all(map(lambda x: x.type == "endl", result[-3:])):
                result.append(endl_base_node.copy())
                result.append(endl_base_node.copy())
                result.append(endl_base_node.copy())
        elif self.next:
            # I need to finish with 2 endl nodes
            if not all(map(lambda x: x.type == "endl", result[-2:])):
                result.append(endl_base_node.copy())
            elif not all(map(lambda x: x.type == "endl", result[-3:])):
                result.append(endl_base_node.copy())
                result.append(endl_base_node.copy())

            result[-1].indent = self.indentation

        return result

    def __setattr__(self, key, value):
        super(CodeBlockNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, LineProxyList):
            setattr(self, "value", LineProxyList(self.value, on_attribute="value"))

        elif key == "decorators" and not isinstance(self.decorators, LineProxyList):
            setattr(self, "decorators", DecoratorsLineProxyList(self.decorators, on_attribute="decorators"))


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


class ElseAttributeNode(CodeBlockNode):
    def _get_last_member_to_clean(self):
        return self

    def _convert_input_to_one_indented_member(self, indented_type, string, parent, on_attribute):
        def remove_trailing_endl(node):
            if isinstance(node.value, ProxyList):
                while node.value.node_list[-1].type == "endl":
                    node.value.node_list.pop()
            else:
                while node.value[-1].type == "endl":
                    node.value.pop()

        if not string:
            last_member = self
            remove_trailing_endl(last_member)
            if isinstance(last_member.value, ProxyList):
                last_member.value.node_list.append(
                    nodes.EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=last_member, on_attribute="value"))
            else:
                last_member.value.append(
                    nodes.EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=last_member, on_attribute="value"))
            return ""

        if re.match(r"^\s*%s" % indented_type, string):

            # we've got indented text, let's deindent it
            if string.startswith((" ", "    ")):
                # assuming that the first spaces are the indentation
                indentation = len(re.search("^ +", string).group())
                string = re.sub("(\r?\n)%s" % (" " * indentation), "\\1", string)
                string = string.lstrip()

            node = Node.from_fst(baron.parse("try: pass\nexcept: pass\n%s" % string)[0][indented_type], parent=parent,
                                 on_attribute=on_attribute)
            node.value = self.parse_code_block(node.value.dumps(), parent=node, on_attribute="value")

        else:
            # XXX quite hackish way of doing this
            fst = {'first_formatting': [],
                   'second_formatting': [],
                   'type': indented_type,
                   'value': [{'type': 'pass'},
                             {'formatting': [],
                              'indent': '',
                              'type': 'endl',
                              'value': '\n'}]}

            node = Node.from_fst(fst, parent=parent, on_attribute=on_attribute)
            node.value = self.parse_code_block(string=string, parent=parent, on_attribute=on_attribute)

        # ensure that the node ends with only one endl token, we'll add more later if needed
        remove_trailing_endl(node)
        node.value.node_list.append(
            nodes.EndlNode({"type": "endl",
                            "indent": "",
                            "formatting": [],
                            "value": "\n"},
                           parent=node,
                           on_attribute="value"))

        last_member = self._get_last_member_to_clean()

        # XXX this risk to remove comments
        if self.next:
            remove_trailing_endl(last_member)
            if isinstance(last_member.value, ProxyList):
                last_member.value.node_list.append(
                    nodes.EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=last_member,
                                   on_attribute="value"))
            else:
                last_member.value.append(
                    nodes.EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=last_member,
                                   on_attribute="value"))

            if self.indentation:
                node.value.node_list.append(nodes.EndlNode(
                    {"type": "endl", "indent": self.indentation,
                     "formatting": [], "value": "\n"},
                    parent=node, on_attribute="value"))
            else:  # we are on root level and followed: we need 2 blanks lines after the node
                node.value.node_list.append(
                    nodes.EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=node, on_attribute="value"))
                node.value.node_list.append(
                    nodes.EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=node, on_attribute="value"))

        if isinstance(last_member.value, ProxyList):
            last_member.value.node_list[-1].indent = self.indentation
        else:
            last_member.value[-1].indent = self.indentation

        return node

    def _string_to_node(self, string, parent, on_attribute):
        if on_attribute != "else":
            return super(ElseAttributeNode, self)._string_to_node(string, parent=parent, on_attribute=on_attribute)

        return self._convert_input_to_one_indented_member("else", string, parent, on_attribute)

    def __setattr__(self, name, value):
        if name == "else_":
            name = "else"

        return super(ElseAttributeNode, self).__setattr__(name, value)


class IterableNode(Node):
    def __len__(self):
        return len(self.node_list)

    def __getitem__(self, key):
        if hasattr(self, "value") and isinstance(self.value, ProxyList):
            return self.value[key]

        raise TypeError("'%s' object does not support indexing" % self.__class__)

    def __getslice__(self, i, j):
        if hasattr(self, "value") and isinstance(self.value, ProxyList):
            return self.value.__getslice__(i, j)

        raise AttributeError("__getslice__")

    def __setitem__(self, key, value):
        if hasattr(self, "value") and isinstance(self.value, ProxyList):
            self.value[key] = value

        else:
            raise TypeError("'%s' object does not support item assignment" % self.__class__)

    def __setslice__(self, i, j, value):
        if hasattr(self, "value") and isinstance(self.value, ProxyList):
            return self.value.__setslice__(i, j, value)

        raise TypeError("'%s' object does not support slice setting" % self.__class__)

    def __delitem__(self, key):
        if hasattr(self, "value") and isinstance(self.value, ProxyList):
            del self.value[key]

        else:
            raise AttributeError("__delitem__")

    def __delslice__(self, i, j):
        if hasattr(self, "value") and isinstance(self.value, ProxyList):
            self.value.__delslice__(i, j)

        else:
            raise AttributeError("__delitem__")
