from . import nodes as nodes
from .base_nodes import Node, NodeList
from .redbaron import RedBaron as RedBaron

DEBUG = False
FORCE_IPYTHON_BEHAVIOR = False


def node(source_code: str):
    return Node.generic_from_str(source_code)


def nodelist(source_code: str):
    return NodeList.generic_from_str(source_code)
