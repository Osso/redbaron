from redbaron.utils import (deindent_str,
                            in_a_shell,
                            in_ipython,
                            indent_str,
                            redbaron_classname_to_baron_type,
                            squash_successive_duplicates,
                            truncate)


def test_redbaron_classname_to_baron_type():
    assert redbaron_classname_to_baron_type("SpaceNode") == 'space'
    assert redbaron_classname_to_baron_type("RawStringNode") == 'raw_string'


def test_in_a_shell():
    assert not in_a_shell()


def test_in_ipython():
    assert not in_ipython()


def test_indent_str():
    test_indent_code = """
def a():
    # plop
    1 + 2
    if caramba:
        plop
    pouf
"""
    indented_code = """
    def a():
        # plop
        1 + 2
        if caramba:
            plop
        pouf
"""
    assert indent_str(test_indent_code, "    ") == "    " + indented_code


def test_deindent_str():
    test_indent_code = """
def a():
    # plop
    1 + 2
    if caramba:
        plop
    pouf
"""
    indented_code = """
def a():
  # plop
  1 + 2
  if caramba:
      plop
  pouf
"""
    assert deindent_str(test_indent_code, "  ") == indented_code


def test_truncate():
    assert truncate("1234", 2) == "1234"
    assert truncate("12345", 4) == "12345"
    assert truncate("123456", 5) == "1...6"
    assert truncate("12345678901234567890", 10) == "123456...0"

def test_squash_successive_duplicates():
    assert list(squash_successive_duplicates([1, 2, 3, 3, 4])) == [1, 2, 3, 4]