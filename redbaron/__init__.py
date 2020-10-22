from . import nodes
from .base_nodes import (Node,
                         NodeList)
from .redbaron import RedBaron

DEBUG = False

ipython_behavior = True
force_ipython_behavior = False


def node(source_code: str):
    return Node.generic_from_str(source_code)


def nodelist(source_code: str):
    return NodeList.generic_from_str(source_code)
