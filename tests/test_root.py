""" Tests the root method """

# pylint: disable=redefined-outer-name
import pytest

from redbaron import RedBaron


@pytest.fixture
def red():
    return RedBaron("""\
@deco
def a(c, d):
    b = c + d
""")


def test_root(red):
    nodes = [
        red.find("def"),
        red.find("def").decorators,
        red.find("def").decorators.node_list[0],
        red.find("def").decorators.node_list[0].value,
        red.find("def").decorators.node_list[0].value.value,
        red.find("def").decorators.node_list[0].value.value[0],
        red.find("def").decorators.node_list[1],
        red.find("def").first_formatting,
        red.find("def").first_formatting[0],
        red.find("def").second_formatting,
        red.find("def").third_formatting,
        red.find("def").arguments,
        red.find("def").arguments.node_list[0],
        red.find("def").arguments.node_list[1],
        red.find("def").arguments.node_list[2],
        red.find("def").fourth_formatting,
        red.find("def").fifth_formatting,
        red.find("def").sixth_formatting,
        red.find("def").value,
        red.find("def").value.node_list[0],
        red.find("def").value.node_list[1],
        red.find("def").value.node_list[2].target,
        red.find("def").value.node_list[2].value,
        red.find("def").value.node_list[2].value.first,
        red.find("def").value.node_list[2].value.second,
        red.find("def").value.node_list[3]
    ]

    for node in nodes:
        assert red is node.root


def test_get_root():
    red = RedBaron("def a(b=c):\n    return 42")
    assert red is red.find("number").root
