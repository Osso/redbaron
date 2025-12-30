from redbaron import RedBaron


def test_get_helpers():
    red = RedBaron("a")
    assert list(red[0]._get_helpers()) == []
    red = RedBaron("import a")
    assert list(red[0]._get_helpers()) == ["modules", "names"]


def test_help_is_not_crashing1():
    some_code = "ax + (z * 4)"
    red = RedBaron(some_code)
    red.help()
    red[0].help()
    red.help(5)
    red[0].help(5)
    red.help(True)
    red[0].help(True)


def test_help_is_not_crashing2():
    some_code = "a(b)"
    red = RedBaron(some_code)
    red.help()
    red[0].help()
    red.help(5)
    red[0].help(5)
    red.help(True)
    red[0].help(True)


def test_help_is_not_crashing3():
    some_code = "a(b, c)"
    red = RedBaron(some_code)
    red.help()
    red[0].help()
    red.help(5)
    red[0].help(5)
    red.help(True)
    red[0].help(True)


def test_help_is_not_crashing4():
    some_code = "a(b)"
    red = RedBaron(some_code)
    red[0].find("call").append("c")
    red.help()
    red[0].help()
    red.help(5)
    red[0].help(5)
    red.help(True)
    red[0].help(True)
