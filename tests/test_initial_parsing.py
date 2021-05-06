""" Tests initial parsing through the RedBaron() base function """
from redbaron import (RedBaron,
                      node)
from redbaron.nodes import (AssignmentNode,
                            EndlNode,
                            IntNode,
                            NameNode,
                            PassNode)


def test_empty():
    RedBaron("")


def test_is_list():
    assert list(RedBaron("")) == []


def test_name():
    red = RedBaron("a\n")
    assert len(red.value.node_list) == 2
    assert isinstance(red.value.node_list[0], NameNode)
    assert isinstance(red.value.node_list[1], EndlNode)
    assert red[0].value == "a"


def test_int():
    red = node("1")
    assert isinstance(red, IntNode)
    assert red.value == "1"


def test_assignment():
    red = RedBaron("a = 2")
    assert isinstance(red[0], AssignmentNode)
    assert isinstance(red[0].value, IntNode)
    assert red[0].value.value == "2"
    assert isinstance(red[0].target, NameNode)
    assert red[0].target.value == "a"


def test_binary_operator_plus():
    binop = node("z +  42")
    assert binop.value == "+"
    assert isinstance(binop.first, NameNode)
    assert binop.first.value == "z"
    assert isinstance(binop.second, IntNode)
    assert binop.second.value == "42"


def test_binary_operator_minus():
    binop = node("z  -      42")
    assert binop.value == "-"
    assert isinstance(binop.first, NameNode)
    assert binop.first.value == "z"
    assert isinstance(binop.second, IntNode)
    assert binop.second.value == "42"


def test_binary_operator_more_complex():
    binop = node("ax + (z * 4)")
    assert binop.first.value == "ax"


def test_pass():
    red = node("pass")
    assert isinstance(red, PassNode)


def test_parent_and_on_attribute():
    red = RedBaron("a = 1 + caramba")
    assert red.parent is None
    assert red.value.parent is red
    assert red[0].parent is red.value
    assert red[0].parent.parent is red
    assert red.value.on_attribute == "value"
    assert red[0].on_attribute is None
    assert red[0].target.parent is red[0]
    assert red[0].target.on_attribute == "target"
    assert red[0].value.parent is red[0]
    assert red[0].value.on_attribute == "value"
    assert red[0].value.first.parent is red[0].value
    assert red[0].value.first.on_attribute == "first"
    assert red[0].value.second.parent is red[0].value
    assert red[0].value.second.on_attribute == "second"


def test_parent_and_on_attribute_list():
    red = RedBaron("[1, 2, 3]")
    assert red.parent is None
    assert red[0].parent is red.value
    assert red[0].parent.parent is red
    assert [x.parent for x in red[0].value.node_list] == [red[0].value] * 5
    assert [x.on_attribute for x in red[0].value.node_list] == [None] * 5
    assert [x.parent for x in red[0].value] == [red[0].value] * 3
    assert [x.on_attribute for x in red[0].value] == [None] * 3


def test_kwargs_only_marker_node():
    RedBaron("def a(*): pass")


def test_import():
    red = RedBaron("from m import a")
    assert red[0].targets.dumps() == "a"


def test_import_multi():
    red = RedBaron("from m import a, b")
    assert red[0].targets.dumps() == "a, b"


def test_import_multiline():
    red = RedBaron("from m import (a,\n   b)")
    assert red[0].targets.dumps() == "(a,\n   b)"


def test_import_on_new_line():
    red = RedBaron("from m import (\n"
                   "   a)")
    assert red[0].targets.dumps() == "(\n   a)"


def test_double_separator():
    red = RedBaron("fun(a,,)")
    assert red[0].dumps() == "fun(a,)"


def test_comment_in_args():
    red = RedBaron("fun(\n"
                   "# comment\n"
                   "a)")
    assert red[0].dumps() == "fun(\n# comment\na)"
