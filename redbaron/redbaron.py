from .base_nodes import Node
from .node_mixin import CodeBlockMixin, ValueIterableMixin


class RedBaron(CodeBlockMixin, ValueIterableMixin, Node):
    baron_type = "root"

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

    @property
    def value_on_new_line(self):
        return True
