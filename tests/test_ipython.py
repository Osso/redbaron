from contextlib import redirect_stdout
import io

import redbaron
from redbaron import RedBaron
from redbaron.syntax_highlight import HAS_PYGMENTS


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
    value = "1 + caramba"
    red = RedBaron(f"a = {value}")
    assert str(red[0].value.first.parent) == value


def test_highlight(monkeypatch):
    assert HAS_PYGMENTS
    monkeypatch.setattr(redbaron, 'FORCE_IPYTHON_BEHAVIOR', True)

    out = io.StringIO()
    with redirect_stdout(out):
        RedBaron("a = []").help()

    assert "\x1b[" in out.getvalue()
