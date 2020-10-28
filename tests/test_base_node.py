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
