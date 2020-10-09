from redbaron import nodes
from redbaron.base_nodes import *
from redbaron.nodes import *
from redbaron.redbaron import *
from redbaron.utils import *

DEBUG = False
ALL_IDENTIFIERS = set()

ipython_behavior = True
force_ipython_behavior = False


for name in list(filter(lambda x: x.endswith("Node"), dir(nodes))):
    list(map(ALL_IDENTIFIERS.add, filter(None, getattr(nodes, name).generate_identifiers())))
