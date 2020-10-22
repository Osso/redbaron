""" Tests the rendering feature """

from redbaron import RedBaron
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
    indented_code = """
def a():
  # plop
  1 + 2
  if caramba:
      plop
  pouf
"""
    assert deindent_str(test_indent_code, "  ") == indented_code
    assert red.dumps() == deindent_str(test_indent_code, "  ")


def test_increase_indentation_single_node():
    red = RedBaron(test_indent_code)
    red.find("if")[0].increase_indentation("   ")
    assert len(red.find("if")[0].indentation) == 8 + 3


def test_decrease_indentation_single_node():
    red = RedBaron(test_indent_code)
    red.find("if")[0].decrease_indentation("   ")
    assert len(red.find("if")[0].indentation) == 8 - 3
