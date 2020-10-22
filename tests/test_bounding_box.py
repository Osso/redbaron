""" Tests the relative_box feature """

import pytest
from redbaron import RedBaron

red_1 = RedBaron("""\
@deco
def a(c, d):
    b = c + d
""")

boxes = [
    (((1, 1), (4, 1)), ((1, 1), (4, 1)), red_1),
    (((1, 1), (4, 1)), ((1, 1), (4, 1)), red_1.find('def')),
    (((1, 1), (2, 1)), ((1, 1), (2, 1)), red_1.find('def').decorators),
    (((1, 1), (1, 6)), ((1, 1), (1, 6)), red_1.find('def').decorators.node_list[0]),
    (((1, 2), (1, 6)), ((1, 1), (1, 5)), red_1.find('def').decorators.node_list[0].value),
    (((1, 2), (1, 6)), ((1, 1), (1, 5)), red_1.find('def').decorators.node_list[0].value.value),
    (((1, 2), (1, 6)), ((1, 1), (1, 5)), red_1.find('def').decorators.node_list[0].value.value[0]),
    (((1, 6), (2, 1)), ((1, 1), (2, 1)), red_1.find('def').decorators.node_list[1]),
    (((2, 4), (2, 5)), ((1, 1), (1, 2)), red_1.find('def').first_formatting),
    (((2, 4), (2, 5)), ((1, 1), (1, 2)), red_1.find('def').first_formatting[0]),
    (((2, 6), (2, 6)), ((1, 1), (1, 1)), red_1.find('def').second_formatting),
    (((2, 7), (2, 7)), ((1, 1), (1, 1)), red_1.find('def').third_formatting),
    (((2, 7), (2, 11)), ((1, 1), (1, 5)), red_1.find('def').arguments),
    (((2, 7), (2, 8)), ((1, 1), (1, 2)), red_1.find('def').arguments.node_list[0]),
    (((2, 8), (2, 10)), ((1, 1), (1, 3)), red_1.find('def').arguments.node_list[1]),
    (((2, 10), (2, 11)), ((1, 1), (1, 2)), red_1.find('def').arguments.node_list[2]),
    (((2, 11), (2, 11)), ((1, 1), (1, 1)), red_1.find('def').fourth_formatting),
    (((2, 12), (2, 12)), ((1, 1), (1, 1)), red_1.find('def').fifth_formatting),
    (((2, 13), (2, 13)), ((1, 1), (1, 1)), red_1.find('def').sixth_formatting),
    (((2, 13), (4, 1)), ((1, 1), (3, 1)), red_1.find('def').value),
    (((2, 13), (3, 1)), ((1, 1), (2, 1)), red_1.find('def').value.node_list[0]),
    (((3, 1), (3, 5)), ((1, 1), (1, 5)), red_1.find('def').value.node_list[1]),
    (((3, 5), (3, 14)), ((1, 1), (1, 10)), red_1.find('def').value.node_list[2]),
    (((3, 5), (3, 6)), ((1, 1), (1, 2)), red_1.find('def').value.node_list[2].target),
    (((3, 9), (3, 14)), ((1, 1), (1, 6)), red_1.find('def').value.node_list[2].value),
    (((3, 9), (3, 10)), ((1, 1), (1, 2)), red_1.find('def').value.node_list[2].value.first),
    (((3, 13), (3, 14)), ((1, 1), (1, 2)), red_1.find('def').value.node_list[2].value.second),
    (((3, 14), (4, 1)), ((1, 1), (2, 1)), red_1.find('def').value.node_list[3])
]


@pytest.mark.parametrize("box,relative_box,node", boxes)
def test_box(box, relative_box, node):
    assert node.box == box, node.path().to_baron_path()
    assert node.relative_box == relative_box, node.path().to_baron_path()


def test_relative_box_of_attribute():
    assert red_1.find("def").box_of_attribute("def") == ((2, 1), (2, 4))


def test_relative_box_of_attribute_no_attribute():
    with pytest.raises(KeyError):
        red_1.find("def").box_of_attribute("xxx")


def test_relative_box_empty():
    tree = RedBaron("a()")
    box = tree.find("atomtrailers").value[1].value.box
    assert box == ((1, 3), (1, 3))


red_2 = RedBaron("""\
class A:
    ''' Class docstring

    Class description
    '''
    attrA = [ a,
         b,
            c,
               d]

    def a(self):
        ''' Function a docstring

        Function description
        '''
        pass

    attrB = valB

    @myDecorator
    def b(self):
        ''' Function b docstring

        Function description
        '''
        pass

    attrC = [ a,
         b,
            c,
               d]\
""")


def test_relative_box_with_proxy_list():
    assert red_2.box == ((1, 1), (32, 1))
    assert red_2.find("class").box == ((1, 1), (32, 1))
    assert red_2.find("class").value[0].box == ((2, 5), (5, 8))
    assert red_2.find("class").value[1].box == ((6, 5), (9, 18))
    assert red_2.find("class").value[2].box == ((10, 1), (10, 1))
    assert red_2.find("class").value[3].box == ((11, 5), (17, 1))
    assert red_2.find("class").value[4].box == ((17, 1), (17, 1))
    assert red_2.find("class").value[5].box == ((18, 5), (18, 17))
    assert red_2.find("class").value[6].box == ((19, 1), (19, 1))
    assert red_2.find("class").value[7].box == ((20, 5), (27, 1))
    assert red_2.find("class").value[8].box == ((27, 1), (27, 1))
    assert red_2.find("class").value[9].box == ((28, 5), (31, 18))
    with pytest.raises(IndexError):
        red_2.find("class").value[10]  # pylint: disable=expression-not-assigned
