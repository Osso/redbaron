""" Main redbaron test module """

from redbaron import RedBaron
from redbaron.utils import truncate


def test_other_name_assignment():
    red = RedBaron("a = b")
    assert red.assign is red[0]


def test_index():
    red = RedBaron("a = [1, 2, 3]")
    assert red[0].value.value[2].index_on_parent == 2
    assert red[0].index_on_parent == 0
    assert red[0].value.index_on_parent is None


def test_index_raw():
    red = RedBaron("a = [1, 2, 3]")
    assert red[0].value.value.node_list[2].index_on_parent_raw == 2
    assert red[0].index_on_parent == 0
    assert red[0].value.index_on_parent_raw is None


def test_regression_find_all_recursive():
    red = RedBaron("a.b()")
    assert red[0].value("name", recursive=False) == [red.name, red("name")[1]]


def test_truncate():
    assert truncate("1234", 2) == "1234"
    assert truncate("12345", 4) == "12345"
    assert truncate("123456", 5) == "1...6"
    assert truncate("12345678901234567890", 10) == "123456...0"
