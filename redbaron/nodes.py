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
                         ReturnAnnotationMixin,
                         ValueMixin)
from .node_property import (node_property,
                            nodelist_property)
from .proxy_list import (CommaProxyList,
                         DotProxyList,
                         LineProxyList,
                         ProxyList)


class ArgumentGeneratorComprehensionNode(Node):
    @nodelist_property()
    def generators(self, value):
        return baron.parse("(x %s)" % value)[0]["generators"]

    @node_property()
    def result(self, value):
        return baron.parse("(%s for x in x)" % value)[0]["result"]


class AssertNode(Node):
    @node_property()
    def value(self, value):
        return baron.parse("assert %s" % value)[0]["value"]

    @node_property()
    def message(self, value):
        return baron.parse("assert plop, %s" % value)[0]["message"]

    @message.after_set
    def message_after_set(self, value):
        if value:
            self.third_formatting = [SpaceNode()]
        else:
            self.third_formatting = []


class AssignmentNode(Node, AnnotationMixin):
    _other_identifiers = ["assign"]

    @node_property()
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

    @node_property()
    def target(self, value):
        return baron.parse("%s = a" % value)[0]["target"]

    @node_property()
    def value(self, value):
        return baron.parse("a = %s" % value)[0]["value"]


class AssociativeParenthesisNode(Node):
    @node_property()
    def value(self, value):
        return baron.parse("(%s)" % value)[0]["value"]


class AtomtrailersNode(Node):
    @nodelist_property(list_type=DotProxyList)
    def value(self, value):
        return baron.parse("(%s)" % value)[0]["value"]["value"]


class AwaitNode(Node):
    @node_property()
    def value(self, value):
        return baron.parse("await %s" % value)[0]["value"]


class BinaryNode(Node, LiteralyEvaluableMixin, ValueMixin):
    pass


class BinaryOperatorNode(Node):
    @node_property()
    def first(self, value):
        return baron.parse("%s + b" % value)[0]["first"]

    @node_property()
    def second(self, value):
        return baron.parse("bb + %s" % value)[0]["second"]


class BinaryStringNode(Node, LiteralyEvaluableMixin):
    pass


class BinaryRawStringNode(Node, LiteralyEvaluableMixin):
    pass


class BooleanOperatorNode(Node):
    @node_property()
    def first(self, value):
        return baron.parse("%s and b" % value)[0]["first"]

    @node_property()
    def second(self, value):
        return baron.parse("bb and %s" % value)[0]["second"]


class BreakNode(Node):
    pass


class CallNode(Node):
    @nodelist_property(list_type=CommaProxyList)
    def value(self, value):
        return baron.parse("a(%s)" % value)[0]["value"][1]["value"]


class CallArgumentNode(Node):
    @node_property()
    def value(self, value):
        return baron.parse("a(%s)" % value)[0]["value"][1]["value"][0]["value"]

    @node_property()
    def target(self, value):
        code = "a(%s=b)" % value
        return baron.parse(code)[0]["value"][1]["value"][0]["target"]


class ClassNode(CodeBlockNode, DecoratorsMixin):
    _default_test_value = "name"
    parenthesis = False

    @nodelist_property(list_type=CommaProxyList)
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
    @node_property()
    def value(self, value):
        return baron.parse("a %s b" % value)[0]["value"]

    @node_property()
    def first(self, value):
        return baron.parse("%s > b" % value)[0]["first"]

    @node_property()
    def second(self, value):
        return baron.parse("bb > %s" % value)[0]["second"]


class ComparisonOperatorNode(Node):
    pass


class ComplexNode(Node):
    pass


class ComprehensionIfNode(Node):
    @node_property()
    def value(self, value):
        code = "[x for x in x if %s]" % value
        return baron.parse(code)[0]["generators"][0]["ifs"][0]["value"]


class ComprehensionLoopNode(Node):
    @nodelist_property()
    def ifs(self, value):
        code = "[x for x in x %s]" % value
        return baron.parse(code)[0]["generators"][0]["ifs"]

    @node_property()
    def iterator(self, value):
        code = "[x for %s in x]" % value
        return baron.parse(code)[0]["generators"][0]["iterator"]

    @node_property()
    def target(self, value):
        code = "[x for s in %s]" % value
        return baron.parse(code)[0]["generators"][0]["target"]


class ContinueNode(Node):
    pass


class DecoratorNode(Node):
    @node_property()
    def value(self, value):
        code = "@%s()\ndef a(): pass" % value
        return baron.parse(code)[0]["decorators"][0]["value"]

    @node_property()
    def call(self, value):
        return baron.parse("@a%s\ndef a(): pass" % value)


class DefNode(CodeBlockNode, DecoratorsMixin, ReturnAnnotationMixin):
    _other_identifiers = ["funcdef", "funcdef_"]
    _default_test_value = "name"
    async_formatting = nodelist_property("async_formatting")

    @async_formatting.after_set
    def async_formatting_after_set(self, value):
        if not value:
            self.async_formatting = []
        elif not self.async_formatting:
            self.async_formatting = [" "]

    def __init__(self, *args, **kwargs):
        self.async_formatting = []
        super().__init__(*args, **kwargs)

    @nodelist_property(list_type=CommaProxyList)
    def arguments(self, value):
        return baron.parse("def a(%s): pass" % value)[0]["arguments"]


class DefArgumentNode(Node, AnnotationMixin):
    @node_property()
    def value(self, value):
        code = "def a(b=%s): pass" % value
        return baron.parse(code)[0]["arguments"][0]["value"]

    @node_property()
    def target(self, value):
        code = "def a(%s=b): pass" % value
        return baron.parse(code)[0]["arguments"][0]["target"]


class DelNode(Node):
    @node_property()
    def value(self, value):
        return baron.parse("del %s" % value)[0]["value"]


class DictArgumentNode(Node, AnnotationMixin):
    @node_property()
    def value(self, value):
        code = "a(**%s)" % value
        return baron.parse(code)[0]["value"][1]["value"][0]["value"]


class DictitemNode(Node):
    @node_property()
    def value(self, value):
        code = "{a: %s}" % value
        return baron.parse(code)[0]["value"][0]["value"]

    @node_property()
    def key(self, value):
        code = "{%s: a}" % value
        return baron.parse(code)[0]["value"][0]["key"]


class DictNode(Node, LiteralyEvaluableMixin):
    @nodelist_property(list_type=CommaProxyList)
    def value(self, value):
        code = "{%s}" % value
        return baron.parse(code)[0]["value"]


class DictComprehensionNode(Node):
    @nodelist_property()
    def generators(self, value):
        return baron.parse("{x %s}" % value)[0]["generators"]

    @node_property()
    def result(self, value):
        return baron.parse("{%s for x in x}" % value)[0]["result"]


class DotNode(Node):
    def _default_fst(self):
        return {"type": "dot", "first_formatting": [], "second_formatting": []}


class DottedAsNameNode(IterableNode):
    @nodelist_property(list_type=DotProxyList)
    def value(self, value):
        code = "import %s" % value
        return baron.parse(code)[0]["value"][0]["value"]

    @node_property()
    def target(self, value):
        if not (re.match(r'^[a-zA-Z_]\w*$', value) or value in ("", None)):
            raise Exception("The target of a dotted as name node can only "
                            "be a 'name' or an empty string or None")
        return baron.parse(value)[0]

    @target.after_set
    def target_after_set(self, value):
        if not value:
            self.first_formatting = []
            self.second_formatting = []
        else:
            if not self.first_formatting:
                self.first_formatting = [" "]

            if not self.second_formatting:
                self.second_formatting = [" "]


class DottedNameNode(IterableNode):
    pass


class ElifNode(IfElseBlockSiblingNode):
    @node_property()
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
    delimiter = node_property("delimiter")

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
                self.third_formatting = [self.from_fst({"type": "space", "value": " "},
                                                       on_attribute="delimiter")]
            elif value == "as":
                self.second_formatting = [self.from_fst({"type": "space", "value": " "},
                                                        on_attribute="delimiter")]
                self.third_formatting = [self.from_fst({"type": "space", "value": " "},
                                                       on_attribute="delimiter")]
            elif value:
                raise Exception("Delimiters of an except node can only be "
                                "'as' or ',' (without spaces around it).")

        super().__setattr__(key, value)

    def from_str(self, value, on_attribute=None):
        if on_attribute == "exception":
            if value:
                self.first_formatting = [self.from_fst({"type": "space", "value": " "},
                                                       on_attribute=on_attribute)]
                code = "try: pass\nexcept %s: pass" % value
                fst = baron.parse(code)[0]["excepts"][0]["exception"]
                return self.from_fst(fst, on_attribute=on_attribute)

            self.first_formatting = []
            self.delimiter = ""
            self.target = ""
            return ""

        elif on_attribute == "target":
            if not self.exception:
                raise Exception("Can't set a target to an exception node "
                                "that doesn't have an exception set")

            if value:
                self.delimiter = "as"
                self.second_formatting = [self.from_fst({"type": "space", "value": " "},
                                                        on_attribute=on_attribute)]
                self.third_formatting = [self.from_fst({"type": "space", "value": " "},
                                                       on_attribute=on_attribute)]
                code = "try: pass\nexcept a as %s: pass" % value
                fst = baron.parse(code)[0]["excepts"][0]["target"]
                return self.from_fst(fst, on_attribute=on_attribute)

            self.delimiter = ""
            self.second_formatting = []
            self.third_formatting = []
            return ""

        else:
            raise Exception("Unhandled case")


class ExecNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            return self.from_fst(baron.parse("exec %s" % value)[0]["value"],
                                 on_attribute=on_attribute)

        elif on_attribute == "globals":
            if value:
                self.second_formatting = [{"type": "space", "value": " "}]
                self.third_formatting = [{"type": "space", "value": " "}]
                return self.from_fst(baron.parse("exec a in %s" % value)[0]["globals"],
                                     on_attribute=on_attribute)
            return None

        elif on_attribute == "locals":
            if not self.globals:
                raise Exception("I can't set locals when globals aren't set.")

            if value:
                self.fifth_formatting = [{"type": "space", "value": " "}]
                return self.from_fst(baron.parse("exec a in b, %s" % value)[0]["locals"],
                                     on_attribute=on_attribute)
            return None

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
        super().__setattr__(key, value)

        if key == "value" and not isinstance(self.value, LineProxyList):
            setattr(self, "value", LineProxyList(self.value, on_attribute="value"))


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

    def __setattr__(self, name, value):
        if name == "else_":
            name = "else"

        return super().__setattr__(name, value)


class ForNode(ElseAttributeNode):
    async_formatting = None

    @property
    def next_intuitive(self):
        if self.else_:
            return self.else_

        return self.next

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key in ("async", "async_") and getattr(self, "async") and not self.async_formatting:
            self.async_formatting = " "

    def from_str(self, value, on_attribute=None):
        if on_attribute == "target":
            fst = baron.parse("for i in %s: pass" % value)[0]["target"]
            return self.from_fst(fst, on_attribute=on_attribute)

        if on_attribute == "iterator":
            fst = baron.parse("for %s in i: pass" % value)[0]["iterator"]
            return self.from_fst(fst, on_attribute=on_attribute)

        return super().from_str(value, on_attribute=on_attribute)


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

    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "targets":
            fst = baron.parse("from a import %s" % value)[0]["targets"]
            return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

        if on_attribute == "value":
            fst = baron.parse("from %s import s" % value)[0]["value"]
            return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key == "value" and not isinstance(self.value, DotProxyList):
            setattr(self, "value", DotProxyList(self.value, on_attribute="value"))

        if key == "targets" and not isinstance(self.targets, CommaProxyList):
            setattr(self, "targets", CommaProxyList(self.targets, on_attribute="targets"))


class GeneratorComprehensionNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "generators":
            fst = baron.parse("(x %s)" % value)[0]["generators"]
            return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def from_str(self, value, on_attribute=None):
        if on_attribute == "result":
            return self.from_fst(baron.parse("(%s for x in x)" % value)[0]["result"],
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class GetitemNode(Node):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            fst = baron.parse("a[%s]" % value)[0]["value"][1]["value"]
            return self.from_fst(fst, on_attribute=on_attribute)
        return super().from_str(value, on_attribute=on_attribute)


class GlobalNode(Node):
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


class HexaNode(Node, LiteralyEvaluableMixin):
    pass


class IfNode(IfElseBlockSiblingNode):
    def from_str(self, value, on_attribute=None):
        if on_attribute == "test":
            fst = baron.parse("if %s: pass" % value)[0]["value"][0]["test"]
            return self.from_fst(fst,
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")


class IfelseblockNode(Node):
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute != "value":
            return super().nodelist_from_str(value, on_attribute=on_attribute)

        value = value.rstrip()
        value += "\n"

        if self.next and self.on_attribute == "root":
            value += "\n\n"
        elif self.next:
            value += "\n"

        clean_value = re.sub("^ *\n", "", value) if "\n" in value else value
        indentation = len(re.search("^ *", clean_value).group())

        if indentation:
            value = "\n".join(map(lambda x: x[indentation:], value.split("\n")))

        result = NodeList.generic_from_fst(baron.parse(value)[0]["value"],
                                   parent=self, on_attribute=on_attribute)

        if self.indentation:
            result.increase_indentation(len(self.indentation))
            if self.next:
                result[-1].value.node_list[-1].indent = self.indentation

        return result


class ImportNode(Node):
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

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

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
    def nodelist_from_str(self, value, on_attribute=None):
        if on_attribute == "arguments":
            self.first_formatting = [{"type": "space", "value": " "}] if value else []
            fst = baron.parse("lambda %s: x" % value)[0]["arguments"]
            return NodeList.generic_from_fst(fst, parent=self, on_attribute=on_attribute)

        return super().nodelist_from_str(value, on_attribute=on_attribute)

    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            return self.from_fst(baron.parse("lambda: %s" % value)[0]["value"],
                                 on_attribute=on_attribute)

        else:
            raise Exception("Unhandled case")

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key == "arguments" and not isinstance(self.arguments, CommaProxyList):
            setattr(self, "arguments", CommaProxyList(self.arguments, on_attribute="arguments"))


class LeftParenthesisNode(Node):
    pass


class ListArgumentNode(Node):
    annotation_first_formatting = None
    annotation_second_formatting = None

    def from_str(self, value, on_attribute=None):
        if on_attribute == "value":
            fst = baron.parse("lambda *%s: x" % value)[0]["arguments"][0]["value"]
            return self.from_fst(fst, on_attribute=on_attribute)

        elif on_attribute == "annotation":
            if not self.annotation_first_formatting:
                node = self.from_fst({"type": "space", "value": " "},
                                     on_attribute="annotation_first_formatting")
                self.annotation_first_formatting = [node]

            if not self.annotation_second_formatting:
                node = self.from_fst({"type": "space", "value": " "},
                                     on_attribute="annotation_second_formatting")
                self.annotation_second_formatting = [node]

            code = "def a(a:%s=b): pass" % value
            fst = baron.parse(code)[0]["arguments"][0]["annotation"]
            return self.from_fst(fst, on_attribute=on_attribute) if value else ""

        else:
            raise Exception("Unhandled case")


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
