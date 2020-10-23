from .base_nodes import IterableNode
from .node_mixin import CodeBlockMixin


class RedBaron(CodeBlockMixin, IterableNode):
    _baron_type = "root"

    def _default_fst(self):
        return {"type": "root", "value": []}

    def __init__(self, source_code: str):
        super().__init__()
        self.value = source_code

    @property
    def indentation(self):
        return ""

    @indentation.setter
    def indentation(self, value):
        if self.on_attribute:
            raise ValueError("Unhandled indentation on root")
