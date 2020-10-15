import re

from redbaron.syntax_highlight import python_html_highlight

import baron

from .base_nodes import (NODE_TYPE_MAPPING,
                         CodeBlockNode,
                         IfElseBlockSiblingNode,
                         IterableNode,
                         Node,
                         NodeList)
from .node_mixin import LiteralyEvaluableMixin
from .proxy_list import (CommaProxyList,
                         DotProxyList,
                         LineProxyList,
                         ProxyList)


class ArgumentGeneratorComprehensionNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "generators":
            fst = baron.parse("(x %s)" % value)[0]["generators"]
            return NodeList.from_fst(fst, parent=self.parent,
                                     on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def from_str(self, value, on_attribute=None):
        if on_attribute == "result":
            return self.from_fst(baron.parse("(%s for x in x)" % value)[0]["result"],
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class AssertNode(Node):
    third_formatting = None

    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            return self.from_fst(baron.parse("assert %s" % value)[0]["value"],
                                 on_attribute=on_attribute)

        elif on_attribute == "message":
            if value:
                self.third_formatting = [self.from_fst({"type": "space", "value": " "},
                                                       on_attribute=on_attribute)]
                return self.from_fst(baron.parse("assert plop, %s" % value)[0]["message"],
                                     on_attribute=on_attribute)

        raise Exception("Unhandled case")


class AssignmentNode(Node):
    _other_identifiers = ["assign"]
    annotation_first_formatting = None
    annotation_second_formatting = None

    def __setattr__(self, key, value):
        if key == "operator":
            if len(value) == 2 and value[1] == "=":
                value = value[0]
            elif len(value) == 1 and value == "=":
                value = ""
            elif value is None:
                value = ""
            elif len(value) not in (0, 1, 2):
                raise Exception("The value of the operator can only be a string of one or two char, for eg: '+', '+=', '=', ''")

        return super(AssignmentNode, self).__setattr__(key, value)

    def from_str(self, value, on_attribute=None):
        if on_attribute == "target":
            return self.from_fst(baron.parse("%s = a" % value)[0]["target"],
                                 on_attribute=on_attribute)

        elif on_attribute == "value":
            return self.from_fst(baron.parse("a = %s" % value)[0]["value"],
                                 on_attribute=on_attribute)

        elif on_attribute == "annotation":
            if not value.strip():
                self.annotation_first_formatting = []
                self.annotation_second_formatting = []
                return ""

            else:
                if not self.annotation_first_formatting:
                    self.annotation_first_formatting = [self.from_fst({"type": "space", "value": " "},
                                                                      on_attribute="return_annotation_first_formatting")]

                if not self.annotation_second_formatting:
                    self.annotation_second_formatting = [self.from_fst({"type": "space", "value": " "},
                                                                       on_attribute="return_annotation_first_formatting")]

                return self.from_fst(baron.parse("a: %s = a" % value)[0]["annotation"],
                                     on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class AssociativeParenthesisNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            return self.from_fst(baron.parse("(%s)" % value)[0]["value"],
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class AtomtrailersNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            return NodeList.from_fst(baron.parse("(%s)" % value)[0]["value"]["value"],
                                     parent=self.parent,
                                     on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super(AtomtrailersNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, DotProxyList):
            setattr(self, "value", DotProxyList(self.value))


class AwaitNode(Node):
    def from_str(self, string, on_attribute):
        if on_attribute == "value":
            return Node.from_fst(baron.parse("await %s" % string)[0]["value"],
                                 parent=self.parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class BinaryNode(Node, LiteralyEvaluableMixin):
    def __setattr__(self, key, value):
        if key == "value" and isinstance(value, str):
            assert baron.parse(value)[0]["type"] == "binary"

        return super(BinaryNode, self).__setattr__(key, value)


class BinaryOperatorNode(Node):
    def __setattr__(self, key, value):
        if key == "value" and isinstance(value, str):
            assert baron.parse("a %s b" % value)[0]["type"] == "binary_operator"

        return super(BinaryOperatorNode, self).__setattr__(key, value)

    def from_str(self, string, on_attribute):
        if on_attribute == "first":
            return Node.from_fst(baron.parse("%s + b" % string)[0]["first"],
                                 parent=self.parent, on_attribute=on_attribute)

        elif on_attribute == "second":
            return Node.from_fst(baron.parse("bb + %s" % string)[0]["second"],
                                 parent=self.parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class BinaryStringNode(Node, LiteralyEvaluableMixin):
    pass


class BinaryRawStringNode(Node, LiteralyEvaluableMixin):
    pass


class BooleanOperatorNode(Node):
    def __setattr__(self, key, value):
        if key == "value" and isinstance(value, str):
            assert baron.parse("a %s b" % value)[0]["type"] == "boolean_operator"

        return super(BooleanOperatorNode, self).__setattr__(key, value)

    def from_str(self, string, on_attribute):
        if on_attribute == "first":
            return Node.from_fst(baron.parse("%s and b" % string)[0]["first"],
                                 parent=self.parent, on_attribute=on_attribute)

        elif on_attribute == "second":
            return Node.from_fst(baron.parse("bb and %s" % string)[0]["second"],
                                 parent=self.parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class BreakNode(Node):
    pass


class CallNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            fst = baron.parse("a(%s)" % value)[0]["value"][1]["value"]
            return self.nodelist_from_fst(fst, on_attribute=on_attribute)

        raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        if key == "value" and not isinstance(value, CommaProxyList):
            value = CommaProxyList(value, on_attribute=key)

        super(CallNode, self).__setattr__(key, value)


class CallArgumentNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            code = "a(%s)" % value
            fst = baron.parse(code)[0]["value"][1]["value"][0]["value"]
            return self.from_fst(fst, on_attribute=on_attribute)

        if on_attribute == "target":
            code = "a(%s=b)" % value
            fst = baron.parse(code)[0]["value"][1]["value"][0]["target"]
            return self.from_fst(fst, on_attribute=on_attribute)

        raise Exception("Unhandled case")


class ClassNode(CodeBlockNode):
    _default_test_value = "name"
    inherit_from = None
    parenthesis = False

    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "decorators":
            return self.parse_decorators(value, on_attribute=on_attribute)

        if on_attribute == "inherit_from":
            fst = baron.parse("class a(%s): pass" % value)[0]["inherit_from"]
            return self.node_list_from_fst(fst, on_attribute=on_attribute)

        return super().nodelist_from_str(value, on_attribute)

    def __setattr__(self, key, value):
        if key == "inherit_from" and not isinstance(value, CommaProxyList):
            value = CommaProxyList(value, on_attribute=key)
            self.parenthesis = True

        super().__setattr__(key, value)

    def parse_decorators(self, value, on_attribute):
        assert value.lstrip()[0] == '@'

        def _detect_indentation(s):
            return s.index("@")
        indentation = _detect_indentation(value)

        code = "%s\n%sdef a(): pass" % (value, indentation)
        fst = baron.parse(code)[0]["decorators"]
        return self.nodelist_from_fst(fst, on_attribute=on_attribute)


class CommaNode(Node):
    def _default_fst(self):
        return {"type": "comma", "first_formatting": [],
                "second_formatting": [{"type": "space", "value": " "}]}


class CommentNode(Node):
    pass


class ComparisonNode(Node):
    def __setattr__(self, key, value):
        if key == "value" and isinstance(value, str):
            assert baron.parse("a %s b" % value)[0]["type"] == "comparison"

        return super(ComparisonNode, self).__setattr__(key, value)

    def from_str(self, value, on_attribute=None):
        if on_attribute == "first":
            return self.from_fst(baron.parse("%s > b" % value)[0]["first"],
                                 on_attribute=on_attribute)

        if on_attribute == "value":
            return self.from_fst(baron.parse("a %s b" % value)[0]["value"],
                                 on_attribute=on_attribute)

        if on_attribute == "second":
            return self.from_fst(baron.parse("bb > %s" % value)[0]["second"],
                                 on_attribute=on_attribute)

        raise Exception("Unhandled case")


class ComparisonOperatorNode(Node):
    pass


class ComplexNode(Node):
    pass


class ComprehensionIfNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            code = "[x for x in x if %s]" % value
            fst = baron.parse(code)[0]["generators"][0]["ifs"][0]["value"]
            return self.from_fst(fst, on_attribute=on_attribute)

        raise Exception("Unhandled case")


class ComprehensionLoopNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "ifs":
            return NodeList.from_fst(baron.parse("[x for x in x %s]" % value)[0]["generators"][0]["ifs"],
                                     on_attribute=on_attribute)

        else:
            return super().nodelist_from_str(value, on_attribute=on_attribute)

    def from_str(self, value, on_attribute=None):
        if on_attribute == "iterator":
            return Node.from_fst(baron.parse("[x for %s in x]" % value)[0]["generators"][0]["iterator"],
                                 parent=self.parent, on_attribute=on_attribute)

        elif on_attribute == "target":
            return Node.from_fst(baron.parse("[x for s in %s]" % value)[0]["generators"][0]["target"],
                                 parent=self.parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class ContinueNode(Node):
    pass


class DecoratorNode(Node):
    def from_str(self, string, on_attribute):
        if on_attribute == "value":
            return self.from_fst(baron.parse("@%s()\ndef a(): pass" % string)[0]["decorators"][0]["value"],
                                 on_attribute=on_attribute)

        elif on_attribute == "call":
            if string:
                return self.from_fst(baron.parse("@a%s\ndef a(): pass" % string)[0]["decorators"][0]["call"],
                                     on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class DefNode(CodeBlockNode):
    _other_identifiers = ["funcdef", "funcdef_"]
    _default_test_value = "name"
    return_annotation_first_formatting = None
    return_annotation_second_formatting = None
    async_formatting = None

    def from_str(self, string, on_attribute):
        if on_attribute == "return_annotation":
            if not string.strip():
                self.return_annotation_first_formatting = []
                self.return_annotation_second_formatting = []
                return ""

            else:
                fst = baron.parse("def a() -> %s: pass" % string)[0]["return_annotation"]

                if not self.return_annotation_first_formatting:
                    self.return_annotation_first_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="return_annotation_first_formatting", parent=self)]

                if not self.return_annotation_second_formatting:
                    self.return_annotation_second_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="return_annotation_second_formatting", parent=self)]

                return Node.from_fst(fst, on_attribute=on_attribute)

        return super().from_str(string, on_attribute)

    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "arguments":
            fst = baron.parse("def a(%s): pass" % string)[0]["arguments"]
            return NodeList.from_fst(fst, on_attribute=on_attribute)

        if on_attribute == "decorators":
            return self.parse_decorators(string, parent=parent, on_attribute=on_attribute)

        return super(DefNode, self).nodelist_from_str(string, parent, on_attribute)

    def __setattr__(self, key, value):
        super(DefNode, self).__setattr__(key, value)

        if key == "arguments" and not isinstance(self.arguments, CommaProxyList):
            setattr(self, "arguments", CommaProxyList(self.arguments, on_attribute="arguments"))

        elif key in ("async", "async_") and getattr(self, "async") and hasattr(self, "async_formatting") and not self.async_formatting:
            self.async_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="return_annotation_first_formatting", parent=self)]


class DefArgumentNode(Node):
    annotation_first_formatting = None
    annotation_second_formatting = None

    def from_str(self, string, on_attribute):
        if on_attribute == "value":
            return Node.from_fst(baron.parse("def a(b=%s): pass" % string)[0]["arguments"][0]["value"], parent=parent, on_attribute=on_attribute) if string else ""

        elif on_attribute == "target":
            return Node.from_fst(baron.parse("def a(%s=b): pass" % string)[0]["arguments"][0]["target"], parent=parent, on_attribute=on_attribute) if string else ""

        elif on_attribute == "annotation":
            if not self.annotation_first_formatting:
                self.annotation_first_formatting = [Node.from_fst({"type": "space", "value": " "},
                                                                  on_attribute="annotation_first_formatting")]

            if not self.annotation_second_formatting:
                self.annotation_second_formatting = [Node.from_fst({"type": "space", "value": " "},
                                                                   on_attribute="annotation_second_formatting")]

            return Node.from_fst(baron.parse("def a(a:%s=b): pass" % string)[0]["arguments"][0]["annotation"], parent=parent, on_attribute=on_attribute) if string else ""

        else:
            raise Exception("Unhandled case")


class DelNode(Node):
    def from_str(self, string, on_attribute):
        if on_attribute == "value":
            return Node.from_fst(baron.parse("del %s" % string)[0]["value"],
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class DictArgumentNode(Node):
    annotation_first_formatting = None
    annotation_second_formatting = None

    def from_str(self, string, on_attribute):
        if on_attribute == "value":
            return self.from_fst(baron.parse("a(**%s)" % string)[0]["value"][1]["value"][0]["value"],
                                 on_attribute=on_attribute)

        elif on_attribute == "annotation":
            if not self.annotation_first_formatting:
                self.annotation_first_formatting = [Node.from_fst({"type": "space", "value": " "},
                                                                  on_attribute="annotation_first_formatting")]

            if not self.annotation_second_formatting:
                self.annotation_second_formatting = [Node.from_fst({"type": "space", "value": " "},
                                                                   on_attribute="annotation_second_formatting")]

            return self.from_fst(baron.parse("def a(a:%s=b): pass" % string)[0]["arguments"][0]["annotation"],
                                 on_attribute=on_attribute) if string else ""

        else:
            raise Exception("Unhandled case")


class DictitemNode(Node):
    def from_str(self, string, on_attribute):
        if on_attribute == "value":
            return self.from_fst(baron.parse("{a: %s}" % string)[0]["value"][0]["value"],
                                 on_attribute=on_attribute)

        elif on_attribute == "key":
            return self.from_fst(baron.parse("{%s: a}" % string)[0]["value"][0]["key"],
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class DictNode(Node, LiteralyEvaluableMixin):
    def nodelist_from_str(self, value, on_attribute=None):
        fst = baron.parse("{%s}" % string)[0]["value"]
        return NodeList.from_fst(fst, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super(DictNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class DictComprehensionNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "generators":
            fst = baron.parse("{x %s}" % string)[0]["generators"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def from_str(self, string, on_attribute):
        if on_attribute == "result":
            return Node.from_fst(baron.parse("{%s for x in x}" % string)[0]["result"],
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class DotNode(Node):
    def _default_fst(self):
        return {"type": "dot",
                "first_formatting": [],
                "second_formatting": []}


class DottedAsNameNode(IterableNode):
    first_formatting = None
    second_formatting = None

    def __setattr__(self, key, value):
        if key == "target":
            if not (re.match(r'^[a-zA-Z_]\w*$', value) or value in ("", None)):
                raise Exception("The target of a dotted as name node can only be a 'name' or an empty string or None")

            if value:
                self.first_formatting = [self.from_fst({"type": "space", "value": " "},
                                                       on_attribute="delimiter")]
                self.second_formatting = [self.from_fst({"type": "space", "value": " "},
                                                        on_attribute="delimiter")]

        super(DottedAsNameNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, DotProxyList):
            setattr(self, "value", DotProxyList(self.value))

    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            fst = baron.parse("import %s" % string)[0]["value"][0]["value"]
            return NodeList.from_fst(fst, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class DottedNameNode(IterableNode):
    pass


class ElifNode(IfElseBlockSiblingNode):
    def from_str(self, string, on_attribute):
        if on_attribute == "test":
            return Node.from_fst(baron.parse("if %s: pass" % string)[0]["value"][0]["test"], on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class EllipsisNode(Node):
    pass


class ElseNode(IfElseBlockSiblingNode):
    @property
    def next_intuitive(self):
        if self.parent.type == "ifelseblock":
            return super(ElseNode, self).next_intuitive

        if self.parent.type == "try":
            if self.parent.finally_:
                return self.parent.finally_

            return self.parent.next

        if self.parent.type in ("for", "while"):
            return self.parent.next

        return None

    @property
    def previous_intuitive(self):
        if self.parent.type == "ifelseblock":
            return super(ElseNode, self).previous_intuitive

        if self.parent.type == "try":
            return self.parent.excepts[-1]

        if self.parent.type in ("for", "while"):
            return self.parent

        return None


class EndlNode(Node):
    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def _bytes_repr_html_(self):
        return python_html_highlight(self.__repr__())

    def _default_fst(self):
        return {"type": "endl", "formatting": [],
                "value": "\n", "indent": ""}


class ExceptNode(CodeBlockNode):
    @property
    def next_intuitive(self):
        next_ = self.next

        if next_:
            return next_

        if self.parent.else_:
            return self.parent.else_

        if self.parent.finally_:
            return self.parent.finally_

        if self.parent.next:
            return self.parent.next

        return None

    @property
    def previous_intuitive(self):
        previous_ = self.previous

        if previous_:
            return previous_

        return self.parent

    def __setattr__(self, key, value):
        if key == "delimiter":
            if value == ",":
                self.second_formatting = []
                self.third_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="delimiter", parent=self)]
            elif value == "as":
                self.second_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="delimiter", parent=self)]
                self.third_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="delimiter", parent=self)]
            elif value:
                raise Exception("Delimiters of an except node can only be 'as' or ',' (without spaces around it).")

        super(ExceptNode, self).__setattr__(key, value)

    def from_str(self, string, parent, on_attribute):
        if on_attribute == "exception":
            if string:
                self.first_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute=on_attribute, parent=parent)]
                return Node.from_fst(baron.parse("try: pass\nexcept %s: pass" % string)[0]["excepts"][0]["exception"], parent=parent, on_attribute=on_attribute)
            else:
                self.first_formatting = []
                self.delimiter = ""
                self.target = ""
                return ""

        elif on_attribute == "target":
            if not self.exception:
                raise Exception("Can't set a target to an exception node that doesn't have an exception set")

            if string:
                self.delimiter = "as"
                self.second_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute=on_attribute, parent=parent)]
                self.third_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute=on_attribute, parent=parent)]
                return Node.from_fst(baron.parse("try: pass\nexcept a as %s: pass" % string)[0]["excepts"][0]["target"], parent=parent, on_attribute=on_attribute)

            else:
                self.delimiter = ""
                self.second_formatting = []
                self.third_formatting = []
                return ""

        else:
            raise Exception("Unhandled case")


class ExecNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            return Node.from_fst(baron.parse("exec %s" % string)[0]["value"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "globals":
            if string:
                self.second_formatting = [{"type": "space", "value": " "}]
                self.third_formatting = [{"type": "space", "value": " "}]
                return Node.from_fst(baron.parse("exec a in %s" % string)[0]["globals"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "locals":
            if not self.globals:
                raise Exception("I can't set locals when globals aren't set.")

            if string:
                self.fifth_formatting = [{"type": "space", "value": " "}]
                return Node.from_fst(baron.parse("exec a in b, %s" % string)[0]["locals"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class FinallyNode(CodeBlockNode):
    @property
    def next_intuitive(self):
        return self.parent.next

    @property
    def previous_intuitive(self):
        if self.parent.else_:
            return self.parent.else_

        if self.parent.excepts:
            return self.parent.excepts[-1]

        return self.parent

    def __setattr__(self, key, value):
        super(FinallyNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, LineProxyList):
            setattr(self, "value", LineProxyList(self.value, on_attribute="value"))


class ElseAttributeNode(CodeBlockNode):
    def _get_last_member_to_clean(self):
        return self

    def _convert_input_to_one_indented_member(self, indented_type, string,
                                              parent, on_attribute):
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
                    EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=last_member, on_attribute="value"))
            else:
                last_member.value.append(
                    EndlNode({"type": "endl", "indent": "",
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
            EndlNode({"type": "endl",
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
                    EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=last_member,
                                   on_attribute="value"))
            else:
                last_member.value.append(
                    EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=last_member,
                                   on_attribute="value"))

            if self.indentation:
                node.value.node_list.append(EndlNode(
                    {"type": "endl", "indent": self.indentation,
                     "formatting": [], "value": "\n"},
                    parent=node, on_attribute="value"))
            else:  # we are on root level and followed: we need 2 blanks lines after the node
                node.value.node_list.append(
                    EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=node, on_attribute="value"))
                node.value.node_list.append(
                    EndlNode({"type": "endl", "indent": "",
                                    "formatting": [], "value": "\n"},
                                   parent=node, on_attribute="value"))

        if isinstance(last_member.value, ProxyList):
            last_member.value.node_list[-1].indent = self.indentation
        else:
            last_member.value[-1].indent = self.indentation

        return node

    def from_str(self, string, parent, on_attribute):
        if on_attribute != "else":
            return super(ElseAttributeNode, self).from_str(string, parent=parent, on_attribute=on_attribute)

        return self._convert_input_to_one_indented_member("else", string, parent, on_attribute)

    def __setattr__(self, name, value):
        if name == "else_":
            name = "else"

        return super(ElseAttributeNode, self).__setattr__(name, value)


class ForNode(ElseAttributeNode):
    @property
    def next_intuitive(self):
        if self.else_:
            return self.else_

        return self.next

    def __setattr__(self, key, value):
        super(ForNode, self).__setattr__(key, value)

        if key in ("async", "async_") and getattr(self, "async") and hasattr(self, "async_formatting") and not self.async_formatting:
            self.async_formatting = " "

    def from_str(self, string, parent, on_attribute):
        if on_attribute == "target":
            return Node.from_fst(baron.parse("for i in %s: pass" % string)[0]["target"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "iterator":
            return Node.from_fst(baron.parse("for %s in i: pass" % string)[0]["iterator"], parent=parent, on_attribute=on_attribute)

        else:
            return super(ForNode, self).from_str(string, parent, on_attribute)


class FloatNode(Node, LiteralyEvaluableMixin):
    pass


class FloatExponantNode(Node, LiteralyEvaluableMixin):
    pass


class FloatExponantComplexNode(Node, LiteralyEvaluableMixin):
    pass


class FromImportNode(Node):
    def names(self):
        """Return the list of new names imported

        For example:
            RedBaron("from qsd import a, c, e as f").names() == ['a', 'c', 'f']
        """
        return [x.target if getattr(x, "target", None) else x.value
                for x in self.targets
                if not isinstance(x, (LeftParenthesisNode, RightParenthesisNode))]

    def modules(self):
        """Return the list of the targets imported

        For example (notice 'e' instead of 'f'):
            RedBaron("from qsd import a, c, e as f").names() == ['a', 'c', 'e']
        """
        return [x.value for x in self.targets]

    def full_path_names(self):
        """Return the list of new names imported with the full module path

        For example (notice 'e' instead of 'f'):
            RedBaron("from qsd import a, c, e as f").names() == ['qsd.a', 'qsd.c', 'qsd.f']
        """
        return [self.value.dumps() + "." + (x.target if x.target else x.value)
                for x in self.targets
                if not isinstance(x, (LeftParenthesisNode, RightParenthesisNode))]

    def full_path_modules(self):
        """Return the list of the targets imported with the full module path

        For example (notice 'e' instead of 'f'):
            RedBaron("from qsd import a, c, e as f").names() == ['qsd.a', 'qsd.c', 'qsd.e']
        """
        return [self.value.dumps() + "." + x.value
                for x in self.targets
                if not isinstance(x, (LeftParenthesisNode, RightParenthesisNode))]

    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "targets":
            fst = baron.parse("from a import %s" % string)[0]["targets"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        if on_attribute == "value":
            fst = baron.parse("from %s import s" % string)[0]["value"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super(FromImportNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, DotProxyList):
            setattr(self, "value", DotProxyList(self.value, on_attribute="value"))

        if key == "targets" and not isinstance(self.targets, CommaProxyList):
            setattr(self, "targets", CommaProxyList(self.targets, on_attribute="targets"))


class GeneratorComprehensionNode(Node):
    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "generators":
            fst = baron.parse("(x %s)" % string)[0]["generators"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def from_str(self, string, parent, on_attribute):
        if on_attribute == "result":
            return Node.from_fst(baron.parse("(%s for x in x)" % string)[0]["result"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class GetitemNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            return Node.from_fst(baron.parse("a[%s]" % string)[0]["value"][1]["value"], parent=parent, on_attribute=on_attribute)


class GlobalNode(Node):
    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            fst = baron.parse("global %s" % string)[0]["value"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super(GlobalNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value, on_attribute="value"))


class HexaNode(Node, LiteralyEvaluableMixin):
    pass


class IfNode(IfElseBlockSiblingNode):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "test":
            return Node.from_fst(baron.parse("if %s: pass" % string)[0]["value"][0]["test"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class IfelseblockNode(Node):
    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute != "value":
            return super(IfelseblockNode, self).nodelist_from_str(string, parent=parent, on_attribute=on_attribute)

        string = string.rstrip()
        string += "\n"

        if self.next and self.on_attribute == "root":
            string += "\n\n"
        elif self.next:
            string += "\n"

        clean_string = re.sub("^ *\n", "", string) if "\n" in string else string
        indentation = len(re.search("^ *", clean_string).group())

        if indentation:
            string = "\n".join(map(lambda x: x[indentation:], string.split("\n")))

        result = NodeList.from_fst(baron.parse(string)[0]["value"], parent=parent, on_attribute=on_attribute)

        if self.indentation:
            result.increase_indentation(len(self.indentation))
            if self.next:
                result[-1].value.node_list[-1].indent = self.indentation

        return result


class ImportNode(Node):
    def modules(self):
        "return a list of string of modules imported"
        return [x.value.dumps()for x in self('dotted_as_name')]

    def names(self):
        "return a list of string of new names inserted in the python context"
        return [x.target if x.target else x.value.dumps() for x in self('dotted_as_name')]

    def nodelist_from_str(self, string, parent, on_attribute):
        fst = baron.parse("import %s" % string)[0]["value"]
        return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super(ImportNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value, on_attribute="value"))


class IntNode(Node, LiteralyEvaluableMixin):
    def fst(self):
        return {
            "type": "int",
            "value": self.value,
            "section": "number",
        }


class InterpolatedStringNode(Node, LiteralyEvaluableMixin):
    _other_identifiers = ["fstring"]


class InterpolatedRawStringNode(Node, LiteralyEvaluableMixin):
    _other_identifiers = ["raw_fstring"]


class KwargsOnlyMarkerNode(Node):
    pass


class LambdaNode(Node):
    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "arguments":
            self.first_formatting = [{"type": "space", "value": " "}] if string else []
            fst = baron.parse("lambda %s: x" % string)[0]["arguments"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        else:
            return super(DefNode, self).nodelist_from_str(string, parent, on_attribute)

    def from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            return Node.from_fst(baron.parse("lambda: %s" % string)[0]["value"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super(LambdaNode, self).__setattr__(key, value)

        if key == "arguments" and not isinstance(self.arguments, CommaProxyList):
            setattr(self, "arguments", CommaProxyList(self.arguments, on_attribute="arguments"))


class LeftParenthesisNode(Node):
    pass


class ListArgumentNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            return Node.from_fst(baron.parse("lambda *%s: x" % string)[0]["arguments"][0]["value"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "annotation":
            if not self.annotation_first_formatting:
                self.annotation_first_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="annotation_first_formatting", parent=self)]

            if not self.annotation_second_formatting:
                self.annotation_second_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="annotation_second_formatting", parent=self)]

            return Node.from_fst(baron.parse("def a(a:%s=b): pass" % string)[0]["arguments"][0]["annotation"], parent=parent, on_attribute=on_attribute) if string else ""

        else:
            raise Exception("Unhandled case")


class ListComprehensionNode(Node):
    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "generators":
            fst = baron.parse("[x %s]" % string)[0]["generators"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def from_str(self, string, parent, on_attribute):
        if on_attribute == "result":
            return Node.from_fst(baron.parse("[%s for x in x]" % string)[0]["result"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class ListNode(Node, LiteralyEvaluableMixin):
    def nodelist_from_str(self, string, parent, on_attribute):
        fst = baron.parse("[%s]" % string)[0]["value"]
        return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super(ListNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class LongNode(Node, LiteralyEvaluableMixin):
    pass


class NameNode(Node, LiteralyEvaluableMixin):
    pass


class TypedNameNode(Node):
    pass


class NameAsNameNode(Node):
    def __setattr__(self, key, value):
        if key == "target":
            if not (re.match(r'^[a-zA-Z_]\w*$', value) or value in ("", None)):
                raise Exception("The target of a name as name node can only be a 'name' or an empty string or None")

            if value:
                self.first_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="delimiter", parent=self)]
                self.second_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="delimiter", parent=self)]

        elif key == "value":
            if not (re.match(r'^[a-zA-Z_]\w*$', value) or value in ("", None)):
                raise Exception("The value of a name as name node can only be a 'name' or an empty string or None")

        return super(NameAsNameNode, self).__setattr__(key, value)


class NonlocalNode(Node):
    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            fst = baron.parse("global %s" % string)[0]["value"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super(NonlocalNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value, on_attribute="value"))


class OctaNode(Node, LiteralyEvaluableMixin):
    pass


class PassNode(Node):
    pass


class PrintNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "destination":
            if string and not self.value:
                self.formatting = [{"type": "space", "value": " "}]
                return Node.from_fst(baron.parse("print >>%s" % string)[0]["destination"], parent=parent, on_attribute=on_attribute)

            elif string and self.value:
                self.formatting = [{"type": "space", "value": " "}]
                result = Node.from_fst(baron.parse("print >>%s" % string)[0]["destination"], parent=parent, on_attribute=on_attribute)
                if len(self.value.node_list) and not self.value.node_list[0].type == "comma":
                    self.value = NodeList([Node.from_fst({"type": "comma", "second_formatting": [{"type": "space", "value": " "}], "first_formatting": []}, parent=parent, on_attribute=on_attribute)]) + self.value
                return result

            elif self.value.node_list and self.value.node_list[0].type == "comma":
                self.formatting = [{"type": "space", "value": " "}]
                self.value = self.value.node_list[1:]

            else:
                self.formatting = []

        else:
            raise Exception("Unhandled case")


    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            if string:
                self.formatting = [{"type": "space", "value": " "}]

                fst = baron.parse(("print %s" if not self.destination else "print >>a, %s") % string)[0]["value"]
                return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)
            else:
                self.formatting = [] if not string and not self.destination else [{"type": "space", "value": " "}]
                return NodeList()

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super(PrintNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class RaiseNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            self.first_formatting = [{"type": "space", "value": " "}] if string else []
            if string:
                return Node.from_fst(baron.parse("raise %s" % string)[0]["value"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "instance":
            if not self.value:
                raise Exception("Can't set instance if there is not value")

            if string:
                self.third_formatting = [{"type": "space", "value": " "}]
                if not self.comma_or_from:
                    self.comma_or_from = ","
                return Node.from_fst(baron.parse("raise a, %s" % string)[0]["instance"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "traceback":
            if not self.instance:
                raise Exception("Can't set traceback if there is not instance")

            if string:
                self.fifth_formatting = [{"type": "space", "value": " "}]
                return Node.from_fst(baron.parse("raise a, b, %s" % string)[0]["traceback"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        current = getattr(self, "comma_or_from", None)

        super(RaiseNode, self).__setattr__(key, value)

        if key == "comma_or_from":
            if value == current:
                return

            if value == "from":
                self.second_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="second_formatting", parent=self)]
                self.third_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="third_formatting", parent=self)]

            elif value == ",":
                self.second_formatting = []
                self.third_formatting = [Node.from_fst({"type": "space", "value": " "}, on_attribute="third_formatting", parent=self)]



class RawStringNode(Node, LiteralyEvaluableMixin):
    pass


class RightParenthesisNode(Node):
    pass


class ReprNode(Node):
    def nodelist_from_str(self, string, parent, on_attribute):
        fst = baron.parse("`%s`" % string)[0]["value"]
        return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super(ReprNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class ReturnNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            self.formatting = [{"type": "space", "value": " "}] if string else []
            if string:
                return Node.from_fst(baron.parse("return %s" % string)[0]["value"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class SemicolonNode(Node):
    pass


class SetNode(Node):
    def nodelist_from_str(self, string, parent, on_attribute):
        fst = baron.parse("{%s}" % string)[0]["value"]
        return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super(SetNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class SetComprehensionNode(Node):
    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "generators":
            fst = baron.parse("{x %s}" % string)[0]["generators"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def from_str(self, string, parent, on_attribute):
        if on_attribute == "result":
            return Node.from_fst(baron.parse("{%s for x in x}" % string)[0]["result"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class SliceNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "lower":
            if string:
                return Node.from_fst(baron.parse("a[%s:]" % string)[0]["value"][1]["value"]["lower"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "upper":
            if string:
                return Node.from_fst(baron.parse("a[:%s]" % string)[0]["value"][1]["value"]["upper"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "step":
            self.has_two_colons = bool(string)
            if string:
                return Node.from_fst(baron.parse("a[::%s]" % string)[0]["value"][1]["value"]["step"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class SpaceNode(Node):
    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def _default_fst(self):
        return {"type": "space", "first_formatting": [],
                "second_formatting": [{"type": "space", "value": " "}]}


class StandaloneAnnotationNode(Node):
    pass


class StarExpressionNode(Node):
    pass


class StarNode(Node):
    pass


class StringNode(Node, LiteralyEvaluableMixin):
    pass


class StringChainNode(Node, LiteralyEvaluableMixin):
    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            fst = baron.parse("a = %s" % string)[0]["value"]["value"]
            return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class TernaryOperatorNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "first":
            return Node.from_fst(baron.parse("%s if b else c" % string)[0]["first"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "second":
            return Node.from_fst(baron.parse("a if b else %s" % string)[0]["second"], parent=parent, on_attribute=on_attribute)

        elif on_attribute == "value":
            return Node.from_fst(baron.parse("a if %s else s" % string)[0]["value"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class TryNode(ElseAttributeNode):
    @property
    def next_intuitive(self):
        if self.excepts:
            return self.excepts[0]

        if self.finally_:
            return self.finally_

        raise Exception("incoherent state of TryNode, try should be followed either by except or finally")

    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute != "excepts":
            return super(TryNode, self).nodelist_from_str(string, parent=parent, on_attribute=on_attribute)

        clean_string = re.sub("^ *\n", "", string) if "\n" in string else string
        indentation = len(re.search("^ *", clean_string).group())

        if indentation:
            string = "\n".join(map(lambda x: x[indentation:], string.split("\n")))

        string = string.rstrip()
        string += "\n"

        if self.next and self.on_attribute == "root":
            string += "\n\n"
        elif self.next:
            string += "\n"

        result = NodeList.from_fst(baron.parse("try:\n pass\n%sfinally:\n pass" % string)[0]["excepts"], parent=parent, on_attribute=on_attribute)

        if self.indentation:
            result.increase_indentation(len(self.indentation))
            if self._get_last_member_to_clean().type != "except":
                # assume that this is an endl node, this might break
                result[-1].value.node_list[-1].indent = self.indentation
            elif self.next:
                result[-1].value.node_list[-1].indent = self.indentation

        return result

    def from_str(self, string, parent, on_attribute):
        if on_attribute == "finally":
            return self._convert_input_to_one_indented_member("finally", string, parent, on_attribute)

        else:
            return super(TryNode, self).from_str(string, parent=parent, on_attribute=on_attribute)

    def __setattr__(self, name, value):
        if name == "finally_":
            name = "finally"

        return super(TryNode, self).__setattr__(name, value)

    def _get_last_member_to_clean(self):
        if self.finally_:
            return self.finally_
        if self.else_:
            return self.else_
        return self.excepts[-1]

    def __getattr__(self, name):
        if name == "finally_":
            return getattr(self, "finally")

        return super(TryNode, self).__getattr__(name)


class TupleNode(Node, LiteralyEvaluableMixin):
    def nodelist_from_str(self, string, parent, on_attribute):
        fst = baron.parse("(%s)" % string)[0]["value"]

        # I assume that I've got an AssociativeParenthesisNode here instead of a tuple
        # because string is only one single element
        if not isinstance(fst, list):
            fst = baron.parse("(%s,)" % string)[0]["value"]

        return NodeList.from_fst(fst, parent=parent, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super(TupleNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class UnicodeStringNode(Node, LiteralyEvaluableMixin):
    pass


class UnicodeRawStringNode(Node, LiteralyEvaluableMixin):
    pass


class UnitaryOperatorNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "target":
            return Node.from_fst(baron.parse("-%s" % string)[0]["target"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class YieldNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            self.formatting = [{"type": "space", "value": " "}] if string else []
            if string:
                return Node.from_fst(baron.parse("yield %s" % string)[0]["value"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class YieldFromNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            return Node.from_fst(baron.parse("yield from %s" % string)[0]["value"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class YieldAtomNode(Node):
    def from_str(self, string, parent, on_attribute):
        if on_attribute == "value":
            self.second_formatting = [{"type": "space", "value": " "}] if string else []
            if string:
                return Node.from_fst(baron.parse("yield %s" % string)[0]["value"], parent=parent, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class WhileNode(ElseAttributeNode):
    @property
    def next_intuitive(self):
        if self.else_:
            return self.else_

        return self.next

    def from_str(self, string, parent, on_attribute):
        if on_attribute == "test":
            return Node.from_fst(baron.parse("while %s: pass" % string)[0]["test"], parent=parent, on_attribute=on_attribute)

        else:
            return super(WhileNode, self).from_str(string, parent, on_attribute)


    def __setattr__(self, key, value):
        super(WhileNode, self).__setattr__(key, value)

        if key == "value" and not isinstance(self.value, LineProxyList):
            setattr(self, "value", LineProxyList(self.value, on_attribute="value"))


class WithContextItemNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            return self.from_fst(baron.parse("with %s: pass" % value)[0]["contexts"][0]["value"],
                                 on_attribute=on_attribute)

        elif on_attribute == "as":
            if value:
                self.first_formatting = [{"type": "space", "value": " "}]
                self.second_formatting = [{"type": "space", "value": " "}]
                return self.from_fst(baron.parse("with a as %s: pass" % value)[0]["contexts"][0]["as"],
                                     on_attribute=on_attribute)
            self.first_formatting = []
            self.second_formatting = []
            return ""

        raise Exception("Unhandled case")

    def __getattr__(self, name):
        if name == "as_":
            return getattr(self, "as")

        return super(WithContextItemNode, self).__getattr__(name)

    def __setattr__(self, name, value):
        if name == "as_":
            name = "as"

        return super(WithContextItemNode, self).__setattr__(name, value)


class WithNode(CodeBlockNode):
    async_formatting = None

    def nodelist_from_str(self, string, parent, on_attribute):
        if on_attribute == "contexts":
            return NodeList.from_fst(baron.parse("with %s: pass" % string)[0]["contexts"], parent=parent, on_attribute=on_attribute)

        else:
            return super(WithNode, self).nodelist_from_str(string, parent, on_attribute)

    def __setattr__(self, key, value):
        super(WithNode, self).__setattr__(key, value)

        if key == "contexts" and not isinstance(self.contexts, CommaProxyList):
            setattr(self, "contexts", CommaProxyList(self.contexts, on_attribute="contexts"))

        if key in ("async", "async_") and getattr(self, "async") and hasattr(self, "async_formatting") and not self.async_formatting:
            self.async_formatting = " "


class EmptyLine(Node):
    def _default_fst(self):
        return {"type": "space", "value": ""}


NODE_TYPE_MAPPING.update({
    'def': DefNode,
    'class': ClassNode,
    'with': WithNode,
})
