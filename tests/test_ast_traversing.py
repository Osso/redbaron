from redbaron import RedBaron, node


def test_node_next_neighbors():
    red = node("[1, 2, 3]")
    assert list(red[2].next_neighbors) == list(red[3:])


def test_node_previous_neighbors():
    red = node("[1, 2, 3]")
    assert list(red[2].previous_neighbors) == list(reversed(red[:2]))


def test_node_next():
    red = RedBaron("[1, 2, 3]")
    assert red.next is None
    assert red[0].next is None
    node_list = red[0].value
    assert node_list[0].next == node_list[1]
    assert node_list[1].next == node_list[2]
    assert node_list[2].next is None


def test_node_previous():
    red = RedBaron("[1, 2, 3]")
    assert red.previous is None
    assert red[0].previous is None
    node_list = red[0].value
    assert node_list[2].previous == node_list[1]
    assert node_list[1].previous == node_list[0]
    assert node_list[0].previous is None


def test_node_displayable_next():
    node_list = node("[1, 2, 3]")
    node_list.hide(node_list[1])
    assert node_list[0].displayable_next == node_list[2]
    assert node_list[2].displayable_next is None


def test_node_displayable_previous():
    node_list = node("[1, 2, 3]")
    node_list.hide(node_list[1])
    assert node_list[2].displayable_previous == node_list[0]
    assert node_list[0].displayable_previous is None


def test_node_next_recursive():
    red = RedBaron("def a():\n    b = 1\n    c = 1\ndef c():\n    d = 1")
    first_def, second_def = red.find_all('def')

    assert first_def.next is second_def
    assert second_def.next_recursive is None

    assert first_def[0].next_recursive == first_def[1]
    assert first_def[1].next_recursive == second_def


def test_node_previous_recursive():
    red = RedBaron("def a():\n    b = 1\ndef c():\n    d = 1\n    e = 1\n")
    first_def, second_def = red.find_all('def')

    assert first_def.previous_recursive is None
    assert second_def.previous_recursive is first_def

    assert second_def[0].previous_recursive == first_def
    assert second_def[1].previous_recursive == second_def[0]


def test_node_next_intuitive():
    red = node("[1, 2, 3]")
    assert red[0].next_intuitive == red[1]


def test_node_previous_intuitive():
    red = node("[1, 2, 3]")
    assert red[1].previous_intuitive == red[0]


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
    assert red.find("if").previous_intuitive is red.find("name", "chocolat")
    red = RedBaron("pouet\nif a:\n    pass\nelif a:\n    pass\nelse:\n    pass")
    assert red.find("else").previous_intuitive is red.find("elif")
    assert red.find("elif").previous_intuitive is red.find("if")


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
    assert red.find("name", "outside").next_intuitive is red.find("if")


def test_node_if_ifelseblock_outside_previous_intuitive():
    red = RedBaron("if a:\n    pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("if")


def test_node_if_ifelseblock_outside_previous_intuitive_elif():
    red = RedBaron("if a:\n    pass\nelif a: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("elif")


def test_node_if_ifelseblock_outside_previous_intuitive_elif_elif():
    red = RedBaron("if a:\n    pass\nelif a: pass\nelif a: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find_all("elif")[-1]


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
    assert red.find("except").next_intuitive is red.find_all("except")[1]


def test_node_exceptnode_next_intuitive_else():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass")
    assert red.find("except").next_intuitive is red.find("else")


def test_node_exceptnode_next_intuitive_except_else():
    red = RedBaron("try: pass\nexcept: pass\nexcept: pass\nelse: pass")
    assert red.find("except").next_intuitive is red.find_all("except")[1]


def test_node_exceptnode_next_intuitive_finally():
    red = RedBaron("try: pass\nexcept: pass\nfinally: pass")
    assert red.find("except").next_intuitive is red.find("finally")


def test_node_exceptnode_next_intuitive_else_finally():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass\nfinally: pass")
    assert red.find("except").next_intuitive is red.find("else")


def test_node_exceptnode_previous_intuitive_except():
    red = RedBaron("try: pass\nexcept: pass")
    assert red.find("except").previous_intuitive is red.find("try")


def test_node_exceptnode_previous_intuitive_except_except():
    red = RedBaron("try: pass\nexcept: pass\nexcept: pass")
    assert red.find_all("except")[1].previous_intuitive is red.find("except")


def test_node_try_elsenode_next_intuitive():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass")
    assert red.find("else").next_intuitive is None


def test_node_try_elsenode_next_intuitive_after():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass\nafter")
    assert red.find("else").next_intuitive is red.find("name", "after")


def test_node_try_elsenode_next_intuitive_finally():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass\nfinally: pass")
    assert red.find("else").next_intuitive is red.find("finally")


def test_node_try_elsenode_previous_intuitive():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass")
    assert red.find("else").previous_intuitive is red.find("except")


def test_node_finally_next_intuitive():
    red = RedBaron("try: pass\nexcept: pass\nfinally: pass")
    assert red.find("finally").next_intuitive is None


def test_node_finally_next_intuitive_after():
    red = RedBaron("try: pass\nexcept: pass\nfinally: pass\nafter")
    assert red.find("finally").next_intuitive is red.find("name", "after")


def test_node_finally_previous_intuitive():
    red = RedBaron("try: pass\nfinally: pass\n")
    assert red.find("finally").previous_intuitive is red.find("try")


def test_node_finally_previous_intuitive_except():
    red = RedBaron("try: pass\nexcept: pass\nfinally: pass\n")
    assert red.find("finally").previous_intuitive is red.find("except")


def test_node_finally_previous_intuitive_excepts():
    red = RedBaron("try: pass\nexcept: pass\nexcept: pass\nfinally: pass\n")
    assert red.find("finally").previous_intuitive is red.find_all("except")[-1]


def test_node_finally_previous_intuitive_except_else():
    red = RedBaron("try: pass\nexcept: pass\nelse: pass\nfinally: pass\n")
    assert red.find("finally").previous_intuitive is red.find("else")


def test_node_trynode_outside_next_intuitive():
    red = RedBaron("outside\ntry:\n    pass\nexcept: pass")
    assert red.find("name", "outside").next_intuitive is red.find("try")


def test_node_trynode_outside_previous_intuitive_except():
    red = RedBaron("try:\n    pass\nexcept: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("except")


def test_node_trynode_outside_previous_intuitive_except_except():
    red = RedBaron("try:\n    pass\nexcept: pass\nexcept: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find_all("except")[1]


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
    assert red.find("for").next_intuitive is None


def test_node_for_next_intuitive_after():
    red = RedBaron("for a in b: pass\nafter")
    assert red.find("for").next_intuitive is red[1]


def test_node_for_next_intuitive_else_after():
    red = RedBaron("for a in b: pass\nelse: pass\nafter")
    assert red.find("for").next_intuitive is red.find("else")


def test_node_for_previous_intuitive_after():
    red = RedBaron("before\nfor a in b: pass\nafter")
    assert red.find("for").previous_intuitive is red.find("name", "before")


def test_node_for_else_next_intuitive():
    red = RedBaron("for a in b: pass\nelse: pass")
    assert red.find("else").next_intuitive is None


def test_node_for_else_next_intuitive_after():
    red = RedBaron("for a in b: pass\nelse: pass\nafter")
    assert red.find("else").next_intuitive is red[1]


def test_node_for_else_previous_intuitive_after():
    red = RedBaron("before\nfor a in b: pass\nelse: pass\nafter")
    assert red.find("else").previous_intuitive is red.find("for")


def test_node_fornode_outside_next_intuitive():
    red = RedBaron("outside\nfor a in b:\n    pass\n")
    assert red.find("name", "outside").next_intuitive is red.find("for")


def test_node_fornode_outside_next_intuitive_else():
    red = RedBaron("outside\nfor a in b:\n    pass\nelse: pass")
    assert red.find("name", "outside").next_intuitive is red.find("for")


def test_node_fornode_outside_previous_intuitive():
    red = RedBaron("for a in b:\n    pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("for")


def test_node_fornode_outside_previous_intuitive_else():
    red = RedBaron("for a in b:\n    pass\nelse: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("else")


def test_node_while_next_intuitive():
    red = RedBaron("while a: pass")
    assert red.find("while").next_intuitive is None


def test_node_while_next_intuitive_after():
    red = RedBaron("while a: pass\nafter")
    assert red.find("while").next_intuitive is red[1]


def test_node_while_next_intuitive_else_after():
    red = RedBaron("while a: pass\nelse: pass\nafter")
    assert red.find("while").next_intuitive is red.find("else")


def test_node_while_previous_intuitive_after():
    red = RedBaron("before\nwhile a: pass\nafter")
    assert red.find("while").previous_intuitive is red.find("name", "before")


def test_node_while_else_next_intuitive():
    red = RedBaron("while a in b: pass\nelse: pass")
    assert red.find("else").next_intuitive is None


def test_node_while_else_next_intuitive_after():
    red = RedBaron("while a in b: pass\nelse: pass\nafter")
    assert red.find("else").next_intuitive is red[1]


def test_node_while_else_previous_intuitive_after():
    red = RedBaron("bewhilee\nwhile a in b: pass\nelse: pass\nafter")
    assert red.find("else").previous_intuitive is red.find("while")


def test_node_whilenode_outside_next_intuitive():
    red = RedBaron("outside\nwhile a:\n    pass\n")
    assert red.find("name", "outside").next_intuitive is red.find("while")


def test_node_whilenode_outside_next_intuitive_else():
    red = RedBaron("outside\nwhile a:\n    pass\nelse: pass")
    assert red.find("name", "outside").next_intuitive is red.find("while")


def test_node_whilenode_outside_previous_intuitive():
    red = RedBaron("while a:\n    pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("while")


def test_node_whilenode_outside_previous_intuitive_else():
    red = RedBaron("while a:\n    pass\nelse: pass\nafter")
    assert red.find("name", "after").previous_intuitive is red.find("else")
