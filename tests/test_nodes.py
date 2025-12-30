from baron.render import nodes_rendering_order

from redbaron import RedBaron
from redbaron.base_nodes import NodeRegistration


def test_all_baron_types_are_mapped():
    for node_type in nodes_rendering_order:
        assert NodeRegistration.class_from_baron_type(node_type)


def test_try_except_endl():
    red = RedBaron("""
try:
    pass
except:
    pass
""")[0]
    assert red.endl
