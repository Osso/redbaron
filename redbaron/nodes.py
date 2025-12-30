import re

import baron

from redbaron.utils import deindent_str, indent_str

from .base_nodes import Node, NodeList
from .node_mixin import (
    AnnotationMixin,
    CodeBlockMixin,
    DecoratorsMixin,
    ElseMixin,
    FinallyMixin,
    FourthFormattingIndentMixin,
    IfElseBlockSiblingMixin,
    IndentedCodeBlockMixin,
    IndentedValueMixin,
    ListTupleMixin,
    LiteralyEvaluableMixin,
    ReturnAnnotationMixin,
    SecondFormattingIndentMixin,
    SeparatorMixin,
    ValueIterableMixin,
)
from .node_property import NodeListProperty, NodeProperty, conditional_formatting_property, nodelist_property
from .proxy_list import (
    ArgsProxyList,
    CodeProxyList,
    CommaProxyList,
    ContextsProxyList,
    DefArgsProxyList,
    DictProxyList,
    DotProxyList,
    ImportsProxyList,
)


class ArgumentGeneratorComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse(f"(x {value})")[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse(f"({value} for x in x)")[0]["result"]


class AssertNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"assert {value}")[0]["value"]

    @NodeProperty
    def message(self, value):
        if not value:
            return None
        return baron.parse(f"assert plop, {value}")[0]["message"]

    @conditional_formatting_property(NodeList, [" "], [])
    def third_formatting(self):
        return self.message


class AssignmentNode(AnnotationMixin, Node):
    _other_identifiers = ["assign"]
    _operator = ""

    @property
    def operator(self):
        return self._operator

    @operator.setter
    def operator(self, value):
        if len(value) == 2 and value[1] == "=":
            value = value[0]
        elif len(value) == 1 and value == "=" or value is None:
            value = ""
        elif len(value) not in (0, 1, 2):
            raise Exception(
                "The value of the operator can only be a string of one or two char, for eg: '+', '+=', '=', ''"
            )

        self._operator = value

    @NodeProperty
    def target(self, value):
        return baron.parse(f"{value} = a")[0]["target"]

    @NodeProperty
    def value(self, value):
        return baron.parse(f"a = {value}")[0]["value"]

    def increase_indentation(self, indent=None):
        super().increase_indentation(indent=indent)
        self.second_formatting.increase_indentation(indent=indent)
        self.value.increase_indentation(indent=indent)

    def decrease_indentation(self, indent=None):
        super().decrease_indentation(indent=indent)
        self.second_formatting.decrease_indentation(indent=indent)
        self.value.decrease_indentation(indent=indent)


class AssociativeParenthesisNode(ValueIterableMixin, IndentedValueMixin, Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"({value})")[0]["value"]

    @property
    def _endl(self):
        return self.third_formatting.find("endl")

    def remove_endl(self):
        self.third_formatting.pop()


class AtomtrailersNode(ValueIterableMixin, IndentedValueMixin, Node):
    @nodelist_property(DotProxyList)
    def value(self, value):
        return baron.parse(f"({value})")[0]["value"]["value"]


class AwaitNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"await {value}")[0]["value"]


class BinaryNode(Node, LiteralyEvaluableMixin):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not re.match(r"^0b[01]+$", value):
            raise ValueError(f"invalid value {value} for binary node")
        self._value = value  # pylint: disable=attribute-defined-outside-init


class BinaryOperatorNode(Node):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value not in ("+", "-", "*", "/", "//", "%", "@", "**", "&", "^", "|"):
            raise ValueError(f"invalid value {value} for binary node")
        self._value = value  # pylint: disable=attribute-defined-outside-init

    @NodeProperty
    def first(self, value):
        return baron.parse(f"{value} + b")[0]["first"]

    @NodeProperty
    def second(self, value):
        return baron.parse(f"bb + {value}")[0]["second"]

    @property
    def _endl(self):
        return None

    def remove_endl(self):
        pass


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
        return baron.parse(f"{value} and b")[0]["first"]

    @NodeProperty
    def second(self, value):
        return baron.parse(f"bb and {value}")[0]["second"]

    @property
    def _endl(self):
        return None

    def remove_endl(self):
        pass


class BreakNode(Node):
    pass


class CallNode(ValueIterableMixin, IndentedValueMixin, Node):
    @nodelist_property(ArgsProxyList)
    def value(self, value):
        return baron.parse(f"a({value})")[0]["value"][1]["value"]

    def increase_indentation(self, indent=None):
        if indent is None:
            indent = self.indent_unit

        super().increase_indentation(indent=indent)
        self.fourth_formatting.increase_indentation(indent=indent)

    def decrease_indentation(self, indent=None):
        if indent is None:
            indent = self.indent_unit

        super().decrease_indentation(indent=indent)
        self.fourth_formatting.decrease_indentation(indent=indent)


class CallArgumentNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"a({value})")[0]["value"][1]["value"][0]["value"]

    @NodeProperty
    def target(self, value):
        if not value:
            return None

        code = f"a({value}=b)"
        return baron.parse(code)[0]["value"][1]["value"][0]["target"]


class CaseNode(IndentedCodeBlockMixin, Node):
    """Pattern matching case clause (Python 3.10+)."""

    @NodeProperty
    def pattern(self, value):
        code = f"match x:\n    case {value}: pass"
        return baron.parse(code)[0]["cases"][1]["pattern"]

    @NodeProperty
    def guard(self, value):
        if not value:
            return None
        code = f"match x:\n    case _ if {value}: pass"
        return baron.parse(code)[0]["cases"][1]["guard"]


class ClassNode(IndentedCodeBlockMixin, Node, DecoratorsMixin):
    _default_test_value = "name"
    parenthesis = False

    def __init__(self, fst=None, parent=None, on_attribute=None):
        self.class_ = True
        super().__init__(fst=fst, parent=parent, on_attribute=on_attribute)

    @nodelist_property(CommaProxyList)
    def inherit_from(self, value):
        return baron.parse(f"class a({value}): pass")[0]["inherit_from"]

    @inherit_from.after_set
    def inherit_from(self, value):
        self.parenthesis = bool(value)


class CommaNode(SeparatorMixin, Node):
    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def _default_fst(self):
        return {"type": "comma", "first_formatting": [], "second_formatting": [{"type": "space", "value": " "}]}


class CommentNode(Node):
    pass


class ComparisonNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"a {value} b")[0]["value"]

    @NodeProperty
    def first(self, value):
        return baron.parse(f"{value} > b")[0]["first"]

    @NodeProperty
    def second(self, value):
        return baron.parse(f"bb > {value}")[0]["second"]


class ComparisonOperatorNode(Node):
    pass


class ComplexNode(Node):
    pass


class ComprehensionIfNode(Node):
    @NodeProperty
    def value(self, value):
        code = f"[x for x in x if {value}]"
        return baron.parse(code)[0]["generators"][0]["ifs"][0]["value"]


class ComprehensionLoopNode(Node):
    @nodelist_property(NodeList)
    def ifs(self, value):
        code = f"[x for x in x {value}]"
        return baron.parse(code)[0]["generators"][0]["ifs"]

    @NodeProperty
    def iterator(self, value):
        code = f"[x for {value} in x]"
        return baron.parse(code)[0]["generators"][0]["iterator"]

    @NodeProperty
    def target(self, value):
        code = f"[x for s in {value}]"
        return baron.parse(code)[0]["generators"][0]["target"]


class ContinueNode(Node):
    pass


class DecoratorNode(Node):
    @NodeProperty
    def value(self, value):
        code = f"@{value}()\ndef a(): pass"
        return baron.parse(code)[0]["decorators"][0]["value"]

    @NodeProperty
    def call(self, value):
        return baron.parse(f"@a{value}\ndef a(): pass")[0]["decorators"][0]["call"]


class DefNode(IndentedCodeBlockMixin, DecoratorsMixin, ReturnAnnotationMixin, Node):
    _default_test_value = "name"

    def __init__(self, fst=None, parent=None, on_attribute=None):
        # Fixes the value partly stored in formatting
        fst["value"] = fst["sixth_formatting"] + fst["value"]
        fst["sixth_formatting"] = []
        super().__init__(fst=fst, parent=parent, on_attribute=on_attribute)

    @conditional_formatting_property(NodeList, [" "], [])
    def async_formatting(self):
        return self.async_

    @nodelist_property(DefArgsProxyList)
    def arguments(self, value):
        return baron.parse(f"def a({value}): pass")[0]["arguments"]

    def fst(self):
        fst = super().fst()

        # Force indentation for each decorator
        for el in fst["decorators"]:
            if el["type"] == "endl":
                el["indent"] = self.indentation

        return fst


class DefArgumentNode(Node, AnnotationMixin):
    @NodeProperty
    def value(self, value):
        code = f"def a(b={value}): pass"
        return baron.parse(code)[0]["arguments"][0]["value"]

    @NodeProperty
    def target(self, value):
        code = f"def a({value}=b): pass"
        return baron.parse(code)[0]["arguments"][0]["target"]


class DelNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"del {value}")[0]["value"]


class DictArgumentNode(Node, AnnotationMixin):
    @NodeProperty
    def value(self, value):
        code = f"a(**{value})"
        return baron.parse(code)[0]["value"][1]["value"][0]["value"]


class DictitemNode(Node):
    @NodeProperty
    def value(self, value):
        code = f"{{a: {value}}}"
        return baron.parse(code)[0]["value"][0]["value"]

    @NodeProperty
    def key(self, value):
        code = f"{{{value}: a}}"
        return baron.parse(code)[0]["value"][0]["key"]

    def consume_leftover_indentation(self):
        return self.value.consume_leftover_indentation()


class DictNode(FourthFormattingIndentMixin, ValueIterableMixin, LiteralyEvaluableMixin, Node):
    @nodelist_property(DictProxyList)
    def value(self, value):
        code = f"{{{value}}}"
        return baron.parse(code)[0]["value"]

    def put_on_new_line(self, item, indentation=None):
        return self.value.put_on_new_line(item, indentation=indentation)

    @property
    def value_on_new_line(self):
        return bool(self.second_formatting.find("endl"))

    @property
    def _endl(self):
        return self.fourth_formatting.find("endl")

    def remove_endl(self):
        self.fourth_formatting.pop()


class DictComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse(f"{{x {value}}}")[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse(f"{{{value} for x in x}}")[0]["result"]


class DotNode(Node):
    def _default_fst(self):
        return {"type": "dot", "first_formatting": [], "second_formatting": []}

    @property
    def on_new_line(self):
        return super().on_new_line or self.first_formatting.endl

    def increase_indentation(self, indent=None):
        self.first_formatting.increase_indentation(indent=indent)
        self.second_formatting.increase_indentation(indent=indent)

    def decrease_indentation(self, indent=None):
        self.first_formatting.decrease_indentation(indent=indent)
        self.second_formatting.decrease_indentation(indent=indent)


class DottedAsNameNode(ValueIterableMixin, Node):
    _target = None

    @nodelist_property(DotProxyList)
    def value(self, value):
        code = f"import {value}"
        return baron.parse(code)[0]["value"][0]["value"]

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        if not (re.match(r"^[a-zA-Z_]\w*$", value) or value in ("", None)):
            raise Exception("The target of a dotted as name node can only be a 'name' or an empty string or None")
        self._target = value

    @conditional_formatting_property(NodeList, [" "], [])
    def first_formatting(self):
        return self.target

    @conditional_formatting_property(NodeList, [" "], [])
    def second_formatting(self):
        return self.target


class DottedNameNode(ValueIterableMixin, Node):
    pass


class ElifNode(IfElseBlockSiblingMixin, IndentedCodeBlockMixin, Node):
    @NodeProperty
    def test(self, value):
        code = f"if {value}: pass"
        return baron.parse(code)[0]["value"][0]["test"]


class EllipsisNode(Node):
    pass


class ElseNode(IfElseBlockSiblingMixin, IndentedCodeBlockMixin, Node):
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
        return {"type": "endl", "formatting": [], "value": "\n", "indent": ""}

    def consume_leftover_indentation(self):
        indent = self.indent
        self.indent = ""
        return indent

    @property
    def _endl(self):
        return self

    def increase_indentation(self, indent=None):
        if indent is None:
            indent = self.indent_unit

        super().increase_indentation(indent=indent)
        self.indent = indent_str(self.indent + "a", indent)[:-1]  # pylint: disable=attribute-defined-outside-init

    def decrease_indentation(self, indent=None):
        if indent is None:
            indent = self.indent_unit

        super().decrease_indentation(indent=indent)
        self.indent = deindent_str(self.indent, indent)  # pylint: disable=attribute-defined-outside-init


class ExceptNode(IndentedCodeBlockMixin, Node):
    @NodeProperty
    def target(self, value):
        if not self.exception:
            raise Exception("Can't set a target to an exception node that doesn't have an exception set")

        if value == "":
            return None

        code = f"try: pass\nexcept a as {value}: pass"
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
        code = f"try: pass\nexcept {value}: pass"
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


class ExceptStarNode(IndentedCodeBlockMixin, Node):
    """Exception group handler (except*) node for Python 3.11+."""

    @NodeProperty
    def target(self, value):
        if not self.exception:
            raise Exception("Can't set a target to an except* node that doesn't have an exception set")

        if value == "":
            return None

        code = f"try: pass\nexcept* a as {value}: pass"
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
        code = f"try: pass\nexcept* {value}: pass"
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
        return baron.parse(f"exec {value}")[0]["value"]

    @NodeProperty
    def locals(self, value):
        if not value:
            return None

        if not self.globals:
            raise Exception("I can't set locals when globals aren't set.")
        return baron.parse(f"exec a in b, {value}")[0]["locals"]

    @NodeProperty
    def globals(self, value):
        if not value:
            return None
        return baron.parse(f"exec a in {value}")[0]["globals"]

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
        code = f"try: pass\nexcept: pass\nelse:\n{value}"
        return baron.parse(code)[0]["else"]


class ForNode(ElseMixin, IndentedCodeBlockMixin, Node):
    @conditional_formatting_property(NodeList, [" "], [])
    def async_formatting(self):
        return self.async_

    @NodeProperty
    def target(self, value):
        return baron.parse(f"for i in {value}: pass")[0]["target"]

    @NodeProperty
    def iterator(self, value):
        return baron.parse(f"for {value} in i: pass")[0]["iterator"]

    @property
    def next_intuitive(self):
        if self.else_:
            return self.else_

        return self.next


class FromImportNode(ValueIterableMixin, Node):
    def names(self):
        """Return the list of new names imported

        For example:
            RedBaron("from qsd import a, c, e as f").names() == ['a', 'c', 'f']
        """
        return [
            x.target if x.target else x.value
            for x in self.targets  # pylint: disable=not-an-iterable
            if not isinstance(x, (LeftParenthesisNode, RightParenthesisNode))
        ]

    def modules(self):
        """Return the list of the targets imported

        For example (notice 'e' instead of 'f'):
            RedBaron("from qsd import a, c, e as f").names() == ['a', 'c', 'e']
        """
        return [x.value for x in self.targets]  # pylint: disable=not-an-iterable

    def full_path_names(self):
        """Return the list of new names imported with the full module path

        For example (notice 'e' instead of 'f'):
            RedBaron("from qsd import a, c, e as f").names() == ['qsd.a', 'qsd.c', 'qsd.f']
        """
        base = self.value.dumps()
        return [
            base + "." + (x.target if x.target else x.value)  # pylint: disable=no-member
            for x in self.targets  # pylint: disable=not-an-iterable
            if not isinstance(x, (LeftParenthesisNode, RightParenthesisNode))
        ]

    def full_path_modules(self):
        """Return the list of the targets imported with the full module path

        For example (notice 'e' instead of 'f'):
            RedBaron("from qsd import a, c, e as f").names() == ['qsd.a', 'qsd.c', 'qsd.e']
        """
        base = self.value.dumps()
        return [
            base + "." + x.value  # pylint: disable=no-member
            for x in self.targets  # pylint: disable=not-an-iterable
            if not isinstance(x, (LeftParenthesisNode, RightParenthesisNode))
        ]

    @nodelist_property(ImportsProxyList)
    def targets(self, value):
        return baron.parse(f"from a import {value}")[0]["targets"]

    @nodelist_property(DotProxyList)
    def value(self, value):
        return baron.parse(f"from {value} import s")[0]["value"]


class GeneratorComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse(f"(x {value})")[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse(f"({value} for x in x)")[0]["result"]


class GetitemNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"a[{value}]")[0]["value"][1]["value"]


class GlobalNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse(f"global {value}")[0]["value"]


class HexaNode(Node, LiteralyEvaluableMixin):
    pass


class IfNode(IfElseBlockSiblingMixin, IndentedCodeBlockMixin, Node):
    @NodeProperty
    def test(self, value):
        return baron.parse(f"if {value}: pass")[0]["value"][0]["test"]

    @property
    def value_on_new_line(self):
        return bool(self.second_formatting.find("endl"))

    def increase_indentation(self, indent=None):
        self.value.increase_indentation(indent)

    def decrease_indentation(self, indent=None):
        self.value.decrease_indentation(indent)


class IfelseblockNode(CodeBlockMixin, Node):
    @nodelist_property(CodeProxyList)
    def value(self, value):
        if value.startswith(" "):
            raise ValueError("except cannot be indented")
        return super()._parse_value(value, replace=True)

    @property
    def value_on_new_line(self):
        return True

    def increase_indentation(self, indent=None):
        Node.increase_indentation(self, indent)
        self.value.increase_indentation(indent)

    def decrease_indentation(self, indent=None):
        Node.decrease_indentation(self, indent)
        self.value.decrease_indentation(indent)


class ImportNode(ValueIterableMixin, Node):
    def modules(self):
        "return a list of string of modules imported"
        return [x.value.dumps() for x in self.find_all("dotted_as_name")]

    def names(self):
        "return a list of string of new names inserted in the python context"
        return [x.target if x.target else x.value.dumps() for x in self.find_all("dotted_as_name")]

    @nodelist_property(ImportsProxyList)
    def value(self, value):
        return baron.parse(f"import {value}")[0]["value"]


class NumberNode(Node, LiteralyEvaluableMixin):
    def fst(self):
        return {
            "type": "number",
            "sub_type": "int",
            "value": self.value,
        }

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self.sub_type == "binary" and not re.match(r"^0b[01]+$", value):
            raise ValueError(f"invalid value {value} for binary node")
        self._value = value  # pylint: disable=attribute-defined-outside-init


class InterpolatedStringNode(Node, LiteralyEvaluableMixin):
    _other_identifiers = ["fstring"]


class InterpolatedRawStringNode(Node, LiteralyEvaluableMixin):
    _other_identifiers = ["raw_fstring"]


class KwargsOnlyMarkerNode(Node):
    pass


class LambdaNode(Node):
    @nodelist_property(ArgsProxyList)
    def arguments(self, value):
        return baron.parse(f"lambda {value}: x")[0]["arguments"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def first_formatting(self):
        return self.arguments

    @NodeProperty
    def value(self, value):
        return baron.parse(f"lambda: {value}")[0]["value"]


class LeftParenthesisNode(Node):
    def _default_fst(self):
        return {"type": "left_parenthesis", "value": "("}


class ListArgumentNode(AnnotationMixin, Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"lambda *{value}: x")[0]["arguments"][0]["value"]


class ListComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse(f"[x {value}]")[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse(f"[{value} for x in x]")[0]["result"]


class ListNode(FourthFormattingIndentMixin, ListTupleMixin, ValueIterableMixin, LiteralyEvaluableMixin, Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse(f"[{value}]")[0]["value"]

    @value.after_set
    def value(self, value):
        self.move_second_formatting()

    def move_second_formatting(self):
        indent = self.second_formatting.consume_leftover_indentation()
        if indent:
            if self.value:
                self.value[0].indentation += indent
                self.value._data_to_node_list()
            else:
                self.value.append(SpaceNode.make(indent))

    @property
    def _endl(self):
        return self.fourth_formatting.find("endl")

    def remove_endl(self):
        self.fourth_formatting.pop()

    def consume_leftover_indentation(self):
        if self.fourth_formatting and self.fourth_formatting.find("endl"):
            return self.fourth_formatting.consume_leftover_indentation()

        if self.fourth_formatting:
            return self.value.consume_leftover_indentation() + self.fourth_formatting.consume_leftover_indentation()

        return self.value.consume_leftover_indentation()


class LongNode(Node):
    pass


class MatchNode(IndentedCodeBlockMixin, Node):
    """Pattern matching statement (Python 3.10+)."""

    @NodeProperty
    def subject(self, value):
        code = f"match {value}:\n    case _: pass"
        return baron.parse(code)[0]["subject"]


class NameNode(LiteralyEvaluableMixin, Node):
    pass


class NamedExprNode(Node):
    """Walrus operator (:=) node."""

    @NodeProperty
    def value(self, value):
        return baron.parse(f"({self.target} := {value})")[0]["value"]["value"]


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
        if not (re.match(r"^[a-zA-Z_]\w*$", value) or value in ("", None)):
            raise Exception("The target of a name as name node can only be a 'name' or an empty string or None")
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
        if not (re.match(r"^[a-zA-Z_]\w*$", value) or value in ("", None)):
            raise Exception("The value of a name as name node can only be a 'name' or an empty string or None")
        self._value = value


class NonlocalNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse(f"global {value}")[0]["value"]


class OctaNode(LiteralyEvaluableMixin, Node):
    pass


class PassNode(Node):
    pass


class PatternAsNode(Node):
    """Pattern with 'as' binding (Python 3.10+)."""

    @NodeProperty
    def pattern(self, value):
        code = f"match x:\n    case {value} as y: pass"
        return baron.parse(code)[0]["cases"][1]["pattern"]["pattern"]


class PatternOrNode(Node):
    """Pattern with '|' alternatives (Python 3.10+)."""

    pass


class PositionalOnlyMarkerNode(Node):
    """Positional-only parameter marker (/) node."""

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
        return baron.parse(f"print{value}")[0]["value"]


class RaiseNode(Node):
    @property
    def comma_or_from(self):
        return "from" if self.instance else ""

    @comma_or_from.setter
    def comma_or_from(self, value):
        if value == "":
            value = None

        if value not in (None, "from"):
            raise ValueError(f"invalid value {value} for comma_or_from")

    @NodeProperty
    def value(self, value):
        return baron.parse(f"raise {value}")[0]["value"]

    @value.after_set
    def value(self, value):
        if value:
            if not self.first_formatting:
                self.first_formatting = [" "]
        elif value is not None:
            self.first_formatting = []

    @NodeProperty
    def instance(self, value):
        if not self.value:
            raise ValueError("Can't set instance if there is no value")
        if not value:
            return None
        return baron.parse(f"raise a from {value}")[0]["instance"]

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
        return baron.parse(f"raise a, b, {value}")[0]["traceback"]


class RawStringNode(LiteralyEvaluableMixin, Node):
    pass


class RightParenthesisNode(Node):
    def _default_fst(self):
        return {"type": "right_parenthesis", "value": ")"}


class ReprNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse(f"`{value}`")[0]["value"]


class ReturnNode(Node):
    formatting = NodeListProperty(NodeList)

    @NodeProperty
    def value(self, value):
        return baron.parse(f"return {value}")[0]["value"]

    @value.after_set
    def value(self, value):
        if value:
            if not self.formatting:
                self.formatting = [" "]
        elif value is not None:
            self.formatting = []


class SemicolonNode(Node):
    pass


class SetNode(Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        return baron.parse(f"{{{value}}}")[0]["value"]


class SetComprehensionNode(Node):
    @nodelist_property(NodeList)
    def generators(self, value):
        return baron.parse(f"{{x {value}}}")[0]["generators"]

    @NodeProperty
    def result(self, value):
        return baron.parse(f"{{{value} for x in x}}")[0]["result"]


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
        return baron.parse(f"a[{value}:]")[0]["value"][1]["value"]["lower"]

    @NodeProperty
    def upper(self, value):
        return baron.parse(f"a[:{value}]")[0]["value"][1]["value"]["upper"]

    @NodeProperty
    def step(self, value):
        return baron.parse(f"a[::{value}]")[0]["value"][1]["value"]["step"]


class SpaceNode(SeparatorMixin, Node):
    value = ""

    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def _default_fst(self):
        return {"type": "space", "value": " "}

    @classmethod
    def make(cls, value, parent=None, on_attribute=None):
        return cls({"type": "space", "value": value}, parent=parent, on_attribute=on_attribute)

    def consume_leftover_indentation(self):
        try:
            indent = self.value.splitlines()[-1]  # pylint: disable=access-member-before-definition
        except IndexError:
            indent = ""
        self.value = ""  # pylint: disable=attribute-defined-outside-init
        return indent

    @property
    def _endl(self):
        return super()._endl or "\n" in self.value

    def increase_indentation(self, indent=None):
        if indent is None:
            indent = self.indent_unit

        super().increase_indentation(indent=indent)
        self.value = indent_str(self.value + "a", indent)[len(indent) : -1]  # pylint: disable=attribute-defined-outside-init

    def decrease_indentation(self, indent=None):
        if indent is None:
            indent = self.indent_unit

        if "\n" not in self.value:
            return

        super().decrease_indentation(indent=indent)
        self.value = deindent_str(indent + self.value, indent)  # pylint: disable=attribute-defined-outside-init


class StandaloneAnnotationNode(Node):
    pass


class StarExpressionNode(Node):
    pass


class StarNode(Node):
    pass


class StringNode(LiteralyEvaluableMixin, SecondFormattingIndentMixin, Node):
    pass


class StringChainNode(LiteralyEvaluableMixin, Node):
    @nodelist_property(NodeList)
    def value(self, value):
        return baron.parse(f"a = {value}")[0]["value"]["value"]


class TernaryOperatorNode(Node):
    @NodeProperty
    def first(self, value):
        return baron.parse(f"{value} if b else c")[0]["first"]

    @NodeProperty
    def second(self, value):
        return baron.parse(f"a if b else {value}")[0]["second"]

    @NodeProperty
    def value(self, value):
        return baron.parse(f"a if {value} else s")[0]["value"]

    @property
    def _endl(self):
        return self.value.endl

    def remove_endl(self):
        self.value.remove_endl()


class TryNode(ElseMixin, FinallyMixin, IndentedCodeBlockMixin, Node):
    @property
    def next_intuitive(self):
        if self.excepts:
            return self.excepts[0]  # pylint: disable=unsubscriptable-object

        if self.finally_:
            return self.finally_

        raise Exception("incoherent state of TryNode, try should be followed either by except or finally")

    @nodelist_property(NodeList)
    def excepts(self, value):
        if value.startswith(" "):
            raise ValueError("except cannot be indented")
        code = f"try:\n pass\n{value}finally:\n pass"
        return baron.parse(code)[0]["excepts"]

    @excepts.after_set
    def excepts(self, value):
        self.value.consume_leftover_indentation()
        # self.excepts.indentation = self.indentation

    def get_last_member(self):
        if self.finally_:
            return self.finally_
        if self.else_:
            return self.else_
        return self.excepts[-1]  # pylint: disable=unsubscriptable-object

    def fst(self):
        fst = super().fst()

        space = {"type": "space", "value": self.indentation}
        if self.excepts:
            fst["value"].append(space)

        if self.else_:
            if self.excepts:
                fst["excepts"].append(space)
            else:
                fst["value"].append(space)

        if self.finally_:
            if self.else_:
                fst["else"]["value"].append(space)
            elif self.excepts:
                fst["excepts"].append(space)
            else:
                fst["value"].append(space)

        return fst

    def increase_indentation(self, indent=None):
        ElseMixin.increase_indentation(self, indent)
        self.excepts.increase_indentation(indent)
        if self.finally_:
            self.finally_.increase_indentation(indent)

    def decrease_indentation(self, indent=None):
        ElseMixin.decrease_indentation(self, indent)
        for except_ in self.excepts:
            except_.decrease_indentation(indent)
        if self.finally_:
            self.finally_.decrease_indentation(indent)


class TupleNode(ListTupleMixin, ValueIterableMixin, LiteralyEvaluableMixin, Node):
    @nodelist_property(CommaProxyList)
    def value(self, value):
        fst = baron.parse(f"({value})")[0]["value"]

        # I assume that I've got an AssociativeParenthesisNode here instead
        # of a tuple because string is only one single element
        if not isinstance(fst, list):
            assert fst["type"] == "associativeparenthesis"
            fst = baron.parse(f"({value},)")[0]["value"]

        return fst


class TypeParamNode(Node):
    """Type parameter node for PEP 695 (Python 3.12+)."""

    @NodeProperty
    def bound(self, value):
        if not value:
            return None
        code = f"def foo[T: {value}](): pass"
        return baron.parse(code)[0]["type_params"][0]["bound"]


class TypeParamStarNode(Node):
    """TypeVarTuple parameter (*Ts) for PEP 695 (Python 3.12+)."""

    pass


class TypeParamDoubleStarNode(Node):
    """ParamSpec parameter (**P) for PEP 695 (Python 3.12+)."""

    pass


class UnicodeStringNode(LiteralyEvaluableMixin, Node):
    pass


class UnicodeRawStringNode(LiteralyEvaluableMixin, Node):
    pass


class UnitaryOperatorNode(Node):
    @NodeProperty
    def target(self, value):
        return baron.parse(f"-{value}")[0]["target"]


class YieldNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"yield {value}")[0]["value"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def formatting(self):
        return self.value


class YieldFromNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"yield from {value}")[0]["value"]


class YieldAtomNode(Node):
    @NodeProperty
    def value(self, value):
        return baron.parse(f"yield {value}")[0]["value"]

    @conditional_formatting_property(NodeList, [" "], [], allow_set=False)
    def second_formatting(self):
        return self.value


class WhileNode(ElseMixin, IndentedCodeBlockMixin, Node):
    @NodeProperty
    def test(self, value):
        return baron.parse(f"while {value}: pass")[0]["test"]

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
        return baron.parse(f"with {value}: pass")[0]["contexts"][0]["value"]

    @NodeProperty
    def as_(self, value):
        if not value:
            return None
        return baron.parse(f"with {value}: pass")[0]["contexts"][0]["value"]

    @conditional_formatting_property(NodeList, [" "], [])
    def first_formatting(self):
        return self.as_

    @conditional_formatting_property(NodeList, [" "], [])
    def second_formatting(self):
        return self.as_


class WithNode(IndentedCodeBlockMixin, Node):
    @nodelist_property(ContextsProxyList)
    def contexts(self, value):
        return baron.parse(f"with {value}: pass")[0]["contexts"]

    @conditional_formatting_property(NodeList, [" "], [])
    def async_formatting(self):
        return self.async_  # pylint: disable=no-member


class EmptyLineNode(Node):
    def _default_fst(self):
        return {"type": "empty_line", "value": ""}

    def __repr__(self):
        return repr(baron.dumps([self.fst()]))

    def fst(self):
        return self._default_fst()


class IndentationNode(SpaceNode):
    baron_type = "indentation"

    def __init__(self, node, parent=None, on_attribute=None):
        from .base_nodes import BaseNode

        assert isinstance(node, BaseNode)
        self.node = node
        super().__init__(parent=parent, on_attribute=on_attribute)

    def _default_fst(self):
        return {"type": "indentation", "value": None}

    @property
    def value(self):
        return self.node.indentation

    @value.setter
    def value(self, new_value):
        assert new_value is None

    def fst(self):
        fst = super().fst()
        fst["type"] = "space"
        return fst

    def consume_leftover_indentation(self):
        return ""
