from redbaron import RedBaron, node
from redbaron.nodes import NameNode
from redbaron.proxy_list import CommaProxyList


def test_assign_on_string_value():
    binop = node("ax + (z * 4)")

    binop.first.value = "pouet"
    assert binop.first.value == "pouet"


def test_assign_on_object_value():
    binop = node("ax + (z * 4)")

    binop.first = "pouet"  # will be parsed as a name
    assert binop.first.value == "pouet"
    assert binop.first.type == "name"

    binop.first = "42"  # will be parsed as a int
    assert binop.first.value == "42"
    assert binop.first.type == "number"


def test_assign_on_object_value_fst():
    binop = node("ax + (z * 4)")
    assert binop.first.value == "ax"

    binop.first = {"type": "name", "value": "pouet"}
    assert binop.first.value == "pouet"
    assert binop.first.type == "name"


def test_assign_node_list():
    list_node = node("[1, 2, 3]")

    list_node.value = ["pouet"]
    assert list_node.value[0].value == "pouet"
    assert list_node.value[0].type == "name"
    assert isinstance(list_node.value, CommaProxyList)


def test_assign_node_list_fst():
    list_node = node("[1, 2, 3]")

    list_node.value = [{"type": "name", "value": "pouet"}]
    assert list_node.value[0].value == "pouet"
    assert list_node.value[0].type == "name"
    assert isinstance(list_node.value, CommaProxyList)


def test_assign_node_list_mixed():
    list_node = node("[1, 2, 3]")

    list_node.value = [
        "plop",
        {"type": "comma", "first_formatting": [], "second_formatting": []},
        {"type": "name", "value": "pouet"},
    ]
    assert isinstance(list_node.value, CommaProxyList)

    assert list_node.value[0].value == "plop"
    assert list_node.value[0].type == "name"

    assert list_node.value.node_list[1].type == "comma"
    assert list_node.value[1].value == "pouet"
    assert list_node.value[1].type == "name"

    assert list_node.value.node_list[2].value == "pouet"
    assert list_node.value.node_list[2].type == "name"


def test_parent_assign():
    assign_node = node("a = 1 + caramba")
    assert assign_node.target.parent is assign_node
    assert assign_node.target.on_attribute == "target"

    assign_node.target = "plop"
    assert assign_node.target.parent is assign_node
    assert assign_node.target.on_attribute == "target"

    assign_node.target = {"type": "name", "value": "pouet"}
    assert assign_node.target.parent is assign_node
    assert assign_node.target.on_attribute == "target"

    assign_node.target = NameNode({"type": "name", "value": "pouet"})
    assert assign_node.target.parent is assign_node
    assert assign_node.target.on_attribute == "target"


def test_parent_assign_list():
    red = RedBaron("[1, 2, 3]")
    list_node = red[0]

    list_node.value = "['pouet']"
    assert list_node.parent == red.value
    assert [x.parent for x in list_node.value] == [list_node.value]
    assert [x.on_attribute for x in list_node.value] == [None]

    list_node.value = ["pouet"]
    assert [x.parent for x in list_node.value] == [list_node.value]
    assert [x.on_attribute for x in list_node.value] == [None]

    list_node.value = [{"type": "name", "value": "plop"}]
    assert [x.parent for x in list_node.value] == [list_node.value]
    assert [x.on_attribute for x in list_node.value] == [None]

    list_node.value = [NameNode({"type": "name", "value": "pouet"})]
    assert [x.parent for x in list_node.value] == [list_node.value]
    assert [x.on_attribute for x in list_node.value] == [None]


def test_assign_list_index():
    list_node = node("[1, 2, 3]")
    list_node[0] = "pouet"
    assert list_node[0].parent == list_node.value
    assert list_node[0].value == "pouet"
