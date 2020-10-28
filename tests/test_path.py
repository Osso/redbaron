""" Tests the path method """

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


def check_path(root, node, path):
    assert node.path().to_baron_path()[1:] == path
    assert root.find_by_path(path) is node


def test_path_root(red):
    check_path(red, red, [])


def test_path_invalid_type(red):
    with pytest.raises(ValueError):
        assert red.find_by_path([7])


def test_path_none(red):
    with pytest.raises(ValueError):
        assert red.find_by_path(["value", 7])


def test_path_first_statement(red):
    check_path(red, red.find("def"), [0])


def test_path_def_decorators(red):
    check_path(red, red.find("def").decorators, [0, "decorators"])


def test_path_decorators_first(red):
    check_path(red, red.find("def").decorators.node_list[0], [0, "decorators", 0])


def test_path_decorators_first_dotted_name(red):
    check_path(red, red.find("def").decorators.node_list[0].value,
               [0, "decorators", 0, "value"])


def test_path_decorators_first_dotted_name_value(red):
    check_path(red, red.find("def").decorators.node_list[0].value.value,
               [0, "decorators", 0, "value", "value"])


def test_path_decorators_first_dotted_name_value_first(red):
    check_path(red, red.find("def").decorators.node_list[0].value.value[0],
               [0, "decorators", 0, "value", "value", 0])


def test_path_decorators_endl(red):
    check_path(red, red.find("def").decorators.node_list[1], [0, "decorators", 1])


def test_path_first_formatting(red):
    check_path(red, red.find("def").first_formatting, [0, "first_formatting"])


def test_path_first_formatting_value(red):
    check_path(red, red.find("def").first_formatting[0], [0, "first_formatting", 0])


def test_path_second_formatting(red):
    check_path(red, red.find("def").second_formatting, [0, "second_formatting"])


def test_path_third_formatting(red):
    check_path(red, red.find("def").third_formatting, [0, "third_formatting"])


def test_path_arguments(red):
    check_path(red, red.find("def").arguments, [0, "arguments"])


def test_path_arguments_first(red):
    check_path(red, red.find("def").arguments.node_list[0], [0, "arguments", 0])


def test_path_arguments_comma(red):
    check_path(red, red.find("def").arguments.node_list[1], [0, "arguments", 1])


def test_path_arguments_second(red):
    check_path(red, red.find("def").arguments.node_list[2], [0, "arguments", 2])


def test_path_fourth_formatting(red):
    check_path(red, red.find("def").fourth_formatting, [0, "fourth_formatting"])


def test_path_fifth_formatting(red):
    check_path(red, red.find("def").fifth_formatting, [0, "fifth_formatting"])


def test_path_sixth_formatting(red):
    check_path(red, red.find("def").sixth_formatting, [0, "sixth_formatting"])


def test_path_value(red):
    check_path(red, red.find("def").value, [0, "value"])


def test_path_value_first_endl(red):
    check_path(red, red.find("def").value.node_list[0], [0, "value", 0])


def test_path_value_assignment(red):
    check_path(red, red.find("def").value.node_list[2], [0, "value", 2])


def test_path_value_assignment_target(red):
    check_path(red, red.find("def").value.node_list[2].target,
               [0, "value", 2, "target"])


def test_path_value_assignment_value(red):
    check_path(red, red.find("def").value.node_list[2].value,
               [0, "value", 2, "value"])


def test_path_value_assignment_value_first(red):
    check_path(red, red.find("def").value.node_list[2].value.first,
               [0, "value", 2, "value", "first"])


def test_path_value_assignment_value_second(red):
    check_path(red, red.find("def").value.node_list[2].value.second,
               [0, "value", 2, "value", "second"])


def test_path_value_second_endl(red):
    check_path(red, red.find("def").value.node_list[3], [0, "value", 3])
