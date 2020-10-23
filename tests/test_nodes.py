from redbaron.base_nodes import NodeRegistration

from baron.render import nodes_rendering_order


def test_all_baron_types_are_mapped():
    for node_type in nodes_rendering_order:
        assert NodeRegistration.class_from_baron_type(node_type)
