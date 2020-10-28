from contextlib import redirect_stdout
import io

import redbaron
from redbaron import RedBaron


def test_repr(monkeypatch):
    monkeypatch.setattr(redbaron, 'FORCE_IPYTHON_BEHAVIOR', True)

    RedBaron("a = 1").__str__()
    RedBaron("a = 1")[0].__str__()
    RedBaron("a = 1").__repr__()
    RedBaron("a = 1")[0].__repr__()


def test_help(monkeypatch):
    monkeypatch.setattr(redbaron, 'FORCE_IPYTHON_BEHAVIOR', True)

    RedBaron("a = 1").help()
    RedBaron("a = 1")[0].help()


def test_regression_repr(monkeypatch):
    monkeypatch.setattr(redbaron, 'FORCE_IPYTHON_BEHAVIOR', True)

    value = "1 + caramba"
    red = RedBaron(f"a = {value}")
    assert str(red[0].value.first.parent) == value


def test_highlight(monkeypatch):
    monkeypatch.setattr(redbaron, 'FORCE_IPYTHON_BEHAVIOR', True)

    out = io.StringIO()
    with redirect_stdout(out):
        RedBaron("a = []").help()
    assert out.getvalue() == """\
0 -----------------------------------------------------
\x1b[38;5;148mAssignmentNode\x1b[39m\x1b[38;5;197m(\x1b[39m\x1b[38;5;197m)\x1b[39m
\x1b[38;5;15m  \x1b[39m\x1b[38;5;242m# identifiers: assign, assignment, assignment_, assignmentnode\x1b[39m
\x1b[38;5;15m  \x1b[39m\x1b[38;5;15moperator\x1b[39m\x1b[38;5;197m=\x1b[39m\x1b[38;5;186m''\x1b[39m
\x1b[38;5;15m  \x1b[39m\x1b[38;5;15mtarget\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;197m->\x1b[39m
\x1b[38;5;15m    \x1b[39m\x1b[38;5;148mNameNode\x1b[39m\x1b[38;5;197m(\x1b[39m\x1b[38;5;197m)\x1b[39m
\x1b[38;5;15m      \x1b[39m\x1b[38;5;242m# identifiers: name, name_, namenode\x1b[39m
\x1b[38;5;15m      \x1b[39m\x1b[38;5;15mvalue\x1b[39m\x1b[38;5;197m=\x1b[39m\x1b[38;5;186m'a'\x1b[39m
\x1b[38;5;15m  \x1b[39m\x1b[38;5;15mannotation\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;197m->\x1b[39m
\x1b[38;5;15m    \x1b[39m\x1b[38;5;186mNone\x1b[39m
\x1b[38;5;15m  \x1b[39m\x1b[38;5;15mvalue\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;197m->\x1b[39m
\x1b[38;5;15m    \x1b[39m\x1b[38;5;15m[\x1b[39m\x1b[38;5;15m]\x1b[39m
"""
