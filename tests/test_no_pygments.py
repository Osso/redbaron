import pytest
import redbaron
from redbaron import RedBaron


class Test():
    def setup_method(self, method):
        redbaron.force_ipython_behavior = True
        redbaron.DEBUG = True

    def teardown_method(self, method):
        redbaron.force_ipython_behavior = False
        redbaron.DEBUG = False

    def test_repr(self):
        RedBaron("a = 1").__str__()
        RedBaron("a = 1")[0].__str__()
        RedBaron("a = 1").__repr__()
        RedBaron("a = 1")[0].__repr__()

    def test_help(self):
        RedBaron("a = 1").help()
        RedBaron("a = 1")[0].help()

    def test_regression_repr(self):
        red = RedBaron("a = 1 + caramba")
        red[0].value.first.parent
        str(red[0].value.first.parent)


def test_highlight(capsys, monkeypatch):
    monkeypatch.setattr(redbaron, 'force_ipython_behavior', True)

    RedBaron("a = []").help()
    captured = capsys.readouterr()

    if tuple(map(int, pytest.__version__.split('.'))) <= (3, 3):
        out = captured[0]
    else:
        out = captured.out
    assert out == """\
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
