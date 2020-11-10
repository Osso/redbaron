""" Main redbaron test module """

import re

import pytest
from redbaron import RedBaron


def test_regression_find_all_in_children():
    red = RedBaron("a.b()")
    assert red[0].value.find_all("name") == red.find_all("name")


def test_regression_find_all_not_recursive():
    red = RedBaron("a.b()")
    assert red[0].find_all("name", recursive=False) == red.find_all("name")
    red = RedBaron("fun(arg=sub(arg1))")
    assert red[0].find_all("call", recursive=False)
    assert red[0].find_all("call", recursive=False) == red.find_all("call")[:1]


SOME_DATA_FOR_TEST = """\
def plop():
    def a():
        with b as c:
            d = e
"""


def test_parent_find_empty():
    red = RedBaron("a")
    assert red[0].parent_find('a') is None


def test_parent_find_direct():
    red = RedBaron(SOME_DATA_FOR_TEST)
    target = red.find("assignment").target
    assert target.parent_find('with') is red.find("with")


def test_parent_find_two_levels():
    red = RedBaron(SOME_DATA_FOR_TEST)
    target = red.find("assignment").target
    assert target.parent_find('def') is red.find('def', name='a')


def test_parent_find_two_levels_options():
    red = RedBaron(SOME_DATA_FOR_TEST)
    target = red.find("assignment").target
    assert target.parent_find('def', name='plop') is red.find("def")
    assert target.parent_find('def', name='dont_exist') is None


def test_find_empty():
    red = RedBaron("")
    assert red.find("stuff") is None
    assert red.find("something_else") is None
    assert red.find("something_else", useless="pouet") is None
    with pytest.raises(AttributeError):
        red.will_raises  # pylint: disable=pointless-statement


def test_find():
    red = RedBaron("def a(): b = c")
    assert red.find("name") is red[0].value[0].target
    assert red.find("name", value="c") is red[0].value[0].value
    assert red.find("name") is red[0].value[0].target


def test_find_other_properties():
    red = RedBaron("b = c")
    assert red.find("assignment") == red[0]
    assert red.find("assign") == red[0]


def test_find_case_insensitive():
    red = RedBaron("a")
    assert red.find("NameNode") is red[0]
    assert red.find("NaMeNoDe") is red[0]
    assert red.find("namenode") is red[0]


def test_find_kwarg_lambda():
    red = RedBaron("[1, 2, 3, 4]")
    assert red.find("int", value=lambda x: int(x) % 2 == 0) == red.find_all("int")[1]
    assert red.find_all("int", value=lambda x: int(x) % 2 == 0) == red.find_all("int")[1::2]


def test_find_lambda():
    red = RedBaron("[1, 2, 3, 4]")
    assert red.find("int", lambda x: int(x.value) % 2 == 0) == red.find_all("int")[1]
    assert red.find_all("int", lambda x: int(x.value) % 2 == 0) == red.find_all("int")[1::2]


def test_find_kwarg_regex_instance():
    red = RedBaron("plop\npop\npouf\nabcd")
    assert red.find("name", value=re.compile("^po")) == red[1]


def test_find_all_kwarg_regex_instance():
    red = RedBaron("plop\npop\npouf\nabcd")
    assert red.find("name", value=re.compile("^po")) \
        == red.find("name", value=lambda x: x.startswith("po"))


def test_find_kwarg_regex_syntaxe():
    red = RedBaron("plop\npop\npouf\nabcd")
    assert red.find("name", value="re:^po") == red[1]


def test_find_all_kwarg_regex_syntaxe():
    red = RedBaron("plop\npop\npouf\nabcd")
    assert red.find("name", value="re:^po") \
        == red.find("name", value=lambda x: x.startswith("po"))


def test_find_kwarg_glob_syntaxe():
    red = RedBaron("plop\npop\npouf\nabcd")
    assert red.find("name", value="g:po*") == red[1]


def test_find_all_kwarg_glob_syntaxe():
    red = RedBaron("plop\npop\npouf\nabcd")
    assert red.find("name", value="g:po*") \
        == red.find("name", value=lambda x: x.startswith("po"))


def test_identifier_find_kwarg_lambda():
    red = RedBaron("stuff\n1\n'string'")
    assert red.find(lambda x: x in ["name", "int"]) == red[0]
    assert red.find_all(lambda x: x in ["name", "int"]) == list(red[:2])


def test_identifier_find_kwarg_regex_instance():
    red = RedBaron("stuff\n1\n'string'")
    assert red.find(re.compile("^[ni]")) == red[0]


def test_identifier_find_all_kwarg_regex_instance():
    red = RedBaron("stuff\n1\n'string'")
    assert red.find_all(re.compile("^[ni]")) == list(red[:2])


def test_identifier_find_kwarg_regex_syntaxe():
    red = RedBaron("stuff\n1\n'string'")
    assert red.find("re:^[ni]") == red[0]


def test_identifier_find_all_kwarg_regex_syntaxe():
    red = RedBaron("stuff\n1\n'string'")
    assert red.find_all("re:^[ni]") == list(red[:2])


def test_identifier_find_kwarg_glob_syntaxe():
    red = RedBaron("stuff\n1\n'string'")
    assert red.find("g:s*") == red[-1]


def test_identifier_find_all_kwarg_glob_syntaxe():
    red = RedBaron("stuff\n1\n'string'")
    assert red.find_all("g:s*") == list(red[2:])


def test_find_kwarg_list_tuple_instance():
    red = RedBaron("pouet\n'string'\n1")
    assert red.find("name", value=["pouet", 1]) == red[0]
    assert red.find("name", value=("pouet", 1)) == red[0]


def test_find_all_kwarg_list_tuple_instance():
    red = RedBaron("pouet\nstuff\n1")
    assert red.find_all("name", value=["pouet", "stuff"]) == list(red[:2])
    assert red.find_all("name", value=("pouet", "stuff")) == list(red[:2])


def test_identifier_find_kwarg_list_tuple_instance():
    red = RedBaron("pouet\n'string'\n1")
    assert red.find(["name", "string"]) == red[0]
    assert red.find(("name", "string")) == red[0]


def test_identifier_find_all_kwarg_list_tuple_instance():
    red = RedBaron("pouet\n'string'\n1")
    assert red.find_all(["name", "string"]) == list(red[:2])
    assert red.find_all(("name", "string")) == list(red[:2])


def test_default_test_value_find():
    red = RedBaron("badger\nmushroom\nsnake")
    assert red.find("name", "snake") == red.find("name", value="snake")


def test_default_test_value_find_all():
    red = RedBaron("badger\nmushroom\nsnake")
    assert red.find("name", "snake") == red.find("name", value="snake")


def test_find_comment_node():
    red = RedBaron("def f():\n    #a\n    pass\n#b")
    assert red.find('comment').value == '#a'


def test_find_all_comment_nodes():
    red = RedBaron("def f():\n    #a\n    pass\n#b")
    assert [x.value for x in red.find_all('comment')] == ['#a', '#b']


def test_default_test_value_find_def():
    red = RedBaron("def a(): pass\ndef b(): pass")
    assert red.find("def", "b") == red.find("def", name="b")


def test_default_test_value_find_class():
    red = RedBaron("class a(): pass\nclass b(): pass")
    assert red.find("class", "b") == red.find("class", name="b")


def test_find_other_name_assignment():
    red = RedBaron("a = b")
    assert red.find("assign") is red[0]


def test_find_empty_call():
    red = RedBaron("a()")
    assert red.find("call") is red[0][1]
