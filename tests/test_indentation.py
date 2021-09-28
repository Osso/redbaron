""" Tests the rendering feature """

from redbaron import (NodeList,
                      RedBaron,
                      node)
from redbaron.nodes import SpaceNode
from redbaron.utils import (deindent_str,
                            indent_str)

test_indent_code = """
def a():
    # plop
    1 + 2
    if caramba:
        plop
    pouf
"""


def test_increase_indentation():
    red = RedBaron(test_indent_code)
    red.increase_indentation("    ")
    assert red.dumps() == indent_str(test_indent_code, "    ")


def test_decrease_indentation():
    red = RedBaron(test_indent_code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(test_indent_code, "  ")


def test_increase_indentation_single_node():
    red = RedBaron(test_indent_code)
    red.find("if")[0].increase_indentation("   ")
    assert len(red.find("if")[0].indentation) == 8 + 3


def test_decrease_indentation_single_node():
    red = RedBaron(test_indent_code)
    red.find("if")[0].decrease_indentation("   ")
    assert len(red.find("if")[0].indentation) == 8 - 3


def test_indentation_no_parent():
    red = RedBaron("a")
    assert red[0].copy().indentation == ''


def test_indentation_root():
    red = RedBaron("pouet")
    assert red[0].indentation == ""
    red = RedBaron("pouet\nplop\npop")
    assert [x.indentation for x in red.value.node_list] == ["", "", "", "", ""]


def test_in_while():
    red = RedBaron("while a:\n    pass\n")
    node_list = red[0].value.node_list
    assert node_list[-2].indentation == "    "
    assert node_list[-1].indentation == ""


def test_one_line_while():
    red = RedBaron("while a: pass\n")
    assert red[0].value.node_list[0].indentation == ""


def test_inner_node():
    red = RedBaron("while a: pass\n")
    assert red[0].test.indentation == ""


def test_indentation_endl():
    red = RedBaron("a.b.c.d")
    assert red[0].value[-3].indentation == ""


def test_decrease_indentation_if_else():
    code = """
    if cond:
        pass
    elif cond:
        pass
    else:
        pass
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_decrease_indentation_for_else():
    code = """
    for a in b:
        pass
    else:
        pass
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_decrease_indentation_while_else():
    code = """
    while cond:
        pass
    else:
        pass
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_decrease_indentation_try_finally():
    code = """
    try:
        pass
    finally:
        pass
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_decrease_indentation_try_except_else():
    code = """
    try:
        pass
    except:
        pass
    else:
        pass
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_decrease_indentation_atom_node():
    code = """
    fun() \\
        .more()
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_decrease_indentation_assignement():
    code = """
    a = \\
        1
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_decrease_indentation_assignement_and_atom_node():
    code = """
    a = fun() \\
            .more()
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_decrease_indentation_assignement_and_atom_node_2():
    code = """
    a = fun(). \\
            more()
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_decrease_indentation_space_node():
    code = [SpaceNode({"type": "space", "value": "\n "}), node("# hello")]
    red = NodeList(code)
    red.decrease_indentation("  ")
    assert red.dumps() == "\n# hello"


def test_increase_indentation_brackets():
    code = """
    a = (fun().
            more())
"""
    red = RedBaron(code)
    red.increase_indentation("  ")
    assert red.dumps() == indent_str(code, "  ")


def test_decrease_indentation_brackets():
    code = """
    a = (fun().
            more())
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_increase_indentation_assignement_backslash():
    code = """
    a = \\
        1
"""
    red = RedBaron(code)
    red.increase_indentation("  ")
    assert red.dumps() == indent_str(code, "  ")


def test_decrease_indentation_assignement_backslash():
    code = """
    a = \\
        1
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")


def test_increase_indentation_brackets_2():
    code = """
a = (fun()
  .filter())
"""
    red = RedBaron(code)
    red.increase_indentation("  ")
    assert red.dumps() == indent_str(code, "  ")


def test_decrease_indentation_brackets_2():
    code = """
  a = (fun()
    .filter())
"""
    red = RedBaron(code)
    red.decrease_indentation("  ")
    assert red.dumps() == deindent_str(code, "  ")
