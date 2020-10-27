from redbaron import RedBaron
from redbaron.base_nodes import NodeList
from redbaron.nodes import (CommaNode,
                            DotNode)


def test_node_next():
    red = RedBaron("[1, 2, 3]")
    assert red.next is None
    assert red[0].next is None
    inner = red[0].value
    assert inner[0].next == inner[1]
    assert inner[1].next == inner[2]
    assert inner[2].next is None


def test_node_next_nodelist():
    red = RedBaron("def a():\n    b = 1\ndef c():\n    d = 1")
    first_def, second_def = red.find_all('def')

    assert first_def.next is second_def
    assert second_def.next is None
    assert second_def.next_recursive is None

    first_node_list = first_def.value.node_list
    assert first_node_list[0].next_nodelist == first_node_list[1]
    assert first_node_list[1].next_nodelist == first_node_list[2]
    assert first_node_list[2].next_nodelist == first_node_list[3]
    assert first_node_list[3].next_nodelist is None


def test_node_next_recursive():
    red = RedBaron("def a():\n    b = 1\ndef c():\n    d = 1")
    first_def, second_def = red.find_all('def')

    assert first_def.next is second_def
    assert second_def.next is None
    assert second_def.next_recursive is None

    first_node_list = first_def.value.node_list
    assert first_node_list[0].next == first_node_list[1]
    assert first_node_list[0].next_recursive == first_node_list[1]
    assert first_node_list[1].next == first_node_list[2]
    assert first_node_list[1].next_recursive == first_node_list[2]
    assert first_node_list[2].next == first_node_list[3]
    assert first_node_list[2].next_recursive == first_node_list[3]
    assert first_node_list[3].next is None
    assert first_node_list[3].next_recursive == second_def


def test_node_previous():
    red = RedBaron("[1, 2, 3]")
    assert red.previous is None
    assert red[0].previous is None
    inner = red[0].value.node_list
    assert inner[4].previous == inner[3]
    assert inner[3].previous == inner[2]
    assert inner[2].previous == inner[1]
    assert inner[1].previous == inner[0]
    assert inner[0].previous is None


def test_node_previous_recursive():
    red = RedBaron("def a():\n    b = 1\ndef c():\n    d = 1")
    assert red[0].previous is None
    assert red[0].previous_recursive is None
    first, second = red.find_all('def')
    assert second.previous is first
    inner = second.value.node_list
    assert inner[2].previous == inner[1]
    assert inner[2].previous_recursive == inner[1]
    assert inner[1].previous == inner[0]
    assert inner[1].previous_recursive == inner[0]
    assert inner[0].previous is None
    assert inner[0].previous_recursive == first


def test_node_next_neighbors():
    red = RedBaron("[1, 2, 3]")
    assert list(red[0].value[2].next_neighbors()) == list(red[0].value[3:])


def test_node_previous_neighbors():
    red = RedBaron("[1, 2, 3]")
    assert list(red[0].value.node_list[2].previous_neighbors()) \
        == list(reversed(red[0].value.node_list[:2]))


def test_node_next_intuitive():
    red = RedBaron("[1, 2, 3]")
    assert red[0].value[0].next_intuitive == red[0].node_list[1]


def test_node_previous_intuitive():
    red = RedBaron("[1, 2, 3]")
    assert red[0].value[1].previous_intuitive == red[0].node_list[1]


def test_node_if_ifelseblock_next_intuitive():
    red = RedBaron("if a:\n    pass")
    assert red.find("if").next_intuitive is None
    red = RedBaron("if a:\n    pass\nelse:\n    pass")
    assert red.find("if").next_intuitive is red.find("else")
    red = RedBaron("if a:\n    pass\nchocolat")
    assert red.find("if").next_intuitive is red.find("name", "chocolat")


def test_node_if_ifelseblock_previous_intuitive():
    red = RedBaron("if a:\n    pass")
    assert red.find("if").previous_intuitive is None
    red = RedBaron("chocolat\nif a:\n    pass")
    assert red.find("if").previous_intuitive is red.find("endl")
    red = RedBaron("pouet\nif a:\n    pass\nelif a:\n    pass\nelse:\n    pass")
    assert red.find("else").previous_intuitive is red.find("elif")
    assert red.find("if").previous is None


def test_node_elif_ifelseblock_next_intuitive():
    red = RedBaron("if a:\n    pass\nelif a:\n    pass")
    assert red.find("elif").next_intuitive is None
    red = RedBaron("if a:\n    pass\nelif a:\n    pass\nelse:\n    pass")
    assert red.find("elif").next_intuitive is red.find("else")
    red = RedBaron("if a:\n    pass\nelif a:\n    pass\nchocolat")
    assert red.find("elif").next_intuitive is red.find("name", "chocolat")


def test_node_elif_elifelseblock_previous_intuitive():
    # not a very interesting test
    red = RedBaron("if a:\n    pass\nelif a:\n    pass")
    assert red.find("elif").previous_intuitive is red.find("if")
    red = RedBaron("chocolat\nif a:\n    pass\nelif a:\n    pass")
    assert red.find("elif").previous_intuitive is red.find("if")


def test_node_else_ifelseblock_next_intuitive():
    red = RedBaron("if a:\n    pass\nelse:\n    pass")
    assert red.find("else").next_intuitive is None
    red = RedBaron("if a:\n    pass\nelse:\n    pass\nchocolat")
    assert red.find("else").next_intuitive is red.find("name", "chocolat")


def test_node_else_elseelseblock_previous_intuitive():
    red = RedBaron("if a:\n    pass\nelse:\n    pass")
    assert red.find("else").previous_intuitive is red.find("if")
    red = RedBaron("chocolat\nif a:\n    pass\nelse:\n    pass")
    assert red.find("else").previous_intuitive is red.find("if")


def test_node_if_ifelseblock_outside_next_intuitive():
    red = RedBaron("outside\nif a:\n    pass")
    assert red.endl_.next_intuitive is red.find("if")


def test_node_if_ifelseblock_outside_previous_intuitive():
    red = RedBaron("if a:\n    pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("if")


def test_node_if_ifelseblock_outside_previous_intuitive_elif():
    red = RedBaron("if a:\n    pass\nelif a: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("elif")


def test_node_if_ifelseblock_outside_previous_intuitive_elif_elif():
    red = RedBaron("if a:\n    pass\nelif a: pass\nelif a: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("elif")[1]


def test_node_if_ifelseblock_outside_previous_intuitive_else():
    red = RedBaron("if a:\n    pass\nelse: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("else")


def test_node_trynode_next_intuitive_except():
    red = RedBaron("try: pass\nexcept: pass")
    assert red.find("try").next_intuitive is red.find("except")


def test_node_trynode_next_intuitive_except_else():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass")
    assert red.find("try").next_intuitive is red.find("except")


def test_node_trynode_next_intuitive_except_else_finally():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass\nfinally: pass")
    assert red.find("try").next_intuitive is red.find("except")


def test_node_trynode_next_intuitive_finally():
    red = RedBaron("try: pass\nfinally: pass")
    assert red.find("try").next_intuitive is red.find("finally")


def test_node_exceptnode_next_intuitive_except():
    red = RedBaron("try: pass\nexcept: pass")
    assert red.find("except").next_intuitive is None


def test_node_exceptnode_next_intuitive_except_after():
    red = RedBaron("try: pass\nexcept: pass\nafter")
    assert red.find("except").next_intuitive is red[1]


def test_node_exceptnode_next_intuitive_except_except():
    red = RedBaron("try: pass\nexcept: pass\nexcept: pass")
    assert red.find("except").next_intuitive is red.find("except")[1]


def test_node_exceptnode_next_intuitive_else():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass")
    assert red.find("except").next_intuitive is red.find("else")


def test_node_exceptnode_next_intuitive_except_else():
    red = RedBaron("try: pass\nexcept: pass\nexcept: pass\nelse: pass")
    assert red.find("except").next_intuitive is red.find("except")[1]


def test_node_exceptnode_next_intuitive_finally():
    red = RedBaron("try: pass\nexcept: pass\nfinally: pass")
    assert red.find("except").next_intuitive is red.finally_


def test_node_exceptnode_next_intuitive_else_finally():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass\nfinally: pass")
    assert red.find("except").next_intuitive is red.find("else")


def test_node_exceptnode_previous_intuitive_except():
    red = RedBaron("try: pass\nexcept: pass")
    assert red.find("except").previous_intuitive is red.find("try")


def test_node_exceptnode_previous_intuitive_except_except():
    red = RedBaron("try: pass\nexcept: pass\nexcept: pass")
    assert red.find("except")[1].previous_intuitive is red.find("except")


def test_node_try_elsenode_next_intuitive():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass")
    assert red.find("else").next_intuitive is None


def test_node_try_elsenode_next_intuitive_after():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass\nafter")
    assert red.find("else").next_intuitive is red.find("name", "after")


def test_node_try_elsenode_next_intuitive_finally():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass\nfinally: pass")
    assert red.find("else").next_intuitive is red.finally_


def test_node_try_elsenode_previous_intuitive():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass")
    assert red.find("else").previous_intuitive is red.find("except")


def test_node_finally_next_intuitive():
    red = RedBaron("try: pass\nexcept: pass\nfinally: pass")
    assert red.finally_.next_intuitive is None


def test_node_finally_next_intuitive_after():
    red = RedBaron("try: pass\nexcept: pass\nfinally: pass\nafter")
    assert red.finally_.next_intuitive is red.find("name", "after")


def test_node_finally_previous_intuitive():
    red = RedBaron("try: pass\nfinally: pass\n")
    assert red.finally_.previous_intuitive is red.find("try")


def test_node_finally_previous_intuitive_except():
    red = RedBaron("try: pass\nexcept: pass\nfinally: pass\n")
    assert red.finally_.previous_intuitive is red.find("except")


def test_node_finally_previous_intuitive_excepts():
    red = RedBaron("try: pass\nexcept: pass\nexcept: pass\nfinally: pass\n")
    assert red.finally_.previous_intuitive is red.find("except")[-1]


def test_node_finally_previous_intuitive_except_else():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass\nfinally: pass\n")
    assert red.finally_.previous_intuitive is red.find("else")


def test_node_trynode_outside_next_intuitive():
    red = RedBaron("outside\ntry:\n    pass\nexcept: pass")
    assert red.endl_.next_intuitive is red.find("try")


def test_node_trynode_outside_previous_intuitive_except():
    red = RedBaron("try:\n    pass\nexcept: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("except")


def test_node_trynode_outside_previous_intuitive_except_except():
    red = RedBaron("try:\n    pass\nexcept: pass\nexcept: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("except")[1]


def test_node_trynode_outside_previous_intuitive_except_except_else():
    red = RedBaron("try:\n    pass\nexcept: pass\nexcept: pass\nelse: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("else")


def test_node_trynode_outside_previous_intuitive_except_except_else_finally():
    red = RedBaron("try:\n    pass\nexcept: pass\nexcept: pass\nelse: pass\nfinally: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("finally")


def test_node_trynode_outside_previous_intuitive_except_except_finally():
    red = RedBaron("try:\n    pass\nexcept: pass\nexcept: pass\nfinally: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("finally")


def test_node_trynode_outside_previous_intuitive_finally():
    red = RedBaron("try:\n    pass\nfinally: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("finally")


def test_node_for_next_intuitive():
    red = RedBaron("for a in b: pass")
    assert red.for_.next_intuitive is None


def test_node_for_next_intuitive_after():
    red = RedBaron("for a in b: pass\nafter")
    assert red.for_.next_intuitive is red[1]


def test_node_for_next_intuitive_else_after():
    red = RedBaron("for a in b: pass\nelse: pass\nafter")
    assert red.for_.next_intuitive is red.find("else")


def test_node_for_previous_intuitive_after():
    red = RedBaron("before\nfor a in b: pass\nafter")
    assert red.for_.previous_intuitive is red.endl_


def test_node_for_else_next_intuitive():
    red = RedBaron("for a in b: pass\nelse: pass")
    assert red.find("else").next_intuitive is None


def test_node_for_else_next_intuitive_after():
    red = RedBaron("for a in b: pass\nelse: pass\nafter")
    assert red.find("else").next_intuitive is red[1]


def test_node_for_else_previous_intuitive_after():
    red = RedBaron("before\nfor a in b: pass\nelse: pass\nafter")
    assert red.find("else").previous_intuitive is red.for_


def test_node_fornode_outside_next_intuitive():
    red = RedBaron("outside\nfor a in b:\n    pass\n")
    assert red.endl_.next_intuitive is red.for_


def test_node_fornode_outside_next_intuitive_else():
    red = RedBaron("outside\nfor a in b:\n    pass\nelse: pass")
    assert red.endl_.next_intuitive is red.for_


def test_node_fornode_outside_previous_intuitive():
    red = RedBaron("for a in b:\n    pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.for_


def test_node_fornode_outside_previous_intuitive_else():
    red = RedBaron("for a in b:\n    pass\nelse: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("else")


def test_node_while_next_intuitive():
    red = RedBaron("while a: pass")
    assert red.while_.next_intuitive is None


def test_node_while_next_intuitive_after():
    red = RedBaron("while a: pass\nafter")
    assert red.while_.next_intuitive is red[1]


def test_node_while_next_intuitive_else_after():
    red = RedBaron("while a: pass\nelse: pass\nafter")
    assert red.while_.next_intuitive is red.find("else")


def test_node_while_previous_intuitive_after():
    red = RedBaron("before\nwhile a: pass\nafter")
    assert red.while_.previous_intuitive is red.endl_


def test_node_while_else_next_intuitive():
    red = RedBaron("while a in b: pass\nelse: pass")
    assert red.find("else").next_intuitive is None


def test_node_while_else_next_intuitive_after():
    red = RedBaron("while a in b: pass\nelse: pass\nafter")
    assert red.find("else").next_intuitive is red[1]


def test_node_while_else_previous_intuitive_after():
    red = RedBaron("bewhilee\nwhile a in b: pass\nelse: pass\nafter")
    assert red.find("else").previous_intuitive is red.while_


def test_node_whilenode_outside_next_intuitive():
    red = RedBaron("outside\nwhile a:\n    pass\n")
    assert red.endl_.next_intuitive is red.while_


def test_node_whilenode_outside_next_intuitive_else():
    red = RedBaron("outside\nwhile a:\n    pass\nelse: pass")
    assert red.endl_.next_intuitive is red.while_


def test_node_whilenode_outside_previous_intuitive():
    red = RedBaron("while a:\n    pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.while_


def test_node_whilenode_outside_previous_intuitive_else():
    red = RedBaron("while a:\n    pass\nelse: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("else")


def test_filtered_endl():
    red = RedBaron("while a:\n    pass\n")
    assert red[0].value.node_list.filtered() == (red[0].value.node_list[-2],)


def test_filtered_comma():
    red = RedBaron("[1, 2, 3]")
    assert red[0].value.filtered() \
        == tuple(red[0].value.filter(lambda x: not isinstance(x, CommaNode)))


def test_filtered_dot():
    red = RedBaron("a.b.c(d)")
    assert red[0].value.filtered() \
        == tuple(red[0].value.filter(lambda x: not isinstance(x, DotNode)))


def test_filter():
    red = RedBaron("[1, 2, 3]")
    assert red[0].value.filter(lambda x: x.type != "comma") == red.find("int")
    assert isinstance(red[0].value.filter(lambda x: x.type != "comma"), NodeList)
