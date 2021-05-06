import pytest
from redbaron import (RedBaron,
                      node)
from redbaron.base_nodes import NodeList
from redbaron.nodes import (RawStringNode,
                            SpaceNode)


def test_redbaron_classname_to_baron_type():
    assert SpaceNode.baron_type == 'space'
    assert SpaceNode().type == 'space'
    assert RawStringNode.baron_type == 'raw_string'


def test_dumps():
    some_code = "ax + (z * 4)"
    red = RedBaron(some_code)
    assert some_code == red.dumps()


def test_generate_identifiers():
    red = RedBaron("def a(): pass")
    assert set(red[0].generate_identifiers()) == set(["defnode", "def"])


def test_index():
    red = RedBaron("a = [1, 2, 3]")
    assert red[0].value[2].index_on_parent == 2
    assert red[0].index_on_parent == 0
    with pytest.raises(ValueError):
        red[0].value.index_on_parent  # pylint: disable=pointless-statement


def test_filter():
    red = node("[1, 2, 3]")
    filtered_list = red.value.filter(lambda x: x.value == "2")
    assert isinstance(filtered_list, NodeList)
    assert filtered_list.dumps() == "2"


def test_associated_sep():
    red = node("[1, 2]")
    assert red[0].associated_sep.baron_type == "comma"
    assert red[1].associated_sep is None


def test_endl():
    red = RedBaron("# line1\n#line2")
    assert red[0].endl.baron_type == "endl"
    assert red[1].endl is None
    red = node("[1, 2,\n]")
    assert red[1].endl.baron_type == "endl"


def test_value_on_new_line():
    red = node("[1, 2, 3]")
    assert not red.value_on_new_line
    red = node("(1, 2, 3)")
    assert not red.value_on_new_line
    red = node("[\n1, 2, 3]")
    assert red.value_on_new_line
    red = node("(\n1, 2, 3)")
    assert red.value_on_new_line


def test_on_new_line():
    red = node("[1, 2,\n3]")
    assert not red[0].on_new_line
    assert not red[1].on_new_line
    assert red[2].on_new_line
    red = node("[1, 2, 3]")
    assert not red[0].on_new_line
    red = node("[\n1, 2, 3]")
    assert red[0].on_new_line


def test_copy_with_indentation():
    red = RedBaron("def a():\n    pass")
    assert red[0][0].copy().indentation == "    "


def test_endl_if():
    red = RedBaron("if a:\n pass\nfoo")
    assert red[0].endl
    assert not red[1].endl


def test_on_new_line_if():
    red = RedBaron("if a:\n pass\nfoo")
    assert red[0].on_new_line
    assert red[1].on_new_line


def test_on_new_line_if_content():
    red = RedBaron("if a:\n pass\n")
    assert red[0][0].on_new_line


def test_copy_raise():
    code = "raise NotImplementedError"
    el = node(code).copy()
    assert el.dumps() == code


def test_hide():
    red = node("[1, 2, 3]")
    red.hide(red[0])
    assert red.dumps() == "[2, 3]"
