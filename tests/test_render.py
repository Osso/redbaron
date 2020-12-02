""" Tests the rendering feature """

import pytest
from redbaron import RedBaron


@pytest.mark.skip
def test_rendering_iter():
    red = RedBaron("a + 2")
    assert_red = RedBaron("assert a == 5")
    assert list(red._generate_nodes_in_rendering_order()) == \
           [red[0],
            red.find("name"),
            red[0].first_formatting[0],
            red[0],
            red[0].second_formatting[0],
            red.find("int")]
    assert list(red[0]._generate_nodes_in_rendering_order()) == \
           [red[0],
            red.find("name"),
            red[0].first_formatting[0],
            red[0],
            red[0].second_formatting[0],
            red.find("int")]

    assert list(assert_red._generate_nodes_in_rendering_order()) == \
           [assert_red[0],
            assert_red[0].first_formatting[0],  # SpaceNode in AssertNode
            assert_red[0].value,  # ComparisonNode
            assert_red.find("name"),
            assert_red[0].value.first_formatting[0],  # SpaceNode in ComparisonNode
            assert_red[0].value.value,  # ComparisonOperatorNode
            assert_red[0].value.second_formatting[0],  # SpaceNode in ComparisonNode
            assert_red.find("int")]

    assert list(assert_red[0]._generate_nodes_in_rendering_order()) == \
           [assert_red[0],
            assert_red[0].first_formatting[0],  # SpaceNode in AssertNode
            assert_red[0].value,  # ComparisonNode
            assert_red.find("name"),
            assert_red[0].value.first_formatting[0],  # SpaceNode in ComparisonNode
            assert_red[0].value.value,  # ComparisonOperatorNode
            assert_red[0].value.second_formatting[0],  # SpaceNode in ComparisonNode
            assert_red.find("int")]


@pytest.mark.skip
def test_next_rendered():
    red = RedBaron("a + 2")
    f = red.find("name")

    assert f.next_rendered is red[0].first_formatting[0]
    assert f.next_rendered.next_rendered is red[0]
    assert f.next_rendered.next_rendered.next_rendered is red[0].second_formatting[0]
    assert f.next_rendered.next_rendered.next_rendered.next_rendered is red.int


@pytest.mark.skip
def test_previous_rendered():
    red = RedBaron("a + 2")
    f = red.find("int")

    assert f.previous_rendered is red[0].second_formatting[0]
    assert f.previous_rendered.previous_rendered is red[0]
    assert red[0].first_formatting[0].previous_rendered is red.name


@pytest.mark.skip
def test_next_rendered_trapped():
    test_indent_code = """
    def a():
        # plop
        1 + 2
        if caramba:
            plop
        pouf

    """
    red = RedBaron(test_indent_code)
    assert red.find("endl")[5].next_rendered is red.find("name", "pouf")


def test_indented_for_else():
    code = """
    for a in b:
        pass
    else:
        pass
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_indented_try_except():
    code = """
    try:
        pass
    except:
        pass
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_indented_try_finally():
    code = """
    try:
        pass
    finally:
        pass
"""
    red = RedBaron(code)
    assert red.dumps() == code
