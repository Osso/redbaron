"""Tests for modern Python syntax support (3.10+, 3.11+, 3.12+)."""

from redbaron import RedBaron


class TestPatternMatching:
    """Tests for PEP 634 pattern matching (Python 3.10+)."""

    def test_parse_simple_match(self):
        code = "match x:\n    case 1: pass"
        red = RedBaron(code)
        assert red[0].type == "match"

    def test_parse_match_with_multiple_cases(self):
        code = "match x:\n    case 1: pass\n    case 2: pass"
        red = RedBaron(code)
        assert red[0].type == "match"

    def test_match_subject_property(self):
        red = RedBaron("match x:\n    case _: pass")
        match = red[0]
        assert match.subject.dumps() == "x"

    def test_match_set_subject(self):
        red = RedBaron("match x:\n    case _: pass")
        match = red[0]
        match.subject = "y"
        assert "match y:" in red.dumps()

    def test_find_case_node(self):
        red = RedBaron("match x:\n    case 1: pass")
        case = red.find("case")
        assert case is not None
        assert case.type == "case"

    def test_case_pattern_property(self):
        red = RedBaron("match x:\n    case 1: pass")
        case = red.find("case")
        assert case.pattern is not None

    def test_case_set_pattern(self):
        red = RedBaron("match x:\n    case 1: pass")
        case = red.find("case")
        case.pattern = "2"
        assert "case 2" in red.dumps()

    def test_case_with_guard(self):
        red = RedBaron("match x:\n    case n if n > 0: pass")
        case = red.find("case")
        assert case.guard is not None

    def test_case_set_guard(self):
        red = RedBaron("match x:\n    case n: pass")
        case = red.find("case")
        case.guard = "n > 0"
        assert "if n > 0" in red.dumps()

    def test_case_remove_guard(self):
        red = RedBaron("match x:\n    case n if n > 0: pass")
        case = red.find("case")
        case.guard = ""
        assert case.guard is None

    def test_pattern_as(self):
        red = RedBaron("match x:\n    case [a, b] as pair: pass")
        pattern_as = red.find("pattern_as")
        assert pattern_as is not None
        assert pattern_as.type == "pattern_as"

    def test_pattern_as_set_pattern(self):
        red = RedBaron("match x:\n    case [a, b] as pair: pass")
        pattern = red.find("pattern_as")
        pattern.pattern = "(a, b)"
        assert "(a, b)" in red.dumps()
        assert "as pair" in red.dumps()

    def test_pattern_or(self):
        # Baron uses binary_operator for pattern or expressions
        red = RedBaron("match x:\n    case 1 | 2 | 3: pass")
        case = red.find("case")
        # The pattern is a binary_operator with | value
        assert case.pattern.type == "binary_operator"
        assert case.pattern.value == "|"

    def test_match_case_body(self):
        red = RedBaron("match x:\n    case 1:\n        print('one')")
        case = red.find("case")
        assert len(case.value) > 0

    def test_find_match_node(self):
        red = RedBaron("x = 1\nmatch y:\n    case _: pass\nz = 2")
        matches = red.find_all("match")
        assert len(matches) == 1

    def test_find_all_case_nodes(self):
        red = RedBaron("match x:\n    case 1: pass\n    case 2: pass")
        cases = red.find_all("case")
        assert len(cases) == 2


class TestTypeParameters:
    """Tests for PEP 695 type parameter syntax (Python 3.12+)."""

    def test_type_param_with_bound(self):
        red = RedBaron("def foo[T: int](): pass")
        param = red.find("type_param")
        assert param.bound.dumps() == "int"

    def test_type_param_set_bound(self):
        red = RedBaron("def foo[T: int](): pass")
        param = red.find("type_param")
        param.bound = "str"
        assert "T: str" in red.dumps()

    def test_type_param_remove_bound(self):
        red = RedBaron("def foo[T: int](): pass")
        param = red.find("type_param")
        param.bound = ""
        assert param.bound is None

    def test_type_param_star(self):
        red = RedBaron("def foo[*Ts](): pass")
        param = red.find("type_param_star")
        assert param.type == "type_param_star"
        assert param.name == "Ts"

    def test_type_param_double_star(self):
        red = RedBaron("def foo[**P](): pass")
        param = red.find("type_param_double_star")
        assert param.type == "type_param_double_star"
        assert param.name == "P"


class TestExceptStar:
    """Tests for PEP 654 exception groups (Python 3.11+)."""

    def test_parse_except_star(self):
        code = "try:\n    pass\nexcept* ValueError:\n    pass"
        red = RedBaron(code)
        assert red[0].type == "try"

    def test_except_star_node_type(self):
        red = RedBaron("try:\n    pass\nexcept* ValueError:\n    pass")
        except_node = red[0].excepts[0]
        assert except_node.type == "except_star"

    def test_except_star_exception(self):
        red = RedBaron("try:\n    pass\nexcept* ValueError:\n    pass")
        except_node = red[0].excepts[0]
        assert except_node.exception.dumps() == "ValueError"

    def test_except_star_with_target(self):
        red = RedBaron("try:\n    pass\nexcept* ValueError as e:\n    pass")
        except_node = red[0].excepts[0]
        assert except_node.target.dumps() == "e"

    def test_except_star_set_exception(self):
        red = RedBaron("try:\n    pass\nexcept* ValueError:\n    pass")
        except_node = red[0].excepts[0]
        except_node.exception = "TypeError"
        assert "TypeError" in red.dumps()

    def test_except_star_set_target(self):
        red = RedBaron("try:\n    pass\nexcept* ValueError as e:\n    pass")
        except_node = red[0].excepts[0]
        except_node.target = "exc"
        assert "as exc" in red.dumps()

    def test_multiple_except_star(self):
        code = "try:\n    pass\nexcept* ValueError:\n    pass\nexcept* TypeError:\n    pass"
        red = RedBaron(code)
        assert len(red[0].excepts) == 2
        assert all(e.type == "except_star" for e in red[0].excepts)

    def test_find_except_star(self):
        red = RedBaron("try:\n    pass\nexcept* ValueError:\n    pass")
        excepts = red.find_all("except_star")
        assert len(excepts) == 1


class TestNamedExpr:
    """Tests for PEP 572 walrus operator (Python 3.8+)."""

    def test_parse_named_expr(self):
        code = "if (x := 1): pass"
        red = RedBaron(code)
        assert "x := 1" in red.dumps()

    def test_named_expr_in_condition(self):
        red = RedBaron("if (n := len(a)) > 10: pass")
        named = red.find("named_expr")
        assert named is not None
        assert named.target == "n"

    def test_named_expr_set_value(self):
        red = RedBaron("(x := 1)")
        named = red.find("named_expr")
        named.value = "2"
        assert ":= 2" in red.dumps()

    def test_named_expr_in_comprehension(self):
        red = RedBaron("[y := x for x in range(10)]")
        named = red.find("named_expr")
        assert named is not None


class TestPositionalOnlyMarker:
    """Tests for PEP 570 positional-only parameters (Python 3.8+)."""

    def test_parse_positional_only(self):
        code = "def foo(a, b, /): pass"
        red = RedBaron(code)
        assert "/" in red.dumps()

    def test_positional_only_marker_type(self):
        red = RedBaron("def foo(a, b, /): pass")
        marker = red.find("positional_only_marker")
        assert marker is not None
        assert marker.type == "positional_only_marker"

    def test_positional_only_with_keyword(self):
        code = "def foo(a, /, b): pass"
        red = RedBaron(code)
        assert "/" in red.dumps()
        assert ", b)" in red.dumps()

    def test_positional_only_with_kwargs_marker(self):
        code = "def foo(a, /, *, b): pass"
        red = RedBaron(code)
        assert "/" in red.dumps()
        assert "*" in red.dumps()
