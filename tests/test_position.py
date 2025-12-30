""" Tests the position feature """

# pylint: disable=redefined-outer-name
import pytest

import redbaron
from redbaron import RedBaron
from redbaron.node_path import Path

redbaron.DEBUG = True

fst = RedBaron("""\
@deco

def a(c, d):
    b = c + d
    e = 1
""")


positions = [
    (fst.find('def').decorators[0], [(1, 1)]),
    (fst.find('def').decorators[0].value.value[0], [(1, 2), (1, 3), (1, 4), (1, 5)]),
    # How to get this one ? (2, 0) and (2, 1) does not work, see out of scope
    # (fst.find('def').decorators[1],                                [(?, ?)]),
    (fst.find('def'), [(3, 1), (3, 2), (3, 3)]),
    (fst.find('def').first_formatting[0], [(3, 4)]),
    (fst.find('def'), [(3, 5), (3, 6)]),
    (fst.find('def').arguments.node_list[0].target, [(3, 7)]),
    (fst.find('def').arguments.node_list[1], [(3, 8)]),
    (fst.find('def').arguments.node_list[1].second_formatting[0], [(3, 9)]),
    (fst.find('def').arguments.node_list[2].target, [(3, 10)]),
    (fst.find('def'), [(3, 11), (3, 12)]),
    (fst.find('def').value.node_list[1], [(4, 1), (4, 2), (4, 3), (4, 4)]),
    (fst.find('def').value.node_list[2].target, [(4, 5)]),
    (fst.find('def').value.node_list[2].first_formatting[0], [(4, 6)]),
    (fst.find('def').value.node_list[2], [(4, 7)]),
    (fst.find('def').value.node_list[2].second_formatting[0], [(4, 8)]),
    (fst.find('def').value.node_list[2].value.first, [(4, 9)]),
    (fst.find('def').value.node_list[2].value.first_formatting[0], [(4, 10)]),
    (fst.find('def').value.node_list[2].value, [(4, 11)]),
    (fst.find('def').value.node_list[2].value.second_formatting[0], [(4, 12)]),
    (fst.find('def').value.node_list[2].value.second, [(4, 13)]),
    (fst.find('def').value.node_list[4], [(5, 1), (5, 2), (5, 3), (5, 4)]),
    (fst.find('def').value.node_list[5].target, [(5, 5)]),
    (fst.find('def').value.node_list[5].first_formatting[0], [(5, 6)]),
    (fst.find('def').value.node_list[5], [(5, 7)]),
    (fst.find('def').value.node_list[5].second_formatting[0], [(5, 8)]),
    (fst.find('def').value.node_list[5].value, [(5, 9)]),
    # out of scope
    (fst, [(2, 0), (2, 1)]),
]


@pytest.fixture(params=positions)
def position_fixture(request):
    return request.param


def test_find_by_position(position_fixture):
    node, positions = position_fixture
    for position in positions:
        assert node == fst.find_by_position(position)


def test_path_str():
    red = RedBaron("name")
    assert str(Path(red[0]))
