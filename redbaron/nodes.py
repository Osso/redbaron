import re

import baron

from .base_nodes import (Node,
                         NodeList)
from .node_mixin import (AnnotationMixin,
                         CodeBlockMixin,
                         DecoratorsMixin,
                         ElseMixin,
                         FinallyMixin,
                         IfElseBlockSiblingMixin,
                         IndentedCodeBlockMixin,
                         LiteralyEvaluableMixin,
                         ReturnAnnotationMixin,
                         SeparatorMixin,
                         ValueIterableMixin)
from .node_property import (NodeProperty,
                            conditional_formatting_property,
                            nodelist_property)
from .proxy_list import (ArgsProxyList,
                         CommaProxyList,
                         ContextsProxyList,
                         DictProxyList,
                         DotProxyList,
                         ImportsProxyList)
from .utils import indent_str


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
        if not value:
            return None
        return baron.parse("assert plop, %s" % value)[0]["message"]

    @conditional_formatting_property(NodeList, [" "], [])
    def third_formatting(self):
        return self.message


class AssignmentNode(AnnotationMixin, Node):
    _other_identifiers = ["assign"]
    _operator = ''

    @property
    def operator(self):
        return self._operator

    @operator.setter
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

        self._operator = value

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


class AtomtrailersNode(ValueIterableMixin, Node):
    @nodelist_property(DotProxyList)
    def value(self, value):
        return baron.parse("(%s)" % value)[0]["value"]["value"]


class AwaitNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("await %s" % value)[0]["value"]


class BinaryNode(Node, LiteralyEvaluableMixin):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not re.match(r'^0b[01]+$', value):
            raise ValueError(f"invalid value {value} for binary node")
        self._value = value  # pylint: disable=attribute-defined-outside-init


class BinaryOperatorNode(Node):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value not in ("+", "-", "*", "/", "//", "%", "@", "**", "&", "^"):
            raise ValueError(f"invalid value {value} for binary node")
        self._value = value  # pylint: disable=attribute-defined-outside-init

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
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value not in ("and", "or"):
            raise ValueError(f"invalid value {value} for boolean node")
        self._value = value  # pylint: disable=attribute-defined-outside-init

    @NodeProperty
    def first(self, value):
        return baron.parse("%s and b" % value)[0]["first"]

    @NodeProperty
    def second(self, value):
        return baron.parse("bb and %s" % value)[0]["second"]


class BreakNode(Node):
    pass


class CallNode(ValueIterableMixin, Node):
    @nodelist_property(ArgsProxyList)
    def value(self, value):
        return baron.parse("a(%s)" % value)[0]["value"][1]["value"]


class CallArgumentNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("a(%s)" % value)[0]["value"][1]["value"][0]["value"]

    @NodeProperty
    def target(self, value):
        if not value:
            return None

        code = "a(%s=b)" % value
        return baron.parse(code)[0]["value"][1]["value"][0]["target"]


class ClassNode(IndentedCodeBlockMixin, Node, DecoratorsMixin):
    _default_test_value = "name"
    parenthesis = False

    def __init__(self, fst=None, parent=None, on_attribute=None):
        self.class_ = True
        super().__init__(fst=fst, parent=parent, on_attribute=on_attribute)

    @nodelist_property(CommaProxyList)
    def inherit_from(self, value):
        return baron.parse("class a(%s): pass" % value)[0]["inherit_from"]

    @inherit_from.after_set
    def inherit_from(self, value):
        self.parenthesis = bool(value)


class CommaNode(SeparatorMixin, Node):
    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

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
        return baron.parse("@a%s\ndef a(): pass" % value)[0]["decorators"][0]["call"]


class DefNode(IndentedCodeBlockMixin, DecoratorsMixin,
              ReturnAnnotationMixin, Node):
    _default_test_value = "name"

    @conditional_formatting_property(NodeList, [" "], [])
    def async_formatting(self):
        return self.async_

    @nodelist_property(ArgsProxyList)
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


class DictNode(ValueIterableMixin, LiteralyEvaluableMixin, Node):
    @nodelist_property(DictProxyList)
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


class DottedAsNameNode(ValueIterableMixin, Node):
    _target = None

    @nodelist_property(DotProxyList)
    def value(self, value):
        code = "import %s" % value
        return baron.parse(code)[0]["value"][0]["value"]

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        if not (re.match(r'^[a-zA-Z_]\w*$', value) or value in ("", None)):
            raise Exception("The target of a dotted as name node can only "
                            "be a 'name' or an empty string or None")
        self._target = value

    @conditional_formatting_property(NodeList, [" "], [])
    def first_formatting(self):
        return self.target

    @conditional_formatting_property(NodeList, [" "], [])
    def second_formatting(self):
        return self.target


class DottedNameNode(ValueIterableMixin, Node):
    pass


class ElifNode(IndentedCodeBlockMixin, IfElseBlockSiblingMixin, Node):
    @NodeProperty
    def test(self, value):
        code = "if %s: pass" % value
        return baron.parse(code)[0]["value"][0]["test"]


class EllipsisNode(Node):
    pass


class ElseNode(IndentedCodeBlockMixin, IfElseBlockSiblingMixin, Node):
    @property
    def next_intuitive(self):
        parent = self.parent
        if isinstance(parent, NodeList):
            parent = parent.parent

        if parent.baron_type == "ifelseblock":
            return super().next_intuitive

        if self.parent.baron_type == "try":
            if self.parent.find("finally"):
                return self.parent.find("finally")

            return self.parent.next

        if self.parent.baron_type in ("for", "while"):
            return self.parent.next

        return None

    @property
    def previous_intuitive(self):
        parent = self.parent
        if isinstance(parent, NodeList):
            parent = parent.parent

        if parent.baron_type == "ifelseblock":
            return super().previous_intuitive

        if self.parent.baron_type == "try":
            return self.parent.excepts[-1]

        if self.parent.baron_type in ("for", "while"):
            return self.parent

        return None


class EndlNode(Node):
    def __init__(self, *args, **kwargs):
        self.indent = ""
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def _default_fst(self):
        return {"type": "endl", "formatting": [],
                "value": "\n", "indent": ""}

    def consume_leftover_indentation(self):
        indent = self.indent
        self.indent = ""
        return indent


class ExceptNode(IndentedCodeBlockMixin, Node):
    @NodeProperty
    def target(self, value):
        if not self.exception:
            raise Exception("Can't set a target to an exception node "
                            "that doesn't have an exception set")

        if value == "":
            return None

        code = "try: pass\nexcept a as %s: pass" % value
        return baron.parse(code)[0]["excepts"][0]["target"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
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
        return "as" if self.target and self.exception else ""

    @delimiter.setter
    def delimiter(self, value):
        pass

    @NodeProperty
    def exception(self, value):
        value = indent_str(value, self.el_indentation)
        code = "try: pass\nexcept %s: pass" % value
        return baron.parse(code)[0]["excepts"][0]["exception"]

    @property
    def next_intuitive(self):
        next_ = self.next
        if next_:
            return next_

        parent = self.parent.parent

        if parent.else_:
            return parent.else_

        if parent.finally_:
            return parent.finally_

        if parent.next:
            return parent.next

        return None

    @property
    def previous_intuitive(self):
        previous_ = self.previous

        if previous_:
            return previous_

        return self.parent.parent


class ExecNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("exec %s" % value)[0]["value"]

    @NodeProperty
    def locals(self, value):
        if not value:
            return None

        if not self.globals:
            raise Exception("I can't set locals when globals aren't set.")
        return baron.parse("exec a in b, %s" % value)[0]["locals"]

    @NodeProperty
    def globals(self, value):
        if not value:
            return None
        return baron.parse("exec a in %s" % value)[0]["globals"]

    @conditional_formatting_property(NodeList, [" "], [])
    def second_formatting(self):
        return self.globals

    @conditional_formatting_property(NodeList, [" "], [])
    def third_formatting(self):
        return self.globals

    @conditional_formatting_property(NodeList, [" "], [])
    def fifth_formatting(self):
        return self.globals


class FinallyNode(IndentedCodeBlockMixin, Node):
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


class ElseAttributeNode(IndentedCodeBlockMixin, Node):
    @NodeProperty
    def value(self, value):
        value = indent_str(value, self.el_indentation)
        code = "try: pass\nexcept: pass\nelse:\n%s" % value
        return baron.parse(code)[0]["else"]


class ForNode(ElseMixin, IndentedCodeBlockMixin, Node):
    @conditional_formatting_property(NodeList, [" "], [])
    def async_formatting(self):
        return self.async_

    @NodeProperty
    def target(self, value):
        return baron.parse("for i in %s: pass" % value)[0]["target"]

    @NodeProperty
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


class FromImportNode(ValueIterableMixin, Node):
    def names(self):
        """Return the list of new names imported

        For example:
            RedBaron("from qsd import a, c, e as f").names() == ['a', 'c', 'f']
        """
        return [x.target if x.target else x.value
                for x in self.targets   # pylint: disable=not-an-iterable
                if not isinstance(x, (LeftParenthesisNode, RightParenthesisNode))]

    def modules(self):
        """Return the list of the targets imported

        For example (notice 'e' instead of 'f'):
            RedBaron("from qsd import a, c, e as f").names() == ['a', 'c', 'e']
        """
        return [x.value for x in self.targets]   # pylint: disable=not-an-iterable

    def full_path_names(self):
        """Return the list of new names imported with the full module path

        For example (notice 'e' instead of 'f'):
            RedBaron("from qsd import a, c, e as f").names() == ['qsd.a', 'qsd.c', 'qsd.f']
        """
        base = self.value.dumps()
        return [base + "." + (x.target if x.target else x.value)  # pylint: disable=no-member
                for x in self.targets   # pylint: disable=not-an-iterable
                if not isinstance(x, (LeftParenthesisNode, RightParenthesisNode))]

    def full_path_modules(self):
        """Return the list of the targets imported with the full module path

        For example (notice 'e' instead of 'f'):
            RedBaron("from qsd import a, c, e as f").names() == ['qsd.a', 'qsd.c', 'qsd.e']
        """
        base = self.value.dumps()
        return [base + "." + x.value  # pylint: disable=no-member
                for x in self.targets   # pylint: disable=not-an-iterable
                if not isinstance(x, (LeftParenthesisNode, RightParenthesisNode))]

    @nodelist_property(ImportsProxyList)
    def targets(self, value):
        return baron.parse("from a import %s" % value)[0]["targets"]

    @nodelist_property(DotProxyList)
    def value(self, value):
        return baron.parse("from %s import s" % value)[0]["value"]


class GeneratorComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse("(x %s)" % value)[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse("(%s for x in x)" % value)[0]["result"]


class GetitemNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("a[%s]" % value)[0]["value"][1]["value"]


class GlobalNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse("global %s" % value)[0]["value"]


class HexaNode(Node, LiteralyEvaluableMixin):
    pass


class IfNode(IfElseBlockSiblingMixin, IndentedCodeBlockMixin, Node):
    @NodeProperty
    def test(self, value):
        return baron.parse("if %s: pass" % value)[0]["value"][0]["test"]


class IfelseblockNode(CodeBlockMixin, Node):
    pass


class ImportNode(ValueIterableMixin, Node):
    def modules(self):
        "return a list of string of modules imported"
        return [x.value.dumps() for x in self.find_all('dotted_as_name')]

    def names(self):
        "return a list of string of new names inserted in the python context"
        return [x.target if x.target else x.value.dumps()
                for x in self.find_all('dotted_as_name')]

    @nodelist_property(ImportsProxyList)
    def value(self, value):
        return baron.parse("import %s" % value)[0]["value"]


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
    @nodelist_property(ArgsProxyList)
    def arguments(self, value):
        return baron.parse("lambda %s: x" % value)[0]["arguments"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def first_formatting(self):
        return self.arguments

    @NodeProperty
    def value(self, value):
        return baron.parse("lambda: %s" % value)[0]["value"]


class LeftParenthesisNode(Node):
    pass


class ListArgumentNode(AnnotationMixin, Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("lambda *%s: x" % value)[0]["arguments"][0]["value"]


class ListComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse("[x %s]" % value)[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse("[%s for x in x]" % value)[0]["result"]


class ListNode(ValueIterableMixin, LiteralyEvaluableMixin, Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse("[%s]" % value)[0]["value"]

    @value.after_set
    def value(self, value):
        self.fix_second_formatting()

    def fix_second_formatting(self):
        if self.value and self.second_formatting:
            if isinstance(self.second_formatting[-1], EndlNode):
                indent = self.second_formatting[-1].indent
                self.second_formatting[-1].indent = ""
                self.value[0].indentation = indent
            else:
                self.value[0].indentation = self.second_formatting.pop().value
            self.value.detect_indentation()


class LongNode(Node):
    pass


class NameNode(LiteralyEvaluableMixin, Node):
    pass


class TypedNameNode(Node):
    pass


class NameAsNameNode(Node):
    _target = None
    _value = None

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        if not (re.match(r'^[a-zA-Z_]\w*$', value) or value in ("", None)):
            raise Exception("The target of a name as name node can only "
                            "be a 'name' or an empty string or None")
        self._target = value

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def first_formatting(self):
        return self.target

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def second_formatting(self):
        return self.target

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not (re.match(r'^[a-zA-Z_]\w*$', value) or value in ("", None)):
            raise Exception("The value of a name as name node can only "
                            "be a 'name' or an empty string or None")
        self._value = value


class NonlocalNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse("global %s" % value)[0]["value"]


class OctaNode(LiteralyEvaluableMixin, Node):
    pass


class PassNode(Node):
    pass


class PrintNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        if not value:
            raise ValueError("print call cannot be empty")
        if value.lstrip(" ")[0] != "(":
            raise ValueError("print call must start with (")
        if value.rstrip(" ")[-1] != ")":
            raise ValueError("print call must end with )")
        return baron.parse("print%s" % value)[0]["value"]


class RaiseNode(Node):
    @property
    def comma_or_from(self):
        return "from" if self.instance else ""

    @comma_or_from.setter
    def comma_or_from(self, value):
        if value not in (None, "from"):
            raise ValueError(f"invalid value {value} for comma_or_from")

    @NodeProperty
    def value(self, value):
        return baron.parse("raise %s" % value)[0]["value"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def first_formatting(self):
        return self.value

    @NodeProperty
    def instance(self, value):
        if not self.value:
            raise ValueError("Can't set instance if there is no value")
        if not value:
            return None
        return baron.parse("raise a from %s" % value)[0]["instance"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def second_formatting(self):
        return self.instance

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def third_formatting(self):
        return self.instance and self.comma_or_from != ","

    @NodeProperty
    def traceback(self, value):
        if not self.instance:
            raise Exception("Can't set traceback if there is not instance")
        return baron.parse("raise a, b, %s" % value)[0]["traceback"]


class RawStringNode(LiteralyEvaluableMixin, Node):
    pass


class RightParenthesisNode(Node):
    pass


class ReprNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse("`%s`" % value)[0]["value"]


class ReturnNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("return %s" % value)[0]["value"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def formatting(self):
        return self.value


class SemicolonNode(Node):
    pass


class SetNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse("{%s}" % value)[0]["value"]


class SetComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse("{x %s}" % value)[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse("{%s for x in x}" % value)[0]["result"]


class SliceNode(Node):
    @property
    def has_two_colons(self):
        return bool(self.step)

    @has_two_colons.setter
    def has_two_colons(self, value):
        if value not in (True, False):
            raise ValueError(f"invalid value {value} for has_two_colons")

    @NodeProperty
    def lower(self, value):
        return baron.parse("a[%s:]" % value)[0]["value"][1]["value"]["lower"]

    @NodeProperty
    def upper(self, value):
        return baron.parse("a[:%s]" % value)[0]["value"][1]["value"]["upper"]

    @NodeProperty
    def step(self, value):
        return baron.parse("a[::%s]" % value)[0]["value"][1]["value"]["step"]


class SpaceNode(SeparatorMixin, Node):
    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def _default_fst(self):
        return {"type": "space", "value": " "}

    @classmethod
    def make(cls, value, parent=None, on_attribute=None):
        return cls({"type": "space", "value": value}, parent=parent,
                   on_attribute=on_attribute)

    def consume_leftover_indentation(self):
        indent = self.value  # pylint: disable=access-member-before-definition
        self.value = ""  # pylint: disable=attribute-defined-outside-init
        return indent


class StandaloneAnnotationNode(Node):
    pass


class StarExpressionNode(Node):
    pass


class StarNode(Node):
    pass


class StringNode(LiteralyEvaluableMixin, Node):
    pass


class StringChainNode(LiteralyEvaluableMixin, Node):
    @nodelist_property(NodeList)
    def value(self, value):
        return baron.parse("a = %s" % value)[0]["value"]["value"]


class TernaryOperatorNode(Node):
    @NodeProperty
    def first(self, value):
        return baron.parse("%s if b else c" % value)[0]["first"]

    @NodeProperty
    def second(self, value):
        return baron.parse("a if b else %s" % value)[0]["second"]

    @NodeProperty
    def value(self, value):
        return baron.parse("a if %s else s" % value)[0]["value"]


class TryNode(ElseMixin, FinallyMixin, IndentedCodeBlockMixin, Node):
    @property
    def next_intuitive(self):
        if self.excepts:
            return self.excepts[0]  # pylint: disable=unsubscriptable-object

        if self.finally_:
            return self.finally_

        raise Exception("incoherent state of TryNode, try should be followed "
                        "either by except or finally")

    @nodelist_property(NodeList)
    def excepts(self, value):
        code = "try:\n pass\n%sfinally:\n pass" % value
        return baron.parse(code)[0]["excepts"]

    def get_last_member(self):
        if self.finally_:
            return self.finally_
        if self.else_:
            return self.else_
        return self.excepts[-1]  # pylint: disable=unsubscriptable-object


class TupleNode(ValueIterableMixin, LiteralyEvaluableMixin, Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        fst = baron.parse("(%s)" % value)[0]["value"]

        # I assume that I've got an AssociativeParenthesisNode here instead
        # of a tuple because string is only one single element
        if not isinstance(fst, list):
            assert fst["type"] == "associativeparenthesis"
            fst = baron.parse("(%s,)" % value)[0]["value"]

        return fst


class UnicodeStringNode(LiteralyEvaluableMixin, Node):
    pass


class UnicodeRawStringNode(LiteralyEvaluableMixin, Node):
    pass


class UnitaryOperatorNode(Node):
    @NodeProperty
    def target(self, value):
        return baron.parse("-%s" % value)[0]["target"]


class YieldNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("yield %s" % value)[0]["value"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def formatting(self):
        return self.value


class YieldFromNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("yield from %s" % value)[0]["value"]


class YieldAtomNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse("yield %s" % value)[0]["value"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def second_formatting(self):
        return self.value


class WhileNode(ElseMixin, IndentedCodeBlockMixin, Node):
    @NodeProperty
    def test(self, value):
        return baron.parse("while %s: pass" % value)[0]["test"]

    @property
    def next_intuitive(self):
        if self.else_:
            return self.else_

        return self.next


class WithContextItemNode(Node):
    @NodeProperty
    def value(self, value):
        if not value:
            return None
        return baron.parse("with %s: pass" % value)[0]["contexts"][0]["value"]

    @NodeProperty
    def as_(self, value):
        if not value:
            return None
        return baron.parse("with %s: pass" % value)[0]["contexts"][0]["value"]

    @conditional_formatting_property(NodeList, [" "], [])
    def first_formatting(self):
        return self.as_

    @conditional_formatting_property(NodeList, [" "], [])
    def second_formatting(self):
        return self.as_


class WithNode(IndentedCodeBlockMixin, Node):
    @nodelist_property(ContextsProxyList)
    def contexts(self, value):
        return baron.parse("with %s: pass" % value)[0]["contexts"]

    @conditional_formatting_property(NodeList, [" "], [])
    def async_formatting(self):
        return self.async_  # pylint: disable=no-member


class EmptyLineNode(Node):
    def _default_fst(self):
        return {"type": "empty_line", "value": ""}

    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def fst(self):
        return {"type": "space", "value": ""}
