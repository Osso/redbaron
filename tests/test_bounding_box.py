""" Tests the bounding_box feature """

import pytest
from redbaron import RedBaron


def red():
    return RedBaron("""\
@deco
def a(c, d):
    b = c + d
""")


fst = red()
bounding_boxes = [
    (((1, 1), (4, 1)), ((1, 1), (4, 1)), fst),
    (((1, 1), (4, 1)), ((1, 1), (4, 1)), fst.find('def')),
    (((1, 1), (2, 1)), ((1, 1), (2, 1)), fst.find('def').decorators),
    (((1, 1), (1, 6)), ((1, 1), (1, 6)), fst.find('def').decorators.node_list[0]),
    (((1, 2), (1, 6)), ((1, 1), (1, 5)), fst.find('def').decorators.node_list[0].value),
    (((1, 2), (1, 6)), ((1, 1), (1, 5)), fst.find('def').decorators.node_list[0].value.value),
    (((1, 2), (1, 6)), ((1, 1), (1, 5)), fst.find('def').decorators.node_list[0].value.value[0]),
    (((1, 6), (2, 1)), ((1, 1), (2, 1)), fst.find('def').decorators.node_list[1]),
    (((2, 4), (2, 5)), ((1, 1), (1, 2)), fst.find('def').first_formatting),
    (((2, 4), (2, 5)), ((1, 1), (1, 2)), fst.find('def').first_formatting[0]),
    (((2, 6), (2, 6)), ((1, 1), (1, 1)), fst.find('def').second_formatting),
    (((2, 7), (2, 7)), ((1, 1), (1, 1)), fst.find('def').third_formatting),
    (((2, 7), (2, 11)), ((1, 1), (1, 5)), fst.find('def').arguments),
    (((2, 7), (2, 8)), ((1, 1), (1, 2)), fst.find('def').arguments.node_list[0]),
    (((2, 8), (2, 10)), ((1, 1), (1, 3)), fst.find('def').arguments.node_list[1]),
    (((2, 10), (2, 11)), ((1, 1), (1, 2)), fst.find('def').arguments.node_list[2]),
    (((2, 11), (2, 11)), ((1, 1), (1, 1)), fst.find('def').fourth_formatting),
    (((2, 12), (2, 12)), ((1, 1), (1, 1)), fst.find('def').fifth_formatting),
    (((2, 13), (2, 13)), ((1, 1), (1, 1)), fst.find('def').sixth_formatting),
    (((2, 13), (4, 1)), ((1, 1), (3, 1)), fst.find('def').value),
    (((2, 13), (3, 1)), ((1, 1), (2, 1)), fst.find('def').value.node_list[0]),
    (((3, 1), (3, 5)), ((1, 1), (1, 5)), fst.find('def').value.node_list[1]),
    (((3, 5), (3, 14)), ((1, 1), (1, 10)), fst.find('def').value.node_list[2]),
    (((3, 5), (3, 6)), ((1, 1), (1, 2)), fst.find('def').value.node_list[2].target),
    (((3, 9), (3, 14)), ((1, 1), (1, 6)), fst.find('def').value.node_list[2].value),
    (((3, 9), (3, 10)), ((1, 1), (1, 2)), fst.find('def').value.node_list[2].value.first),
    (((3, 13), (3, 14)), ((1, 1), (1, 2)), fst.find('def').value.node_list[2].value.second),
    (((3, 14), (4, 1)), ((1, 1), (2, 1)), fst.find('def').value.node_list[3])
]


@pytest.mark.parametrize("absolute_bounding_box,bounding_box,node", bounding_boxes)
def test_bounding_box(absolute_bounding_box, bounding_box, node):
    assert absolute_bounding_box == node.absolute_bounding_box, node.dumps()
    assert bounding_box == node.bounding_box, node.dumps()


def test_bounding_box_of_attribute():
    assert ((2, 1), (2, 4)) == red().find("def").get_absolute_bounding_box_of_attribute("def")


def test_bounding_box_of_attribute_no_attribute():
    with pytest.raises(KeyError):
        red().find("def").get_absolute_bounding_box_of_attribute("xxx")


def test_bounding_box_empty():
    tree = RedBaron("a()")
    boxes = tree.find("atomtrailers").value[1].value.absolute_bounding_box
    assert boxes == ((1, 3), (1, 3))


RED = RedBaron("""\
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


def test_bounding_box_with_proxy_list():
    assert ((1, 1), (32, 1)) == RED.absolute_bounding_box
    assert ((1, 1), (32, 1)) == RED.find("class").absolute_bounding_box
    assert ((2, 5), (5, 8)) == RED.find("class").value[0].absolute_bounding_box
    assert ((6, 5), (9, 18)) == RED.find("class").value[1].absolute_bounding_box
    assert ((10, 1), (10, 1)) == RED.find("class").value[2].absolute_bounding_box
    assert ((11, 5), (17, 1)) == RED.find("class").value[3].absolute_bounding_box
    assert ((17, 1), (17, 1)) == RED.find("class").value[4].absolute_bounding_box
    assert ((18, 5), (18, 17)) == RED.find("class").value[5].absolute_bounding_box
    assert ((19, 1), (19, 1)) == RED.find("class").value[6].absolute_bounding_box
    assert ((20, 5), (27, 1)) == RED.find("class").value[7].absolute_bounding_box
    assert ((27, 1), (27, 1)) == RED.find("class").value[8].absolute_bounding_box
    assert ((28, 5), (31, 18)) == RED.find("class").value[9].absolute_bounding_box
    with pytest.raises(IndexError):
        RED.find("class").value[10]  # pylint: disable=expression-not-assigned
