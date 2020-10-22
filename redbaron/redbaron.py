from .base_nodes import IterableNode
from .node_mixin import CodeBlockMixin


class RedBaron(CodeBlockMixin, IterableNode):
    def _default_fst(self):
        return {"type": "root", "value": []}

    def __init__(self, source_code: str):
        super().__init__()
        self.value = source_code
