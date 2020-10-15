"""Test for at method"""

import redbaron
from redbaron import RedBaron

redbaron.DEBUG = True

red = RedBaron("""
class Foo(object):
    def __init__(self):
        self.a = None
    def bar(self):
        for x in range(5):
            yield self.a + x

setup(name='redbaron',
      version='0.6.1')
""")


def test_at_root():
    assert red.at(0) is red


def test_at_1():
    assert red.at(1) is red.find('ClassNode')


def test_at_2():
    assert red.at(2) is red.find_all('DefNode')[0]


def test_at_3():
    assert red.at(3) is red.find('AssignmentNode')


def test_at_4():
    assert red.at(4) is red.find_all('DefNode')[1]


def test_at_5():
    assert red.at(5) is red.find('ForNode')


def test_at_6():
    assert red.at(6) is red.find('YieldNode')


def test_at_7():
    assert red.at(7) is red.find_all('EndlNode')[6]


def test_at_8():
    assert red.at(8) is red.find_all('AtomTrailersNode')[3]


def test_at_9():
    assert red.at(9) is red.find_all('CallArgumentNode')[2]
