import re

import baron

from .base_nodes import (CodeBlockNode,
                         IfElseBlockSiblingNode,
                         IterableNode,
                         Node,
                         NodeList)
from .node_mixin import (AnnotationMixin,
                         DecoratorsMixin,
                         LiteralyEvaluableMixin,
                         ReturnAnnotationMixin)
from .node_property import (NodeListProperty,
                            NodeProperty,
                            conditional_formatting_property,
                            nodelist_property)
from .proxy_list import (CommaProxyList,
                         DotProxyList,
                         LineProxyList,
                         ProxyList)


class ArgumentGeneratorComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse("(x %s)" % value)[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse("(%s for x in x)" % value)[0]["result"]


class AssertNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("assert %s" % value)[0]["value"]

    @NodeProperty
    def message(self, value):
        return baron.parse("assert plop, %s" % value)[0]["message"]

    @conditional_formatting_property(NodeList, [" "], [])
    def third_formatting(self):
        return self.message


class AssignmentNode(Node, AnnotationMixin):
    _other_identifiers = ["assign"]

    @NodeProperty
    def operator(self, value):
        if len(value) == 2 and value[1] == "=":
            value = value[0]
        elif len(value) == 1 and value == "=":
            value = ""
        elif value is None:
            value = ""
        elif len(value) not in (0, 1, 2):
            raise Exception("The value of the operator can only be a "
                            "string of one or two char, for "
                            "eg: '+', '+=', '=', ''")

        return baron.parse(value)[0]

    @NodeProperty
    def target(self, value):
        return baron.parse("%s = a" % value)[0]["target"]

    @NodeProperty
    def value(self, value):
        return baron.parse("a = %s" % value)[0]["value"]


class AssociativeParenthesisNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("(%s)" % value)[0]["value"]


class AtomtrailersNode(Node):
    @nodelist_property(DotProxyList)
    def value(self, value):
        return baron.parse("(%s)" % value)[0]["value"]["value"]


class AwaitNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("await %s" % value)[0]["value"]


class BinaryNode(Node, LiteralyEvaluableMixin):
    value = NodeProperty()


class BinaryOperatorNode(Node):
    @NodeProperty
    def first(self, value):
        return baron.parse("%s + b" % value)[0]["first"]

    @NodeProperty
    def second(self, value):
        return baron.parse("bb + %s" % value)[0]["second"]


class BinaryStringNode(Node, LiteralyEvaluableMixin):
    pass


class BinaryRawStringNode(Node, LiteralyEvaluableMixin):
    pass


class BooleanOperatorNode(Node):
    @NodeProperty
    def first(self, value):
        return baron.parse("%s and b" % value)[0]["first"]

    @NodeProperty
    def second(self, value):
        return baron.parse("bb and %s" % value)[0]["second"]


class BreakNode(Node):
    pass


class CallNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse("a(%s)" % value)[0]["value"][1]["value"]


class CallArgumentNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("a(%s)" % value)[0]["value"][1]["value"][0]["value"]

    @NodeProperty
    def target(self, value):
        code = "a(%s=b)" % value
        return baron.parse(code)[0]["value"][1]["value"][0]["target"]


class ClassNode(CodeBlockNode, DecoratorsMixin):
    _default_test_value = "name"
    parenthesis = False

    @nodelist_property(CommaProxyList)
    def inherit_from(self, value):
        return baron.parse("class a(%s): pass" % value)[0]["inherit_from"]

    @inherit_from.after_set
    def inherit_from_after_set(self, value):
        self.parenthesis = bool(value)


class CommaNode(Node):
    def _default_fst(self):
        return {"type": "comma", "first_formatting": [],
                "second_formatting": [{"type": "space", "value": " "}]}


class CommentNode(Node):
    pass


class ComparisonNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("a %s b" % value)[0]["value"]

    @NodeProperty
    def first(self, value):
        return baron.parse("%s > b" % value)[0]["first"]

    @NodeProperty
    def second(self, value):
        return baron.parse("bb > %s" % value)[0]["second"]


class ComparisonOperatorNode(Node):
    pass


class ComplexNode(Node):
    pass


class ComprehensionIfNode(Node):
    @NodeProperty
    def value(self, value):
        code = "[x for x in x if %s]" % value
        return baron.parse(code)[0]["generators"][0]["ifs"][0]["value"]


class ComprehensionLoopNode(Node):
    @nodelist_property(NodeList)
    def ifs(self, value):
        code = "[x for x in x %s]" % value
        return baron.parse(code)[0]["generators"][0]["ifs"]

    @NodeProperty
    def iterator(self, value):
        code = "[x for %s in x]" % value
        return baron.parse(code)[0]["generators"][0]["iterator"]

    @NodeProperty
    def target(self, value):
        code = "[x for s in %s]" % value
        return baron.parse(code)[0]["generators"][0]["target"]


class ContinueNode(Node):
    pass


class DecoratorNode(Node):
    @NodeProperty
    def value(self, value):
        code = "@%s()\ndef a(): pass" % value
        return baron.parse(code)[0]["decorators"][0]["value"]

    @NodeProperty
    def call(self, value):
        return baron.parse("@a%s\ndef a(): pass" % value)


class DefNode(CodeBlockNode, DecoratorsMixin, ReturnAnnotationMixin):
    _other_identifiers = ["funcdef", "funcdef_"]
    _default_test_value = "name"

    @conditional_formatting_property(NodeList, [" "], [])
    def async_formatting(self):
        return self.async

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @nodelist_property(CommaProxyList)
    def arguments(self, value):
        return baron.parse("def a(%s): pass" % value)[0]["arguments"]


class DefArgumentNode(Node, AnnotationMixin):
    @NodeProperty
    def value(self, value):
        code = "def a(b=%s): pass" % value
        return baron.parse(code)[0]["arguments"][0]["value"]

    @NodeProperty
    def target(self, value):
        code = "def a(%s=b): pass" % value
        return baron.parse(code)[0]["arguments"][0]["target"]


class DelNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("del %s" % value)[0]["value"]


class DictArgumentNode(Node, AnnotationMixin):
    @NodeProperty
    def value(self, value):
        code = "a(**%s)" % value
        return baron.parse(code)[0]["value"][1]["value"][0]["value"]


class DictitemNode(Node):
    @NodeProperty
    def value(self, value):
        code = "{a: %s}" % value
        return baron.parse(code)[0]["value"][0]["value"]

    @NodeProperty
    def key(self, value):
        code = "{%s: a}" % value
        return baron.parse(code)[0]["value"][0]["key"]


class DictNode(Node, LiteralyEvaluableMixin):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        code = "{%s}" % value
        return baron.parse(code)[0]["value"]


class DictComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse("{x %s}" % value)[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse("{%s for x in x}" % value)[0]["result"]


class DotNode(Node):
    def _default_fst(self):
        return {"type": "dot", "first_formatting": [], "second_formatting": []}


class DottedAsNameNode(IterableNode):
    @nodelist_property(DotProxyList)
    def value(self, value):
        code = "import %s" % value
        return baron.parse(code)[0]["value"][0]["value"]

    @NodeProperty
    def target(self, value):
        if not (re.match(r'^[a-zA-Z_]\w*$', value) or value in ("", None)):
            raise Exception("The target of a dotted as name node can only "
                            "be a 'name' or an empty string or None")
        return baron.parse(value)[0]

    @conditional_formatting_property(NodeList, [" "], [])
    def first_formatting(self):
        return self.target

    @conditional_formatting_property(NodeList, [" "], [])
    def second_formatting(self):
        return self.target


class DottedNameNode(IterableNode):
    pass


class ElifNode(IfElseBlockSiblingNode):
    @NodeProperty
    def test(self, value):
        code = "if %s: pass" % value
        return baron.parse(code)[0]["value"][0]["test"]


class EllipsisNode(Node):
    pass


class ElseNode(IfElseBlockSiblingNode):
    @property
    def next_intuitive(self):
        if self.parent.type == "ifelseblock":
            return super().next_intuitive

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
            return super().previous_intuitive

        if self.parent.type == "try":
            return self.parent.excepts[-1]

        if self.parent.type in ("for", "while"):
            return self.parent

        return None


class EndlNode(Node):
    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def _default_fst(self):
        return {"type": "endl", "formatting": [],
                "value": "\n", "indent": ""}


class ExceptNode(CodeBlockNode):
    @NodeProperty
    def target(self, value):
        if not self.exception:
            raise Exception("Can't set a target to an exception node "
                            "that doesn't have an exception set")

        code = "try: pass\nexcept a as %s: pass" % value
        return baron.parse(code)[0]["excepts"][0]["target"]

    @conditional_formatting_property(NodeList, [" "], [])
    def first_formatting(self):
        return self.exception

    @conditional_formatting_property(NodeList, [" "], [])
    def second_formatting(self):
        return self.target

    @conditional_formatting_property(NodeList, [" "], [])
    def third_formatting(self):
        return self.target

    @property
    def delimiter(self):
        try:
            return self._delimiter
        except AttributeError:
            return "as" if self.target else ""

    @NodeProperty
    def exception(self, value):
        code = "try: pass\nexcept %s: pass" % value
        return baron.parse(code)[0]["excepts"][0]["exception"]

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


class ExecNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("exec %s" % value)[0]["value"]

    @NodeProperty
    def locals(self, value):
        if not self.globals:
            raise Exception("I can't set locals when globals aren't set.")
        return baron.parse("exec a in b, %s" % value)[0]["locals"]

    @conditional_formatting_property(NodeList, [" "], [])
    def second_formatting(self):
        return self.globals

    @conditional_formatting_property(NodeList, [" "], [])
    def third_formatting(self):
        return self.globals

    @conditional_formatting_property(NodeList, [" "], [])
    def fifth_formatting(self):
        return self.globals


class FinallyNode(CodeBlockNode):
    value = NodeListProperty(LineProxyList)

    @property
    def next_intuitive(self):
        return self.parent.next

    @property
    def previous_intuitive(self):
        if self.parent.find("else"):
            return self.parent.find("else")

        if self.parent.excepts:
            return self.parent.excepts[-1]

        return self.parent


class ElseAttributeNode(CodeBlockNode):
    def _get_last_member_to_clean(self):
        return self

    def _convert_input_to_one_indented_member(self, indented_type, value,
                                              on_attribute):
        def remove_trailing_endl(node):
            if isinstance(node.value, ProxyList):
                while node.value.node_list[-1].type == "endl":
                    node.value.node_list.pop()
            else:
                while node.value[-1].type == "endl":
                    node.value.pop()

        if not value:
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

        if re.match(r"^\s*%s" % indented_type, value):

            # we've got indented text, let's deindent it
            if value.startswith((" ", "    ")):
                # assuming that the first spaces are the indentation
                indentation = len(re.search("^ +", value).group())
                value = re.sub("(\r?\n)%s" % (" " * indentation), "\\1", value)
                value = value.lstrip()

            code = "try: pass\nexcept: pass\n%s" % value
            fst = baron.parse(code)[0][indented_type]
            node = self.from_fst(fst, on_attribute=on_attribute)
            node.value = self.parse_code_block(node.value.dumps(), parent=node,
                                               on_attribute="value")

        else:
            # quite hackish way of doing this
            fst = {'first_formatting': [],
                   'second_formatting': [],
                   'type': indented_type,
                   'value': [{'type': 'pass'},
                             {'formatting': [],
                              'indent': '',
                              'type': 'endl',
                              'value': '\n'}]}

            node = self.from_fst(fst, on_attribute=on_attribute)
            node.value = self.parse_code_block(value,
                                               on_attribute=on_attribute)

        # ensure that the node ends with only one endl token, we'll add more later if needed
        remove_trailing_endl(node)
        node.value.node_list.append(
            EndlNode({"type": "endl", "indent": "",
                      "formatting": [], "value": "\n"},
                     parent=node, on_attribute="value"))

        last_member = self._get_last_member_to_clean()

        # risk to remove comments
        if self.next:
            remove_trailing_endl(last_member)
            last_member.value.node_list.append(
                EndlNode({"type": "endl", "indent": "",
                          "formatting": [], "value": "\n"},
                         parent=last_member, on_attribute="value"))

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

    def from_str(self, value, on_attribute=None):
        if on_attribute != "else":
            return super().from_str(value, on_attribute=on_attribute)

        return self._convert_input_to_one_indented_member("else", value,
                                                          on_attribute=on_attribute)


class ForNode(ElseAttributeNode):
    @conditional_formatting_property(NodeList, [" "], [])
    def async_formatting(self):
        return self.async

    @NodeProperty()
    def target(self, value):
        return baron.parse("for i in %s: pass" % value)[0]["target"]

    @NodeProperty()
    def iterator(self, value):
        return baron.parse("for %s in i: pass" % value)[0]["iterator"]

    @property
    def next_intuitive(self):
        if self.else_:
            return self.else_

        return self.next


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

    @nodelist_property(CommaProxyList)
    def targets(self, value):
        return baron.parse("from a import %s" % value)[0]["targets"]

    @nodelist_property(DotProxyList)
    def value(self, value):
        return baron.parse("from %s import s" % value)[0]["value"]


class GeneratorComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse("(x %s)" % value)[0]["generators"]

    @NodeProperty()
    def result(self, value):
        return baron.parse("(%s for x in x)" % value)[0]["result"]


class GetitemNode(Node):
    @NodeProperty()
    def value(self, value):
        return baron.parse("a[%s]" % value)[0]["value"][1]["value"]


class GlobalNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse("global %s" % value)[0]["value"]


class HexaNode(Node, LiteralyEvaluableMixin):
    pass


class IfNode(IfElseBlockSiblingNode):
    @NodeProperty()
    def test(self, value):
        return baron.parse("if %s: pass" % value)[0]["value"][0]["test"]


class IfelseblockNode(CodeBlockNode):
    value = nodelist_property(NodeList)

    # def nodelist_from_str(self, value, on_attribute=None):
    #     value = value.rstrip()
    #     value += "\n"

    #     if self.next and self.on_attribute == "root":
    #         value += "\n\n"
    #     elif self.next:
    #         value += "\n"

    #     clean_value = re.sub("^ *\n", "", value) if "\n" in value else value
    #     indentation = len(re.search("^ *", clean_value).group())

    #     if indentation:
    #         value = "\n".join(map(lambda x: x[indentation:], value.split("\n")))

    #     result = NodeList.generic_from_fst(baron.parse(value)[0]["value"],
    #                                        parent=self,
    #                                        on_attribute=on_attribute)

    #     if self.indentation:
    #         result.increase_indentation(len(self.indentation))
    #         if self.next:
    #             result[-1].value.node_list[-1].indent = self.indentation

    #     return result


class ImportNode(Node):
    value = NodeListProperty(CommaProxyList)

    def modules(self):
        "return a list of string of modules imported"
        return [x.value.dumps()for x in self.find('dotted_as_name')]

    def names(self):
        "return a list of string of new names inserted in the python context"
        return [x.target if x.target else x.value.dumps()
                for x in self.find('dotted_as_name')]

    def nodelist_from_str(self, value, on_attribute=None):
        fst = baron.parse("import %s" % value)[0]["value"]
        return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)


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
    @nodelist_property(CommaProxyList)
    def arguments(self, value):
        return baron.parse("lambda %s: x" % value)[0]["arguments"]

    @conditional_formatting_property(NodeList, [" "], [])
    def first_formatting(self):
        return self.arguments

    @NodeProperty()
    def value(self, value):
        return baron.parse("lambda: %s" % value)[0]["value"]


class LeftParenthesisNode(Node):
    pass


class ListArgumentNode(Node):
    @conditional_formatting_property(NodeList, [" "], [])
    def annotation_first_formatting(self):
        return self.annotation

    @conditional_formatting_property(NodeList, [" "], [])
    def annotation_second_formatting(self):
        return self.annotation

    @NodeProperty()
    def value(self, value):
        return baron.parse("lambda *%s: x" % value)[0]["arguments"][0]["value"]

    @NodeProperty()
    def annotation(self, value):
        code = "def a(a:%s=b): pass" % value
        return baron.parse(code)[0]["arguments"][0]["annotation"]


class ListComprehensionNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "generators":
            fst = baron.parse("[x %s]" % value)[0]["generators"]
            return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def from_str(self, value, on_attribute=None):
        if on_attribute == "result":
            fst = baron.parse("[%s for x in x]" % value)[0]["result"]
            return self.from_fst(fst, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class ListNode(Node, LiteralyEvaluableMixin):
    def nodelist_from_str(self, value, on_attribute=None):
        fst = baron.parse("[%s]" % value)[0]["value"]
        return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

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
                raise Exception("The target of a name as name node can only "
                                "be a 'name' or an empty string or None")

            if value:
                self.first_formatting = [self.from_fst({"type": "space", "value": " "},
                                                       on_attribute="delimiter")]
                self.second_formatting = [self.from_fst({"type": "space", "value": " "},
                                                        on_attribute="delimiter")]

        elif key == "value":
            if not (re.match(r'^[a-zA-Z_]\w*$', value) or value in ("", None)):
                raise Exception("The value of a name as name node can only "
                                "be a 'name' or an empty string or None")

        return super().__setattr__(key, value)


class NonlocalNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            fst = baron.parse("global %s" % value)[0]["value"]
            return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value, on_attribute="value"))


class OctaNode(Node, LiteralyEvaluableMixin):
    pass


class PassNode(Node):
    pass


class PrintNode(Node):
    value = None

    def from_str(self, value, on_attribute=None):
        if on_attribute == "destination":
            if value and not self.value:
                self.formatting = [{"type": "space", "value": " "}]
                fst = baron.parse("print >>%s" % value)[0]["destination"]
                return self.from_fst(fst, on_attribute=on_attribute)

            elif value and self.value:
                self.formatting = [{"type": "space", "value": " "}]
                result = self.from_fst(baron.parse("print >>%s" % value)[0]["destination"],
                                       on_attribute=on_attribute)
                if self.value.node_list and not self.value.node_list[0].type == "comma":
                    fst = {"type": "comma",
                           "second_formatting": [{"type": "space",
                                                  "value": " "}],
                           "first_formatting": []}
                    node = self.from_fst(fst, on_attribute=on_attribute)
                    self.value = NodeList([node]) + self.value
                return result

            elif self.value.node_list and self.value.node_list[0].type == "comma":
                self.formatting = [{"type": "space", "value": " "}]
                self.value = self.value.node_list[1:]
                return None
            else:
                self.formatting = []
                return None

        else:
            raise Exception("Unhandled case")

    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            if value:
                self.formatting = [{"type": "space", "value": " "}]

                code = "print %s" if not self.destination else "print >>a, %s"
                fst = baron.parse(code % value)[0]["value"]
                return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)
            else:
                if not value and not self.destination:
                    self.formatting = []
                else:
                    self.formatting = [{"type": "space", "value": " "}]
                return NodeList()

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class RaiseNode(Node):
    comma_or_from = ""
    fifth_formatting = None

    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            self.first_formatting = [{"type": "space", "value": " "}] if value else []
            if value:
                fst = baron.parse("raise %s" % value)[0]["value"]
                return self.from_fst(fst, on_attribute=on_attribute)
            return None

        elif on_attribute == "instance":
            if not self.value:
                raise Exception("Can't set instance if there is not value")

            if value:
                self.third_formatting = [{"type": "space", "value": " "}]
                if not self.comma_or_from:
                    self.comma_or_from = ","
                fst = baron.parse("raise a, %s" % value)[0]["instance"]
                return self.from_fst(fst, on_attribute=on_attribute)
            return None

        elif on_attribute == "traceback":
            if not self.instance:
                raise Exception("Can't set traceback if there is not instance")

            if value:
                self.fifth_formatting = [{"type": "space", "value": " "}]
                return self.from_fst(baron.parse("raise a, b, %s" % value)[0]["traceback"],
                                     on_attribute=on_attribute)
            return None

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        current = getattr(self, "comma_or_from", None)

        super().__setattr__(key, value)

        if key == "comma_or_from":
            if value == current:
                return

            if value == "from":
                self.second_formatting = [self.from_fst({"type": "space", "value": " "},
                                                        on_attribute="second_formatting")]
                self.third_formatting = [self.from_fst({"type": "space", "value": " "},
                                                       on_attribute="third_formatting")]

            elif value == ",":
                self.second_formatting = []
                self.third_formatting = [self.from_fst({"type": "space", "value": " "},
                                                       on_attribute="third_formatting")]


class RawStringNode(Node, LiteralyEvaluableMixin):
    pass


class RightParenthesisNode(Node):
    pass


class ReprNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        fst = baron.parse("`%s`" % value)[0]["value"]
        return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class ReturnNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            self.formatting = [{"type": "space", "value": " "}] if value else []
            if value:
                fst = baron.parse("return %s" % value)[0]["value"]
                return self.from_fst(fst, on_attribute=on_attribute)
            return None

        else:
            raise Exception("Unhandled case")


class SemicolonNode(Node):
    pass


class SetNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        fst = baron.parse("{%s}" % value)[0]["value"]
        return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class SetComprehensionNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "generators":
            fst = baron.parse("{x %s}" % value)[0]["generators"]
            return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def from_str(self, value, on_attribute=None):
        if on_attribute == "result":
            fst = baron.parse("{%s for x in x}" % value)[0]["result"]
            return self.from_fst(fst, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class SliceNode(Node):
    has_two_colons = False

    def from_str(self, value, on_attribute=None):
        if on_attribute == "lower":
            if value:
                fst = baron.parse("a[%s:]" % value)[0]["value"][1]["value"]["lower"]
                return self.from_fst(fst, on_attribute=on_attribute)
            return None

        elif on_attribute == "upper":
            if value:
                fst = baron.parse("a[:%s]" % value)[0]["value"][1]["value"]["upper"]
                return self.from_fst(fst, on_attribute=on_attribute)
            return None

        elif on_attribute == "step":
            self.has_two_colons = bool(value)
            if value:
                fst = baron.parse("a[::%s]" % value)[0]["value"][1]["value"]["step"]
                return self.from_fst(fst, on_attribute=on_attribute)
            return None

        else:
            raise Exception("Unhandled case")


class SpaceNode(Node):
    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def _default_fst(self):
        return {"type": "space", "value": " "}


class StandaloneAnnotationNode(Node):
    pass


class StarExpressionNode(Node):
    pass


class StarNode(Node):
    pass


class StringNode(Node, LiteralyEvaluableMixin):
    pass


class StringChainNode(Node, LiteralyEvaluableMixin):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            fst = baron.parse("a = %s" % value)[0]["value"]["value"]
            return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class TernaryOperatorNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "first":
            fst = baron.parse("%s if b else c" % value)[0]["first"]
            return self.from_fst(fst, on_attribute=on_attribute)

        elif on_attribute == "second":
            fst = baron.parse("a if b else %s" % value)[0]["second"]
            return self.from_fst(fst, on_attribute=on_attribute)

        elif on_attribute == "value":
            fst = baron.parse("a if %s else s" % value)[0]["value"]
            return self.from_fst(fst, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class TryNode(ElseAttributeNode):
    @property
    def next_intuitive(self):
        if self.excepts:
            return self.excepts[0]

        if self.finally_:
            return self.finally_

        raise Exception("incoherent state of TryNode, try should be followed "
                        "either by except or finally")

    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute != "excepts":
            return super().nodelist_from_str(value, on_attribute=on_attribute)

        clean_value = re.sub("^ *\n", "", value) if "\n" in value else value
        indentation = len(re.search("^ *", clean_value).group())

        if indentation:
            value = "\n".join(map(lambda x: x[indentation:], value.split("\n")))

        value = value.rstrip()
        value += "\n"

        if self.next and self.on_attribute == "root":
            value += "\n\n"
        elif self.next:
            value += "\n"

        code = "try:\n pass\n%sfinally:\n pass" % value
        fst = baron.parse(code)[0]["excepts"]
        result = NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

        if self.indentation:
            result.increase_indentation(len(self.indentation))
            if self._get_last_member_to_clean().type != "except":
                # assume that this is an endl node, this might break
                result[-1].value.node_list[-1].indent = self.indentation
            elif self.next:
                result[-1].value.node_list[-1].indent = self.indentation

        return result

    def from_str(self, value, on_attribute=None):
        if on_attribute == "finally":
            return self._convert_input_to_one_indented_member("finally", value,
                                                              on_attribute=on_attribute)

        return super().from_str(value, on_attribute=on_attribute)

    def __setattr__(self, name, value):
        if name == "finally_":
            name = "finally"

        return super().__setattr__(name, value)

    def _get_last_member_to_clean(self):
        if self.finally_:
            return self.finally_
        if self.else_:
            return self.else_
        return self.excepts[-1]

    def __getattr__(self, name):
        if name == "finally_":
            return getattr(self, "finally")

        return super().__getattr__(name)


class TupleNode(Node, LiteralyEvaluableMixin):
    def nodelist_from_str(self, value, on_attribute=None):
        fst = baron.parse("(%s)" % value)[0]["value"]

        # I assume that I've got an AssociativeParenthesisNode here instead of a tuple
        # because string is only one single element
        if not isinstance(fst, list):
            fst = baron.parse("(%s,)" % value)[0]["value"]

        return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key == "value" and not isinstance(self.value, CommaProxyList):
            setattr(self, "value", CommaProxyList(self.value))


class UnicodeStringNode(Node, LiteralyEvaluableMixin):
    pass


class UnicodeRawStringNode(Node, LiteralyEvaluableMixin):
    pass


class UnitaryOperatorNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "target":
            return self.from_fst(baron.parse("-%s" % value)[0]["target"],
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class YieldNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            self.formatting = [{"type": "space", "value": " "}] if value else []
            if value:
                return self.from_fst(baron.parse("yield %s" % value)[0]["value"],
                                     on_attribute=on_attribute)
            return None

        else:
            raise Exception("Unhandled case")


class YieldFromNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            return self.from_fst(baron.parse("yield from %s" % value)[0]["value"],
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class YieldAtomNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            self.second_formatting = [{"type": "space", "value": " "}] if value else []
            if value:
                fst = baron.parse("yield %s" % value)[0]["value"]
                return self.from_fst(fst, on_attribute=on_attribute)
            return None
        else:
            raise Exception("Unhandled case")


class WhileNode(ElseAttributeNode):
    @property
    def next_intuitive(self):
        if self.else_:
            return self.else_

        return self.next

    def __setattr__(self, key, value):
        if key == "test" and isinstance(value, str):
            fst = baron.parse("while %s: pass" % value)[0]["test"]
            value = self.from_fst(fst, on_attribute=key)

        super().__setattr__(key, value)


class WithContextItemNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            return self.from_fst(baron.parse("with %s: pass" % value)[0]["contexts"][0]["value"],
                                 on_attribute=on_attribute)

        elif on_attribute == "as":
            if value:
                self.first_formatting = [{"type": "space", "value": " "}]
                self.second_formatting = [{"type": "space", "value": " "}]
                fst = baron.parse("with a as %s: pass" % value)[0]["contexts"][0]["as"]
                return self.from_fst(fst, on_attribute=on_attribute)
            self.first_formatting = []
            self.second_formatting = []
            return ""

        raise Exception("Unhandled case")

    def __getattr__(self, name):
        if name == "as_":
            return getattr(self, "as")

        return super().__getattr__(name)

    def __setattr__(self, name, value):
        if name == "as_":
            name = "as"

        return super().__setattr__(name, value)


class WithNode(CodeBlockNode):
    async_formatting = None

    def nodelist_from_str(self, value, on_attribute=None):
        assert isinstance(value, str)

        if on_attribute == "contexts":
            fst = baron.parse("with %s: pass" % value)[0]["contexts"]
            return self.from_fst(fst, on_attribute=on_attribute)

        return super().nodelist_from_str(value, on_attribute=on_attribute)

    def __setattr__(self, key, value):
        if key == "contexts" and not isinstance(value, CommaProxyList):
            if isinstance(value, str):
                value = baron.parse("with %s: pass" % value)[0]["contexts"]
            value = CommaProxyList(value, parent=self, on_attribute=key)

        if key in ("async", "async_") and value and not self.async_formatting:
            self.async_formatting = " "

        super().__setattr__(key, value)


class EmptyLine(Node):
    def _default_fst(self):
        return {"type": "space", "value": ""}
