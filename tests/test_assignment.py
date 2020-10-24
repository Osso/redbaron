from redbaron import (RedBaron,
                      node)
from redbaron.nodes import NameNode
from redbaron.proxy_list import CommaProxyList


def test_assign_on_string_value():
    binop = node("ax + (z * 4)")
    assert binop.first.value == "ax"

    binop.first.value = "pouet"
    assert binop.first.value == "pouet"


def test_assign_on_object_value():
    binop = node("ax + (z * 4)")
    assert binop.first.value == "ax"

    binop.first = "pouet"  # will be parsed as a name
    assert binop.first.value == "pouet"
    assert binop.first.type == "name"
    binop.first = "42"  # will be parsed as a int
    assert binop.first.value == "42"
    assert binop.first.type == "int"


def test_assign_on_object_value_fst():
    binop = node("ax + (z * 4)")
    assert binop.first.value == "ax"

    binop.first = {"type": "name", "value": "pouet"}
    assert binop.first.value == "pouet"
    assert binop.first.type == "name"


def test_assign_node_list():
    list_node = node("[1, 2, 3]")
    list_node.value = "pouet"
    assert list_node.value[0].value == "pouet"
    assert list_node.value[0].type == "name"
    assert isinstance(list_node.value, CommaProxyList)
    list_node.value = ["pouet"]
    assert list_node.value[0].value == "pouet"
    assert list_node.value[0].type == "name"
    assert isinstance(list_node.value, CommaProxyList)


def test_assign_node_list_fst():
    red = RedBaron("[1, 2, 3]")
    tree = red[0]
    tree.value[0] = {"type": "name", "value": "pouet"}
    assert tree.value[0].value == "pouet"
    assert tree.value[0].type == "name"
    assert isinstance(tree.value, CommaProxyList)
    tree.value = [{"type": "name", "value": "pouet"}]
    assert tree.value[0].value == "pouet"
    assert tree.value[0].type == "name"
    assert isinstance(tree.value, CommaProxyList)


def test_assign_node_list_mixed():
    red = RedBaron("[1, 2, 3]")
    tree = red[0]
    tree.value = ["plop",
                  {"type": "comma",
                   "first_formatting": [],
                   "second_formatting": []},
                  {"type": "name", "value": "pouet"}]
    assert tree.value[0].value == "plop"
    assert tree.value[0].type == "name"
    assert tree.value.node_list[1].type == "comma"
    assert tree.value[1].value == "pouet"
    assert tree.value[1].type == "name"
    assert tree.value.node_list[2].value == "pouet"
    assert tree.value.node_list[2].type == "name"
    assert isinstance(tree.value, CommaProxyList)


def test_parent_assign():
    red = RedBaron("a = 1 + caramba")
    assert red[0].target.parent is red[0]
    red[0].target = "plop"
    assert red[0].target.parent is red[0]
    assert red[0].target.on_attribute == "target"
    red[0].target = {"type": "name", "value": "pouet"}
    assert red[0].target.parent is red[0]
    assert red[0].target.on_attribute == "target"
    red[0].target = NameNode({"type": "name", "value": "pouet"})
    assert red[0].target.parent is red[0]
    assert red[0].target.on_attribute == "target"


def test_parent_assign_list():
    red = RedBaron("[1, 2, 3]")
    assert [x.parent for x in red[0].value] == [red[0].value] * 3
    assert [x.on_attribute for x in red[0].value] == [None] * 3
    assert [x.parent for x in red[0].value.node_list] == [red[0].value] * 5
    assert [x.on_attribute for x in red[0].value.node_list] == [None] * 5
    red[0] = "['pouet']"
    assert red[0].parent == red.value
    assert [x.parent for x in red[0].value] == [red[0].value]
    assert [x.on_attribute for x in red[0].value] == [None]
    red[0].value = ["pouet"]
    assert [x.parent for x in red[0].value] == [red[0].value]
    assert [x.on_attribute for x in red[0].value] == [None]
    red[0].value = [{"type": "name", "value": "plop"}]
    assert [x.parent for x in red[0].value] == [red[0].value]
    assert [x.on_attribute for x in red[0].value] == [None]
    red[0].value = [NameNode({"type": "name", "value": "pouet"})]
    assert [x.parent for x in red[0].value] == [red[0].value]
    assert [x.on_attribute for x in red[0].value] == [None]
