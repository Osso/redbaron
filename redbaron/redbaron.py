from .base_nodes import IterableNode
from .node_mixin import CodeBlockMixin


class RedBaron(CodeBlockMixin, IterableNode):
    def _default_fst(self):
        return {"type": "root", "value": []}

    def __init__(self, source_code: str):
        super().__init__(on_attribute="root")
        self.value = source_code


def node(source_code: str):
    tree = RedBaron(source_code)
    if len(tree) == 1:
        return tree[0]
    return tree
