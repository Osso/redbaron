from redbaron.nodes import (RawStringNode,
                            SpaceNode)


def test_redbaron_classname_to_baron_type():
    assert SpaceNode.baron_type == 'space'
    assert SpaceNode().type == 'space'
    assert RawStringNode.baron_type == 'raw_string'
