""" Tests initial parsing through the RedBaron() base function """
from redbaron import (RedBaron,
                      node)
from redbaron.base_nodes import Node
from redbaron.nodes import (AssignmentNode,
                            EndlNode,
                            NameNode,
                            NumberNode,
                            PassNode,
                            SpaceNode)


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
    red = node("1")
    assert isinstance(red, NumberNode)
    assert red.value == "1"


def test_assignment():
    red = RedBaron("a = 2")
    assert isinstance(red[0], AssignmentNode)
    assert isinstance(red[0].value, NumberNode)
    assert red[0].value.value == "2"
    assert isinstance(red[0].target, NameNode)
    assert red[0].target.value == "a"


def test_binary_operator_plus():
    binop = node("z +  42")
    assert binop.value == "+"
    assert isinstance(binop.first, NameNode)
    assert binop.first.value == "z"
    assert isinstance(binop.second, NumberNode)
    assert binop.second.value == "42"


def test_binary_operator_minus():
    binop = node("z  -      42")
    assert binop.value == "-"
    assert isinstance(binop.first, NameNode)
    assert binop.first.value == "z"
    assert isinstance(binop.second, NumberNode)
    assert binop.second.value == "42"


def test_binary_operator_more_complex():
    binop = node("ax + (z * 4)")
    assert binop.first.value == "ax"


def test_pass():
    red = node("pass")
    assert isinstance(red, PassNode)


def test_parent_and_on_attribute():
    red = RedBaron("a = 1 + caramba")
    assert red.parent is None
    assert red.value.parent is red
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


def test_import():
    red = RedBaron("from m import a")
    assert red[0].targets.dumps() == "a"


def test_import_multi():
    red = RedBaron("from m import a, b")
    assert red[0].targets.dumps() == "a, b"


def test_import_multiline():
    red = RedBaron("from m import (a,\n   b)")
    assert red[0].targets.dumps() == "(a,\n   b)"


def test_import_on_new_line():
    red = RedBaron("from m import (\n"
                   "   a)")
    assert red[0].targets.dumps() == "(\n   a)"


def test_double_separator():
    red = RedBaron("fun(a,,)")
    assert red[0].dumps() == "fun(a,)"


def test_comment_in_args():
    red = RedBaron("fun(\n"
                   "# comment\n"
                   "a)")
    assert red[0].dumps() == "fun(\n# comment\na)"


def test_multiline_dict():
    red = RedBaron("""
    {
        'key': 'value'
    }""")
    assert len(red[0].value.footer) == 1
    assert isinstance(red[0].value.footer[0], SpaceNode)


def test_embedded_dict():
    code = """
{
    "key1": {
        'sub_key1': {
            'queue': 'value1',
        },
        'sub_key3': {
            'queue': 'value3',
        },
    }
}
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_embedded_dict2():
    code = """
{
        "key": {}
    }
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_embedded_list():
    code = """
{
    "key1": [
        'sub_key1'
        ],
}
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_embedded_list2():
    code = """
{
        "key": []
    }
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_fst_dict():
    code = """
'sub_key2': {
    'queue': 'value2',
}"""
    red = RedBaron(code)
    assert Node.generic_from_fst(red[0].fst()).fst() == red[0].fst()


def test_ternary_dict():
    code = """
{'scheme': 'https' if condition else 'http'}
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_while_ending_comment():
    code = """
while True:
    pass
# comment 2

# more
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_return_with_comment():
    code = """
def f():
    return  # comment
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_raise_with_comment():
    code = """
def f():
    raise  # comment
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_def_inline():
    code = """
def fun(): pass
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_def_multiline():
    code = """
def fun():
    pass
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_class_inline():
    code = """
class C: pass
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_class_multiline():
    code = """
class C:
    pass
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_dict():
    code = """
{'status': condition1 and
    condition2}
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_def_inside_def():
    code = """
def fun():

    def sub():
        pass
"""
    red = RedBaron(code)
    assert red.dumps() == code
