""" Tests initial parsing through the RedBaron() base function """
from redbaron import RedBaron
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
    red = RedBaron("1\n")
    assert isinstance(red[0], IntNode)
    assert red[0].value == "1"


def test_assignment():
    red = RedBaron("a = 2")
    assert isinstance(red[0], AssignmentNode)
    assert isinstance(red[0].value, IntNode)
    assert red[0].value.value == "2"
    assert isinstance(red[0].target, NameNode)
    assert red[0].target.value == "a"


def test_binary_operator():
    red = RedBaron("z +  42")
    assert red[0].value == "+"
    assert isinstance(red[0].first, NameNode)
    assert red[0].first.value == "z"
    assert isinstance(red[0].second, IntNode)
    assert red[0].second.value == "42"

    red = RedBaron("z  -      42")
    assert red[0].value == "-"
    assert isinstance(red[0].first, NameNode)
    assert red[0].first.value == "z"
    assert isinstance(red[0].second, IntNode)
    assert red[0].second.value == "42"


def test_pass():
    red = RedBaron("pass")
    assert isinstance(red[0], PassNode)


def test_parent_and_on_attribute():
    red = RedBaron("a = 1 + caramba")
    assert red.parent is None
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


def test_other_name_assignment():
    red = RedBaron("a = b")
    assert red.assign is red[0]
