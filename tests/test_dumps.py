"""Tests the rendering feature"""

from redbaron import RedBaron


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


def test_indented_try_else():
    code = """
    try:
        pass
    except Exception:
        pass
    else:
        pass
"""
    red = RedBaron(code)
    assert red.dumps() == code


def test_indented_decorators():
    code = """
        @dec1
        @dec2
        def fun():
            pass
"""
    red = RedBaron(code)
    assert red.dumps() == code
